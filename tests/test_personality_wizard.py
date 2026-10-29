from streamlit.testing.v1 import AppTest

APP = '''
import streamlit as st
from types import SimpleNamespace
from support_agent.conversations import Conversation
from support_agent.personality_ui import render_personality
if 'c' not in st.session_state:
    st.session_state.c=Conversation()
render_personality(st.session_state.c, bool(st.session_state.get('research_confirmed')), SimpleNamespace(ready=False))
'''

def app():
    return AppTest.from_string(APP).run()

def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception

def start_local(at,label):
    click(at,label)
    assert not at.radio
    assert len(at.checkbox)==1
    if not at.checkbox[0].value: at.checkbox[0].check().run()
    click(at,'开始八题问答' if label=='八题偏好问答' else '开始自我确认')

def test_menu_and_one_question_draft_survives_return():
    at=app()
    assert not at.radio
    start_local(at, '八题偏好问答')
    assert len(at.radio)==1
    at.radio[0].set_value('E').run()
    click(at, '下一题')
    assert len(at.radio)==1
    click(at, '上一题')
    assert at.radio[0].value=='E'
    click(at, '返回人格功能')
    start_local(at, '八题偏好问答')
    assert at.radio[0].value=='E'
    assert at.session_state.c.exploration.self_answers=={}

def test_self_answers_only_saved_after_review():
    at=app()
    start_local(at, '八题偏好问答')
    for _ in range(8):
        assert len(at.radio)==1
        click(at, '下一题')
    assert not at.radio
    assert at.session_state.c.exploration.self_answers=={}
    click(at, '保存偏好自述')
    assert len(at.session_state.c.exploration.self_answers)==8

def test_confirmation_is_one_dimension_and_saved_at_end():
    at=app()
    start_local(at, '我的自我确认')
    for _ in range(4):
        assert len(at.radio)==1
        assert not at.session_state.c.exploration.confirmations
        click(at, '下一项')
    click(at, '保存自我确认')
    assert len(at.session_state.c.exploration.confirmations)==4

def test_observation_default_has_no_model_action():
    at=app()
    click(at, '从对话观察偏好')
    assert not any(b.key=='analyze_personality' for b in at.button)
    assert at.session_state.c.exploration.observation.request_count==0
    assert at.session_state.c.exploration.profile is None

def test_live_mode_still_requires_separate_consent_before_model_action(monkeypatch):
    import support_agent.personality_ui as ui
    def forbidden_gateway(*args, **kwargs):
        raise AssertionError('A gateway must never be created during preparation')
    monkeypatch.setattr(ui, 'make_gateway', forbidden_gateway)
    live=APP.replace("render_personality(st.session_state.c, bool(st.session_state.get('research_confirmed')), SimpleNamespace(ready=False))", '''
from support_agent.schemas import Message
st.session_state.c.gateway_mode='live'
if not st.session_state.c.state.messages:
    st.session_state.c.state.messages=[Message(role='user',content='日常我喜欢先计划。'),Message(role='user',content='我休息时喜欢独处。')]
render_personality(st.session_state.c, True, SimpleNamespace(ready=True))
''')
    at=AppTest.from_string(live).run()
    click(at, '从对话观察偏好')
    assert len(at.checkbox)==1
    assert next(b for b in at.button if b.label=='下一步').disabled
    at.checkbox[0].check().run()
    click(at, '下一步')
    assert len(at.checkbox)==1
    assert next(b for b in at.button if b.label=='下一步').disabled
    at.checkbox[0].check().run()
    click(at, '下一步')
    assert len(at.checkbox)==1
    assert next(b for b in at.button if b.label=='下一步').disabled
    at.checkbox[0].check().run()
    click(at, '下一步')
    assert not next(b for b in at.button if b.key=='analyze_personality').disabled
    assert at.session_state.c.exploration.observation.request_count==0
    assert at.session_state.c.exploration.profile is None


def test_new_user_can_complete_local_flows_without_gateway(monkeypatch):
    import support_agent.personality_ui as ui
    def forbidden_gateway(*args, **kwargs):
        raise AssertionError('Local preference flows must not create a gateway')
    monkeypatch.setattr(ui,'make_gateway',forbidden_gateway)
    at=app()
    start_local(at,'八题偏好问答')
    for _ in range(8): click(at,'下一题')
    click(at,'保存偏好自述')
    assert len(at.session_state.c.exploration.self_answers)==8
    click(at,'返回人格功能')
    start_local(at,'我的自我确认')
    for _ in range(4): click(at,'下一项')
    click(at,'保存自我确认')
    assert len(at.session_state.c.exploration.confirmations)==4
    assert at.session_state.c.exploration.observation.request_count==0


def test_first_scope_confirmation_immediately_enables_next():
    at=app()
    click(at,'从对话观察偏好')
    assert next(b for b in at.button if b.label=='下一步').disabled
    at.checkbox[0].check().run()
    assert not next(b for b in at.button if b.label=='下一步').disabled
    click(at,'下一步')
    assert not at.exception
    assert len(at.checkbox)==1
