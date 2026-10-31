"""Consent-scoped conversational observations; literal provenance is not validity."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from pydantic import ConfigDict, Field, ValidationError

from .personality import _usable_behavior_quote
from .schemas import CallBudget, Message, ModelCallError, StrictModel

DIMENSIONS = {
    'mbti': ('EI', 'SN', 'TF', 'JP'),
    'big_five': ('extraversion', 'agreeableness', 'conscientiousness', 'neuroticism', 'openness'),
    'attachment': ('anxiety', 'avoidance'),
}
SAFE_ERRORS = frozenset(('auth','balance','rate_limit','timeout','deadline','budget','unavailable','missing_key','invalid_endpoint'))
SUBJECT_MODES = frozenset(('self', 'synthetic_case'))
MODEL_OBSERVATION_FIELDS = (
    'domain', 'dimension', 'direction', 'scope', 'subject', 'relation_id',
    'evidence', 'counter_evidence',
)
DERIVED_OBSERVATION_FIELDS = frozenset(('coverage', 'tentative_direction', 'coverage_reason'))
Direction = Literal['E','I','S','N','T','F','J','P','higher','lower','mixed','unknown']


class FrozenObservationMessage(Message):
    model_config = ConfigDict(extra='forbid', frozen=True)


def _authorized_exclusions(keys, domains):
    result = []
    for key in keys:
        parts = key.split(':', 2)
        if len(parts) == 3 and parts[0] in domains:
            if parts[0] == 'attachment' or not parts[2]:
                result.append(key)
    return tuple(sorted(set(result)))


@dataclass(frozen=True)
class ObservationSnapshot:
    conversation_id: str
    generation: str
    consent_revision: int
    observation_revision: int
    domains: tuple[str, ...]
    messages: tuple[FrozenObservationMessage, ...]
    fingerprint: str
    relations: Mapping[str, str]
    message_relations: Mapping[str, str]
    excluded_keys: tuple[str, ...] = ()
    subject_mode: Literal['self', 'synthetic_case'] = 'self'

    def __post_init__(self):
        if self.subject_mode not in SUBJECT_MODES:
            raise ValueError('invalid subject mode')
        object.__setattr__(self, 'messages', tuple(FrozenObservationMessage(**m.model_dump()) for m in self.messages))
        object.__setattr__(self, 'relations', MappingProxyType(dict(self.relations)))
        object.__setattr__(self, 'message_relations', MappingProxyType(dict(self.message_relations)))


def build_snapshot(conversation_id, generation, consent_revision, observation_revision,
                   messages, domains, relations=None, message_relations=None, excluded_keys=(),
                   subject_mode='self'):
    if subject_mode not in SUBJECT_MODES:
        raise ValueError('invalid subject mode')
    users = tuple(FrozenObservationMessage(**m.model_dump()) for m in messages if m.role == 'user')
    domains = tuple(sorted(set(domains)))
    relations = dict(relations or {})
    user_ids={m.id for m in users}
    message_relations = {mid:rid for mid,rid in (message_relations or {}).items() if mid in user_ids}
    excluded_keys = _authorized_exclusions(excluded_keys, domains)
    data = dict(conversation_id=conversation_id, generation=generation, consent_revision=consent_revision,
                observation_revision=observation_revision, domains=domains,
                messages=[m.model_dump() for m in users], relations=relations,
                message_relations=message_relations, excluded_keys=excluded_keys,
                subject_mode=subject_mode)
    fingerprint = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return ObservationSnapshot(conversation_id, generation, consent_revision, observation_revision,
                               domains, users, fingerprint, relations, message_relations, excluded_keys,
                               subject_mode)


class ObservationEvidence(StrictModel):
    message_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    context_kind: str = Field(min_length=1)


class Observation(StrictModel):
    domain: Literal['mbti', 'big_five', 'attachment']
    dimension: str
    direction: Direction = 'unknown'
    scope: Literal['habit','state','unclear'] = 'unclear'
    subject: Literal['self','case_narrator','other','quoted','hypothetical','unknown'] = 'unknown'
    relation_id: str = ''
    evidence: list[ObservationEvidence] = Field(default_factory=list)
    counter_evidence: list[ObservationEvidence] = Field(default_factory=list)
    coverage: Literal['none','limited','supported','conflicting','state','out_of_scope'] = 'none'
    tentative_direction: Direction = 'unknown'
    coverage_reason: str = ''

    @property
    def key(self):
        return f'{self.domain}:{self.dimension}:{self.relation_id}'


class ObservationReport(StrictModel):
    status: Literal['ok','insufficient','failed'] = 'insufficient'
    observations: list[Observation] = Field(default_factory=list)
    fingerprint: str = ''
    error_code: str | None = None
    metrics: dict = Field(default_factory=dict)


class _Response(StrictModel):
    observations: list[Observation] = Field(max_length=16)


def _evidence(items, users):
    valid, source_owners, quotes = [], {}, set()
    for item in items:
        source = users.get(item.message_id)
        if source is None or not item.quote.strip() or item.quote not in source:
            raise ValueError('invalid citation')
        normalized = ''.join(source.split())
        normalized_quote = ''.join(item.quote.split())
        if (normalized_quote in quotes
                or normalized in source_owners and source_owners[normalized] != item.message_id
                or not _usable_behavior_quote(item.quote, source)):
            continue
        source_owners[normalized] = item.message_id
        quotes.add(normalized_quote)
        valid.append(item)
    return valid


def _quote_spans(source, quote):
    start = source.find(quote)
    while start >= 0:
        yield start, start + len(quote)
        start = source.find(quote, start + 1)


def _overlaps_support(counter, evidence, users):
    quote = ''.join(counter.quote.split())
    source = ''.join(users[counter.message_id].split())
    for support in evidence:
        other_quote = ''.join(support.quote.split())
        if quote == other_quote:
            return True
        if source == ''.join(users[support.message_id].split()):
            if any(left < other_end and other_start < right
                   for left, right in _quote_spans(source, quote)
                   for other_start, other_end in _quote_spans(source, other_quote)):
                return True
    return False


def _guard(item, users, snapshot):
    if item.domain != 'attachment' and item.relation_id:
        raise ValueError('relationship scope is not valid for this domain')
    if item.dimension not in DIMENSIONS[item.domain]:
        raise ValueError('invalid dimension')
    allowed = item.dimension if item.domain == 'mbti' else ('higher','lower')
    if item.direction not in ('unknown','mixed') and item.direction not in allowed:
        raise ValueError('invalid direction')
    evidence = _evidence(item.evidence, users)
    raw_counter = _evidence(item.counter_evidence, users)
    overlapping_counter = any(_overlaps_support(citation,evidence,users) for citation in raw_counter)
    counter = [citation for citation in raw_counter
               if not _overlaps_support(citation, evidence, users)]
    message_count = len({e.message_id for e in evidence})
    event_count = len({e.event_id for e in evidence})
    context_count = len({e.context_kind for e in evidence})
    sufficient = message_count >= 3 and event_count >= 3 and context_count >= 2
    subject_allowed = (item.subject == 'self'
                       or item.subject == 'case_narrator' and snapshot.subject_mode == 'synthetic_case')
    relation_allowed = True
    if item.domain == 'attachment':
        relation_allowed = bool(item.relation_id) and item.relation_id in snapshot.relations
        relation_allowed = relation_allowed and all(
            snapshot.message_relations.get(e.message_id) == item.relation_id for e in evidence + counter)
    direction = 'unknown'
    tentative = 'unknown'
    counts = f'已核对{message_count}条不同消息、{event_count}个不同事件、{context_count}类情境。'
    if not subject_allowed:
        coverage = 'out_of_scope'
        reason = ('本次只整理可信模式允许的同一叙述主体；他人、引述、假设或主体不明的材料'
                  '不归为该主体的习惯。虚构案例叙述者仅在synthetic_case模式适用。')
    elif not relation_allowed:
        coverage = 'out_of_scope'
        reason = '关系对象尚未明确，或引用未绑定到同一匿名关系；需先核对关系标注。'
    elif not evidence and not counter:
        coverage = 'none'
        reason = '尚无可核对的具体行为原话；类型标签、重复引用及过短片段不作为行为线索。'
    elif item.scope == 'state':
        coverage = 'state'
        reason = '这些原话描述当次或当前处境，保留为状态线索，不据此推定通常习惯或人格方向。'
    elif item.scope != 'habit':
        coverage = 'limited'
        reason = '已有可核对的经历，但尚未区分通常习惯与当次处境；可补充平时及不同情境的例子。'
    elif overlapping_counter:
        coverage = 'limited'
        reason = '支持与反例的引文重复或重叠，需重新核对并拆出独立原话；不据此认定矛盾或单向支持。'
    elif evidence and counter:
        coverage = 'conflicting'
        direction = 'mixed'
        reason = '存在独立的支持与相反原话；需比较情境、动机或角色要求，暂不选择单向趋势。'
    elif not evidence:
        coverage = 'limited'
        reason = '只有相反线索，尚无支持候选方向的具体行为原话；需先核对候选方向与经历。'
    elif item.direction in ('unknown', 'mixed'):
        coverage = 'limited'
        reason = counts + ('未提供独立反例，不能认定矛盾；候选方向仍待核对。'
                           if item.direction == 'mixed' else '候选方向尚不明确，需核对这些经历说明了哪种偏好。')
    elif sufficient:
        coverage = 'supported'
        direction = item.direction
        reason = counts + '满足三消息、三事件、两情境的支持要求，仅表示本次叙述中的趋势。'
    else:
        coverage = 'limited'
        tentative = item.direction
        gaps = []
        if message_count < 3:
            gaps.append('还需不同消息中的经历，至少3条')
        if event_count < 3:
            gaps.append('还需独立事件，至少3个')
        if context_count < 2:
            gaps.append('还需不同情境，至少2类')
        reason = counts + '；'.join(gaps) + '；初步方向不能作为有支持的习惯趋势。'
    return item.model_copy(update=dict(
        evidence=evidence, counter_evidence=counter, direction=direction,
        coverage=coverage, tentative_direction=tentative, coverage_reason=reason,
    ))


def _schema(domains):
    schema = _Response.model_json_schema()
    observation_schema = schema['$defs']['Observation']
    definition = observation_schema['properties']
    for field in DERIVED_OBSERVATION_FIELDS:
        definition.pop(field)
    observation_schema['required'] = list(MODEL_OBSERVATION_FIELDS)
    definition['domain'] = {'type':'string', 'enum':list(domains)}
    definition['dimension'] = {'type':'string', 'enum':[d for domain in domains for d in DIMENSIONS[domain]]}
    return schema


def analyze_observations(snapshot, gateway, budget: CallBudget) -> ObservationReport:
    """At most one structural/citation repair, using the caller's shared budget."""
    def report(**kwargs):
        return ObservationReport(fingerprint=snapshot.fingerprint, metrics={
            'attempts': budget.attempts, 'input_tokens': budget.input_tokens,
            'output_tokens': budget.output_tokens, 'message_count': len(snapshot.messages),
            'character_count': sum(len(m.content) for m in snapshot.messages),
            'source_digests': {m.id:hashlib.sha256(m.content.encode('utf-8')).hexdigest() for m in snapshot.messages},
            'subject_mode':snapshot.subject_mode,'generation':snapshot.generation,
            'consent_revision':snapshot.consent_revision,'observation_revision':snapshot.observation_revision}, **kwargs)

    if any(d not in DIMENSIONS for d in snapshot.domains):
        return report(status='failed', error_code='invalid_input')
    if snapshot.subject_mode not in SUBJECT_MODES:
        return report(status='failed', error_code='invalid_input')
    users = {m.id:m.content for m in snapshot.messages if m.role == 'user'}
    if len(users) != len(snapshot.messages) or not all(users):
        return report(status='failed', error_code='invalid_input')
    if sum(len(t) for t in users.values()) > 16000:
        return report(status='failed', error_code='context_limit')
    if not snapshot.domains or not any(t.strip() for t in users.values()) or getattr(gateway,'mode',None) == 'mock':
        return report()
    instructions = (Path(__file__).resolve().parents[1] / 'prompts/conversation_observation_runtime.md').read_text(encoding='utf-8')
    instructions += '\n本次授权主题与维度：' + json.dumps({d:DIMENSIONS[d] for d in snapshot.domains}, ensure_ascii=False)
    instructions += '\n程序指定的可信主体模式：' + snapshot.subject_mode
    payload = {'messages':[{'id':m.id,'content':m.content} for m in snapshot.messages],
               'subject_mode':snapshot.subject_mode,
               'relations':dict(snapshot.relations) if 'attachment' in snapshot.domains else {},
               'message_relations':dict(snapshot.message_relations) if 'attachment' in snapshot.domains else {},
               'excluded_keys':_authorized_exclusions(snapshot.excluded_keys, snapshot.domains)}
    serialized = [Message(role='user',content=json.dumps(payload, ensure_ascii=False))]
    for attempt in range(2):
        try:
            result = gateway.generate(serialized, instructions, _schema(snapshot.domains), budget)
        except ModelCallError as exc:
            code = str(exc)
            return report(status='failed', error_code=code if code in SAFE_ERRORS else 'unavailable')
        except Exception:
            return report(status='failed', error_code='unavailable')
        try:
            raw = json.loads(result.text)
            if isinstance(raw, dict) and isinstance(raw.get('observations'), list):
                if any(isinstance(o, dict) and 'domain' in o and o['domain'] not in snapshot.domains
                       for o in raw['observations']):
                    return report(status='failed', error_code='invalid_response')
            if isinstance(raw, dict) and isinstance(raw.get('observations'), list):
                for item in raw['observations']:
                    if isinstance(item, dict):
                        if not set(MODEL_OBSERVATION_FIELDS) <= item.keys():
                            raise ValueError('missing observation fields')
                        # Provider-supplied grades are never used as input evidence.
                        for field in DERIVED_OBSERVATION_FIELDS:
                            item.pop(field, None)
            candidate = _Response.model_validate(raw)
            if any(o.domain not in snapshot.domains for o in candidate.observations):
                return report(status='failed', error_code='invalid_response')
            guarded, keys = [], set()
            for item in candidate.observations:
                item = _guard(item, users, snapshot)
                if item.key in keys:
                    raise ValueError('duplicate observation')
                keys.add(item.key)
                if item.key not in snapshot.excluded_keys:
                    guarded.append(item)
            return report(observations=guarded, status='ok' if any(o.direction != 'unknown' for o in guarded) else 'insufficient')
        except (ValidationError, ValueError, TypeError):
            instructions += '\n前次输出未通过结构或原话校验，请仅根据原始材料重新核对并返回JSON。'
    return report(status='failed', error_code='invalid_response')
