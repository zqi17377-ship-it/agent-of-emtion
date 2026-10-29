import html
import streamlit as st
from . import personality
from .model_client import make_gateway
from .schemas import ModelCallError
from .exploration_state import AXIS_LABELS,export_personality_report
from .personality_questions import QUESTION_ITEMS,CHOICE_UNSURE,score_self_report,confirmed_type
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
    state=conversation.exploration
    st.markdown('### 从对话认识自己的偏好')
    st.write('观察日常习惯中的线索，再由你确认。这里使用 MBTI 风格的四维表达，不是官方 MBTI 测试。')
    users=[m for m in conversation.state.messages if m.role=='user']
    prefix='explore_'+conversation.id+'_'
    consent=st.checkbox('同意分析当前对话中我发送的文字，探索性格偏好',key=prefix+'personality_consent',disabled=not allowed)
    can_call=allowed and consent and conversation.gateway_mode=='live' and readiness.ready and bool(st.session_state.get('api_consent')) and len(users)>=2
    observation=state.observation
    can_call=can_call and observation.request_count+observation.ledger.reserved<6
    if conversation.gateway_mode!='live': st.caption('对话分析需要 DeepSeek；离线模式可以使用下方的原创偏好问答。')
    elif len(users)<2: st.caption('先在对话页说两段自己的日常偏好，再来分析；也可以先填写下面的问答。')
    elif not st.session_state.get('api_consent'): st.caption('请先在上方确认 DeepSeek 数据流向与调用费用。')
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
                        and bool(st.session_state.get('research_confirmed')) and bool(st.session_state.get(prefix+'personality_consent')))
            gateway=_AccountedGateway(lambda:make_gateway(live=True),reservation,current)
            with st.spinner('正在核对日常偏好和原文依据…'):
                profile=personality.analyze_personality(conversation.state.messages,gateway)
            state.record_profile(profile)
            st.rerun()
        except ModelCallError:
            state.profile_error='unavailable'
            st.rerun()
        finally:
            if gateway and hasattr(gateway,'close'): gateway.close()
            if reservation: reservation.release()
    st.caption(f'每次最多两次请求；与自动对话观察共用每会话6次额外请求额度，已使用{observation.request_count}次。未知和矛盾会保留。一时情绪不能证明固定性格。')
    show_profile(conversation)
    with st.expander('补充八题偏好自述 · 本机计算'):
        st.caption('原创、非标准化的自我探索问题，没有好坏答案，可以选择“看情况”。不会发送给模型。')
        with st.form(prefix+'self_report'):
            answers={}
            for question in QUESTION_ITEMS:
                values=['unknown',question.left_pole,question.right_pole]
                labels={'unknown':CHOICE_UNSURE,question.left_pole:question.left_label,question.right_pole:question.right_label}
                old=state.self_answers.get(question.id,'unknown')
                answers[question.id]=st.radio(question.prompt,values,index=values.index(old),format_func=lambda value,labels=labels:labels[value],key=prefix+'preference_'+question.id,disabled=not allowed)
            submitted=st.form_submit_button('保存偏好自述',key='save_personality_self_report',disabled=not allowed)
        if submitted:
            state.self_answers=dict(answers)
            st.rerun()
    if state.self_answers:
        st.markdown('#### 你在原创问答中的偏好')
        for axis,pole in score_self_report(state.self_answers).items():
            label='两端都有，暂不归类' if pole=='mixed' else '待补充' if pole=='unknown' else pole
            st.write(AXIS_LABELS[axis][0]+'：'+label)
    with st.expander('我的自我确认 · 可以留空'):
        st.caption('这是你自行认可的偏好，不是模型给你的结论；与对话线索不同也没关系。')
        for axis,labels in AXIS_LABELS.items():
            options=['unknown',*axis]
            display={'unknown':'暂不确认',axis[0]:labels[1],axis[1]:labels[2]}
            old=state.confirmations.get(axis,'unknown')
            value=st.selectbox(labels[0],options,index=options.index(old),format_func=lambda v,display=display:display[v],key=prefix+'confirm_'+axis,disabled=not allowed)
            state.confirmations[axis]=value
    own=confirmed_type(state.confirmations)
    if own: st.success('你自行确认的偏好：'+own+'。它可以随着你的理解继续调整。')
    if state.profile or state.self_answers or own:
        st.download_button('导出性格探索记录',data=export_personality_report(state,conversation.state.messages),file_name='personality-exploration.md',mime='text/markdown',key='download_personality',on_click='ignore')
