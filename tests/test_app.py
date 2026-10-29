from pathlib import Path
from streamlit.testing.v1 import AppTest
import pytest
from support_agent.config import ConfigurationReadiness
from support_agent.schemas import Message, TurnResult


@pytest.fixture(autouse=True)
def ready_connection_for_ui_checks(monkeypatch):
    import support_agent.ui as ui
    monkeypatch.setattr(ui,'configuration_readiness',lambda:ConfigurationReadiness(True,True,True,None))
    monkeypatch.setattr(ui,'make_gateway',lambda *a,**k:object())


def launch():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=10).run()
    assert not app.exception
    return app


def chat(app,text='这是虚构案例，想聊聊工作。'):
    # Seed rendering state only. Real API behavior is checked separately with
    # explicit synthetic live requests, never by a demonstration gateway.
    prepare(app)
    w=app.session_state['workspace']
    w.active.state.messages=[Message(role='user',content=text),Message(role='assistant',content='用于页面控件检查的既有记录。')]
    w.record_turn(TurnResult(text=w.active.state.messages[-1].content,action='listen',status='ok'))
    app.run()
    assert not app.exception
    return app


def prepare(app):
    if any(b.key=='home_chat' for b in app.button): app.button(key='home_chat').click().run()
    elif any(b.key=='prepare_chat' for b in app.button): app.button(key='prepare_chat').click().run()
    else: return app
    if any(b.key=='chat_setup_next' for b in app.button):
        app.checkbox(key='chat_setup_research').check().run()
        app.button(key='chat_setup_next').click().run()
        app.checkbox(key='chat_setup_api').check().run()
        app.button(key='chat_setup_finish').click().run()
    return app


def test_page_conversation_record_and_clear():
    app=launch()
    assert app.chat_input[0].disabled
    chat(app)
    assert len(app.chat_message)==2
    app.button(key='clear_current').click().run()
    assert len(app.chat_message)==0


def test_starter_fills_composer_without_sending():
    app=prepare(launch())
    app.button(key='starter_pressure').click().run()
    assert not app.exception
    assert app.chat_input[0].value
    assert not app.session_state['workspace'].active.state.messages


def test_new_and_switch_restore_conversation():
    app=launch(); chat(app)
    old=app.session_state['workspace'].active.id
    app.button(key='new_top').click().run()
    assert len(app.chat_message)==0
    app.button(key='conversation_'+old).click().run()
    assert len(app.chat_message)==2


def test_feedback_does_not_call_model_again(monkeypatch):
    import support_agent.workflow as workflow
    calls=[]; original=workflow.run_turn
    def tracked(*args,**kwargs):
        calls.append(1)
        return original(*args,**kwargs)
    monkeypatch.setattr(workflow,'run_turn',tracked)
    app=launch(); chat(app)
    c=app.session_state['workspace'].active
    mid=c.state.messages[-1].id
    app.button(key='helpful_'+c.id+'_'+mid).click().run()
    assert app.session_state['workspace'].active.feedback[mid]=='helpful'
    assert len(calls)==0


def test_connection_settings_preserve_current_api_chat():
    app=launch(); chat(app)
    old=app.session_state['workspace'].active.id
    app.button(key='chat_connection_settings').click().run()
    assert not app.exception
    assert not app.radio
    assert len(app.session_state['workspace'].items)==1
    assert app.session_state['workspace'].active.state.messages
    app.button(key='conversation_'+old).click().run()
    assert len(app.chat_message)==2
    assert app.session_state['workspace'].active.gateway_mode=='live'


def test_rejected_turn_is_visible_without_corrupting_previous_reply(monkeypatch):
    import support_agent.workflow as workflow
    from support_agent.schemas import TurnResult
    app=launch(); chat(app)
    c=app.session_state['workspace'].active
    mid=c.state.messages[-1].id
    original=c.results[mid].text
    rejected=TurnResult(text='上下文过长，本轮未发送。请另开对话。',action='clarify',status='fallback',error_code='context_limit')
    monkeypatch.setattr(workflow,'run_turn',lambda *a,**k:rejected)
    app.chat_input[0].set_value('又一条虚构消息').run()
    assert app.warning[0].value==rejected.text
    assert app.session_state['workspace'].active.results[mid].text==original
    assert len(app.chat_message)==2
