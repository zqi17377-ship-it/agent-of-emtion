from threading import Event
from types import SimpleNamespace
from time import monotonic,sleep
import pytest
from support_agent.schemas import Message,ModelResult,ModelCallError
from support_agent.observation_scheduler import ObservationState,configure_observation,correct_observation,fresh_observation_state

def messages(n=2):
    return [Message(id=str(i),role='user',content=f'今天事件{i}我和朋友讨论自己工作中遇到的选择和烦恼') for i in range(n)]

class Gateway:
    mode='live'; model_id='test'
    def __init__(self,gate=None,fail=False): self.gate=gate; self.fail=fail; self.closed=False
    def generate(self,messages,instructions,schema,budget):
        budget.consume()
        if self.gate: self.gate.wait(2)
        if self.fail: raise ModelCallError('timeout')
        result=ModelResult(text='{}',model_id='test',input_tokens=10,output_tokens=2)
        budget.record(result); return result
    def close(self): self.closed=True

def setup(monkeypatch,gate=None,fail=False):
    from support_agent import observation_jobs as jobs
    def analyze(snapshot,gateway,budget):
        gateway.generate([], '',None,budget)
        return SimpleNamespace(status='ok',observations=[],fingerprint=snapshot.fingerprint,error_code=None)
    monkeypatch.setattr(jobs,'analyze_observations',analyze)
    s=ObservationState();configure_observation(s,'manual',('mbti',))
    g=Gateway(gate,fail)
    return jobs,s,g

def finish(jobs,s,ms):
    until=monotonic()+3
    while s.pending_job and monotonic()<until:
        jobs.poll_observation(s,ms,authorized=True,live=True,paused=False);sleep(.005)
    assert s.pending_job is None

def start(jobs,s,g,ms):
    return jobs.start_observation(s,ms,'c1',lambda:g,manual=True,authorized=True,live=True,paused=False)

def test_slow_job_nonblocking_and_duplicate_rejected(monkeypatch):
    gate=Event();jobs,s,g=setup(monkeypatch,gate)
    before=monotonic();assert start(jobs,s,g,messages());assert monotonic()-before<.2
    assert not start(jobs,s,g,messages())
    gate.set();finish(jobs,s,messages())
    assert s.report is not None and s.request_count==1 and s.total_tokens==12 and g.closed
    assert not start(jobs,s,g,messages())

@pytest.mark.parametrize('change',['consent','correction','clear','unauthorized','deleted'])
def test_late_results_never_restore_revoked_or_deleted_data(monkeypatch,change):
    gate=Event();jobs,s,g=setup(monkeypatch,gate);ms=messages()
    assert start(jobs,s,g,ms)
    if change=='consent': configure_observation(s,'manual',('big_five',))
    if change=='correction': correct_observation(s,'mbti:EI:','delete')
    if change=='clear':
        old=s;s=fresh_observation_state(old)
    if change=='deleted': ms=ms[:1]
    gate.set()
    if change=='clear':
        finish(jobs,old,[]);assert s.report is None;assert s.request_count==1
    elif change=='unauthorized':
        s.pending_job.future.result(3)
        jobs.poll_observation(s,ms,authorized=False,live=True,paused=False)
        assert s.report is None
    else:
        finish(jobs,s,ms);assert s.report is None

def test_new_messages_leave_report_stale_and_failure_retains_previous(monkeypatch):
    gate=Event();jobs,s,g=setup(monkeypatch,gate)
    assert start(jobs,s,g,messages());gate.set();finish(jobs,s,messages(3))
    assert s.report is not None and s.is_stale(messages(3))
    report=s.report;bad=Gateway(fail=True)
    assert start(jobs,s,bad,messages(3));finish(jobs,s,messages(3))
    assert s.report is report and s.error_code=='timeout' and s.request_count==2

def test_last_request_usable_and_failure_spend_not_refunded(monkeypatch):
    jobs,s,g=setup(monkeypatch,fail=True);s.ledger.spent=5
    assert start(jobs,s,g,messages());finish(jobs,s,messages())
    assert s.request_count==6 and s.ledger.reserved==0
    assert not start(jobs,s,g,messages(3))

def test_snapshot_identity_dedup_and_stale_follow_relations_and_corrections(monkeypatch):
    jobs,s,g=setup(monkeypatch);configure_observation(s,'manual',('mbti','attachment'))
    assert start(jobs,s,g,messages());finish(jobs,s,messages())
    assert not s.is_stale(messages())
    assert not start(jobs,s,g,messages())
    s.relations['friend_1']='friend';s.message_relations['0']='friend_1'
    assert s.is_stale(messages())
    assert start(jobs,s,g,messages());finish(jobs,s,messages())
    correct_observation(s,'mbti:EI:','disagree')
    assert start(jobs,s,g,messages());finish(jobs,s,messages())

def test_auto_schedule_counts_failures_and_requires_ten_new_candidates(monkeypatch):
    jobs,s,g=setup(monkeypatch,fail=True);configure_observation(s,'auto',('mbti',))
    def ms(n): return [Message(id=str(i),role='user',content=f'事件{i}我在不同情境与朋友商量自己经历的事情'+ '甲'*60) for i in range(n)]
    def auto(n): return jobs.start_observation(s,ms(n),'c1',lambda:Gateway(fail=True),manual=False,authorized=True,live=True,paused=False)
    assert auto(20);finish(jobs,s,ms(20));assert not auto(29)
    assert auto(30);finish(jobs,s,ms(30))
    assert auto(40);finish(jobs,s,ms(40));assert not auto(50)
    assert s.automatic_count==3 and s.request_count==3

def test_repairs_share_request_cap_and_frozen_correction_constraints(monkeypatch):
    jobs,s,g=setup(monkeypatch);s.ledger.spent=5
    configure_observation(s,'manual',('mbti','attachment'))
    correct_observation(s,'mbti:EI:','state')
    s.relations['r1']='friend';s.message_relations['0']='r1'
    gate=Event();seen=[]
    def repair(snapshot,gateway,budget):
        gate.wait(2);seen.append(snapshot)
        gateway.generate([], '',None,budget)
        gateway.generate([], '',None,budget)
    monkeypatch.setattr(jobs,'analyze_observations',repair)
    ms=messages();assert start(jobs,s,g,ms)
    s.relations['r1']='partner';s.excluded_keys.add('mbti:SN:')
    ms[0].content='changed'
    gate.set();finish(jobs,s,ms)
    assert s.request_count==5 and s.ledger.reserved==0
    assert seen[0].relations=={'r1':'friend'}
    assert seen[0].excluded_keys==('mbti:EI:',)
    assert seen[0].messages[0].content!='changed'

def test_relation_changed_during_job_rejects_old_report(monkeypatch):
    gate=Event();jobs,s,g=setup(monkeypatch,gate);configure_observation(s,'manual',('mbti','attachment'))
    assert start(jobs,s,g,messages())
    s.relations['r1']='friend';s.message_relations['0']='r1'
    gate.set();finish(jobs,s,messages())
    assert s.report is None

def test_invalid_oversize_snapshot_does_not_construct_gateway(monkeypatch):
    from support_agent import observation_jobs as jobs
    s=ObservationState();configure_observation(s,'manual',('mbti',))
    called=[]
    ms=[Message(id=str(i),role='user',content='甲'*9000+str(i)) for i in range(2)]
    assert jobs.start_observation(s,ms,'c1',lambda:called.append(True),manual=True,authorized=True,live=True,paused=False)
    finish(jobs,s,ms)
    assert not called and s.request_count==0 and s.error_code=='context_limit'

def test_concurrent_start_launches_one_job_per_conversation(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    gate=Event();jobs,s,g=setup(monkeypatch,gate)
    with ThreadPoolExecutor(max_workers=8) as pool:
        accepted=list(pool.map(lambda _:start(jobs,s,g,messages()),range(8)))
    assert accepted.count(True)==1
    gate.set();finish(jobs,s,messages())
    assert s.request_count==1

def test_disabled_offline_paused_and_unconsented_never_create_job(monkeypatch):
    jobs,s,g=setup(monkeypatch)
    for flags in [dict(authorized=False,live=True,paused=False),dict(authorized=True,live=False,paused=False),dict(authorized=True,live=True,paused=True)]:
        assert not jobs.start_observation(s,messages(),'c1',lambda:g,manual=True,**flags)
    configure_observation(s,'off',('mbti',))
    assert not start(jobs,s,g,messages())
    assert s.request_count==0 and s.pending_job is None

def test_withdrawal_during_first_response_prevents_structural_repair(monkeypatch):
    from support_agent import observation_jobs as jobs
    entered=Event();release=Event();calls=[]
    class InvalidGateway(Gateway):
        def generate(self,messages,instructions,schema,budget):
            budget.consume();calls.append(True);entered.set();release.wait(2)
            return ModelResult(text='invalid json',model_id='test')
    s=ObservationState();configure_observation(s,'manual',('mbti',));g=InvalidGateway()
    assert start(jobs,s,g,messages());assert entered.wait(2)
    configure_observation(s,'off',('mbti',));release.set();finish(jobs,s,messages())
    assert len(calls)==1 and s.request_count==1 and s.report is None

def test_withdrawal_before_first_send_never_constructs_gateway(monkeypatch):
    from support_agent import observation_jobs as jobs
    entered=Event();release=Event();created=[]
    real=jobs.analyze_observations
    def queued(snapshot,gateway,budget):
        entered.set();release.wait(2)
        return real(snapshot,gateway,budget)
    monkeypatch.setattr(jobs,'analyze_observations',queued)
    s=ObservationState();configure_observation(s,'manual',('mbti',))
    assert jobs.start_observation(s,messages(),'c1',lambda:created.append(True),manual=True,authorized=True,live=True,paused=False)
    assert entered.wait(2);configure_observation(s,'off',('mbti',));release.set();finish(jobs,s,messages())
    assert created==[] and s.request_count==0 and s.report is None


def test_last_request_cannot_be_reused_for_repair(monkeypatch):
    jobs,s,g=setup(monkeypatch);s.ledger.spent=5
    def repair(snapshot,gateway,budget):
        gateway.generate([], '',None,budget)
        gateway.generate([], '',None,budget)
    monkeypatch.setattr(jobs,'analyze_observations',repair)
    assert start(jobs,s,g,messages());finish(jobs,s,messages())
    assert s.request_count==6 and s.error_code=='budget' and s.ledger.reserved==0

def test_clear_during_first_response_prevents_structural_repair():
    from support_agent import observation_jobs as jobs
    entered=Event();release=Event();calls=[]
    class InvalidGateway(Gateway):
        def generate(self,messages,instructions,schema,budget):
            budget.consume();calls.append(True);entered.set();release.wait(2)
            return ModelResult(text='invalid json',model_id='test')
    s=ObservationState();configure_observation(s,'manual',('mbti',));g=InvalidGateway()
    assert start(jobs,s,g,messages());assert entered.wait(2)
    clean=fresh_observation_state(s);release.set();finish(jobs,s,messages())
    assert len(calls)==1 and clean.request_count==1 and clean.report is None

def test_mbti_job_ignores_retained_unauthorized_attachment_metadata(monkeypatch):
    jobs,s,g=setup(monkeypatch)
    s.relations['r1']='friend';s.message_relations['0']='r1'
    s.excluded_keys.add('attachment:anxiety:r1')
    assert start(jobs,s,g,messages());finish(jobs,s,messages())
    assert s.request_count==1 and s.report is not None and not s.is_stale(messages())
