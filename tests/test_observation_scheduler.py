from concurrent.futures import ThreadPoolExecutor
import pytest
from support_agent.schemas import Message

def messages(n, size=60):
    return [Message(id=str(i), role='user', content=f'事件{i}我在工作生活中感到需要仔细思考'+ '甲'*size) for i in range(n)]

def test_candidates_ignore_assistant_repetition_and_short_assent():
    from support_agent.observation_scheduler import count_candidates
    text='今天我在公司和同事讨论了项目进度'
    items=[Message(role='user',content=text),Message(role='user',content=text),Message(role='assistant',content=text),Message(role='user',content='嗯嗯'),Message(role='user',content='😀'*60)]
    assert count_candidates(items)==(1,len(text))

def test_thresholds_and_authorization():
    from support_agent.observation_scheduler import ObservationState,configure_observation,eligibility_reason
    s=ObservationState(); configure_observation(s,'auto',('mbti',))
    check=lambda ms,**kw: eligibility_reason(s,ms,manual=False,live=True,authorized=True,paused=False,**kw)
    assert check(messages(5)) is not None
    assert check(messages(6,0)) is not None
    assert check(messages(6)) is None
    assert eligibility_reason(s,messages(20),manual=True,live=True,authorized=False,paused=False) is not None
    assert eligibility_reason(s,messages(1),manual=True,live=True,authorized=True,paused=False) is not None

def test_atomic_reservations_and_clear_preserve_spend():
    from support_agent.observation_scheduler import ObservationState,fresh_observation_state
    s=ObservationState()
    with ThreadPoolExecutor(max_workers=8) as pool:
        reservations=list(pool.map(lambda _: s.ledger.reserve(2),range(8)))
    assert sum(r.remaining for r in reservations if r)==6
    for r in reservations:
        if r:
            r.commit(); r.release()
    assert s.request_count==3
    clean=fresh_observation_state(s)
    assert clean.generation!=s.generation and clean.request_count==3
    assert clean.ledger.reserve(2).remaining==2

def test_corrections_and_consent_invalidate_visible_data():
    from types import SimpleNamespace
    from support_agent.observation_scheduler import ObservationState,configure_observation,correct_observation
    s=ObservationState(); configure_observation(s,'auto',('mbti','attachment'))
    s.report=SimpleNamespace(observations=[SimpleNamespace(key='mbti:EI:',domain='mbti'),SimpleNamespace(key='attachment:anxiety:r1',domain='attachment')])
    correct_observation(s,'mbti:EI:','state')
    assert s.observation_revision==1 and 'mbti:EI:' in s.excluded_keys
    assert len(s.report.observations)==1
    configure_observation(s,'manual',('mbti',))
    assert s.consent_revision==2 and s.report is None

def test_clearing_observation_records_preserves_automatic_session_limit():
    from support_agent.observation_scheduler import ObservationState,fresh_observation_state,configure_observation,eligibility_reason
    previous=ObservationState(automatic_count=3,last_auto_candidate_count=40)
    previous.ledger.spent=3
    clean=fresh_observation_state(previous);configure_observation(clean,'auto',('mbti',))
    assert clean.automatic_count==3 and clean.last_auto_candidate_count==40
    assert clean.request_count==3
    assert eligibility_reason(clean,messages(50),manual=False,live=True,authorized=True,paused=False)=='auto_limit'


def test_new_chat_text_requires_initial_threshold_while_retaining_auto_spend():
    from support_agent.observation_scheduler import ObservationState,fresh_observation_state,configure_observation,eligibility_reason
    previous=ObservationState(automatic_count=1,last_auto_candidate_count=20)
    clean=fresh_observation_state(previous);clean.last_auto_candidate_count=0
    configure_observation(clean,'auto',('mbti',))
    def check(ms): return eligibility_reason(clean,ms,manual=False,live=True,authorized=True,paused=False)
    assert check(messages(3)) is not None
    assert check(messages(5)) is not None
    assert check(messages(6,0)) is not None
    assert check(messages(6)) is None
    clean.last_auto_candidate_count=6
    assert check(messages(11)) is not None
    assert check(messages(12)) is None
