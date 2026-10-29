from support_agent.schemas import ModelCallError


def test_smoke_does_not_report_fallback_as_success(tmp_path):
    from scripts.live_smoke import run_smoke
    class FailingGateway:
        mode='live'
        model_id='test-model'
        def generate(self,messages,instructions,schema,budget):
            budget.consume()
            raise ModelCallError('auth')
    report=run_smoke(FailingGateway(),tmp_path)
    assert report['success'] is False
    assert report['stages'][0]['error_code']=='auth'
    assert report['result']['status']=='fallback'


def test_smoke_only_uses_fixed_synthetic_input(tmp_path):
    from scripts.live_smoke import run_smoke
    from tests.helpers import FakeGateway
    report=run_smoke(FakeGateway(),tmp_path)
    assert report['gateway_mode']=='mock'
    assert report['success'] is False
    assert report['synthetic'] is True
    assert report['professional_review']=='pending'
