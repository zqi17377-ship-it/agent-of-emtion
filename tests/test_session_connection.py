from concurrent.futures import Future
from dataclasses import field, make_dataclass
from types import SimpleNamespace
import pytest
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


def stale_connection_settings(api_key='synthetic-first',model='first-model',base_url='https://api.deepseek.com'):
    """Recreate an old module identity using only synthetic fixture values."""
    old_class=make_dataclass('ConnectionSettings',[
        ('api_key',str,field(repr=False)),('model',str),('base_url',str),
    ],namespace={'__module__':'support_agent.config','__qualname__':'ConnectionSettings'},frozen=True)
    old_class.__module__='support_agent.config'
    old_class.__qualname__='ConnectionSettings'
    return old_class(api_key,model,base_url)


def test_hot_reload_migrates_old_settings_without_invalidating_consent_or_records():
    from support_agent import config
    from support_agent.schemas import Message
    app=launch();click(app,'save first')
    c=app.session_state['workspace'].active
    observation=c.exploration.observation
    c.state.messages.append(Message(role='user',content='虚构案例：周末我喜欢安静地阅读。'))
    messages=c.state.messages[:]
    report=SimpleNamespace(fingerprint='synthetic-saved',observations=[])
    pending=SimpleNamespace(future=Future())
    observation.mode='auto';observation.domains=('mbti',)
    observation.report=report;observation.pending_job=pending
    observation.ledger.spent=2
    generation,consent_revision=observation.generation,observation.consent_revision
    setup={'page':'report','step':4,'consent':True,'mode':'auto'}
    personality={'page':'questions','consent':True,'answers':{'ei_1':'I'}}
    c.exploration.flows['observation_setup']=setup.copy()
    c.exploration.flows['personality']=personality.copy()
    c.exploration.confirmations={'EI':'I'}
    app.session_state['api_consent']=True
    app.session_state['chat_setup_api']=True
    app.session_state['personality_'+c.id+'_api']=True
    connection_revision=app.session_state['connection_revision']
    old=stale_connection_settings()
    assert type(old) is not config.ConnectionSettings
    assert type(old).__module__==config.ConnectionSettings.__module__
    assert type(old).__qualname__==config.ConnectionSettings.__qualname__
    app.session_state['connection_settings']=old

    app.run()

    assert not app.exception and app.markdown[0].value=='ready'
    normalized=app.session_state['connection_settings']
    assert type(normalized) is config.ConnectionSettings
    assert normalized.api_key=='synthetic-first' and normalized.model=='first-model'
    assert normalized.base_url=='https://api.deepseek.com'
    assert app.session_state['connection_revision']==connection_revision
    assert app.session_state['api_consent'] is True
    assert app.session_state['chat_setup_api'] is True
    assert app.session_state['personality_'+c.id+'_api'] is True
    assert observation.mode=='auto' and observation.domains==('mbti',)
    assert observation.generation==generation and observation.consent_revision==consent_revision
    assert observation.pending_job is pending and observation.report is report
    assert observation.ledger.spent==2 and observation.ledger.reserved==0
    assert c.exploration.flows['observation_setup']==setup
    assert c.exploration.flows['personality']==personality
    assert c.exploration.confirmations=={'EI':'I'} and c.state.messages==messages
    click(app,'save first')
    assert app.session_state['connection_revision']==connection_revision
    assert app.session_state['api_consent'] is True and observation.mode=='auto'


def test_stale_settings_are_revalidated_and_normalized_using_current_constructor():
    from support_agent import config
    app=launch()
    app.session_state['connection_settings']=stale_connection_settings(
        ' synthetic-fixture ',' synthetic-model ',' https://api.deepseek.com/v1/ ',
    )

    app.run()

    assert not app.exception and app.markdown[0].value=='ready'
    normalized=app.session_state['connection_settings']
    assert type(normalized) is config.ConnectionSettings
    assert normalized.api_key=='synthetic-fixture'
    assert normalized.model=='synthetic-model'
    assert normalized.base_url=='https://api.deepseek.com/v1'
    assert 'connection_revision' not in app.session_state


@pytest.mark.parametrize('field_name,invalid_value',[
    ('api_key',''),('api_key','synthetic invalid'),('api_key',123),
    ('model','invalid model'),('base_url','https://third-party.invalid/v1'),
])
def test_hot_reload_rejects_invalid_stale_values_without_borrowing_configuration(monkeypatch,field_name,invalid_value):
    from support_agent import config
    def forbidden_configuration_read():
        raise AssertionError('must not read process or local configuration')
    monkeypatch.setattr(config,'load_configuration',forbidden_configuration_read)
    monkeypatch.setattr(config,'load_local_env',forbidden_configuration_read)
    values={'api_key':'synthetic-fixture','model':'synthetic-model','base_url':'https://api.deepseek.com'}
    values[field_name]=invalid_value
    app=launch()
    app.session_state['connection_settings']=stale_connection_settings(**values)

    app.run()

    assert not app.exception and app.markdown[0].value=='missing'
    assert 'connection_revision' not in app.session_state


@pytest.mark.parametrize('object_kind',[
    'mapping','namespace','foreign_dataclass','same_module_other_name_dataclass','same_name_object',
])
def test_hot_reload_rejects_attribute_compatible_objects_from_other_types(object_kind):
    values={'api_key':'synthetic-fixture','model':'synthetic-model','base_url':'https://api.deepseek.com'}
    if object_kind=='mapping':
        candidate=values
    elif object_kind=='namespace':
        candidate=SimpleNamespace(**values)
    elif object_kind in ('foreign_dataclass','same_module_other_name_dataclass'):
        foreign=make_dataclass('ConnectionSettings',[(name,str) for name in values],frozen=True)
        foreign.__module__='third_party_fixture' if object_kind=='foreign_dataclass' else 'support_agent.config'
        foreign.__qualname__='ConnectionSettings' if object_kind=='foreign_dataclass' else 'OtherSettings'
        candidate=foreign(**values)
    else:
        unrelated=type('ConnectionSettings',(),{'__module__':'support_agent.config','__qualname__':'ConnectionSettings'})
        candidate=unrelated()
        for name,value in values.items():
            setattr(candidate,name,value)
    app=launch()
    app.session_state['connection_settings']=candidate

    app.run()

    assert not app.exception and app.markdown[0].value=='missing'
    assert 'connection_revision' not in app.session_state


def test_config_class_replacement_uses_current_constructor_and_readiness(monkeypatch):
    from support_agent import config
    app=launch();click(app,'save first')
    original_class=config.ConnectionSettings
    new_namespace={
        '__module__':original_class.__module__,
        '__qualname__':original_class.__qualname__,
        '__post_init__':original_class.__post_init__,
    }
    reloaded_class=make_dataclass('ConnectionSettings',[
        ('api_key',str,field(repr=False)),('model',str,'deepseek-flash'),
        ('base_url',str,'https://api.deepseek.com'),
    ],namespace=new_namespace,frozen=True)
    reloaded_class.__module__=original_class.__module__
    reloaded_class.__qualname__=original_class.__qualname__
    monkeypatch.setattr(config,'ConnectionSettings',reloaded_class)

    app.run()

    assert not app.exception and app.markdown[0].value=='ready'
    assert type(app.session_state['connection_settings']) is reloaded_class
    revision=app.session_state['connection_revision']
    click(app,'save first')
    assert app.session_state['connection_revision']==revision
