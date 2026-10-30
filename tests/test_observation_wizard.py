from streamlit.testing.v1 import AppTest

SCRIPT = '''
import streamlit as st
from support_agent.conversations import Workspace
from support_agent.config import ConfigurationReadiness
from support_agent.observation_ui import render_observation_panel,render_observation_monitor
if 'workspace' not in st.session_state: st.session_state.workspace=Workspace()
c=st.session_state.workspace.active
render_observation_panel(c,bool(st.session_state.get('research_confirmed')),ConfigurationReadiness(True,True,True,None))
render_observation_monitor(ConfigurationReadiness(True,True,True,None))
'''

def launch():
    app=AppTest.from_string(SCRIPT,default_timeout=10).run()
    assert not app.exception
    return app

def advance(app):
    app.button(key='observation_next').click().run()
    assert not app.exception

def ready(app):
    c=app.session_state['workspace'].active
    p='explore_'+c.id+'_observe_wizard_'
    app.checkbox(key=p+'research').check().run();advance(app)
    app.checkbox(key=p+'api').check().run();advance(app)
    app.checkbox(key=p+'domain_big_five').uncheck().run()
    app.checkbox(key=p+'domain_attachment').uncheck().run();advance(app)
    app.radio(key=p+'mode').set_value('auto').run();advance(app)
    return c,p

def test_confirmation_is_only_activation_and_pages_preserve_draft(monkeypatch):
    import support_agent.observation_ui as ui
    monkeypatch.setattr(ui,'make_gateway',lambda **kw: (_ for _ in ()).throw(AssertionError('unexpected API')))
    app=launch();c,p=ready(app)
    assert c.exploration.observation.mode=='off'
    app.button(key='observation_back').click().run()
    app.button(key='observation_back').click().run()
    assert app.checkbox(key=p+'domain_mbti').value
    assert not app.checkbox(key=p+'domain_big_five').value
    assert not app.checkbox(key=p+'domain_attachment').value
    advance(app);advance(app)
    app.checkbox(key=p+'consent').check().run()
    assert c.exploration.observation.mode=='off'
    app.button(key='observation_confirm').click().run()
    assert c.exploration.observation.mode=='auto'
    assert c.exploration.observation.domains==('mbti',)
    assert not app.selectbox and not app.multiselect
    app.button(key='observation_relations').click().run()
    assert app.selectbox(key='explore_'+c.id+'_observe_new_relation_kind')
    assert not any(b.key=='analyze_observations' for b in app.button)
    app.button(key='observation_done').click().run()
    app.button(key='observation_report').click().run()
    assert not app.selectbox
    app.button(key='observation_revoke').click().run()
    assert c.exploration.observation.mode=='off'
    assert c.exploration.flows['observation_setup']['consent'] is False

def test_auto_draft_with_sufficient_messages_cannot_start_hidden_request(monkeypatch):
    import support_agent.observation_ui as ui
    from tests.test_observation_integration import synthetic_messages
    calls=[]
    monkeypatch.setattr(ui,'make_gateway',lambda **kw:calls.append(kw))
    app=launch();c,p=ready(app)
    c.state.messages=synthetic_messages()
    app.run();app.run()
    assert c.exploration.observation.mode=='off'
    assert c.exploration.observation.request_count==0 and calls==[]
    assert c.exploration.observation.pending_job is None
