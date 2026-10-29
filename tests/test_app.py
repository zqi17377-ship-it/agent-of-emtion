from pathlib import Path
from streamlit.testing.v1 import AppTest


def launch():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=10).run()
    assert not app.exception
    return app


def chat(app,text='这是虚构案例，想聊聊工作。'):
    app.checkbox(key='research_confirmed').check().run()
    app.chat_input[0].set_value(text).run()
    assert not app.exception
    return app


def test_page_mock_conversation_and_clear():
    app=launch()
    assert app.chat_input[0].disabled
    chat(app)
    assert len(app.chat_message)==2
    app.button(key='clear_current').click().run()
    assert len(app.chat_message)==0


def test_starter_fills_composer_without_sending():
    app=launch()
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
    assert len(calls)==1


def test_mode_switch_preserves_previous_chat():
    app=launch(); chat(app)
    old=app.session_state['workspace'].active.id
    app.radio(key='mode_selector').set_value('DeepSeek API').run()
    assert not app.exception
    assert app.chat_input[0].disabled
    assert len(app.session_state['workspace'].items)==2
    app.button(key='conversation_'+old).click().run()
    assert len(app.chat_message)==2
    assert app.radio(key='mode_selector').value=='离线演示'


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
