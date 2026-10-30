from dataclasses import FrozenInstanceError, asdict

import pytest

from support_agent.schemas import ModelCallError, ModelResult


def settings(**changes):
    from support_agent.config import ConnectionSettings
    return ConnectionSettings(**{'api_key':'synthetic-user-key','model':'deepseek-flash',**changes})


def test_connection_settings_normalize_without_exposing_secret_and_are_frozen():
    connection=settings(api_key='  synthetic-user-key  ',model=' deepseek-flash ',base_url='https://api.deepseek.com/v1/')
    assert connection.api_key=='synthetic-user-key'
    assert connection.model=='deepseek-flash'
    assert connection.base_url=='https://api.deepseek.com/v1'
    assert connection.api_key not in repr(connection)
    with pytest.raises(FrozenInstanceError): connection.api_key='changed'


@pytest.mark.parametrize('changes,code',[
    ({'api_key':''},'missing_key'),
    ({'api_key':'key\ninjected'},'invalid_key'),
    ({'api_key':'key with spaces'},'invalid_key'),
    ({'api_key':'key\x80injected'},'invalid_key'),
    ({'api_key':'key\u202einjected'},'invalid_key'),
    ({'api_key':'x'*4097},'invalid_key'),
    ({'model':''},'invalid_model'),
    ({'model':'bad\nmodel'},'invalid_model'),
    ({'model':'x'*101},'invalid_model'),
    ({'base_url':'https://attacker.example'},'invalid_endpoint'),
    ({'base_url':'https://api.deepseek.com.attacker.example'},'invalid_endpoint'),
])
def test_invalid_explicit_settings_fail_with_safe_code(changes,code):
    with pytest.raises(ModelCallError) as error: settings(**changes)
    assert str(error.value)==code


def test_explicit_settings_and_none_never_read_global_configuration(monkeypatch):
    import support_agent.config as config
    from support_agent.model_client import make_gateway
    def forbidden(): raise AssertionError('Global credentials must not be loaded')
    monkeypatch.setattr(config,'load_configuration',forbidden)
    a=make_gateway(settings=settings(api_key='synthetic-user-a',model='model-a'))
    b=make_gateway(settings=settings(api_key='synthetic-user-b',model='model-b'))
    assert (a.api_key,a.model_id)==('synthetic-user-a','model-a')
    assert (b.api_key,b.model_id)==('synthetic-user-b','model-b')
    with pytest.raises(ModelCallError,match='missing_key'): make_gateway(settings=None)
    assert config.readiness_for_settings(None).ready is False
    status=config.readiness_for_settings(settings())
    assert status.ready and status.key_present and status.endpoint_valid
    assert 'synthetic' not in repr(status)


def test_connection_check_uses_one_bounded_synthetic_request_and_closes():
    from support_agent.connection_check import check_connection
    seen=[]
    class Gateway:
        mode='live';model_id='connection-test'
        closed=False
        def generate(self,messages,instructions,schema,budget):
            assert budget.limit==1 and budget.deadline_seconds==15
            assert 0<budget.remaining()<=15
            assert schema is None
            assert len(messages)==1 and messages[0].role=='user'
            assert '连接测试' in messages[0].content
            assert 'synthetic-user-key' not in instructions+messages[0].content
            budget.consume()
            seen.append(1)
            result=ModelResult(text='OK',model_id=self.model_id,input_tokens=10,output_tokens=1)
            budget.record(result)
            return result
        def close(self): self.closed=True
    gateway=Gateway()
    result=check_connection(settings(),gateway_factory=lambda **kwargs:gateway)
    assert result.success is True and result.error_code is None
    assert (result.input_tokens,result.output_tokens)==(10,1)
    assert result.elapsed_ms>=0 and gateway.closed and seen==[1]
    assert 'synthetic-user-key' not in repr(result)
    assert 'text' not in asdict(result)


@pytest.mark.parametrize('error,expected',[
    (ModelCallError('auth'),'auth'),
    (ModelCallError('balance'),'balance'),
    (ModelCallError('timeout'),'timeout'),
    (ModelCallError('invalid_model'),'invalid_model'),
    (ModelCallError('raw synthetic-user-key'),'unavailable'),
    (RuntimeError('raw synthetic-user-key'),'unavailable'),
])
def test_connection_check_never_leaks_errors_or_retries(error,expected):
    from support_agent.connection_check import check_connection
    calls=[]
    class Gateway:
        mode='live'
        closed=False
        def generate(self,*args): calls.append(1);raise error
        def close(self): self.closed=True
    gateway=Gateway()
    result=check_connection(settings(),gateway_factory=lambda **kwargs:gateway)
    assert not result.success and result.error_code==expected
    assert gateway.closed and calls==[1]
    assert 'synthetic-user-key' not in str(asdict(result))


def test_connection_check_missing_settings_never_constructs_gateway():
    from support_agent.connection_check import check_connection
    def forbidden(**kwargs): raise AssertionError('No settings means no factory')
    result=check_connection(None,gateway_factory=forbidden)
    assert result.success is False and result.error_code=='missing_key'


def test_connection_check_passes_exact_snapshot_to_factory():
    from support_agent.connection_check import check_connection
    connection=settings()
    seen=[]
    def factory(**kwargs):
        seen.append(kwargs)
        raise ModelCallError('auth')
    assert check_connection(connection,gateway_factory=factory).error_code=='auth'
    assert seen==[{'settings':connection}]


def test_connection_check_rejects_non_live_gateway_without_generating():
    from support_agent.connection_check import check_connection
    class Gateway:
        mode='mock'
        closed=False
        def generate(self,*args): raise AssertionError('No simulated connection success')
        def close(self): self.closed=True
    gateway=Gateway()
    result=check_connection(settings(),gateway_factory=lambda **kwargs:gateway)
    assert not result.success and result.error_code=='unavailable' and gateway.closed
