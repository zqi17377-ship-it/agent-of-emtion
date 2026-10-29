"""Shared small presentation blocks for one-step-at-a-time product flows."""
import html
import streamlit as st


def step_header(title,steps,index,show_progress=True):
    index=max(0,min(index,len(steps)-1))
    st.markdown(f'<div class="flow-heading"><span>第 {index+1} / {len(steps)} 步</span><h2>{html.escape(title)}</h2><p>{html.escape(steps[index])}</p></div>',unsafe_allow_html=True)
    if show_progress: st.progress(index/max(1,len(steps)-1))


def research_checkbox(key):
    previous=bool(st.session_state.get('research_confirmed'))
    value=st.checkbox('我只输入成年人虚构案例',value=previous,key=key)
    if value!=previous:
        st.session_state['research_confirmed']=value
        if not value:
            from .observation_ui import revoke_observation_consents
            revoke_observation_consents()
    st.caption('当前为研究原型，尚未完成专业审核。')
    return value


def api_checkbox(key):
    previous=bool(st.session_state.get('api_consent'))
    value=st.checkbox('允许发送对话上下文至 DeepSeek，并知悉调用费用',value=previous,key=key)
    if value!=previous:
        st.session_state['api_consent']=value
        if not value:
            from .observation_ui import revoke_observation_consents
            revoke_observation_consents()
    return value


def back_to_tools():
    st.session_state['workspace_view']='exploration'
    st.session_state['feature_flow_active']=False
