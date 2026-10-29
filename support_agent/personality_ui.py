import html
import streamlit as st
from . import personality
from .model_client import make_gateway
from .schemas import ModelCallError
from .exploration_state import AXIS_LABELS,export_personality_report
from .personality_questions import QUESTION_ITEMS,CHOICE_UNSURE,score_self_report,confirmed_type,describe_self_report
from .observation_jobs import _AccountedGateway


def show_profile(conversation):
    state=conversation.exploration
    profile=state.profile
    if state.profile_error:
        st.warning('这次分析未完成，请稍后重试；已有观察会保留，但不会用失败结果覆盖。')
    if profile is None: return
    if state.is_stale(conversation.state.messages):
        st.warning('对话有了新内容。下面是上次的观察，点击更新后再参考。')
    if profile.type_hint=='????': st.info('目前还没有足够的日常线索形成参考类型。')
    else: st.markdown('#### 对话参考：'+' '.join(profile.type_hint)+'　· 待你确认')
    columns=st.columns(4)
    for axis,column in zip(profile.axes,columns):
        with column:
            letter=axis.leaning if axis.leaning not in ('unknown','mixed') else '—'
            st.markdown(f'<div class="personality-axis"><span>{AXIS_LABELS[axis.axis][0]}</span><strong>{letter}</strong><small>{"不同线索并存" if axis.coverage=="conflicting" else "初步线索" if axis.coverage=="supported" else "待观察"}</small></div>',unsafe_allow_html=True)
    for axis in profile.axes:
        with st.expander(AXIS_LABELS[axis.axis][0]+' · 查看依据'):
            st.write(axis.explanation)
            for e in axis.evidence: st.markdown('依据：'+e.quote)
            for e in axis.counter_evidence: st.markdown('不同方向的线索：'+e.quote)
            if not axis.evidence and not axis.counter_evidence: st.caption('尚无可引用的日常例子。')
            st.caption('两端分别是 '+AXIS_LABELS[axis.axis][1]+' / '+AXIS_LABELS[axis.axis][2]+'，不表示好坏。')


def render_personality(conversation,allowed,readiness):
    from .flow_ui import step_header, research_checkbox, api_checkbox
    state=conversation.exploration
    flow=state.flows.setdefault('personality',{})
    page=flow.setdefault('page','menu')
    prefix='personality_'+conversation.id+'_'
    def go(target):
        flow['page']=target
        st.rerun()
    def button(label,key,target,disabled=False):
        if st.button(label,key=prefix+key,disabled=disabled): go(target)
    st.markdown('### 认识自己的偏好')
    st.caption('MBTI 风格的自我探索，不是官方 MBTI 测试。')
    if page=='menu':
        for label,target in [('从对话观察偏好','scope'),('八题偏好问答','self_intro'),('我的自我确认','confirm_intro'),('查看已保存记录','results')]:
            button(label,'open_'+target,target)
        if st.button('返回功能选择',key=prefix+'tools'):
            st.session_state['feature_flow_active']=False
            st.session_state['workspace_view']='exploration'
            st.rerun()
        return
    if st.button('返回人格功能',key=prefix+'menu'): go('menu')
    if page in ('self_intro','confirm_intro'):
        is_self=page=='self_intro'
        step_header('八题偏好问答' if is_self else '我的自我确认',['说明与研究确认','逐项填写','核对并保存'],0)
        st.write('八道原创、非标准化的日常偏好问题，每页一题，可选择不确定。' if is_self else '按四个维度逐项确认你认可的偏好，可以暂不确认。与对话观察不同也没关系。')
        st.caption('答案仅在本机计算与保存，不会发送给模型。')
        confirmed=research_checkbox(prefix+page+'_research')
        button('开始八题问答' if is_self else '开始自我确认','start_'+page,'questions' if is_self else 'confirm',not confirmed)
        return
    if page in ('questions','self_review','confirm','confirm_review'):
        is_self=page in ('questions','self_review')
        items=QUESTION_ITEMS if is_self else list(AXIS_LABELS)
        draft_key='answers' if is_self else 'confirmations'
        index_key='question_index' if is_self else 'confirmation_index'
        draft=flow.setdefault(draft_key,dict(state.self_answers if is_self else state.confirmations))
        index=flow.setdefault(index_key,0)
        review=page.endswith('review')
        step_header('八题偏好问答' if is_self else '我的自我确认',[f'第 {i+1} 项' for i in range(len(items))]+['核对并保存'],len(items) if review else index)
        st.caption('本机计算，不发送给模型。可以选择不确定，返回后草稿会保留。')
        if review:
            for item in items:
                key=item.id if is_self else item
                value=draft.get(key,'unknown')
                st.write((item.prompt if is_self else AXIS_LABELS[item][0])+'：'+('不确定 / 看情况' if value=='unknown' else value))
            if st.button('返回修改',key=prefix+'edit'):
                flow[index_key]=len(items)-1
                go('questions' if is_self else 'confirm')
            if st.button('保存偏好自述' if is_self else '保存自我确认',key=prefix+'save_'+draft_key,disabled=not bool(st.session_state.get('research_confirmed'))):
                if is_self: state.self_answers=dict(draft)
                else: state.confirmations=dict(draft)
                go('results')
            return
        item=items[index]
        key=item.id if is_self else item
        options=['unknown',item.left_pole,item.right_pole] if is_self else ['unknown',*item]
        labels=({'unknown':CHOICE_UNSURE,item.left_pole:item.left_label,item.right_pole:item.right_label} if is_self else {'unknown':'暂不确认',item[0]:AXIS_LABELS[item][1],item[1]:AXIS_LABELS[item][2]})
        value=st.radio(item.prompt if is_self else AXIS_LABELS[item][0],options,index=options.index(draft.get(key,'unknown')),format_func=lambda v:labels[v],key=prefix+draft_key+'_'+key,disabled=not bool(st.session_state.get('research_confirmed')))
        draft[key]=value
        st.caption(f'已完成 {index+1} / {len(items)} 项，剩余 {len(items)-index-1} 项')
        if st.button('上一题' if is_self else '上一项',key=prefix+'previous',disabled=index==0):
            flow[index_key]=index-1
            st.rerun()
        if st.button('下一题' if is_self else '下一项',key=prefix+'next',disabled=not bool(st.session_state.get('research_confirmed'))):
            if index+1==len(items): go('self_review' if is_self else 'confirm_review')
            flow[index_key]=index+1
            st.rerun()
        return
    if page=='results':
        show_profile(conversation)
        if state.self_answers:
            st.markdown('#### 你在原创问答中的偏好')
            for axis,pole in score_self_report(state.self_answers).items():
                st.write(AXIS_LABELS[axis][0]+'：'+('两端都有，暂不归类' if pole=='mixed' else '待补充' if pole=='unknown' else pole))
            st.markdown(describe_self_report(state.self_answers))
        own=confirmed_type(state.confirmations)
        if own: st.success('你自行确认的偏好：'+own)
        if not state.profile and not state.self_answers and not state.confirmations: st.info('还没有保存的记录。可以先填写本机偏好问答。')
        else: st.download_button('导出性格探索记录',data=export_personality_report(state,conversation.state.messages),file_name='personality-exploration.md',mime='text/markdown',key=prefix+'download',on_click='ignore')
        return
    steps=['确认范围与研究用途','了解并单独同意','确认连接','主动开始分析']
    step_header('从对话观察偏好',steps,{'scope':0,'consent':1,'connection':2,'analyze':3}.get(page,0))
    if page=='scope':
        st.write('仅分析当前对话中你发送的文字；一时情绪不能证明固定性格。')
        research=research_checkbox(prefix+'research')
        button('下一步','scope_next','consent',not research)
        return
    if page=='consent':
        st.write('模型根据日常偏好寻找原文依据；未知与矛盾会保留，结果由你确认。')
        consent=st.checkbox('同意分析当前对话中我发送的文字，探索性格偏好',value=flow.get('consent',False),key=prefix+'consent')
        flow['consent']=consent
        button('上一步','consent_previous','scope')
        button('下一步','consent_next','connection',not consent or not st.session_state.get('research_confirmed'))
        return
    if page=='connection':
        st.write('连接已就绪' if conversation.gateway_mode=='live' and readiness.ready else '对话分析需要先连接 DeepSeek；本机问答无需连接。')
        api=api_checkbox(prefix+'api')
        if st.button('设置模型连接',key=prefix+'setup'):
            from .onboarding_ui import begin_chat_setup
            begin_chat_setup(return_to='mbti')
            st.rerun()
        button('上一步','connection_previous','consent')
        button('下一步','connection_next','analyze',not (api and readiness.ready and conversation.gateway_mode=='live' and flow.get('consent') and st.session_state.get('research_confirmed')))
        return
    users=[m for m in conversation.state.messages if m.role=='user']
    observation=state.observation
    can_call=bool(st.session_state.get('research_confirmed')) and flow.get('consent') and conversation.gateway_mode=='live' and readiness.ready and bool(st.session_state.get('api_consent')) and bool(st.session_state.get('research_confirmed')) and len(users)>=2
    can_call=can_call and observation.request_count+observation.ledger.reserved<6
    if len(users)<2: st.info('先在对话页说两段自己的日常偏好，再来分析。')
    unchanged=state.profile is not None and not state.is_stale(conversation.state.messages) and state.profile_error is None
    if st.button('更新对话性格观察' if state.profile else '分析当前对话',key='analyze_personality',type='primary',disabled=not can_call or unchanged):
        gateway=None
        reservation=observation.ledger.reserve(2)
        generation=observation.generation
        revision=observation.consent_revision
        try:
            if reservation is None:
                st.warning('本对话的额外请求额度已用完。')
                return
            def current():
                return (conversation.exploration.observation is observation and observation.generation==generation
                        and observation.consent_revision==revision and bool(st.session_state.get('api_consent'))
                        and bool(st.session_state.get('research_confirmed')) and bool(flow.get('consent')))
            gateway=_AccountedGateway(lambda:make_gateway(live=True),reservation,current)
            with st.spinner('正在核对日常偏好和原文依据…'):
                profile=personality.analyze_personality(conversation.state.messages,gateway)
            state.record_profile(profile)
            flow['page']='results'
            st.rerun()
        except ModelCallError:
            state.profile_error='unavailable'
            flow['page']='results'
            st.rerun()
        finally:
            if gateway and hasattr(gateway,'close'): gateway.close()
            if reservation: reservation.release()
    st.caption(f'每次最多两次请求；与自动对话观察共用每会话6次额外请求额度，已使用{observation.request_count}次。')
    button('上一步','analyze_previous','connection')
