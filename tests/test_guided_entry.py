from pathlib import Path
from streamlit.testing.v1 import AppTest
import pytest
from support_agent.config import ConfigurationReadiness


@pytest.fixture(autouse=True)
def ready_configuration(monkeypatch):
    import support_agent.ui as ui
    monkeypatch.setattr(ui,'configuration_readiness',lambda:ConfigurationReadiness(True,True,True,None))


def home():
    return AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=10).run()


def test_first_visit_has_three_clear_entries_and_no_setup_form():
    app=home()
    assert not app.exception
    assert {b.key for b in app.button}>={'home_chat','home_test','home_observe'}
    assert len(app.checkbox)==0 and len(app.radio)==0 and len(app.selectbox)==0


def test_chat_preparation_is_sequential_and_then_leaves_chat_uncluttered():
    app=home();app.button(key='home_chat').click().run()
    assert len(app.radio)==0 and len(app.checkbox)==1
    assert app.button(key='chat_setup_next').disabled
    app.checkbox(key='chat_setup_research').check().run()
    app.button(key='chat_setup_next').click().run()
    app.checkbox(key='chat_setup_api').check().run()
    app.button(key='chat_setup_finish').click().run()
    assert not app.exception
    assert not app.chat_input[0].disabled
    assert len(app.checkbox)==0 and len(app.radio)==0


def test_tool_catalog_does_not_render_questionnaire_until_a_function_is_chosen():
    app=home();app.button(key='home_test').click().run()
    assert len(app.radio)==0 and len(app.checkbox)==0
    assert any(b.key=='feature_swls' for b in app.button)
    app.button(key='feature_swls').click().run()
    assert app.button(key='feature_begin')
    assert not any(s.label.startswith('1.') for s in app.selectbox)


def test_cancelled_personality_connection_does_not_redirect_later_chat_setup():
    app=home()
    c=app.session_state['workspace'].active
    c.exploration.flows['chat_setup']={'step':2}
    c.exploration.flows['personality']={'page':'connection','consent':True}
    app.session_state['workspace_view']='exploration'
    app.session_state['feature_flow_active']=True
    app.session_state['exploration_tool']='mbti'
    app.session_state['research_confirmed']=True
    app.session_state['api_consent']=True
    app.run()
    app.button(key='personality_'+c.id+'_setup').click().run()
    assert app.session_state['workspace_view']=='api_settings'
    app.button(key='api_settings_back').click().run()
    assert app.session_state['workspace_view']=='exploration'
    app.button(key='open_exploration').click().run()
    app.button(key='home_chat').click().run()
    app.button(key='chat_connection_settings').click().run()
    app.button(key='chat_setup_next').click().run()
    app.button(key='chat_setup_finish').click().run()
    assert app.session_state['workspace_view']=='chat'
