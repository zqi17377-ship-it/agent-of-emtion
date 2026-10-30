from concurrent.futures import Future
from types import SimpleNamespace
from streamlit.testing.v1 import AppTest


APP = '''
import streamlit as st
from support_agent.config import ConnectionSettings
from support_agent.conversations import Workspace
from support_agent.session_connection import get_session_settings,session_readiness,save_session_settings,clear_session_settings
if 'workspace' not in st.session_state: st.session_state.workspace=Workspace()
if st.button('save first'): save_session_settings(ConnectionSettings('synthetic-first',model='first-model'))
if st.button('save second'): save_session_settings(ConnectionSettings('synthetic-second',model='second-model'))
if st.button('clear'): clear_session_settings()
st.write('ready' if session_readiness().ready else 'missing')
'''


def launch():
    app=AppTest.from_string(APP,default_timeout=10).run()
    assert not app.exception
    return app


def click(app,label):
    next(b for b in app.button if b.label==label).click().run()
    assert not app.exception


def test_new_sessions_never_inherit_global_configuration_and_are_isolated(monkeypatch):
    import support_agent.config as config
    monkeypatch.setattr(config,'load_configuration',lambda: (_ for _ in ()).throw(AssertionError('must not read server configuration')))
    first,second=launch(),launch()
    assert first.markdown[0].value=='missing' and second.markdown[0].value=='missing'
    click(first,'save first')
    second.run()
    assert first.markdown[0].value=='ready' and second.markdown[0].value=='missing'
    assert first.session_state['connection_settings'].api_key=='synthetic-first'
    assert 'connection_settings' not in second.session_state
    assert 'synthetic-first' not in str(first.markdown)


def test_replacing_or_clearing_connection_invalidates_jobs_but_retains_records():
    app=launch();click(app,'save first')
    workspace=app.session_state['workspace']
    c=workspace.active
    state=c.exploration.observation
    report=SimpleNamespace(fingerprint='saved',observations=[])
    state.mode='auto';state.domains=('mbti',);state.report=report
    state.ledger.spent=2
    state.pending_job=SimpleNamespace(future=Future())
    generation,revision=state.generation,state.consent_revision
    c.exploration.flows['observation_setup']={'page':'done','step':4,'consent':True,'mode':'auto'}
    c.exploration.flows['personality']={'page':'analyze','consent':True,'answers':{'ei_1':'I'}}
    c.exploration.confirmations={'EI':'I'}
    app.session_state['api_consent']=True
    app.session_state['chat_setup_api']=True
    app.session_state['personality_'+c.id+'_api']=True
    click(app,'save second')
    assert state.mode=='off' and state.report is report
    assert state.generation!=generation and state.consent_revision>revision
    assert state.pending_job is None and state.ledger.spent==2
    assert c.exploration.confirmations=={'EI':'I'}
    assert c.exploration.flows['personality']['answers']=={'ei_1':'I'}
    assert c.exploration.flows['personality']['consent'] is False
    assert c.exploration.flows['observation_setup']['consent'] is False
    assert app.session_state['api_consent'] is False
    assert 'chat_setup_api' not in app.session_state
    assert 'personality_'+c.id+'_api' not in app.session_state
    click(app,'clear')
    assert app.markdown[0].value=='missing'
    assert 'connection_settings' not in app.session_state
    assert state.report is report and state.request_count==2


def test_observation_worker_factory_uses_captured_session_snapshot(monkeypatch):
    import support_agent.observation_ui as ui
    from support_agent.config import ConnectionSettings
    captured=[];made=[]
    first=ConnectionSettings('synthetic-first')
    monkeypatch.setattr(ui,'get_session_settings',lambda:first,raising=False)
    monkeypatch.setattr(ui,'start_observation',lambda state,messages,cid,factory,**kw:captured.append(factory))
    monkeypatch.setattr(ui,'make_gateway',lambda **kw: made.append(kw))
    script='''
import streamlit as st
from support_agent.conversations import Workspace
from support_agent.config import ConfigurationReadiness
from support_agent.observation_ui import render_observation_monitor
if 'workspace' not in st.session_state: st.session_state.workspace=Workspace()
render_observation_monitor(ConfigurationReadiness(True,True,True,None))
st.write('monitor rendered')
'''
    app=AppTest.from_string(script).run()
    assert not app.exception and len(captured)==1
    monkeypatch.setattr(ui,'get_session_settings',lambda: (_ for _ in ()).throw(AssertionError('worker must not read Streamlit state')))
    captured[0]()
    assert made==[{'settings':first}]


def test_connection_changes_keep_read_only_reports_and_local_question_pages():
    app=launch();click(app,'save first')
    c=app.session_state['workspace'].active
    c.exploration.flows['personality']={'page':'questions','consent':True,'answers':{'ei_1':'I'}}
    c.exploration.flows['observation_setup']={'page':'report','consent':True,'step':4}
    click(app,'save second')
    assert c.exploration.flows['personality']['page']=='questions'
    assert c.exploration.flows['personality']['answers']=={'ei_1':'I'}
    assert c.exploration.flows['observation_setup']['page']=='report'
    assert c.exploration.flows['observation_setup']['consent'] is False


def test_changing_credentials_during_response_prevents_repair_with_old_key():
    from threading import Event
    from support_agent import observation_jobs as jobs
    from support_agent.observation_scheduler import configure_observation
    from support_agent.schemas import Message,ModelResult
    app=launch();click(app,'save first')
    c=app.session_state['workspace'].active
    state=c.exploration.observation
    configure_observation(state,'manual',('mbti',))
    old_report=SimpleNamespace(fingerprint='old',observations=[])
    state.report=old_report
    messages=[Message(role='user',content='我休息时更喜欢独自散步。'),Message(role='user',content='周末我会在家安静地读书。')]
    entered,release=Event(),Event()
    calls=[]
    class Gateway:
        mode='live';model_id='test-fixture'
        def generate(self,messages,instructions,schema,budget):
            budget.consume();calls.append(True);entered.set()
            assert release.wait(5)
            return ModelResult(text='invalid json',model_id=self.model_id)
    assert jobs.start_observation(state,messages,c.id,Gateway,manual=True,authorized=True,live=True,paused=False)
    job=state.pending_job
    try:
        assert entered.wait(3)
        click(app,'save second')
    finally:
        release.set()
    job.future.result(5)
    assert calls==[True]
    assert state.mode=='off' and state.report is old_report
    assert state.pending_job is None and state.request_count==1 and state.ledger.reserved==0


def test_clearing_credentials_before_first_worker_send_never_creates_gateway(monkeypatch):
    from threading import Event
    from support_agent import observation_jobs as jobs
    from support_agent.observation_scheduler import configure_observation
    from support_agent.schemas import Message
    app=launch();click(app,'save first')
    c=app.session_state['workspace'].active
    state=c.exploration.observation
    configure_observation(state,'manual',('mbti',))
    entered,release=Event(),Event()
    original=jobs.analyze_observations
    def queued(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    monkeypatch.setattr(jobs,'analyze_observations',queued)
    created=[]
    messages=[Message(role='user',content='我休息时更喜欢独自散步。'),Message(role='user',content='周末我会在家安静地读书。')]
    assert jobs.start_observation(state,messages,c.id,lambda:created.append(True),manual=True,authorized=True,live=True,paused=False)
    job=state.pending_job
    try:
        assert entered.wait(3)
        click(app,'clear')
    finally:
        release.set()
    job.future.result(5)
    assert created==[] and state.request_count==0 and state.ledger.reserved==0
