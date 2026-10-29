from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Message(StrictModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    role: Literal['user', 'assistant']
    content: str


class Evidence(StrictModel):
    id: str = ''
    message_id: str
    quote: str = Field(min_length=1)
    message_index: int = Field(default=0,ge=0)


class SafetySignal(StrictModel):
    id: str
    kind: Literal['self_harm', 'harm_to_others', 'other_urgent', 'needs_professional_assessment']
    subject: Literal['self', 'other', 'quoted', 'unknown'] = 'unknown'
    timeframe: Literal['current', 'past', 'unknown'] = 'unknown'
    assertion: Literal['reported', 'denied', 'unclear'] = 'unclear'
    current_need: Literal['immediate_support', 'clarify', 'professional_review'] = 'clarify'
    evidence_ids: list[str] = Field(min_length=1)


class SignalClarification(StrictModel):
    signal_id: str
    new_evidence_ids: list[str] = Field(min_length=1)
    reason: Literal['subject_or_context_corrected', 'additional_information']


class Assessment(StrictModel):
    concerns: list[str] = Field(default_factory=list)
    duration: str | None = None
    daily_impact: str | None = None
    user_goal: Literal['listen', 'advice', 'clarify', 'unknown'] = 'unknown'
    evidence: list[Evidence] = Field(default_factory=list)
    safety_signals: list[SafetySignal] = Field(default_factory=list)
    clarifications: list[SignalClarification] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    status: Literal['ok', 'insufficient', 'failed'] = 'insufficient'


Action = Literal['listen', 'clarify', 'support', 'refer', 'urgent_support']


class Decision(StrictModel):
    action: Action = 'clarify'
    reason_codes: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    unresolved_safety: list[SafetySignal] = Field(default_factory=list)
    clarification_log: list[SignalClarification] = Field(default_factory=list)


class EligibilityContext(StrictModel):
    adult_status: Literal['confirmed', 'unknown', 'minor'] = 'unknown'
    language: str = 'zh'
    reported_conditions: list[str] = Field(default_factory=list)
    use_purpose: str = 'synthetic_research'


class KnowledgeCard(StrictModel):
    id: str
    title: str
    content: str
    tags: list[str]
    source_url: str
    source_date: str
    permission_status: Literal['permitted', 'research_only', 'unknown', 'prohibited']
    permission_evidence: str
    review_status: Literal['pending', 'approved', 'rejected'] = 'pending'
    reviewer: str | None = None
    review_date: str | None = None
    applicability: dict[str, str] = Field(default_factory=dict)
    exclusions: list[str] = Field(default_factory=list)


class CheckResult(StrictModel):
    allowed: bool = Field(strict=True)
    reason_codes: list[str] = Field(default_factory=list)


class TurnResult(StrictModel):
    text: str
    action: Action
    source_ids: list[str] = Field(default_factory=list)
    status: Literal['ok', 'fallback', 'error']
    error_code: str | None = None
    metrics: dict = Field(default_factory=dict)


class SessionState(StrictModel):
    messages: list[Message] = Field(default_factory=list)
    previous_decision: Decision | None = None
    eligibility: EligibilityContext = Field(default_factory=EligibilityContext)
    mode: Literal['synthetic_research', 'eligible_pilot'] = 'synthetic_research'


class ModelResult(StrictModel):
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    model_id: str


class ModelCallError(Exception):
    """Safe, finite error code only; never include provider response bodies."""


@dataclass
class CallBudget:
    limit: int = 4
    deadline_seconds: float = 45.0
    attempts: int = 0
    started: float = field(default_factory=monotonic)
    _input_total: int = 0
    _output_total: int = 0
    _recorded: int = 0
    _usage_complete: bool = True

    @property
    def input_tokens(self) -> int | None:
        return self._input_total if self.attempts and self._recorded == self.attempts and self._usage_complete else None

    @property
    def output_tokens(self) -> int | None:
        return self._output_total if self.attempts and self._recorded == self.attempts and self._usage_complete else None

    def remaining(self) -> float:
        return max(0.0, self.deadline_seconds - (monotonic() - self.started))

    def consume(self) -> float:
        if self.attempts >= self.limit:
            raise ModelCallError('budget')
        if self.remaining() <= 0:
            raise ModelCallError('deadline')
        self.attempts += 1
        return min(20.0, self.remaining())

    def record(self, result: ModelResult) -> None:
        # Unreported/failed attempts make a complete total unknowable forever.
        if self._recorded + 1 != self.attempts or result.input_tokens is None or result.output_tokens is None:
            self._usage_complete = False
        self._recorded = self.attempts
        self._input_total += result.input_tokens or 0
        self._output_total += result.output_tokens or 0
