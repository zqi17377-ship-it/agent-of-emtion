import pytest
from support_agent.schemas import Assessment, Decision, Message, CallBudget
from tests.helpers import ScriptedGateway


@pytest.mark.parametrize('text', ['你已经患有抑郁症','我已为你转接医生','保证治愈','请立即停药','来源 [[invented]]'])
def test_unsafe_or_invented_claim_not_released(text):
    from support_agent.guardrails import check_reply
    result=check_reply(text,[],Assessment(),Decision(),[],ScriptedGateway(),CallBudget())
    assert not result.allowed


def test_non_boolean_checker_approval_is_rejected():
    from support_agent.guardrails import check_reply
    result=check_reply('一般倾听',[],Assessment(),Decision(),[],ScriptedGateway({'allowed':'true','reason_codes':[]}),CallBudget())
    assert not result.allowed
