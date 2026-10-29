"""Streamlit presentation; private chat state stays in the browser session."""
import html
from pathlib import Path
import streamlit as st
from . import workflow
from .config import ROOT,configuration_readiness
from .conversations import Workspace
from .model_client import make_gateway
from .schemas import EligibilityContext,ModelCallError,TurnResult
from .exploration_state import ExplorationState
from .exploration_ui import render_exploration,purge_exploration_controls
from .observation_ui import render_observation_entry,render_observation_monitor
from .observation_scheduler import ObservationState,configure_observation
from .onboarding_ui import render_home,render_chat_setup,go_home,begin_chat_setup

ACTION_LABELS={'listen':'先听你说','clarify':'慢慢了解','support':'一起梳理','refer':'专业求助建议','urgent_support':'当前支持指引'}
STARTERS=[('pressure','工作压力','从最累的那件事开始','这是成年人虚构案例：最近工作任务很多，我想先说说感受，不急着要建议。'),('sleep','睡眠困扰','说说最近的夜晚','这是成年人虚构案例：最近睡得不太好，白天有些疲惫，想一起梳理。'),('listen','只想倾诉','先被听见，也很好','这是成年人虚构案例：今天有点低落，我只想有人听我说，暂时不需要建议。')]


def workspace():
    return st.session_state['workspace']


def reset_draft():
    st.session_state['composer']=''
    st.session_state['workspace_view']='home'
    st.session_state['feature_flow_active']=False
    st.session_state.pop('saved_composer',None)
    st.session_state.pop('attachment_context',None)
    st.session_state.pop('notice',None)
    st.session_state.pop('setup_return',None)


def new_chat():
    try:
        workspace().new_conversation()
        reset_draft()
    except ValueError:
        st.session_state['notice']='当前已保留 10 个对话。可以在侧栏的“会话管理”中移除不再需要的对话。'


def select_chat(cid):
    c=workspace().select(cid)
    st.session_state['mode_selector']='DeepSeek API' if c.gateway_mode=='live' else '离线演示'
    reset_draft()
    if c.state.messages: st.session_state['workspace_view']='chat'


def clear_current():
    purge_exploration_controls(workspace().active.id)
    workspace().clear_active()
    reset_draft()


def fill_starter(text):
    st.session_state['composer']=text


def feedback(mid,rating):
    w=workspace()
    w.set_feedback(mid,None if w.active.feedback.get(mid)==rating else rating)


def delete_current():
    purge_exploration_controls(workspace().active.id)
    c=workspace().remove_active()
    st.session_state['mode_selector']='DeepSeek API' if c.gateway_mode=='live' else '离线演示'
    st.session_state.pop('confirm_delete',None)
    reset_draft()


def turn_caption(result):
    if result.action=='urgent_support': return '当前支持指引'
    if result.status=='fallback': return '本轮使用备用回复'
    if result.status=='error': return '本轮暂未完成'
    return '回复已生成 · '+ACTION_LABELS[result.action]


def initialize():
    if 'workspace' not in st.session_state:
        w=Workspace()
        # Preserve the earlier single-chat UI state during this upgrade.
        old=st.session_state.pop('agent_session',None)
        old_result=st.session_state.pop('last_result',None)
        if old is not None:
            w.active.state=old
            if old_result:
                try: w.record_turn(TurnResult.model_validate(old_result))
                except ValueError: pass
        if st.session_state.pop('selected_mode',None)=='DeepSeek API':
            w.active.gateway_mode='live'
        st.session_state['workspace']=w
    for conversation in workspace().items:
        if not hasattr(conversation,'exploration'):
            conversation.exploration=ExplorationState()
        if not hasattr(conversation.exploration,'observation'):
            conversation.exploration.observation=ObservationState()
        if not hasattr(conversation.exploration,'flows'):
            conversation.exploration.flows={}
    st.session_state.setdefault('workspace_view','home')
    if 'mode_selector' not in st.session_state:
        st.session_state['mode_selector']='DeepSeek API' if workspace().active.gateway_mode=='live' else '离线演示'


def render_sidebar():
    w=workspace()
    with st.sidebar:
        st.markdown('<div class="sidebar-brand"><span class="brand-mark">心</span><span>知心</span></div><p class="sidebar-tagline">留一点空间，给自己。</p>',unsafe_allow_html=True)
        st.button('发起新对话',icon=':material/add:',key='new_sidebar',type='primary',width='stretch',on_click=new_chat)
        st.markdown('<div class="section-label">本次会话</div>',unsafe_allow_html=True)
        for c in reversed(w.items):
            st.button(c.title,key='conversation_'+c.id,icon=':material/chat_bubble_outline:',type='secondary' if c.id==w.active_id else 'tertiary',width='stretch',on_click=select_chat,args=(c.id,))
        st.caption('这些对话只保存在当前浏览器会话，关闭或刷新后可能丢失。')
        with st.expander('会话管理'):
            st.write(f'当前保留 {len(w.items)} / 10 个对话')
            if st.button('移除当前对话',key='request_delete'):
                st.session_state['confirm_delete']=w.active_id
            if st.session_state.get('confirm_delete')==w.active_id:
                st.caption('移除后无法从本页恢复。需要保留时，请先导出。')
                st.button('确认移除',key='confirm_remove',on_click=delete_current)
                if st.button('取消',key='cancel_remove'):
                    st.session_state.pop('confirm_delete',None)
                    st.rerun()
        st.toggle('显示研究记录',key='show_research',value=False,help='查看软件动作与原文依据；这些记录不是诊断报告。')
        st.markdown('<div class="sidebar-footnote">研究预览 v0.5<br>仅限成年人虚构案例</div>',unsafe_allow_html=True)


def render_welcome():
    st.markdown('''<section class="welcome"><div class="welcome-kicker"><span></span> 给想法一个慢下来的地方</div><h1>慢慢说，<br>我们一起梳理。</h1><p>不用一次把一切说明白。<br class="mobile-break">可以从今天最在意的一件小事开始。</p><div class="welcome-art" aria-hidden="true"><svg viewBox="0 0 240 240" fill="none"><circle cx="122" cy="120" r="94" fill="#e9eee3"/><circle cx="122" cy="120" r="70" stroke="#d5dfcb"/><path d="M118 192V113m0 39c-36 0-58-23-58-55 33 0 58 19 58 55Zm0-18c0-42 27-69 65-69 0 38-25 69-65 69Z" stroke="#78946f" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M81 120l37 32m0-18 44-47" stroke="#78946f" stroke-width="1.8" stroke-linecap="round"/><circle cx="189" cy="174" r="8" fill="#ddc9ab"/></svg></div></section>''',unsafe_allow_html=True)
    with st.container(key='starters'):
        columns=st.columns(3,gap='small')
        for i,((key,title,description,text),column) in enumerate(zip(STARTERS,columns)):
            with column,st.container(key='topic_'+key):
                st.markdown(f'<span class="topic-number">0{i+1}</span>',unsafe_allow_html=True)
                st.button(title+'  ↗',key='starter_'+key,on_click=fill_starter,args=(text,),width='stretch')
                st.caption(description)


def render_composer(c,w,enabled,allow_send=True):
    observation=c.exploration.observation
    relation_key='explore_'+c.id+'_observe_next_relation'
    if allow_send and observation.mode!='off' and 'attachment' in observation.domains and observation.relations:
        st.selectbox('本条消息谈到的关系对象（可留空）',['',*observation.relations],format_func=lambda key:'暂不指定' if not key else key,key=relation_key)
    placeholder='从你想说的那件事开始…' if enabled else '先完成上方确认，就可以开始了…'
    text=st.chat_input(placeholder,key='composer',disabled=not enabled,max_chars=5000)
    if text and allow_send:
        gateway=None
        try:
            gateway=make_gateway(c.gateway_mode=='live')
            c.state.eligibility=EligibilityContext(adult_status='confirmed')
            existing_ids={m.id for m in c.state.messages}
            with st.spinner('正在认真读你说的话…'):
                result=workflow.run_turn(c.state,text,gateway)
            w.record_turn(result)
            if c.state.messages and c.state.messages[-1].role=='assistant':
                last_user=next((m for m in reversed(c.state.messages[:-1]) if m.role=='user'),None)
                selected=st.session_state.get(relation_key,'')
                if last_user and last_user.id not in existing_ids and selected in observation.relations:
                    observation.message_relations[last_user.id]=selected
            st.rerun()
        except ModelCallError:
            st.error('暂时无法连接模型。请展开“连接与使用范围”检查本机配置，或切换离线演示。')
        finally:
            if gateway and hasattr(gateway,'close'): gateway.close()


def render():
    st.set_page_config(page_title='知心 · 留一点空间给自己',page_icon='🌱',layout='wide',initial_sidebar_state='auto')
    st.html('<style>'+(ROOT/'assets/chat.css').read_text(encoding='utf-8')+'</style>')
    initialize()
    render_sidebar()
    w=workspace(); c=w.active
    readiness=configuration_readiness()
    view=st.session_state.get('workspace_view','home')
    enabled=bool(st.session_state.get('research_confirmed')) and (c.gateway_mode!='live' or bool(st.session_state.get('api_consent')) and readiness.ready)
    with st.container(key='brandbar'):
        left,right=st.columns([4,1],vertical_alignment='center')
        with left: st.markdown('<div class="main-brand"><span class="brand-mark">心</span><b>知心</b><span class="brand-description">倾听 · 梳理 · 陪伴</span></div>',unsafe_allow_html=True)
        with right:
            if view!='home': st.button('功能首页',icon=':material/home:',key='open_exploration',on_click=go_home,width='stretch')
    if view!='chat':
        if view=='home': render_home()
        elif view=='chat_setup': render_chat_setup(readiness)
        else: render_exploration(c,bool(st.session_state.get('research_confirmed')),readiness)
        render_observation_monitor(readiness)
        # Keep the frontend chat draft mounted while only the active flow is visible.
        st.html('<style>[data-testid="stBottom"]{display:none!important}</style>')
        render_composer(c,w,enabled,allow_send=False)
        return
    with st.container(key='chat_toolbar'):
        title,actions,export=st.columns([4,1.15,1.15],vertical_alignment='center')
        with title: st.markdown('<div class="conversation-heading">'+html.escape(c.title if c.state.messages else '给自己的一段时间')+'</div>',unsafe_allow_html=True)
        with actions: st.button('新对话',key='new_top',icon=':material/add:',on_click=new_chat,width='stretch')
        with export: st.download_button('导出',data=w.export_markdown(),file_name=f'zhixin-{c.id[:8]}.md',mime='text/markdown; charset=utf-8',key='export_chat',disabled=not bool(c.state.messages),on_click='ignore',icon=':material/download:',width='stretch',help='主动下载当前对话文本，不包含内部判断或密钥。')
    if st.session_state.get('notice'): st.info(st.session_state['notice'])
    if c.last_result is not None and not any(saved is c.last_result for saved in c.results.values()):
        st.warning(c.last_result.text)
    if not c.state.messages:
        render_welcome()
    else:
        for m in c.state.messages:
            with st.container(key=('user_' if m.role=='user' else 'assistant_')+m.id):
                with st.chat_message(m.role,avatar=':material/person:' if m.role=='user' else ':material/spa:'):
                    if m.role=='user':
                        st.markdown('<div class="user-copy">'+html.escape(m.content).replace('\n','<br>')+'</div>',unsafe_allow_html=True)
                    else: st.markdown(m.content)
                if m.role=='assistant':
                    result=c.results.get(m.id)
                    with st.container(horizontal=True,key='feedback_'+m.id,gap='small',vertical_alignment='center'):
                        if result: st.caption(turn_caption(result))
                        selected=c.feedback.get(m.id)
                        st.button('有帮助',icon=':material/thumb_up:',key='helpful_'+c.id+'_'+m.id,type='secondary' if selected=='helpful' else 'tertiary',on_click=feedback,args=(m.id,'helpful'))
                        st.button('需改进',icon=':material/thumb_down:',key='unhelpful_'+c.id+'_'+m.id,type='secondary' if selected=='not_helpful' else 'tertiary',on_click=feedback,args=(m.id,'not_helpful'))
                    if c.feedback.get(m.id): st.caption('反馈已记在本次会话中，不会自动上传。')
        with st.container(horizontal=True,key='conversation_footer'):
            st.caption('当前对话仅在本页保留。')
            st.button('清空本轮',key='clear_current',type='tertiary',icon=':material/delete_sweep:',on_click=clear_current)
    render_observation_entry(c)
    if not enabled:
        st.info('还差一点准备，就可以开始对话。')
        st.button('完成开始前准备',key='prepare_chat',on_click=begin_chat_setup,type='primary')
    else:
        with st.container(horizontal=True):
            st.caption('DeepSeek 已连接' if c.gateway_mode=='live' else '离线演示 · 固定示例回复')
            st.button('连接设置',key='chat_connection_settings',on_click=begin_chat_setup,type='tertiary')
    render_observation_monitor(readiness)
    if c.gateway_mode=='mock':
        st.markdown('<div class="mode-note"><span>演示模式</span> 使用固定示例回复；切换 DeepSeek 后可体验真实对话。</div>',unsafe_allow_html=True)
    render_composer(c,w,enabled)
    if st.session_state.get('show_research') and c.last_result:
        with st.expander('本轮研究记录'):
            st.json(c.last_result.model_dump())
            if c.state.previous_decision: st.json(c.state.previous_decision.model_dump())
            st.caption('这里记录软件动作和证据引用，不是诊断结论。')
