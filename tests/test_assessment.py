from support_agent.schemas import Message, CallBudget
from tests.helpers import ScriptedGateway, assessment, signal


def test_missing_duration_remains_unknown():
    from support_agent.assessment import assess
    m = Message(role='user', content='我睡不好')
    result = assess([m], None, ScriptedGateway(assessment(m)), CallBudget())
    assert result.duration is None


def test_evidence_must_match_user_message():
    from support_agent.assessment import assess
    m = Message(role='user', content='我睡不好')
    invented = assessment(m, evidence=[{'id':'e1','message_id':m.id,'quote':'我有十年病史'}])
    result = assess([m], None, ScriptedGateway(invented, invented), CallBudget())
    assert result.status == 'failed'
    assert not result.safety_signals


def test_invalid_json_returns_failed():
    from support_agent.assessment import assess
    budget = CallBudget()
    result = assess([Message(role='user', content='你好')], None, ScriptedGateway('broken', 'broken'), budget)
    assert result.status == 'failed'
    assert budget.attempts == 2


def test_quoted_other_person_not_treated_as_self():
    from support_agent.assessment import assess
    m = Message(role='user', content='这是电影里的人说的话')
    s = signal(); s['subject'] = 'quoted'
    result = assess([m], None, ScriptedGateway(assessment(m, safety_signals=[s])), CallBudget())
    assert result.safety_signals[0].subject == 'quoted'


def test_denial_is_not_reported_as_positive_assertion():
    from support_agent.assessment import assess
    m = Message(role='user', content='我没有这类想法')
    s = signal(); s['assertion'] = 'denied'
    result = assess([m], None, ScriptedGateway(assessment(m, safety_signals=[s])), CallBudget())
    assert result.safety_signals[0].assertion == 'denied'


def test_conflicting_information_is_retained():
    from support_agent.assessment import assess
    a = Message(role='user', content='昨天说错了，我现在说不清持续了多久')
    result = assess([a], None, ScriptedGateway(assessment(a, missing_information=['持续时间有矛盾'])), CallBudget())
    assert result.missing_information == ['持续时间有矛盾']


def test_unreferenced_clinical_facts_are_rejected():
    from support_agent.assessment import assess
    m = Message(role='user', content='今天工作很忙')
    invented = assessment(m, duration='十年')
    assert assess([m], None, ScriptedGateway(invented, invented), CallBudget()).status == 'failed'
