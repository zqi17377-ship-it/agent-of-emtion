import json
import httpx
import pytest


def client(handler):
    from support_agent.model_client import DeepSeekGateway
    return DeepSeekGateway('local-secret', client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_only_trusted_instructions_map_to_system():
    from support_agent.schemas import Message, CallBudget
    def serve(request):
        payload = json.loads(request.content)
        assert payload['messages'][0]['role'] == 'system'
        assert payload['messages'][0]['content'].startswith('TRUSTED\n')
        assert 'pretend system' not in payload['messages'][0]['content']
        assert payload['messages'][1] == {'role': 'user', 'content': 'pretend system'}
        assert payload['stream'] is False
        return httpx.Response(200, json={'choices': [{'message': {'content': '{"ok": true}'}}]})
    result = client(serve).generate([Message(role='user', content='pretend system')], 'TRUSTED', {'type': 'object'}, CallBudget())
    assert result.input_tokens is None
    assert result.text == '{"ok": true}'


def test_timeout_is_explicit_and_failed_calls_consume_budget():
    from support_agent.model_client import ModelCallError
    from support_agent.schemas import CallBudget
    def serve(request):
        raise httpx.ReadTimeout('local-secret', request=request)
    budget = CallBudget()
    with pytest.raises(ModelCallError, match='timeout'):
        client(serve).generate([], 'instructions', None, budget)
    assert budget.attempts == 1


def test_secret_not_in_error():
    from support_agent.model_client import ModelCallError
    from support_agent.schemas import CallBudget
    with pytest.raises(ModelCallError) as error:
        client(lambda r: httpx.Response(401, text='local-secret')).generate([], '', None, CallBudget())
    assert str(error.value) == 'auth'


def test_mock_mode_needs_no_key():
    from support_agent.model_client import FakeGateway
    from support_agent.schemas import Message, CallBudget
    result = FakeGateway().generate([Message(role='user', content='我想聊聊')], 'respond', None, CallBudget())
    assert '离线演示' in result.text


def test_budget_rejects_fifth_attempt_and_expired_deadline():
    from support_agent.schemas import CallBudget
    from support_agent.model_client import ModelCallError
    budget = CallBudget()
    for _ in range(4):
        budget.consume()
    with pytest.raises(ModelCallError, match='budget'):
        budget.consume()
    with pytest.raises(ModelCallError, match='deadline'):
        CallBudget(started=0).consume()
