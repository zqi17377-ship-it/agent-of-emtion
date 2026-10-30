from streamlit.testing.v1 import AppTest

from tests.test_observation_wizard import SCRIPT,advance


def topics():
    app=AppTest.from_string(SCRIPT,default_timeout=10).run()
    c=app.session_state['workspace'].active
    prefix='explore_'+c.id+'_observe_wizard_'
    app.checkbox(key=prefix+'research').check().run();advance(app)
    app.checkbox(key=prefix+'api').check().run();advance(app)
    return app,c,prefix


def test_visible_topics_require_a_selection_and_survive_back_navigation():
    app,c,p=topics()
    for domain in ('mbti','big_five','attachment'):
        app.checkbox(key=p+'domain_'+domain).uncheck().run()
    assert app.button(key='observation_next').disabled
    assert c.exploration.observation.mode=='off'
    app.checkbox(key=p+'domain_attachment').check().run();advance(app)
    app.radio(key=p+'mode').set_value('auto').run()
    app.button(key='observation_back').click().run()
    assert app.checkbox(key=p+'domain_attachment').value
    assert not app.checkbox(key=p+'domain_mbti').value
    assert not app.checkbox(key=p+'domain_big_five').value
    advance(app)
    assert app.radio(key=p+'mode').value=='auto'
    assert c.exploration.observation.mode=='off'


def test_chat_report_shortcut_preserves_enabled_mode_without_starting_analysis():
    app=AppTest.from_string('''
import streamlit as st
from support_agent.conversations import Workspace
from support_agent.config import ConfigurationReadiness
from support_agent.observation_ui import render_observation_entry,render_observation_panel
if 'workspace' not in st.session_state:
    st.session_state.workspace=Workspace()
    st.session_state.research_confirmed=True
    st.session_state.api_consent=True
    st.session_state.workspace.active.exploration.observation.mode='manual'
    st.session_state.workspace.active.exploration.observation.domains=('mbti',)
c=st.session_state.workspace.active
r=ConfigurationReadiness(True,True,True,None)
if st.session_state.get('workspace_view')=='exploration':
    render_observation_panel(c,True,r)
else:
    render_observation_entry(c,r)
''',default_timeout=10).run()
    assert not app.exception
    app.button(key='open_conversation_report').click().run()
    assert not app.exception
    c=app.session_state['workspace'].active
    assert app.session_state['workspace_view']=='exploration'
    assert app.button(key='analyze_observations').disabled
    assert c.exploration.observation.mode=='manual'
    assert c.exploration.observation.pending_job is None
    assert c.exploration.observation.request_count==0
    app.button(key='observation_done').click().run()
    app.button(key='observation_modify').click().run()
    advance(app);advance(app)
    assert app.checkbox(key='explore_'+c.id+'_observe_wizard_domain_mbti').value
