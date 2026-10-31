"""Finite daemon jobs. Only polling changes visible observation reports."""
from concurrent.futures import Future
from dataclasses import dataclass
from threading import Thread
from .conversation_observation import build_snapshot,analyze_observations
from .schemas import CallBudget,ModelCallError
from .observation_scheduler import eligibility_reason,count_candidates

@dataclass
class ObservationJob:
    snapshot: object
    future: Future

class _AccountedGateway:
    mode='live'
    def __init__(self,factory,reservation,is_current):
        self.factory=factory;self.gateway=None;self.reservation=reservation
        self.is_current=is_current
    def close(self):
        if self.gateway is not None and hasattr(self.gateway,'close'): self.gateway.close()
    def generate(self,*args,**kwargs):
        budget=kwargs.get('budget') or args[-1]
        if budget.remaining()<=0: raise ModelCallError('deadline')
        if budget.attempts>=budget.limit: raise ModelCallError('budget')
        if not self.is_current(): raise ModelCallError('budget')
        if self.gateway is None: self.gateway=self.factory()
        if not self.is_current(): raise ModelCallError('budget')
        self.reservation.commit()
        result=self.gateway.generate(*args,**kwargs)
        ledger=self.reservation.ledger
        with ledger.lock:
            ledger.input_tokens+=result.input_tokens or 0
            ledger.output_tokens+=result.output_tokens or 0
        return result

def start_observation(state,messages,conversation_id,gateway_factory,*,manual,authorized,live,paused):
    with state.lock:
        if eligibility_reason(state,messages,manual=manual,authorized=authorized,live=live,paused=paused): return False
        snapshot=build_snapshot(conversation_id,state.generation,state.consent_revision,state.observation_revision,
                                messages,state.domains,state.relations,state.message_relations,state.excluded_keys,
                                subject_mode=getattr(state,'subject_mode','self'))
        reservation=state.ledger.reserve(2)
        if reservation is None: return False
        state.conversation_id=conversation_id
        state.attempted_fingerprints.add(snapshot.fingerprint)
        if not manual:
            state.automatic_count+=1
            state.last_auto_candidate_count=count_candidates(messages)[0]
        future=Future();state.pending_job=ObservationJob(snapshot,future)
    def is_current():
        with state.lock:
            return _snapshot_is_current(state,snapshot)
    def run():
        gateway=None;result=None;failure=None
        try:
            budget=CallBudget(limit=reservation.remaining,deadline_seconds=90,max_request_seconds=45)
            gateway=_AccountedGateway(gateway_factory,reservation,is_current)
            result=analyze_observations(snapshot,gateway,budget)
        except Exception as error:
            code=str(error) if isinstance(error,ModelCallError) and str(error) in ('timeout','deadline','budget','auth','balance','rate_limit','missing_key','invalid_endpoint') else 'unavailable'
            failure=ModelCallError(code)
        finally:
            reservation.release()
            if gateway is not None and hasattr(gateway,'close'):
                try: gateway.close()
                except Exception: pass
            if failure is not None: future.set_exception(failure)
            else: future.set_result(result)
    Thread(target=run,daemon=True,name='observation-job').start()
    return True

def poll_observation(state,messages,*,authorized,live,paused):
    with state.lock:
        job=state.pending_job
        if job is None or not job.future.done(): return False
        state.pending_job=None
        snapshot=job.snapshot
        valid=authorized and live and not paused and _snapshot_is_current(state,snapshot)
        current={m.id:m.content for m in messages if m.role=='user'}
        valid=valid and all(current.get(m.id)==m.content for m in snapshot.messages)
        if not valid: return False
        try: report=job.future.result()
        except ModelCallError as error:
            state.error_code=str(error);return True
        if report.status=='failed': state.error_code=report.error_code or 'invalid_response'
        else:
            state.report=report;state.error_code=None
        return True


def _snapshot_is_current(state,snapshot):
    """Compare consent-scoped identity while allowing newly appended messages."""
    if state.mode=='off': return False
    current=build_snapshot(state.conversation_id,state.generation,state.consent_revision,
                           state.observation_revision,snapshot.messages,state.domains,
                           state.relations,state.message_relations,state.excluded_keys,
                           subject_mode=getattr(state,'subject_mode','self'))
    return current.fingerprint==snapshot.fingerprint
