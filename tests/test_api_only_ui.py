from pathlib import Path
from streamlit.testing.v1 import AppTest
from support_agent.config import ConfigurationReadiness
from support_agent.schemas import Message


def launch(monkeypatch, ready=True):
    import support_agent.ui as ui
    monkeypatch.setattr(ui, 'configuration_readiness', lambda: ConfigurationReadiness(ready, ready, ready, None))
    monkeypatch.setattr(ui, 'make_gateway', lambda *a, **k: (_ for _ in ()).throw(AssertionError('UI-only check must not send requests')))
    return AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'), default_timeout=10).run()


def test_new_chat_uses_api_and_has_no_mode_choice(monkeypatch):
    app=launch(monkeypatch)
    assert app.session_state['workspace'].active.gateway_mode=='live'
    app.button(key='home_chat').click().run()
    assert not app.radio
    assert len(app.checkbox)==1
    assert app.button(key='chat_setup_next').disabled
    app.checkbox(key='chat_setup_research').check().run()
    app.button(key='chat_setup_next').click().run()
    assert app.button(key='chat_setup_finish').disabled
    app.checkbox(key='chat_setup_api').check().run()
    app.button(key='chat_setup_finish').click().run()
    assert not app.chat_input[0].disabled
    assert not any('离线' in x.value or '演示模式' in x.value for x in app.markdown)


def test_missing_configuration_never_enables_chat_or_uses_demo(monkeypatch):
    app=launch(monkeypatch, ready=False)
    app.button(key='home_chat').click().run()
    app.checkbox(key='chat_setup_research').check().run()
    app.button(key='chat_setup_next').click().run()
    app.checkbox(key='chat_setup_api').check().run()
    assert app.button(key='chat_setup_finish').disabled
    assert app.chat_input[0].disabled
    assert not app.session_state['workspace'].active.state.messages


def test_legacy_demo_history_is_preserved_and_cannot_send_to_api(monkeypatch):
    app=launch(monkeypatch)
    c=app.session_state['workspace'].active
    c.gateway_mode='mock'
    c.state.messages=[Message(role='user',content='历史虚构案例')]
    app.session_state['research_confirmed']=True
    app.session_state['api_consent']=True
    app.session_state['workspace_view']='chat'
    app.run()
    assert app.chat_input[0].disabled
    assert c.gateway_mode=='mock' and len(c.state.messages)==1
    app.button(key='prepare_chat').click().run()
    app.button(key='chat_setup_next').click().run()
    assert app.button(key='chat_setup_finish').disabled
    app.button(key='chat_setup_new_api').click().run()
    assert len(app.session_state['workspace'].items)==2
    assert app.session_state['workspace'].active.gateway_mode=='live'
    assert c.state.messages[0].content=='历史虚构案例'


def test_old_single_chat_demo_migration_cannot_be_relabelled_as_api(monkeypatch):
    from support_agent.session import new_session
    app=launch(monkeypatch)
    old=new_session()
    old.messages=[Message(role='user',content='旧单聊天虚构案例')]
    del app.session_state['workspace']
    app.session_state['agent_session']=old
    app.session_state['selected_mode']='离线演示'
    app.session_state['research_confirmed']=True
    app.session_state['api_consent']=True
    app.session_state['workspace_view']='chat'
    app.run()
    assert app.session_state['workspace'].active.gateway_mode=='mock'
    assert app.chat_input[0].disabled
    assert len(app.session_state['workspace'].active.state.messages)==1
