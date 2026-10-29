"""Feature home and the three-screen chat preparation journey."""
import streamlit as st
from .flow_ui import step_header,research_checkbox,api_checkbox
from .observation_scheduler import configure_observation


def go_home():
    st.session_state['workspace_view']='home'
    st.session_state['feature_flow_active']=False
    st.session_state.pop('setup_return',None)


def choose_feature(tool):
    c=st.session_state['workspace'].active
    st.session_state['workspace_view']='exploration'
    st.session_state['exploration_tool']=tool
    st.session_state['feature_flow_active']=True
    c.exploration.flows['feature_navigation']={'tool':tool,'stage':'version' if tool in ('mini_ipip','swls') else 'run'}


def begin_chat_setup(return_to='chat'):
    st.session_state['workspace_view']='chat_setup'
    st.session_state['workspace'].active.exploration.flows['chat_setup']={'step':0}
    st.session_state['setup_return']=return_to


def start_or_resume_chat():
    c=st.session_state['workspace'].active
    if st.session_state.get('research_confirmed') and (c.gateway_mode=='mock' or st.session_state.get('api_consent')):
        st.session_state['workspace_view']='chat'
    else: begin_chat_setup()


def render_home():
    st.markdown('<section class="welcome"><div class="welcome-kicker">从这里开始</div><h1>今天，想怎样照顾自己？</h1><p>选择一件想做的事，我们会一步一步带你完成。</p></section>',unsafe_allow_html=True)
    items=[('home_chat','01','开始对话','说说最近在意的事，先完成简单准备。',start_or_resume_chat,()),
           ('home_test','02','做心理小测试','先选测试和题数，再一次回答一题。',_open_tests,()),
           ('home_observe','03','从对话探索自己','设置想了解的主题，让对话慢慢积累线索。',choose_feature,('conversation_observation',))]
    for key,number,title,description,callback,args in items:
        with st.container(border=True,key='home_card_'+key):
            st.caption(number)
            st.button(title,key=key,width='stretch',on_click=callback,args=args)
            st.write(description)
    st.caption('当前为成年人虚构案例的研究预览。问卷在本机计分；连接模型前会另行说明。')


def _open_tests():
    st.session_state['workspace_view']='exploration'
    st.session_state['feature_flow_active']=False


def render_chat_setup(readiness):
    w=st.session_state['workspace'];c=w.active
    flow=c.exploration.flows.setdefault('chat_setup',{'step':0})
    step=flow['step']
    step_header('开始对话前，做一点准备',['选择连接方式','确认使用范围','准备开始'],step)
    if step==0:
        mode=st.radio('选择对话方式',['离线演示','DeepSeek API'],index=1 if c.gateway_mode=='live' else 0,key='chat_setup_mode')
        st.write('离线演示使用固定回复，可以先熟悉操作。DeepSeek 会根据对话内容生成回复。')
        if st.button('下一步',key='chat_setup_next',type='primary'):
            target='live' if mode=='DeepSeek API' else 'mock'
            if target!=c.gateway_mode:
                if c.state.messages:
                    try: c=w.new_conversation(gateway_mode=target)
                    except ValueError:
                        st.warning('对话已满，请先在会话管理中移除一个对话。');return
                else:
                    configure_observation(c.exploration.observation,'off',())
                    c.gateway_mode=target
            st.session_state['mode_selector']=mode
            c.exploration.flows['chat_setup']={'step':1}
            st.rerun()
    elif step==1:
        confirmed=research_checkbox('chat_setup_research')
        st.write('本版本用于虚构场景研究，不替代专业评估。对话记录只保存在当前会话，需要时可以主动导出。')
        left,right=st.columns(2)
        if left.button('上一步',key='chat_setup_prev'): flow['step']=0;st.rerun()
        if right.button('下一步',key='chat_setup_next',disabled=not confirmed,type='primary'): flow['step']=2;st.rerun()
    else:
        enabled=bool(st.session_state.get('research_confirmed'))
        if c.gateway_mode=='live':
            st.markdown('#### 确认模型连接')
            if readiness.ready: st.success('DeepSeek 连接配置已就绪。')
            else: st.warning('请先在本机填写 DeepSeek API 配置，再重新检查。')
            enabled=enabled and api_checkbox('chat_setup_api') and readiness.ready
            st.caption('发送消息会产生API请求；额外的对话探索需要单独启用。')
        else: st.success('离线演示已准备好，可以开始体验。')
        left,right=st.columns(2)
        if left.button('上一步',key='chat_setup_prev'): flow['step']=1;st.rerun()
        if right.button('进入对话',key='chat_setup_finish',disabled=not enabled,type='primary'):
            target=st.session_state.pop('setup_return','chat')
            if target=='chat': st.session_state['workspace_view']='chat'
            else: choose_feature(target)
            st.rerun()
    st.button('返回功能首页',key='chat_setup_exit',on_click=go_home,type='tertiary')
