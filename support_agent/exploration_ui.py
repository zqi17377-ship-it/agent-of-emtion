import streamlit as st
from .exploration_catalog import TOOL_LABELS,SURVEY_BY_ID
from .exploration_state import exploration_paused,ExplorationState
from .questionnaire_ui import render_questionnaire
from .personality_ui import render_personality
from .observation_scheduler import fresh_observation_state
from .survey_registry import list_versions
from .observation_ui import render_observation_panel


def purge_exploration_controls(conversation_id):
    prefix='explore_'+conversation_id+'_'
    for key in list(st.session_state):
        if isinstance(key,str) and key.startswith(prefix):
            del st.session_state[key]
    st.session_state.pop('attachment_context',None)


def clear_exploration(conversation):
    conversation.exploration=ExplorationState(observation=fresh_observation_state(conversation.exploration.observation))
    purge_exploration_controls(conversation.id)


def render_exploration(conversation,allowed,readiness):
    st.markdown('<div class="exploration-title"><span>认识自己，多一种视角</span><h1>心理探索</h1><p>从性格偏好到关系模式。按自己的节奏选择，每份记录都可以重新思考。</p></div>',unsafe_allow_html=True)
    if exploration_paused(conversation.state.previous_decision):
        st.info('当前先关注眼前的支持与安全需求，性格和问卷探索稍后再进行。')
        return
    tool=st.selectbox('选择探索工具',list(TOOL_LABELS),index=1,format_func=TOOL_LABELS.get,key='exploration_tool')
    st.caption('问卷在本机计分，不会自动发送给模型；这些记录仅保存在当前浏览器会话。')
    if tool=='mbti': render_personality(conversation,allowed,readiness)
    elif tool=='conversation_observation': render_observation_panel(conversation,allowed,readiness)
    else:
        definition=SURVEY_BY_ID[tool]
        base=next(v for v in list_versions() if v.enabled and v.definition.id==definition.id)
        versions=[v for v in list_versions(base.construct_id) if v.enabled]
        selected=base
        if len(versions)>1:
            lookup={v.id:v for v in versions}
            version_id=st.selectbox('选择题数与版本',list(lookup),index=list(lookup).index(base.id),format_func=lambda key:lookup[key].definition.title,key='explore_'+conversation.id+'_version_'+base.construct_id)
            selected=lookup[version_id]
            st.caption('不同工具和题数分别计分，请结合完整名称阅读结果。')
        render_questionnaire(conversation,selected.definition,allowed,version_id=selected.id)
        candidates=[v for v in list_versions(base.construct_id) if not v.enabled]
        if candidates:
            with st.expander('其他题数 · 待核实版本'):
                for version in candidates:
                    st.write(f'{version.instrument_id} · {version.item_count}题')
                    st.caption(version.notes)
    with st.expander('管理本对话的探索记录'):
        st.button('清除本对话探索记录',key='clear_exploration',on_click=clear_exploration,args=(conversation,))
