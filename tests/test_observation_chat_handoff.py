from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize('mode',['manual','auto'])
def test_final_observation_confirmation_opens_real_chat_and_keeps_settings(monkeypatch,mode):
    from support_agent.config import ConnectionSettings
    import support_agent.ui as ui
    import support_agent.observation_ui as observation_ui
    calls=[]
    def forbidden(*args,**kwargs):
        calls.append(True)
        raise AssertionError('Setup navigation must not create a gateway')
    monkeypatch.setattr(ui,'make_gateway',forbidden)
    monkeypatch.setattr(observation_ui,'make_gateway',forbidden)
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=10).run()
    app.session_state['connection_settings']=ConnectionSettings('synthetic-handoff-key')
    app.button(key='home_observe').click().run()
    c=app.session_state['workspace'].active
    prefix='explore_'+c.id+'_observe_wizard_'
    app.checkbox(key=prefix+'research').check().run()
    app.button(key='observation_next').click().run()
    app.checkbox(key=prefix+'api').check().run()
    app.button(key='observation_next').click().run()
    app.multiselect(key=prefix+'domains').set_value(['mbti','attachment']).run()
    app.button(key='observation_next').click().run()
    app.selectbox(key=prefix+'mode').select(mode).run()
    app.button(key='observation_next').click().run()
    app.checkbox(key=prefix+'consent').check().run()
    app.button(key='observation_confirm').click().run()
    assert not app.exception
    assert app.session_state['workspace_view']=='chat'
    assert not app.chat_input[0].disabled
    assert app.button(key='open_conversation_observation')
    assert not any(b.key=='observation_confirm' for b in app.button)
    assert not any('[data-testid="stBottom"]{display:none!important}' in element.proto.body for element in app.get('html'))
    assert c.exploration.observation.mode==mode
    assert c.exploration.observation.domains==('attachment','mbti')
    assert c.exploration.flows['observation_setup']['page']=='done'
    assert c.state.messages==[] and calls==[]
    app.button(key='open_conversation_observation').click().run()
    assert app.session_state['workspace_view']=='exploration'
    assert app.button(key='observation_modify') and app.button(key='observation_report')
    app.button(key='observation_report').click().run()
    assert c.exploration.observation.mode==mode and calls==[]
