from .schemas import Decision


def choose_action(assessment, previous):
    if assessment.status == 'failed':
        # No fields from a failed assessment may modify prior trusted state.
        kept = previous.model_copy(deep=True) if previous else Decision()
        kept.action = 'urgent_support' if any(s.current_need == 'immediate_support' and s.assertion == 'reported' for s in kept.unresolved_safety) else 'clarify'
        kept.reason_codes = ['assessment_failed']
        return kept
    active = {s.id: s.model_copy(deep=True) for s in (previous.unresolved_safety if previous else [])}
    log = list(previous.clarification_log) if previous else []
    valid_ids = {e.id for e in assessment.evidence}
    old_ids = {eid for s in active.values() for eid in s.evidence_ids}
    old_evidence = {e.id:e for e in previous.evidence} if previous else {}
    new_evidence = {e.id:e for e in assessment.evidence}
    for correction in assessment.clarifications:
        # Only a specific, evidenced correction of a quoted subject can auto-resolve.
        fresh = set(correction.new_evidence_ids)
        old_signal=active.get(correction.signal_id)
        quoted = old_signal is not None and any(s.id == old_signal.id and s.subject == 'quoted' and s.kind == old_signal.kind and fresh <= set(s.evidence_ids) for s in assessment.safety_signals)
        ordered = bool(old_signal and fresh and fresh <= valid_ids and all(eid in old_evidence for eid in old_signal.evidence_ids))
        if ordered:
            ordered = min(new_evidence[eid].message_index for eid in fresh) > max(old_evidence[eid].message_index for eid in old_signal.evidence_ids)
        if correction.reason == 'subject_or_context_corrected' and correction.signal_id in active and fresh and fresh <= valid_ids and not fresh.intersection(old_ids) and quoted and ordered:
            del active[correction.signal_id]
            log.append(correction)
    for s in assessment.safety_signals:
        if s.subject == 'quoted' or s.assertion == 'denied':
            continue
        previous_signal = active.get(s.id)
        if previous_signal and previous_signal.current_need == 'immediate_support' and previous_signal.assertion == 'reported':
            continue
        active[s.id] = s
    signals = list(active.values())
    if any(s.current_need == 'immediate_support' and s.assertion == 'reported' for s in signals):
        action, reasons = 'urgent_support', ['current_support_need']
    elif assessment.status == 'failed':
        action, reasons = 'clarify', ['assessment_failed']
    elif any(s.current_need == 'clarify' or s.assertion == 'unclear' for s in signals):
        action, reasons = 'clarify', ['unresolved_information']
    elif any(s.current_need == 'professional_review' for s in signals):
        action, reasons = 'refer', ['professional_assessment_needed']
    elif assessment.user_goal == 'listen':
        action, reasons = 'listen', ['user_wants_listening']
    elif assessment.missing_information or assessment.status == 'insufficient' or assessment.user_goal == 'unknown':
        action, reasons = 'clarify', ['missing_information']
    else:
        action, reasons = 'support', ['user_wants_support']
    evidence={e.id:e for e in (previous.evidence if previous else [])}
    evidence.update({e.id:e for e in assessment.evidence})
    return Decision(action=action, reason_codes=reasons, evidence_ids=list(evidence), evidence=list(evidence.values()), unresolved_safety=signals, clarification_log=log)
