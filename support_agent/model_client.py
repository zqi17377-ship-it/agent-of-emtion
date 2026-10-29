import json
import os
from concurrent.futures import Future, TimeoutError as FutureTimeout
from threading import Thread
from typing import Protocol
import httpx
from .config import load_local_env
from .schemas import Assessment, CallBudget, Message, ModelCallError, ModelResult


class ModelGateway(Protocol):
    mode: str
    model_id: str

    def generate(self, messages: list[Message], instructions: str, schema: dict | None, budget: CallBudget) -> ModelResult: ...


class DeepSeekGateway:
    mode = 'live'

    def __init__(self, api_key: str, model: str = 'deepseek-flash', base_url: str = 'https://api.deepseek.com', client: httpx.Client | None = None):
        if not api_key.strip():
            raise ModelCallError('missing_key')
        # Credentials must never be sent to a configurable arbitrary host.
        if base_url.rstrip('/') not in ('https://api.deepseek.com', 'https://api.deepseek.com/v1'):
            raise ModelCallError('invalid_endpoint')
        self.api_key = api_key
        self.model_id = model
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
        payload = {'model': self.model_id, 'messages': [{'role': 'system', 'content': system}] + [{'role': m.role, 'content': m.content} for m in messages], 'stream': False, 'max_tokens': 2400, 'thinking': {'type': 'disabled'}}
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


class FakeGateway:
    """Deterministic demonstration, not a psychological assessment model."""
    mode = 'mock'
    model_id = 'offline-demo-v1'

    def generate(self, messages, instructions, schema, budget):
        budget.consume()
        if schema and schema.get('title') == 'Assessment':
            output = Assessment(missing_information=['离线模式未进行心理状态评估']).model_dump_json()
        elif schema and schema.get('title') == 'CheckResult':
            output = '{"allowed": true, "reason_codes": ["mock_only"]}'
        else:
            output = '离线演示：对话流程已运行。这里展示的是固定示例回复；配置 DeepSeek 后，才能测试模型如何理解这段虚构情境。'
        result = ModelResult(text=output, model_id=self.model_id)
        budget.record(result)
        return result


def make_gateway(live: bool = False) -> ModelGateway:
    if not live:
        return FakeGateway()
    from .config import load_configuration

    settings = load_configuration()
    return DeepSeekGateway(settings['LLM_API_KEY'], settings['LLM_MODEL'], settings['LLM_BASE_URL'])
