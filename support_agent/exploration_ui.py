"""Choose a capability, then mount only that capability's current step."""
import streamlit as st
from .exploration_catalog import TOOL_LABELS,SURVEY_BY_ID
from .exploration_state import exploration_paused,ExplorationState
from .questionnaire_ui import render_questionnaire
from .personality_ui import render_personality
from .observation_scheduler import fresh_observation_state
from .survey_registry import list_versions
from .observation_ui import render_observation_panel
from .onboarding_ui import choose_feature
from .flow_ui import step_header,back_to_tools


def purge_exploration_controls(conversation_id):
    for key in list(st.session_state):
        if isinstance(key,str) and (key.startswith('explore_'+conversation_id+'_') or key.startswith('personality_'+conversation_id+'_')):
            del st.session_state[key]
    st.session_state.pop('attachment_context',None)


def clear_exploration(conversation):
    conversation.exploration=ExplorationState(observation=fresh_observation_state(conversation.exploration.observation))
    purge_exploration_controls(conversation.id)


def render_exploration(conversation,allowed,readiness):
    if exploration_paused(conversation.state.previous_decision):
        st.info('当前先关注眼前的支持与安全需求，探索稍后再进行。')
        return
    active=bool(st.session_state.get('feature_flow_active'))
    if not active:
        st.markdown('## 选择一个想了解的方向')
        st.write('选定后再决定题数或方式，每一步都会提示接下来做什么。')
        st.caption(f'目前可作答 {sum(v.enabled for v in list_versions())} 个问卷版本。')
        descriptions={'mbti':'八题偏好问答、自我确认或查看对话中的性格线索。','attachment_exploration':'原创12题、每关系9题ECR-RS或36题ECR-R，分别了解焦虑和回避。','mini_ipip':'10、20、50或100题，按五个维度了解自己。','rses':'10题，了解通常的自我价值感受。','coping_confidence':'6题，回顾面对日常挑战的信心。','swls':'3或5题，回顾整体生活满意度。','scs26':'遇到挫折时怎样对待自己？12题看总体，26题另看六个面向。','maas15':'15题，回顾日常走神、自动行事和对当下活动的觉察。','dospert30':'30题，分别探索社交、娱乐、伦理、健康安全与财务情境中的行为意向。','conversation_observation':'按顺序设置主题和整理方式，再回到对话。'}
        descriptions.update(erq30_en='30题英文原版，分别记录十种情绪调节策略的自报使用，不合成总分。',aaqii7='7题英文原版，了解痛苦体验与担忧对重要行动的影响；高分表示更多心理不灵活或经验性回避。')
        for tool,label in TOOL_LABELS.items():
            with st.container(border=True):
                st.button(label,key='feature_'+tool,width='stretch',on_click=choose_feature,args=(tool,))
                st.caption(descriptions[tool])
        with st.expander('待接入的测试与来源'):
            st.write('以下项目尚未内置题目，暂不能在这里作答，也不计入可作答数量。')
            for version in list_versions():
                if version.instrument_id in ('beq','ffmq') and not version.enabled:
                    st.write(version.notes)
                    st.link_button('查看作者资料',version.source_url,key='pending_source_'+version.instrument_id)
        return
    tool=st.session_state.get('exploration_tool','conversation_observation')
    if tool=='mbti': render_personality(conversation,allowed,readiness)
    elif tool=='conversation_observation': render_observation_panel(conversation,allowed,readiness)
    else:
        base=next(v for v in list_versions() if v.enabled and v.definition.id==SURVEY_BY_ID[tool].id)
        versions=[v for v in list_versions(base.construct_id) if v.enabled]
        navigation=conversation.exploration.flows.setdefault('feature_navigation',{'tool':tool,'stage':'version' if len(versions)>1 else 'run'})
        if navigation.get('tool')!=tool:
            navigation.update(tool=tool,stage='version' if len(versions)>1 else 'run')
        if navigation['stage']=='version':
            step_header('选择适合自己的题数',['选择版本','逐题填写','核对与结果'],0)
            lookup={v.id:v for v in versions}
            old=navigation.get('version',base.id)
            selected=st.radio('本次使用哪个版本？',list(lookup),index=list(lookup).index(old) if old in lookup else 0,format_func=lambda key:lookup[key].definition.title,key='explore_'+conversation.id+'_version_'+base.construct_id)
            navigation['version']=selected
            st.caption('不同工具的题数和计分各自独立；研究译文尚未经过中文信效度验证。')
            if st.button('开始这份测试',key='feature_begin',type='primary'): navigation['stage']='run';st.rerun()
            st.button('返回功能选择',key='feature_exit',on_click=back_to_tools,type='tertiary')
            return
        selected=next(v for v in versions if v.id==navigation.get('version',base.id))
        render_questionnaire(conversation,selected.definition,allowed,version_id=selected.id)
    with st.expander('管理已保存的探索记录'):
        st.button('清除本对话探索记录',key='clear_exploration',on_click=clear_exploration,args=(conversation,))
