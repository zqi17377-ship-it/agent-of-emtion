"""Consent, deterministic scheduling and per-conversation observation spend."""
from __future__ import annotations
from dataclasses import dataclass, field, replace, is_dataclass
from threading import Lock
from uuid import uuid4
from .conversation_observation import build_snapshot
from .schemas import ModelCallError

AUTO_FIRST_MESSAGES=6
AUTO_FIRST_CHARS=240
AUTO_NEW_MESSAGES=6

@dataclass
class RequestLedger:
    spent: int = 0
    reserved: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    lock: object = field(default_factory=Lock,repr=False)

    def reserve(self, maximum=2):
        with self.lock:
            amount=min(maximum,max(0,6-self.spent-self.reserved))
            if not amount: return None
            self.reserved+=amount
            return Reservation(self,amount)

@dataclass
class Reservation:
    ledger: RequestLedger
    remaining: int

    def commit(self):
        with self.ledger.lock:
            if self.remaining<=0: raise ModelCallError('budget')
            self.remaining-=1
            self.ledger.reserved-=1
            self.ledger.spent+=1

    def release(self):
        with self.ledger.lock:
            self.ledger.reserved-=self.remaining
            self.remaining=0

@dataclass
class ObservationState:
    conversation_id: str = ''
    mode: str = 'off'
    domains: tuple[str,...] = ()
    subject_mode: str = 'self'
    consent_revision: int = 0
    generation: str = field(default_factory=lambda:uuid4().hex)
    observation_revision: int = 0
    report: object | None = None
    error_code: str | None = None
    relations: dict[str,str] = field(default_factory=dict)
    message_relations: dict[str,str] = field(default_factory=dict)
    excluded_keys: set[str] = field(default_factory=set)
    automatic_count: int = 0
    last_auto_candidate_count: int = 0
    attempted_fingerprints: set[str] = field(default_factory=set)
    pending_job: object | None = None
    ledger: RequestLedger = field(default_factory=RequestLedger,repr=False)
    lock: object = field(default_factory=Lock,repr=False)

    @property
    def settings(self): return self
    @property
    def request_count(self):
        with self.ledger.lock: return self.ledger.spent
    @property
    def input_tokens(self):
        with self.ledger.lock: return self.ledger.input_tokens
    @property
    def output_tokens(self):
        with self.ledger.lock: return self.ledger.output_tokens
    @property
    def total_tokens(self): return self.input_tokens+self.output_tokens
    def is_stale(self,messages):
        return self.report is not None and self.report.fingerprint != snapshot_fingerprint(self,messages)

def fresh_observation_state(previous=None):
    if previous is None: return ObservationState()
    # Revoke the old object too: a running worker still holds its reference.
    with previous.lock:
        previous.generation=uuid4().hex
        previous.mode='off'
        previous.report=None
    return ObservationState(ledger=previous.ledger,subject_mode=getattr(previous,'subject_mode','self'),automatic_count=previous.automatic_count,
                            last_auto_candidate_count=previous.last_auto_candidate_count)

def configure_observation(state,mode,domains):
    if mode not in ('off','manual','auto'): raise ValueError('invalid observation mode')
    domains=tuple(sorted(set(domains)))
    if (state.mode,state.domains)==(mode,domains): return
    with state.lock:
        state.mode,state.domains=mode,domains
        state.consent_revision+=1
        state.report=None
        state.error_code=None

def correct_observation(state,key,action):
    if action not in ('delete','state','disagree'): raise ValueError('invalid correction')
    with state.lock:
        state.observation_revision+=1
        state.excluded_keys.add(key)
        if state.report is not None:
            observations=[o for o in state.report.observations if o.key!=key]
            if hasattr(state.report,'model_copy'): state.report=state.report.model_copy(update={'observations':observations})
            elif is_dataclass(state.report): state.report=replace(state.report,observations=observations)
            else: state.report.observations=observations

def count_candidates(messages):
    seen=set(); count=chars=0
    assent={'嗯','嗯嗯','好的','好','是的','对','对的','谢谢','明白','知道了','ok','okay','yes','嗯嗯好的谢谢我知道了'}
    for message in messages:
        if message.role!='user': continue
        text=''.join(message.content.split())
        if text in seen or text.lower() in assent or sum(c.isalnum() for c in text)<5: continue
        seen.add(text); count+=1; chars+=len(text)
    return count,chars

def eligibility_reason(state,messages,*,manual,live,authorized,paused):
    if state.mode=='off': return 'off'
    if not state.domains: return 'no_domains'
    if not authorized: return 'unauthorized'
    if not live: return 'offline'
    if paused: return 'paused'
    if state.pending_job is not None: return 'pending'
    with state.ledger.lock:
        if state.ledger.spent+state.ledger.reserved>=6: return 'budget'
    fingerprint=snapshot_fingerprint(state,messages)
    if fingerprint in state.attempted_fingerprints: return 'unchanged'
    count,chars=count_candidates(messages)
    if manual: return None if count>=2 else 'insufficient'
    if state.mode!='auto': return 'manual_only'
    if state.automatic_count>=3: return 'auto_limit'
    if state.automatic_count and state.last_auto_candidate_count>0:
        return None if count-state.last_auto_candidate_count>=AUTO_NEW_MESSAGES else 'insufficient_new'
    return None if count>=AUTO_FIRST_MESSAGES and chars>=AUTO_FIRST_CHARS else 'insufficient'


def snapshot_fingerprint(state,messages):
    return build_snapshot(state.conversation_id,state.generation,state.consent_revision,state.observation_revision,
                          messages,state.domains,state.relations,state.message_relations,state.excluded_keys,
                          subject_mode=getattr(state,'subject_mode','self')).fingerprint
