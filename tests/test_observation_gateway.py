import json

import httpx
import pytest

from support_agent.model_client import DeepSeekGateway, make_gateway
from support_agent.schemas import CallBudget, Message, ModelCallError


def completion(content='{"ok": true}', *, finish_reason='stop'):
    return httpx.Response(200, json={
        'choices': [{
            'index': 0,
            'finish_reason': finish_reason,
            'message': {
                'role': 'assistant',
                'content': content,
                'reasoning_content': 'private-reasoning-must-not-leave-gateway',
            },
        }],
        'usage': {'prompt_tokens': 10, 'completion_tokens': 20},
    })


@pytest.mark.parametrize('model', [
    'deepseek-flash', 'deepseek-v4-pro',
    'deepseek-v4-flash', 'deepseek-v4-flash-vision-exp',
])
def test_observation_requests_reasoning_and_json_without_changing_model(model):
    seen = []
    def serve(request):
        seen.append(json.loads(request.content))
        return completion()
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        gateway = DeepSeekGateway('test-secret', model=model, client=client, purpose='observation')
        result = gateway.generate([Message(role='user', content='A fictional adult case')], 'Analyze', {'type': 'object'}, CallBudget())
    assert len(seen) == 1
    payload = seen[0]
    assert payload['model'] == result.model_id == model
    assert payload['thinking'] == {'type': 'enabled'}
    assert payload['reasoning_effort'] == 'low'
    assert payload['max_tokens'] == 6000
    assert payload['response_format'] == {'type': 'json_object'}
    assert 'JSON' in payload['messages'][0]['content']
    assert payload['stream'] is False


def test_default_chat_keeps_existing_request_profile():
    seen = []
    def serve(request):
        seen.append(json.loads(request.content))
        return completion()
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        DeepSeekGateway('test-secret', client=client).generate([], 'Chat', None, CallBudget())
    assert seen[0]['thinking'] == {'type': 'disabled'}
    assert seen[0]['max_tokens'] == 2400
    assert 'reasoning_effort' not in seen[0]
    assert 'response_format' not in seen[0]


@pytest.mark.parametrize('model', ['deepseek-chat', 'deepseek-reasoner', 'custom-model'])
def test_observation_does_not_force_new_reasoning_options_on_unknown_or_retired_models(model):
    seen = []
    def serve(request):
        seen.append(json.loads(request.content))
        return completion()
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        result = DeepSeekGateway('test-secret', model=model, client=client, purpose='observation').generate([], 'Analyze', None, CallBudget())
    assert seen[0]['model'] == result.model_id == model
    assert seen[0]['max_tokens'] == 6000
    assert seen[0]['thinking'] == {'type': 'disabled'}
    assert 'reasoning_effort' not in seen[0]


def test_observation_returns_only_final_content_and_never_resends_reasoning(capsys, caplog):
    seen = []
    def serve(request):
        seen.append(json.loads(request.content))
        return completion()
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        gateway = DeepSeekGateway('test-secret', client=client, purpose='observation')
        first = gateway.generate([], 'Analyze', None, CallBudget())
        second = gateway.generate([Message(role='assistant', content=first.text)], 'Analyze', None, CallBudget())
    assert first.text == second.text == '{"ok": true}'
    assert first.model_dump() == {'text': '{"ok": true}', 'input_tokens': 10, 'output_tokens': 20, 'model_id': 'deepseek-flash'}
    captured = capsys.readouterr()
    public_output = json.dumps(seen) + first.model_dump_json() + repr(gateway.__dict__) + captured.out + captured.err + caplog.text
    assert 'private-reasoning-must-not-leave-gateway' not in public_output
    assert 'reasoning_content' not in public_output


@pytest.mark.parametrize('content,finish_reason', [
    ('{"ok": true}', 'length'),
    ('{"ok": true}', 'content_filter'),
    ('   ', 'stop'),
    (None, 'stop'),
])
def test_observation_rejects_truncated_or_missing_final_content_without_retry(content, finish_reason):
    seen = []
    def serve(request):
        seen.append(request)
        return completion(content, finish_reason=finish_reason)
    budget = CallBudget(limit=2)
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        gateway = DeepSeekGateway('test-secret', client=client, purpose='observation')
        with pytest.raises(ModelCallError, match='^invalid_response$'):
            gateway.generate([], 'Analyze', {'type': 'object'}, budget)
    assert len(seen) == budget.attempts == 1
    assert budget.output_tokens is None


def test_factory_passes_observation_profile_for_explicit_and_local_settings(monkeypatch):
    from support_agent import config
    from support_agent.config import ConnectionSettings
    monkeypatch.setattr(config, 'load_configuration', lambda: {
        'LLM_API_KEY': 'local-test-secret', 'LLM_MODEL': 'deepseek-flash',
        'LLM_BASE_URL': 'https://api.deepseek.com',
    })
    seen = []
    def serve(request):
        seen.append(json.loads(request.content))
        return completion()
    explicit = ConnectionSettings(api_key='explicit-test-secret', model='deepseek-v4-pro')
    for kwargs in ({}, {'settings': explicit}):
        gateway = make_gateway(purpose='observation', **kwargs)
        with httpx.Client(transport=httpx.MockTransport(serve)) as client:
            gateway.client = client
            gateway.generate([], 'Analyze', None, CallBudget())
    assert [p['model'] for p in seen] == ['deepseek-flash', 'deepseek-v4-pro']
    assert all(p['thinking'] == {'type': 'enabled'} for p in seen)


@pytest.mark.parametrize('endpoint', [
    'https://attacker.example', 'https://api.deepseek.com.attacker.example',
    'http://api.deepseek.com', 'https://api.deepseek.com/beta',
])
def test_observation_profile_keeps_official_endpoint_restriction(endpoint):
    with pytest.raises(ModelCallError, match='^invalid_endpoint$'):
        DeepSeekGateway('test-secret', base_url=endpoint, purpose='observation')


@pytest.mark.parametrize('kwargs, expected', [
    ({}, 20.0),
    ({'deadline_seconds': 60, 'max_request_seconds': 30}, 30.0),
    ({'deadline_seconds': 7, 'max_request_seconds': 30}, 7.0),
])
def test_request_timeout_respects_per_request_cap_and_remaining_budget(monkeypatch, kwargs, expected):
    from support_agent import schemas
    monkeypatch.setattr(schemas, 'monotonic', lambda: 100.0)
    budget = CallBudget(started=100.0, **kwargs)
    seen = []
    def serve(request):
        seen.append(request.extensions['timeout'])
        return completion()
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        gateway = DeepSeekGateway('test-secret', client=client)
        gateway.generate([], 'Chat', None, budget)
    assert seen == [{'connect': expected, 'read': expected, 'write': expected, 'pool': expected}]
    assert budget.attempts == 1


def test_observation_budget_keeps_finite_attempt_limit():
    budget = CallBudget(limit=2, deadline_seconds=60, max_request_seconds=30)
    assert 0 < budget.consume() <= 30
    assert 0 < budget.consume() <= 30
    with pytest.raises(ModelCallError, match='^budget$'):
        budget.consume()


@pytest.mark.parametrize('dimension_count,expected',[(2,'low'),(4,'low'),(5,'low'),(11,'low')])
def test_broad_observation_scope_reserves_time_for_final_evidence_output(dimension_count,expected):
    seen=[]
    def serve(request):
        seen.append(json.loads(request.content))
        return completion()
    schema={'type':'object','$defs':{'Observation':{'properties':{'dimension':{'enum':[f'd{i}' for i in range(dimension_count)]}}}}}
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        gateway=DeepSeekGateway('test-secret',client=client,purpose='observation')
        gateway.generate([],'Analyze JSON',schema,CallBudget())
    assert seen[0]['thinking']=={'type':'enabled'}
    assert seen[0]['reasoning_effort']==expected
    assert seen[0]['max_tokens']==6000
