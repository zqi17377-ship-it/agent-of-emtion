import pytest
from support_agent.schemas import Message, TurnResult, Decision


def completed(workspace):
    c=workspace.active
    c.state.messages.extend([Message(role='user',content='这是虚构的工作压力案例'),Message(role='assistant',content='愿意听你说说。')])
    result=TurnResult(text='愿意听你说说。',action='listen',status='ok',metrics={'hidden':'INTERNAL'})
    workspace.record_turn(result)
    return c.state.messages[-1].id


def test_workspaces_and_conversations_are_isolated():
    from support_agent.conversations import Workspace
    a,b=Workspace(),Workspace()
    completed(a)
    first=a.active.id
    new=a.new_conversation()
    assert new.state.messages==[] and b.active.state.messages==[]
    assert len(a.items)==2
    a.select(first)
    assert len(a.active.state.messages)==2
    assert a.active.title=='这是虚构的工作压力案例'


def test_clear_removes_feedback_results_and_evidence():
    from support_agent.conversations import Workspace
    w=Workspace(); mid=completed(w)
    w.set_feedback(mid,'helpful')
    w.active.state.previous_decision=Decision(action='refer')
    w.clear_active()
    assert not w.active.state.messages
    assert w.active.state.previous_decision is None
    assert not w.active.results and not w.active.feedback
    assert w.active.last_result is None and w.active.title=='新的对话'


def test_feedback_only_accepts_assistant_messages():
    from support_agent.conversations import Workspace
    w=Workspace(); mid=completed(w)
    w.set_feedback(mid,'not_helpful')
    assert w.active.feedback[mid]=='not_helpful'
    w.set_feedback(mid,None)
    assert mid not in w.active.feedback
    with pytest.raises(ValueError): w.set_feedback(w.active.state.messages[0].id,'helpful')


def test_export_contains_visible_messages_not_internals():
    from support_agent.conversations import Workspace
    w=Workspace(); completed(w)
    exported=w.export_markdown()
    assert '工作压力案例' in exported and '愿意听你说说' in exported
    assert 'INTERNAL' not in exported and 'metrics' not in exported
    assert '虚构' in exported


def test_limit_never_silently_deletes_older_conversations():
    from support_agent.conversations import Workspace
    w=Workspace(); first=w.active.id
    for _ in range(9): w.new_conversation()
    with pytest.raises(ValueError,match='conversation_limit'): w.new_conversation()
    assert len(w.items)==10
    assert w.select(first).id==first


def test_remove_last_conversation_keeps_workspace_usable():
    from support_agent.conversations import Workspace
    w=Workspace(); old=w.active.id
    fresh=w.remove_active()
    assert len(w.items)==1 and fresh.id!=old
    with pytest.raises(KeyError): w.select(old)


def test_rejected_turn_never_overwrites_previous_assistant_result():
    from support_agent.conversations import Workspace
    w=Workspace(); mid=completed(w)
    original=w.active.results[mid]
    rejected=TurnResult(text='上下文过长，本轮未发送。',action='clarify',status='fallback',error_code='context_limit')
    w.record_turn(rejected)
    assert w.active.results[mid] is original
    assert w.active.last_result is rejected
