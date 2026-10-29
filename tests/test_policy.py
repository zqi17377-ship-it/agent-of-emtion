from support_agent.schemas import Assessment, Decision, SafetySignal, Evidence, SignalClarification
from tests.helpers import signal


def state(**kwargs):
    return Assessment(status='ok', **kwargs)


def test_urgent_action_has_priority():
    from support_agent.policy import choose_action
    assert choose_action(state(safety_signals=[SafetySignal(**signal())], user_goal='listen'), None).action == 'urgent_support'


def test_unknown_is_not_safe():
    from support_agent.policy import choose_action
    d = choose_action(Assessment(status='failed'), None)
    assert d.action == 'clarify'
    assert 'assessment_failed' in d.reason_codes


def test_new_turn_can_escalate():
    from support_agent.policy import choose_action
    assert choose_action(state(safety_signals=[SafetySignal(**signal())]), Decision(action='support')).action == 'urgent_support'


def test_unresolved_signal_not_erased_by_topic_change():
    from support_agent.policy import choose_action
    previous = Decision(action='urgent_support', unresolved_safety=[SafetySignal(**signal())])
    d = choose_action(state(user_goal='listen'), previous)
    assert d.action == 'urgent_support'
    assert len(d.unresolved_safety) == 1


def test_failed_assessment_does_not_clear_urgent_signal():
    from support_agent.policy import choose_action
    previous = Decision(action='urgent_support', unresolved_safety=[SafetySignal(**signal())])
    assert choose_action(Assessment(status='failed'), previous).action == 'urgent_support'


def test_clarification_requires_new_evidence():
    from support_agent.policy import choose_action
    previous = Decision(unresolved_safety=[SafetySignal(**signal())])
    a = state(clarifications=[SignalClarification(signal_id='s1',new_evidence_ids=['missing'],reason='subject_or_context_corrected')])
    assert choose_action(a, previous).unresolved_safety


def test_context_correction_keeps_audit_record():
    from support_agent.policy import choose_action
    previous = Decision(unresolved_safety=[SafetySignal(**signal())],evidence=[Evidence(id='e1',message_id='old',quote='原话',message_index=0)])
    quoted = signal(); quoted['subject'] = 'quoted'; quoted['evidence_ids'] = ['e2']
    a = state(evidence=[Evidence(id='e2',message_id='new',quote='那是电影台词',message_index=2)], safety_signals=[SafetySignal(**quoted)],clarifications=[SignalClarification(signal_id='s1',new_evidence_ids=['e2'],reason='subject_or_context_corrected')])
    d = choose_action(a, previous)
    assert not d.unresolved_safety
    assert len(d.clarification_log) == 1


def test_denial_alone_cannot_clear_previous_signal():
    from support_agent.policy import choose_action
    previous = Decision(unresolved_safety=[SafetySignal(**signal())])
    denied = signal(); denied['assertion'] = 'denied'
    assert choose_action(state(safety_signals=[SafetySignal(**denied)]), previous).action == 'urgent_support'


def test_quoted_signal_does_not_trigger_self_urgent_route():
    from support_agent.policy import choose_action
    s = signal(); s['subject'] = 'quoted'
    assert choose_action(state(safety_signals=[SafetySignal(**s)]), None).action != 'urgent_support'


def test_unresolved_signal_keeps_original_evidence_on_later_turn():
    from support_agent.policy import choose_action
    e=Evidence(id='e1',message_id='m1',quote='我现在不安全')
    previous=choose_action(state(evidence=[e],safety_signals=[SafetySignal(**signal())]),None)
    next_decision=choose_action(state(user_goal='listen'),previous)
    assert next_decision.evidence[0].quote=='我现在不安全'


def test_unrelated_quoted_signal_cannot_clear_urgent_signal():
    from support_agent.policy import choose_action
    previous=Decision(unresolved_safety=[SafetySignal(**signal())])
    unrelated=signal(kind='needs_professional_assessment'); unrelated['subject']='quoted'; unrelated['evidence_ids']=['e2']
    a=state(evidence=[Evidence(id='e2',message_id='new',quote='这是别人说的睡眠问题')],safety_signals=[SafetySignal(**unrelated)],clarifications=[SignalClarification(signal_id='s1',new_evidence_ids=['e2'],reason='subject_or_context_corrected')])
    assert choose_action(a,previous).action=='urgent_support'


def test_failed_assessment_cannot_apply_quoted_correction():
    from support_agent.policy import choose_action
    previous=Decision(unresolved_safety=[SafetySignal(**signal())],evidence=[Evidence(id='e1',message_id='old',quote='原话',message_index=0)])
    quoted=signal(); quoted['subject']='quoted'; quoted['evidence_ids']=['new']
    a=Assessment(status='failed',evidence=[Evidence(id='new',message_id='m',quote='电影台词',message_index=2)],safety_signals=[SafetySignal(**quoted)],clarifications=[SignalClarification(signal_id='s1',new_evidence_ids=['new'],reason='subject_or_context_corrected')])
    d=choose_action(a,previous)
    assert d.action=='urgent_support'
    assert len(d.unresolved_safety)==1


def test_uncertain_urgent_signal_can_be_confirmed():
    from support_agent.policy import choose_action
    old=signal(); old['assertion']='unclear'
    previous=choose_action(state(safety_signals=[SafetySignal(**old)]),None)
    assert previous.action=='clarify'
    assert choose_action(state(safety_signals=[SafetySignal(**signal())]),previous).action=='urgent_support'


def test_stale_quoted_evidence_cannot_clear_later_urgency():
    from support_agent.policy import choose_action
    previous=Decision(unresolved_safety=[SafetySignal(**signal())],evidence=[Evidence(id='e1',message_id='later',quote='当前原话',message_index=2)])
    q=signal(); q['subject']='quoted'; q['evidence_ids']=['earlier']
    a=state(evidence=[Evidence(id='earlier',message_id='old',quote='之前的电影台词',message_index=0)],safety_signals=[SafetySignal(**q)],clarifications=[SignalClarification(signal_id='s1',new_evidence_ids=['earlier'],reason='subject_or_context_corrected')])
    assert choose_action(a,previous).action=='urgent_support'


def test_unrelated_same_kind_quoted_signal_cannot_clear_urgency():
    from support_agent.policy import choose_action
    previous=Decision(unresolved_safety=[SafetySignal(**signal())],evidence=[Evidence(id='e1',message_id='old',quote='原话',message_index=0)])
    q=signal(); q.update(id='different-signal',subject='quoted',evidence_ids=['new'])
    a=state(evidence=[Evidence(id='new',message_id='new',quote='其他角色的引用',message_index=2)],safety_signals=[SafetySignal(**q)],clarifications=[SignalClarification(signal_id='s1',new_evidence_ids=['new'],reason='subject_or_context_corrected')])
    assert choose_action(a,previous).action=='urgent_support'
