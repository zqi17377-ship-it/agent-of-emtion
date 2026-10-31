import json
from concurrent.futures import Future, TimeoutError as FutureTimeout
from threading import Thread
from typing import Literal, Protocol
import httpx
from .schemas import CallBudget, Message, ModelCallError, ModelResult


class ModelGateway(Protocol):
    mode: str
    model_id: str

    def generate(self, messages: list[Message], instructions: str, schema: dict | None, budget: CallBudget) -> ModelResult: ...


class DeepSeekGateway:
    mode = 'live'

    def __init__(self, api_key: str, model: str = 'deepseek-flash', base_url: str = 'https://api.deepseek.com', client: httpx.Client | None = None, *, purpose: Literal['chat', 'observation'] = 'chat'):
        if not api_key.strip():
            raise ModelCallError('missing_key')
        # Credentials must never be sent to a configurable arbitrary host.
        if base_url.rstrip('/') not in ('https://api.deepseek.com', 'https://api.deepseek.com/v1'):
            raise ModelCallError('invalid_endpoint')
        self.api_key = api_key
        self.model_id = model
        self.purpose = purpose
        self.url = base_url.rstrip('/') + '/chat/completions'
        self.client = client

    def _request(self, payload, timeout):
        # A wall-clock bound in addition to HTTPX's per-I/O timeout. No asyncio
        # self-pipe sockets are needed on Windows. A remote request may still be
        # processed/billed after the local caller stops waiting.
        future = Future()
        def send():
            owned = self.client is None
            client = self.client or httpx.Client(follow_redirects=False, trust_env=False)
            try:
                result = client.post(self.url,headers={'Authorization': f'Bearer {self.api_key}'},json=payload,timeout=timeout)
                if not future.cancelled(): future.set_result(result)
            except Exception as error:
                if not future.cancelled(): future.set_exception(error)
            finally:
                if owned: client.close()
        Thread(target=send,daemon=True,name='model-request').start()
        try:
            return future.result(timeout=timeout)
        except FutureTimeout:
            future.cancel()
            raise ModelCallError('timeout') from None

    def generate(self, messages, instructions, schema, budget):
        timeout = budget.consume()
        if sum(len(m.content) for m in messages) > 24000:
            raise ModelCallError('context_limit')
        system = instructions
        if schema is not None:
            system += '\nReturn one JSON object matching this schema; no markdown:\n' + json.dumps(schema, ensure_ascii=False)
        observation = self.purpose == 'observation'
        payload = {'model': self.model_id, 'messages': [{'role': 'system', 'content': system}] + [{'role': m.role, 'content': m.content} for m in messages], 'stream': False, 'max_tokens': 6000 if observation else 2400, 'thinking': {'type': 'disabled'}}
        # Only opt in models documented by DeepSeek's current Thinking Mode
        # guide / Models & Pricing page, including its accepted Flash aliases.
        # Keep configured model IDs and older callers' compatibility unchanged.
        if observation and self.model_id in ('deepseek-flash', 'deepseek-v4-pro', 'deepseek-v4-flash', 'deepseek-v4-flash-vision-exp'):
            payload['thinking'] = {'type': 'enabled'}
            # Reserve bounded time/output for cited final JSON. In live checks
            # high effort could exhaust the report window before final content.
            payload['reasoning_effort'] = 'low'
        if schema is not None:
            payload['response_format'] = {'type': 'json_object'}
        try:
            timeout = min(timeout,budget.remaining())
            if timeout <= 0:
                raise ModelCallError('deadline')
            response = self._request(payload,timeout)
            errors = {401: 'auth', 402: 'balance', 413: 'context_limit', 429: 'rate_limit'}
            if response.status_code != 200:
                raise ModelCallError(errors.get(response.status_code, 'unavailable'))
            data = response.json()
            choice = data['choices'][0]
            text = choice['message']['content']
            if not isinstance(text, str) or not text.strip() or choice.get('finish_reason') in ('length', 'content_filter'):
                raise ModelCallError('invalid_response')
            usage = data.get('usage') or {}
            result = ModelResult(text=text, input_tokens=usage.get('prompt_tokens'), output_tokens=usage.get('completion_tokens'), model_id=self.model_id)
            if budget.remaining() <= 0:
                raise ModelCallError('deadline')
            budget.record(result)
            return result
        except httpx.TimeoutException:
            raise ModelCallError('timeout') from None
        except httpx.HTTPError:
            raise ModelCallError('unavailable') from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise ModelCallError('invalid_response') from None

    def close(self):
        if self.client is not None:
            self.client.close()


_SETTINGS_UNSET = object()


def make_gateway(live: bool = True, *, settings=_SETTINGS_UNSET, purpose: Literal['chat', 'observation'] = 'chat') -> ModelGateway:
    """Create the only supported product gateway; never fall back to a demo."""
    if not live:
        raise ModelCallError('offline_removed')
    from .config import ConnectionSettings, load_configuration

    if settings is _SETTINGS_UNSET:
        local = load_configuration()
        return DeepSeekGateway(local['LLM_API_KEY'], local['LLM_MODEL'], local['LLM_BASE_URL'], purpose=purpose)
    if settings is None: raise ModelCallError('missing_key')
    if not isinstance(settings,ConnectionSettings): raise ModelCallError('invalid_configuration')
    return DeepSeekGateway(settings.api_key,settings.model,settings.base_url,purpose=purpose)
