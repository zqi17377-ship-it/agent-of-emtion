import pytest
from support_agent.schemas import Assessment,SafetySignal
from tests.helpers import signal


@pytest.mark.parametrize('status',['ok','insufficient'])
def test_explicit_listening_precedes_optional_unknown_details(status):
    from support_agent.policy import choose_action
    a=Assessment(user_goal='listen',status=status,missing_information=['持续时间未知'])
    assert choose_action(a,None).action=='listen'
    assert a.duration is None


@pytest.mark.parametrize('need,expected',[('immediate_support','urgent_support'),('clarify','clarify'),('professional_review','refer')])
def test_listening_never_overrides_safety_or_professional_need(need,expected):
    from support_agent.policy import choose_action
    s=signal(need=need)
    a=Assessment(user_goal='listen',status='ok',safety_signals=[SafetySignal(**s)])
    assert choose_action(a,None).action==expected


def test_failed_assessment_cannot_become_listening():
    from support_agent.policy import choose_action
    assert choose_action(Assessment(status='failed',user_goal='listen'),None).action=='clarify'
