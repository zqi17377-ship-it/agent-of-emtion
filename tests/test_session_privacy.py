import pytest


def test_sessions_do_not_share_history_and_clear_removes_decision():
    from support_agent.session import new_session, clear_session
    from support_agent.schemas import Message, Decision
    a,b = new_session(),new_session()
    a.messages.append(Message(role='user',content='PRIVATE'))
    a.previous_decision = Decision(action='refer')
    assert b.messages == [] and b.previous_decision is None
    clear_session(a)
    assert a.messages == [] and a.previous_decision is None


def test_metrics_reject_unlisted_fields(caplog):
    from support_agent.telemetry import record_event
    with pytest.raises(ValueError):
        record_event('turn', {'text':'PRIVATE','key':'SECRET'})
    assert 'PRIVATE' not in caplog.text and 'SECRET' not in caplog.text


def test_logs_exclude_text_and_keys(caplog):
    from support_agent.telemetry import record_event
    with pytest.raises(ValueError):
        record_event('PRIVATE', {'status':'SECRET'})
    assert 'PRIVATE' not in caplog.text
