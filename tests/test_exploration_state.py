from support_agent.schemas import Message,Decision
from support_agent.personality import PersonalityProfile,user_fingerprint


def test_personality_isolated_and_clear_removes_all_exploration_state():
    from support_agent.conversations import Workspace
    a,b=Workspace(),Workspace()
    p=PersonalityProfile()
    a.active.exploration.profile=p
    a.active.exploration.self_answers={'ei_1':'I'}
    a.active.exploration.survey_answers={'test':{'q1':2}}
    assert b.active.exploration.profile is None
    a.new_conversation()
    assert a.active.exploration.profile is None
    a.select(a.items[0].id); a.clear_active()
    assert a.active.exploration.profile is None
    assert a.active.exploration.self_answers=={}
    assert a.active.exploration.survey_answers=={}


def test_only_new_user_text_marks_personality_stale():
    from support_agent.exploration_state import ExplorationState
    messages=[Message(role='user',content='日常偏好示例')]
    s=ExplorationState(profile=PersonalityProfile(fingerprint=user_fingerprint(messages)))
    assert not s.is_stale(messages)
    messages.append(Message(role='assistant',content='回复'))
    assert not s.is_stale(messages)
    messages.append(Message(role='user',content='新的日常例子'))
    assert s.is_stale(messages)


def test_failed_analysis_keeps_previous_profile_and_safe_error():
    from support_agent.exploration_state import ExplorationState
    old=PersonalityProfile()
    s=ExplorationState(profile=old)
    s.record_profile(PersonalityProfile(status='failed',error_code='timeout'))
    assert s.profile is old
    assert s.profile_error=='timeout'


def test_personality_export_distinguishes_self_confirmation_and_omits_hash():
    from support_agent.exploration_state import ExplorationState,export_personality_report
    s=ExplorationState(profile=PersonalityProfile(fingerprint='INTERNAL_HASH'))
    s.confirmations={'EI':'I','SN':'N','TF':'T','JP':'J'}
    report=export_personality_report(s,[])
    assert 'INTJ' in report and '自行确认' in report
    assert 'INTERNAL_HASH' not in report and 'fingerprint' not in report


def test_immediate_support_pauses_exploration():
    from support_agent.exploration_state import exploration_paused
    assert exploration_paused(Decision(action='urgent_support'))
    assert not exploration_paused(Decision(action='listen'))
