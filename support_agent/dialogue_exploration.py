"""Small, consent-scoped interview plans; dialogue progress is not trait evidence.

Only the builder creates accepted immutable contexts. Plans reuse the existing
assessment, reply and output-check calls; this module has no model or UI access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

from .schemas import InquiryState


_CONTEXT_SEAL = object()
_DOMAINS = ('mbti', 'big_five', 'attachment')
_TOPICS = (
    ('energy', '社交后的恢复方式', (('mbti','EI'),('big_five','extraversion')),
     '最近一次忙完一段事情后的空闲，你实际是怎么度过的？'),
    ('information', '了解新信息的方式', (('mbti','SN'),),
     '最近一次接触不熟悉的任务时，你是怎样开始了解它的？'),
    ('decisions', '做决定时的考虑', (('mbti','TF'),),
     '最近一次难以取舍时，你最后是怎样做出决定的？'),
    ('organization', '安排和推进事情', (('mbti','JP'),('big_five','conscientiousness')),
     '最近一次需要自己安排一件事时，你具体是怎样推进的？'),
    ('cooperation', '意见不同的相处经历', (('big_five','agreeableness'),),
     '最近一次和别人意见不同时，你当时是怎样处理的？'),
    ('stress', '应对计划外的小事', (('big_five','neuroticism'),),
     '最近一次计划外的小事打乱安排后，你实际是怎样应对的？'),
    ('openness', '接触陌生想法或体验', (('big_five','openness'),),
     '最近一次遇到不熟悉的想法或体验时，你具体做了什么？'),
    ('attachment_anxiety', '同一匿名关系中的回应', (('attachment','anxiety'),),
     '在本次选定的这段匿名关系里，最近一次等待对方回应时发生了什么？'),
    ('attachment_avoidance', '同一匿名关系中的靠近与求助', (('attachment','avoidance'),),
     '在本次选定的这段匿名关系里，最近一次需要支持时你实际是怎样处理的？'),
)
_FOLLOWUPS = {
    'behavior': '在你刚提到的那件事里，你实际做了什么？',
    'motivation': '当时对你来说，最主要的考虑是什么？',
    'cross_context': '在另一个不同的场合，有没有能说明你做法的具体小事？',
    'counterexample': '有没有一次你采用了不同做法的具体经历？没有也可以跳过。',
    'relation_scope': '想围绕哪一段匿名关系聊聊？可以只用代号，不需要真实姓名。',
}
_BLOCKING = frozenset(('pause','decline','listen_only','distress'))
_NEXT_STAGE = {
    'event':'behavior', 'behavior':'motivation', 'motivation':'cross_context',
    'cross_context':'counterexample',
}


@dataclass(frozen=True)
class TopicGap:
    topic: str
    label: str
    targets: tuple[str, ...]
    message_count: int = 0
    event_count: int = 0
    context_count: int = 0
    has_counterexample: bool = False
    example_hint: str = ''


@dataclass(frozen=True)
class ExplorationContext:
    context_key: str
    mode: str
    domains: tuple[str, ...]
    gaps: tuple[TopicGap, ...]
    relation_id: str
    subject_scope: str
    _seal: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class InquiryPlan:
    context_key: str
    topic: str
    label: str
    stage: str
    question: str
    targets: tuple[str, ...]
    relation_id: str
    subject_scope: str
    domains: tuple[str, ...]
    gaps: tuple[TopicGap, ...]
    previous_question: str
    current_quote: str
    completed_topics: tuple[str, ...] = ()


def _accepted(context):
    return type(context) is ExplorationContext and context._seal is _CONTEXT_SEAL


def _safe_report(observation, messages):
    report = getattr(observation, 'report', None)
    checker = getattr(observation, 'is_stale', None)
    if report is None or not callable(checker):
        return ()
    try:
        if not checker(messages):
            return tuple(report.observations[:16])
        metadata=getattr(report,'metrics',{})
        if not all(metadata.get(name)==getattr(observation,name,None) for name in
                   ('generation','consent_revision','observation_revision','subject_mode')):
            return ()
        digests=metadata.get('source_digests',{})
        if not isinstance(digests,dict) or not digests:
            return ()
        current={m.id:hashlib.sha256(m.content.encode('utf-8')).hexdigest() for m in messages if m.role=='user'}
        safe=[]
        for item in report.observations[:16]:
            valid=lambda e:e.message_id in current and current[e.message_id]==digests.get(e.message_id)
            support=[e for e in item.evidence if valid(e)]
            counter=[e for e in item.counter_evidence if valid(e)]
            safe.append(item.model_copy(update={'evidence':support,'counter_evidence':counter}))
        return tuple(safe)
    except (AttributeError, TypeError, ValueError):
        return ()


def _coverage(observations, targets, relation_id, users):
    best = (0, 0, 0, False, '')
    for item in observations:
        target = f'{item.domain}:{item.dimension}'
        if target not in targets or item.subject != 'case_narrator' or item.scope != 'habit':
            continue
        if item.domain == 'attachment' and item.relation_id != relation_id:
            continue
        if item.domain != 'attachment' and item.relation_id:
            continue
        valid = [e for e in item.evidence[:12]
                 if e.message_id in users and e.quote.strip() and e.quote in users[e.message_id]]
        counter = [e for e in item.counter_evidence[:12]
                   if e.message_id in users and e.quote.strip() and e.quote in users[e.message_id]]
        candidate = (
            min(3, len({e.message_id for e in valid})),
            min(3, len({e.event_id for e in valid})),
            min(2, len({e.context_kind for e in valid})),
            bool(counter), valid[0].quote[:96] if valid else '',
        )
        # Shared interview examples do not add duplicate evidence across scales.
        if candidate[:3] > best[:3]:
            best = candidate
    return best


def build_exploration_context(observation, messages, *, selected_relation='', subject_mode='synthetic_case'):
    """Build only whitelisted, active research-case context; authorization is UI-owned."""
    mode = getattr(observation, 'mode', 'off')
    if mode not in ('manual','auto') or subject_mode != 'synthetic_case':
        return None
    requested = getattr(observation, 'domains', ())
    if not isinstance(requested, (list, tuple, set, frozenset)):
        return None
    domains = tuple(domain for domain in _DOMAINS if domain in requested)
    if not domains:
        return None
    relations = getattr(observation, 'relations', {})
    relation_id = selected_relation if (
        'attachment' in domains and isinstance(selected_relation, str)
        and len(selected_relation) <= 64 and selected_relation in relations
    ) else ''
    excluded = getattr(observation, 'excluded_keys', ())
    users = {m.id:m.content for m in messages if m.role == 'user'}
    report = _safe_report(observation, messages)
    gaps = []
    for topic, label, dimensions, _ in _TOPICS:
        targets = tuple(f'{domain}:{dimension}' for domain, dimension in dimensions
                        if domain in domains and f'{domain}:{dimension}:{relation_id if domain == "attachment" else ""}' not in excluded)
        if not targets:
            continue
        counts = _coverage(report, targets, relation_id, users)
        gaps.append(TopicGap(topic, label, targets, *counts))
    if not gaps:
        return None
    identity = (getattr(observation,'generation',''), getattr(observation,'consent_revision',0),
                getattr(observation,'observation_revision',0), domains, relation_id, subject_mode,
                tuple(gap.targets for gap in gaps))
    key = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()
    return ExplorationContext(key, mode, domains, tuple(gaps), relation_id,
                              'research_case_narrator', _CONTEXT_SEAL)


def _gap_payload(gap):
    return {
        'topic':gap.topic, 'label':gap.label, 'targets':list(gap.targets),
        'validated_messages':gap.message_count, 'distinct_events':gap.event_count,
        'different_contexts':gap.context_count, 'has_counterexample':gap.has_counterexample,
        'example_hint':gap.example_hint,
        'missing': [name for name, count, required in (
            ('independent_messages',gap.message_count,3), ('different_events',gap.event_count,3),
            ('different_contexts',gap.context_count,2),
        ) if count < required],
    }


def exploration_payload(context, state=None):
    if not _accepted(context):
        return None
    payload = {
        'domains':list(context.domains), 'subject_scope':context.subject_scope,
        'relation_id':context.relation_id, 'gaps':[_gap_payload(g) for g in context.gaps],
        'note':'进度仅指对话阶段；不是性格证据、量表得分或真实用户画像。',
    }
    if state is not None and state.context_key == context.context_key:
        payload['previous_inquiry'] = {
            'topic':state.topic, 'stage':state.stage, 'question':state.last_question[:180],
            'paused':state.paused,
        }
    return payload


def inquiry_plan_payload(plan):
    if type(plan) is not InquiryPlan:
        return None
    return {
        'domains':list(plan.domains), 'subject_scope':plan.subject_scope,
        'topic':plan.topic, 'label':plan.label, 'stage':plan.stage,
        'targets':list(plan.targets), 'relation_id':plan.relation_id,
        'question':plan.question, 'previous_question':plan.previous_question,
        'current_user_quote':plan.current_quote,
        'gaps':[_gap_payload(g) for g in plan.gaps],
    }


def _feedback(assessment, messages):
    latest = next((m for m in reversed(messages) if m.role == 'user'), None)
    quote = assessment.inquiry_quote
    grounded = bool(latest and quote.strip() and quote in latest.content)
    return (assessment.reply_kind, assessment.continuation, assessment.inquiry_topic, quote) if grounded else ('unknown','unknown','','')


def _current_state(state, context):
    return state if state.context_key == context.context_key else InquiryState(context_key=context.context_key,paused=state.paused)


def _completed(state, kind, continuation):
    completed = list(state.completed_topics)
    if state.topic and (continuation in ('skip','switch_topic') or (
        state.stage == 'counterexample' and kind in ('counterexample','none')
    )) and state.topic not in completed:
        completed.append(state.topic)
    return completed


def honor_inquiry_pause(context,state,assessment,messages):
    """A located request to stop takes effect even if reply generation fails."""
    if not _accepted(context) or assessment.status=='failed':
        return state
    _,continuation,_,_=_feedback(assessment,messages)
    if continuation not in _BLOCKING:
        return state
    paused=_current_state(state,context).model_copy(deep=True)
    paused.paused=True
    return paused


def plan_inquiry(context, messages, assessment, decision, state):
    """Choose one neutral question; only located replies advance dialogue stages."""
    if not _accepted(context) or assessment.status == 'failed' or decision.action in ('urgent_support','refer'):
        return None
    if any(s.current_need in ('immediate_support','clarify') and s.kind in ('self_harm','harm_to_others','other_urgent') for s in decision.unresolved_safety):
        return None
    prior = state
    state = _current_state(state, context)
    kind, continuation, requested_topic, quote = _feedback(assessment, messages)
    if assessment.continuation in _BLOCKING or (state.paused and continuation != 'continue'):
        return None
    completed = _completed(state, kind, continuation)
    gaps = [g for g in context.gaps if g.topic not in completed]
    nonrelationship = [g for g in gaps if not g.topic.startswith('attachment_')]
    if not context.relation_id:
        requested_relationship=any(g.topic==requested_topic and g.topic.startswith('attachment_') for g in gaps)
        if nonrelationship and not requested_relationship:
            gaps = nonrelationship
        elif gaps:
            if state.stage == 'relation_scope':
                return None
            return InquiryPlan(context.context_key,'relationship_scope','匿名关系范围','relation_scope',
                               _FOLLOWUPS['relation_scope'],(),'',context.subject_scope,context.domains,
                               context.gaps,state.last_question,quote,tuple(completed))
    if not gaps:
        return None
    by_topic = {g.topic:g for g in gaps}
    # Keep a current event together; explicit switches may select another allowed topic.
    if requested_topic in by_topic and (continuation == 'switch_topic' or not state.topic):
        gap = by_topic[requested_topic]
    elif state.topic in by_topic and continuation not in ('skip','switch_topic'):
        gap = by_topic[state.topic]
    else:
        gap = min(gaps, key=lambda g:(g.message_count,g.event_count,g.context_count))
    stage = 'event'
    changed_relationship = bool(prior.context_key and prior.context_key != context.context_key
                                and prior.relation_id != context.relation_id)
    if gap.topic == state.topic and state.stage and continuation not in ('skip','switch_topic'):
        if kind == 'unknown':
            return None
        stage = _NEXT_STAGE.get(kind, state.stage)
    elif quote and requested_topic == gap.topic and not changed_relationship:
        stage = _NEXT_STAGE.get(kind,'event')
    question = _FOLLOWUPS.get(stage) or next(t[3] for t in _TOPICS if t[0] == gap.topic)
    if question == state.last_question:
        if kind == 'general':
            question = '如果方便，能选刚才提到的一件小事，说说当时实际发生了什么吗？'
        else:
            return None
    return InquiryPlan(context.context_key,gap.topic,gap.label,stage,question,gap.targets,
                       context.relation_id if gap.topic.startswith('attachment_') else '',
                       context.subject_scope,context.domains,context.gaps,state.last_question,quote,tuple(completed))


def advance_inquiry_state(state, context, plan, assessment, messages, *, assistant_message_id=''):
    """Return a new state only after the caller has accepted its visible reply."""
    if not _accepted(context):
        return state
    state = _current_state(state, context).model_copy(deep=True)
    kind, continuation, _, _ = _feedback(assessment, messages)
    if continuation in _BLOCKING:
        state.paused = True
        return state
    if continuation == 'continue':
        state.paused = False
    state.completed_topics = _completed(state, kind, continuation)
    if type(plan) is InquiryPlan and plan.context_key == context.context_key:
        state.topic, state.stage, state.relation_id = plan.topic, plan.stage, plan.relation_id
        state.last_question = plan.question
        state.last_question_message_id = assistant_message_id
        state.completed_topics = list(plan.completed_topics)
    return state
