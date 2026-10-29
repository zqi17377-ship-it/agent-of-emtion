"""Evidence-bound, non-clinical exploration of conversational preferences."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Literal, TYPE_CHECKING

from pydantic import Field, ValidationError, field_validator, model_validator

from .schemas import CallBudget, Message, ModelCallError, StrictModel

if TYPE_CHECKING:
    from .model_client import ModelGateway


AxisName = Literal['EI', 'SN', 'TF', 'JP']
Leaning = Literal['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P', 'unknown', 'mixed']
Coverage = Literal['none', 'limited', 'supported', 'conflicting']
PersonalityErrorCode = Literal[
    'invalid_input', 'context_limit', 'invalid_response', 'auth', 'balance',
    'rate_limit', 'timeout', 'deadline', 'budget', 'unavailable', 'missing_key',
    'invalid_endpoint',
]

_AXES: tuple[AxisName, ...] = ('EI', 'SN', 'TF', 'JP')
_SAFE_ERRORS = frozenset((
    'invalid_input', 'context_limit', 'invalid_response', 'auth', 'balance',
    'rate_limit', 'timeout', 'deadline', 'budget', 'unavailable', 'missing_key',
    'invalid_endpoint',
))
_TYPE_CODE = re.compile(r'(?<![A-Za-z0-9])[EI][SN][TF][JP](?![A-Za-z0-9])', re.IGNORECASE)


class PersonalityEvidence(StrictModel):
    message_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class PersonalityAxis(StrictModel):
    axis: AxisName
    leaning: Leaning = 'unknown'
    evidence: list[PersonalityEvidence] = Field(default_factory=list)
    counter_evidence: list[PersonalityEvidence] = Field(default_factory=list)
    explanation: str = ''
    coverage: Coverage = 'none'

    @model_validator(mode='after')
    def pole_belongs_to_axis(self):
        if self.leaning not in ('unknown', 'mixed') and self.leaning not in self.axis:
            raise ValueError('pole does not belong to axis')
        return self


def _empty_axes() -> list[PersonalityAxis]:
    return [PersonalityAxis(axis=axis, explanation='尚无足够的日常例子，暂不判断这一偏好。') for axis in _AXES]


class _PersonalityAnalysis(StrictModel):
    axes: list[PersonalityAxis] = Field(min_length=4, max_length=4)

    @field_validator('axes')
    @classmethod
    def exactly_four_axes(cls, axes):
        by_name = {axis.axis: axis for axis in axes}
        if len(by_name) != 4 or set(by_name) != set(_AXES):
            raise ValueError('exactly four distinct axes required')
        return [by_name[name] for name in _AXES]


class PersonalityProfile(_PersonalityAnalysis):
    status: Literal['ok', 'insufficient', 'failed'] = 'insufficient'
    axes: list[PersonalityAxis] = Field(default_factory=_empty_axes, min_length=4, max_length=4)
    fingerprint: str = ''
    message_count: int = Field(default=0, ge=0)
    error_code: PersonalityErrorCode | None = None

    @property
    def type_hint(self) -> str:
        return ''.join(
            axis.leaning if axis.coverage == 'supported' and axis.leaning in axis.axis else '?'
            for axis in self.axes
        )


def _user_data(messages: list[Message]) -> list[dict[str, str]]:
    return [{'id': message.id, 'content': message.content} for message in messages if message.role == 'user']


def user_fingerprint(messages: list[Message]) -> str:
    """Bind a saved exploration to ordered user text, without retaining the text."""
    serialized = json.dumps(_user_data(messages), ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _usable_behavior_quote(quote: str, source: str) -> bool:
    # A letter, a bare label fragment, or punctuation cannot describe a habit.
    if sum(character.isalnum() for character in quote) < 5 or _TYPE_CODE.search(quote):
        return False
    type_spans = [match.span() for match in _TYPE_CODE.finditer(source)]
    start = source.find(quote)
    while start >= 0:
        end = start + len(quote)
        if all(end <= type_start or start >= type_end for type_start, type_end in type_spans):
            return True
        start = source.find(quote, start + 1)
    return False


def _validated_evidence(items: list[PersonalityEvidence], users: dict[str, str]) -> list[PersonalityEvidence]:
    validated = []
    seen = set()
    for item in items:
        if item.message_id not in users or not item.quote.strip() or item.quote not in users[item.message_id]:
            raise ValueError('evidence must be literal user text')
        # Check the quote's location as well as its text: a partial type code
        # must not be reassembled into apparently independent axis evidence.
        if not _usable_behavior_quote(item.quote, users[item.message_id]):
            continue
        key = (item.message_id, item.quote)
        if key not in seen:
            validated.append(item)
            seen.add(key)
    return validated


def _guard_axis(axis: PersonalityAxis, users: dict[str, str]) -> PersonalityAxis:
    evidence = _validated_evidence(axis.evidence, users)
    counter_evidence = _validated_evidence(axis.counter_evidence, users)
    distinct_messages = len({item.message_id for item in evidence})
    leaning: Leaning = 'unknown'
    coverage: Coverage = 'limited' if evidence else 'none'
    explanation = '目前只有有限的日常线索，需要更多跨情境的例子。' if evidence else '尚无足够的日常例子，暂不判断这一偏好。'

    if counter_evidence:
        # Conflicting user accounts remain visible even when supporting data is sparse.
        leaning, coverage = 'mixed', 'conflicting'
        explanation = '原话中存在不同方向的线索，可能随情境变化；请结合这些例子确认自己的习惯。'
    elif distinct_messages >= 2 and axis.leaning in axis.axis:
        leaning, coverage = axis.leaning, 'supported'
        explanation = '至少两条不同消息中的日常例子支持这一偏好，仅供自我探索与确认。'

    # Use a code-authored explanation of verified coverage. A medical claim or
    # treatment suggestion cannot be reliably recognized with a keyword list.
    # The original quotes preserve the context the user can review directly.

    return PersonalityAxis(
        axis=axis.axis, leaning=leaning, evidence=evidence,
        counter_evidence=counter_evidence, explanation=explanation, coverage=coverage,
    )


def analyze_personality(messages: list[Message], gateway: ModelGateway) -> PersonalityProfile:
    """Explore preferences using only verified user quotes and a private call budget.

    This result is independent of psychological assessment and clinical routing.
    Offline mode deliberately has no simulated personality result.
    """
    data = _user_data(messages)
    base = {'fingerprint': user_fingerprint(messages), 'message_count': len(data)}
    if getattr(gateway, 'mode', None) == 'mock' or not any(item['content'].strip() for item in data):
        return PersonalityProfile(**base)
    if sum(len(item['content']) for item in data) > 16000:
        return PersonalityProfile(**base, status='failed', error_code='context_limit')
    users = {item['id']: item['content'] for item in data}
    if len(users) != len(data) or not all(users):
        return PersonalityProfile(**base, status='failed', error_code='invalid_input')

    instructions = (Path(__file__).resolve().parents[1] / 'prompts' / 'personality.md').read_text(encoding='utf-8')
    serialized = [Message(role='user', content=json.dumps(data, ensure_ascii=False, separators=(',', ':')))]
    budget = CallBudget(limit=2, deadline_seconds=40)
    for attempt in range(2):
        try:
            result = gateway.generate(serialized, instructions, _PersonalityAnalysis.model_json_schema(), budget)
        except ModelCallError as error:
            code = str(error)
            return PersonalityProfile(**base, status='failed', error_code=code if code in _SAFE_ERRORS else 'unavailable')
        except Exception:
            # Do not serialize or log unexpected provider exceptions or response bodies.
            return PersonalityProfile(**base, status='failed', error_code='unavailable')
        try:
            candidate = _PersonalityAnalysis.model_validate_json(result.text)
            axes = [_guard_axis(axis, users) for axis in candidate.axes]
            status = 'ok' if any(axis.coverage in ('supported', 'conflicting') for axis in axes) else 'insufficient'
            return PersonalityProfile(**base, axes=axes, status=status)
        except (ValidationError, ValueError, TypeError):
            if attempt == 0:
                # Repair from the original user data only; never echo invalid output.
                instructions += '\n前次输出未通过结构或原话校验。请重新核对四个维度及每条用户原话，只返回符合 schema 的 JSON。'
    return PersonalityProfile(**base, status='failed', error_code='invalid_response')
