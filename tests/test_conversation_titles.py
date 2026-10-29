from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from support_agent.conversations import Workspace
from support_agent.config import ConfigurationReadiness
from support_agent.schemas import Message, TurnResult


def reply(workspace, text='第一条虚构消息'):
    workspace.active.state.messages.extend([
        Message(role='user',content=text),
        Message(role='assistant',content='已有回复'),
    ])
    workspace.record_turn(TurnResult(text='已有回复',action='listen',status='ok'))


def test_custom_title_survives_subsequent_replies_and_keeps_chat_state():
    w=Workspace();reply(w)
    c=w.active
    messages=list(c.state.messages)
    w.rename_conversation(c.id,'  工作  与生活 🌱  ')
    assert c.title=='工作 与生活 🌱'
    assert c.title_is_custom is True
    assert c.state.messages==messages
    reply(w,'补充一段虚构消息')
    assert c.title=='工作 与生活 🌱'


def test_rename_targets_id_without_renaming_other_active_conversation():
    w=Workspace();first=w.active
    second=w.new_conversation()
    w.rename_conversation(first.id,'第一段对话')
    assert first.title=='第一段对话'
    assert second.title=='新的对话'
    assert w.active is second
    with pytest.raises(KeyError): w.rename_conversation('missing','名字')


@pytest.mark.parametrize('value',['',' \t\n ','题'*41,None])
def test_invalid_title_keeps_previous_name(value):
    w=Workspace();w.rename_conversation(w.active.id,'已有名称')
    with pytest.raises(ValueError,match='invalid_title'):
        w.rename_conversation(w.active.id,value)
    assert w.active.title=='已有名称'


def test_clear_resets_custom_name_and_new_chat_does_not_inherit_it():
    w=Workspace();w.rename_conversation(w.active.id,'我的名称')
    c=w.active
    w.clear_active()
    assert c.title=='新的对话' and c.title_is_custom is False
    reply(w,'清空后的新内容')
    assert c.title=='清空后的新内容'
    w.rename_conversation(c.id,'重新命名')
    assert w.new_conversation().title=='新的对话'


def test_old_conversation_without_custom_flag_can_auto_name_and_then_rename():
    w=Workspace()
    w.active.__dict__.pop('title_is_custom',None)
    reply(w,'旧会话保留的虚构首句')
    assert w.active.title=='旧会话保留的虚构首句'
    w.rename_conversation(w.active.id,'旧会话自定义')
    reply(w)
    assert w.active.title=='旧会话自定义'


def launch(monkeypatch):
    import support_agent.ui as ui
    monkeypatch.setattr(ui,'configuration_readiness',lambda:ConfigurationReadiness(True,True,True,None))
    def forbidden(*args,**kwargs): raise AssertionError('Naming must not call the model')
    monkeypatch.setattr(ui,'make_gateway',forbidden)
    return AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=10).run()


def test_sidebar_rename_save_updates_sidebar_and_escaped_chat_title_without_api(monkeypatch):
    app=launch(monkeypatch)
    c=app.session_state['workspace'].active
    app.session_state['workspace_view']='chat'
    app.run()
    assert not app.text_input
    app.button(key='rename_conversation').click().run()
    app.text_input(key='rename_value_'+c.id).set_value('我的 <生活> 🌱').run()
    app.button(key='save_conversation_title').click().run()
    assert not app.exception
    assert c.title=='我的 <生活> 🌱'
    assert not app.text_input
    assert app.button(key='conversation_'+c.id).label=='我的 <生活> 🌱'
    assert any('我的 &lt;生活&gt; 🌱' in m.value for m in app.markdown)


def test_sidebar_rename_cancel_and_blank_validation_preserve_name(monkeypatch):
    app=launch(monkeypatch)
    c=app.session_state['workspace'].active
    original=c.title
    app.button(key='rename_conversation').click().run()
    app.text_input(key='rename_value_'+c.id).set_value('未保存草稿').run()
    app.button(key='cancel_conversation_title').click().run()
    assert c.title==original and not app.text_input
    app.button(key='rename_conversation').click().run()
    app.text_input(key='rename_value_'+c.id).set_value('  ').run()
    app.button(key='save_conversation_title').click().run()
    assert c.title==original and app.error
