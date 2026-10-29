import time
import httpx
import pytest


def test_request_has_wall_clock_deadline():
    from support_agent.model_client import DeepSeekGateway, ModelCallError
    from support_agent.schemas import CallBudget
    def slow(request):
        time.sleep(0.2)
        return httpx.Response(200,json={'choices':[{'message':{'content':'too late'}}]})
    client=httpx.Client(transport=httpx.MockTransport(slow))
    gateway=DeepSeekGateway('test',client=client)
    with pytest.raises(ModelCallError,match='timeout|deadline'):
        gateway.generate([], 'trusted', None, CallBudget(deadline_seconds=0.03))


def test_custom_endpoint_cannot_receive_secret():
    from support_agent.model_client import DeepSeekGateway, ModelCallError
    with pytest.raises(ModelCallError,match='invalid_endpoint'):
        DeepSeekGateway('secret',base_url='https://example.com')
