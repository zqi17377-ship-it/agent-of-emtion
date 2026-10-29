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

    def __post_init__(self):
        object.__setattr__(self, 'messages', tuple(FrozenObservationMessage(**m.model_dump()) for m in self.messages))
        object.__setattr__(self, 'relations', MappingProxyType(dict(self.relations)))
        object.__setattr__(self, 'message_relations', MappingProxyType(dict(self.message_relations)))


def build_snapshot(conversation_id, generation, consent_revision, observation_revision,
                   messages, domains, relations=None, message_relations=None, excluded_keys=()):
    users = tuple(FrozenObservationMessage(**m.model_dump()) for m in messages if m.role == 'user')
    domains = tuple(sorted(set(domains)))
    relations = dict(relations or {})
    message_relations = dict(message_relations or {})
    excluded_keys = _authorized_exclusions(excluded_keys, domains)
    data = dict(conversation_id=conversation_id, generation=generation, consent_revision=consent_revision,
                observation_revision=observation_revision, domains=domains,
                messages=[m.model_dump() for m in users], relations=relations,
                message_relations=message_relations, excluded_keys=excluded_keys)
    fingerprint = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return ObservationSnapshot(conversation_id, generation, consent_revision, observation_revision,
                               domains, users, fingerprint, relations, message_relations, excluded_keys)


class ObservationEvidence(StrictModel):
    message_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    context_kind: str = Field(min_length=1)


class Observation(StrictModel):
    domain: Literal['mbti', 'big_five', 'attachment']
    dimension: str
    direction: Literal['E','I','S','N','T','F','J','P','higher','lower','mixed','unknown'] = 'unknown'
    scope: Literal['habit','state','unclear'] = 'unclear'
    subject: Literal['self','other','quoted','hypothetical','unknown'] = 'unknown'
    relation_id: str = ''
    evidence: list[ObservationEvidence] = Field(default_factory=list)
    counter_evidence: list[ObservationEvidence] = Field(default_factory=list)

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
    valid, seen, quotes = [], set(), set()
    for item in items:
        source = users.get(item.message_id)
        if source is None or not item.quote.strip() or item.quote not in source:
            raise ValueError('invalid citation')
        normalized = ''.join(source.split())
        normalized_quote = ''.join(item.quote.split())
        if normalized in seen or normalized_quote in quotes or not _usable_behavior_quote(item.quote, source):
            continue
        seen.add(normalized)
        quotes.add(normalized_quote)
        valid.append(item)
    return valid


def _guard(item, users, snapshot):
    if item.domain != 'attachment' and item.relation_id:
        raise ValueError('relationship scope is not valid for this domain')
    if item.dimension not in DIMENSIONS[item.domain]:
        raise ValueError('invalid dimension')
    allowed = item.dimension if item.domain == 'mbti' else ('higher','lower')
    if item.direction not in ('unknown','mixed') and item.direction not in allowed:
        raise ValueError('invalid direction')
    evidence = _evidence(item.evidence, users)
    counter = _evidence(item.counter_evidence, users)
    sufficient = (len({e.message_id for e in evidence}) >= 3
                  and len({e.event_id for e in evidence}) >= 3
                  and len({e.context_kind for e in evidence}) >= 2)
    eligible = item.subject == 'self' and item.scope == 'habit'
    if item.domain == 'attachment':
        eligible = eligible and bool(item.relation_id) and item.relation_id in snapshot.relations
        eligible = eligible and all(snapshot.message_relations.get(e.message_id) == item.relation_id
                                    for e in evidence + counter)
    direction = 'unknown'
    if eligible and evidence and counter:
        direction = 'mixed'
    elif eligible and sufficient:
        direction = item.direction
    return item.model_copy(update=dict(evidence=evidence, counter_evidence=counter, direction=direction))


def _schema(domains):
    schema = _Response.model_json_schema()
    definition = schema['$defs']['Observation']['properties']
    definition['domain'] = {'type':'string', 'enum':list(domains)}
    definition['dimension'] = {'type':'string', 'enum':[d for domain in domains for d in DIMENSIONS[domain]]}
    return schema


def analyze_observations(snapshot, gateway, budget: CallBudget) -> ObservationReport:
    """At most one structural/citation repair, using the caller's shared budget."""
    def report(**kwargs):
        return ObservationReport(fingerprint=snapshot.fingerprint, metrics={
            'attempts': budget.attempts, 'input_tokens': budget.input_tokens,
            'output_tokens': budget.output_tokens, 'message_count': len(snapshot.messages),
            'character_count': sum(len(m.content) for m in snapshot.messages)}, **kwargs)

    if any(d not in DIMENSIONS for d in snapshot.domains):
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
    payload = {'messages':[{'id':m.id,'content':m.content} for m in snapshot.messages],
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
            candidate = _Response.model_validate_json(result.text)
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
