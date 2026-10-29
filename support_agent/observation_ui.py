"""Opt-in settings, finite background monitoring and correctable observations."""
import streamlit as st
from .model_client import make_gateway
from .observation_scheduler import configure_observation,correct_observation,count_candidates,eligibility_reason
from .observation_jobs import start_observation,poll_observation
from .exploration_state import exploration_paused

DOMAIN_LABELS={'mbti':'MBTI风格偏好','big_five':'大五人格线索','attachment':'关系中的依恋倾向'}
DIMENSION_LABELS={'EI':'社交恢复方式','SN':'信息关注','TF':'决策偏好','JP':'安排方式','extraversion':'外向性','agreeableness':'宜人性','conscientiousness':'尽责性','neuroticism':'负性情绪倾向','openness':'经验开放性','anxiety':'关系焦虑','avoidance':'亲近回避'}
RELATIONS={'partner':'伴侣','friend':'朋友','parent':'家人','other':'其他重要关系'}
MODE_LABELS={'off':'关闭','manual':'仅在我点击时整理','auto':'达到门槛后自动整理'}
DIRECTION_LABELS={'higher':'有较多相关线索','lower':'有较少相关线索','mixed':'不同方向的线索并存','unknown':'信息不足'}


def open_observation():
    st.session_state['workspace_view']='exploration'
    st.session_state['exploration_tool']='conversation_observation'


def revoke_observation_consents():
    workspace=st.session_state.get('workspace')
    if workspace:
        for c in workspace.items:
            configure_observation(c.exploration.observation,'off',())
            prefix='explore_'+c.id+'_observe_'
            st.session_state[prefix+'consent']=False


def _sync_settings(conversation,prefix):
    state=conversation.exploration.observation
    consent=bool(st.session_state.get(prefix+'consent')) and bool(st.session_state.get('research_confirmed'))
    mode=st.session_state.get(prefix+'mode','manual') if consent else 'off'
    domains=tuple(st.session_state.get(prefix+'domains',list(DOMAIN_LABELS)))
    configure_observation(state,mode,domains)


def _authorized(c,readiness):
    return bool(st.session_state.get('research_confirmed')) and bool(st.session_state.get('api_consent')) and readiness.ready and c.gateway_mode=='live'


def export_observation_report(c):
    state=c.exploration.observation
    lines=['# 对话中的性格与关系观察','','探索性线索，不是官方施测、量表得分或心理诊断。']
    if not state.report: return '\n'.join(lines)
    for observation in state.report.observations:
        lines.extend(['','## '+DIMENSION_LABELS.get(observation.dimension,observation.dimension),
                      DIRECTION_LABELS.get(observation.direction,observation.direction)])
        if observation.relation_id: lines.append('本次匿名关系：'+observation.relation_id)
        for item in observation.evidence: lines.append('依据：'+item.quote)
        for item in observation.counter_evidence: lines.append('不同线索：'+item.quote)
    return '\n'.join(lines)


def render_observation_entry(c):
    with st.container(key='observation_entry',horizontal=True,vertical_alignment='center'):
        mode=MODE_LABELS.get(c.exploration.observation.mode,'关闭')
        st.caption('对话观察 · '+mode)
        st.button('设置对话探索',key='open_conversation_observation',icon=':material/psychology:',type='tertiary',on_click=open_observation)


@st.fragment(run_every='1s')
def render_observation_monitor(readiness):
    c=st.session_state['workspace'].active
    state=c.exploration.observation
    authorized=_authorized(c,readiness)
    paused=exploration_paused(c.state.previous_decision)
    accepted=poll_observation(state,c.state.messages,authorized=authorized,live=c.gateway_mode=='live',paused=paused)
    if accepted:
        st.rerun(scope='app')
    start_observation(state,c.state.messages,c.id,lambda:make_gateway(live=True),manual=False,authorized=authorized,live=c.gateway_mode=='live',paused=paused)
    if state.pending_job is not None:
        st.caption('正在后台整理对话线索，你可以继续聊天。')
    elif state.report is not None and st.session_state.get('workspace_view')!='exploration':
        st.caption('对话观察已整理，可在“设置对话探索”中查看依据与修改。')


def render_observation_panel(c,allowed,readiness):
    state=c.exploration.observation
    prefix='explore_'+c.id+'_observe_'
    st.markdown('### 让对话积累可核对的线索')
    st.write('先倾听，再按你的选择整理性格和关系观察。每个方向都会附原话，信息不足就暂不判断。')
    st.checkbox('同意分析本对话的用户文字，知悉会额外调用 DeepSeek',value=state.mode!='off',key=prefix+'consent',disabled=not allowed,on_change=_sync_settings,args=(c,prefix))
    st.selectbox('分析方式',['manual','auto'],index=1 if state.mode=='auto' else 0,format_func=MODE_LABELS.get,key=prefix+'mode',disabled=not allowed,on_change=_sync_settings,args=(c,prefix))
    st.multiselect('允许分析的主题',list(DOMAIN_LABELS),default=list(state.domains or DOMAIN_LABELS),format_func=DOMAIN_LABELS.get,key=prefix+'domains',disabled=not allowed,on_change=_sync_settings,args=(c,prefix))
    st.caption('自动模式：20条有效用户消息且累计至少1,000字后检查；之后每新增10条复查，最多3次。轮数是产品参数，不代表已经测准。')
    st.caption('每段对话的手动、自动和格式修复合计最多6次额外请求；只分析已选择的主题。支持对话的请求另计。')
    if not allowed: st.info('请先确认成年人虚构案例的研究使用范围。')
    elif c.gateway_mode!='live': st.info('连接 DeepSeek 并确认数据流向与费用后，才能整理对话；问卷仍可在本机作答。')
    count,chars=count_candidates(c.state.messages)
    st.caption(f'当前候选消息 {count} 条 · 非空白内容 {chars} 字 · 额外请求 {state.request_count} / 6 · 已报告token {state.total_tokens}')
    if sum(len(m.content) for m in c.state.messages)>14000:
        st.warning('当前对话接近字符上限。可主动查看现有线索、导出或另开对话；不会静默删除历史。')
    reason=eligibility_reason(state,c.state.messages,manual=True,live=c.gateway_mode=='live',authorized=_authorized(c,readiness),paused=exploration_paused(c.state.previous_decision))
    if st.button('整理当前对话线索',key='analyze_observations',type='primary',disabled=reason is not None):
        start_observation(state,c.state.messages,c.id,lambda:make_gateway(live=True),manual=True,authorized=_authorized(c,readiness),live=c.gateway_mode=='live',paused=exploration_paused(c.state.previous_decision))
        st.rerun()
    if reason=='unchanged': st.caption('当前资料已尝试整理；有新的日常例子或关系标注后可再次查看。')
    if reason=='budget': st.info('本对话的额外请求额度已用完。仍可填写本机问卷和查看已有观察。')
    if state.error_code: st.warning('这次整理未完成，已有观察保留；没有自动无限重试。')
    with st.expander('标注关系对象 · 可选'):
        st.caption('依恋观察需要明确是哪段关系。这里使用匿名代号；两位朋友分别建立对象。')
        kind=st.selectbox('新增关系类别',list(RELATIONS),format_func=RELATIONS.get,key=prefix+'new_relation_kind')
        if st.button('添加匿名关系',key=prefix+'add_relation',disabled=not allowed or len(state.relations)>=12):
            index=1
            while f'{kind}_{index}' in state.relations: index+=1
            state.relations[f'{kind}_{index}']=kind
            state.observation_revision+=1
            st.rerun()
        users=[m for m in c.state.messages if m.role=='user']
        if users and state.relations:
            ids=[m.id for m in users]
            texts={m.id:m.content for m in users}
            mid=st.selectbox('选择本人谈到关系的消息',ids,format_func=lambda key:texts[key][:60],key=prefix+'relation_message')
            rid=st.selectbox('这条消息主要谈到的对象',['',*state.relations],format_func=lambda key:'暂不指定' if not key else RELATIONS.get(state.relations[key],'关系')+' · '+key,key=prefix+'relation_object')
            if st.button('保存这条关系标注',key=prefix+'save_relation'):
                if rid: state.message_relations[mid]=rid
                else: state.message_relations.pop(mid,None)
                state.observation_revision+=1
                st.rerun()
            st.caption('同一条消息混合多个对象时，请拆开叙述或暂不指定，不用这条消息建立某一关系的结论。')
    report=state.report
    if report:
        if state.is_stale(c.state.messages): st.warning('对话或标注已更新；下面保留上次快照的观察，等待下一次整理。')
        st.markdown('#### 本次对话观察')
        st.caption('单向习惯需多个不同事件与情境支持。文字校验不证明心理解释正确，你可以修正。')
        if not report.observations: st.info('目前没有足够的本人日常例子，暂不形成观察。')
        for observation in report.observations:
            with st.container(border=True):
                st.markdown('**'+DIMENSION_LABELS.get(observation.dimension,observation.dimension)+'** · '+DIRECTION_LABELS.get(observation.direction,observation.direction))
                if observation.relation_id: st.caption('匿名关系：'+observation.relation_id)
                for item in observation.evidence: st.write('依据：'+item.quote)
                for item in observation.counter_evidence: st.write('不同线索：'+item.quote)
                columns=st.columns(3)
                for column,action,label in zip(columns,('disagree','state','delete'),('不认同','只谈本次感受','删除观察')):
                    column.button(label,key=prefix+action+'_'+observation.key,on_click=correct_observation,args=(state,observation.key,action),type='tertiary')
        st.download_button('导出对话观察记录',data=export_observation_report(c),file_name='conversation-observations.md',mime='text/markdown',key='download_observations',on_click='ignore')
    with st.expander('想补充一些例子？'):
        st.write('这是这次事件的反应，还是在其他场合也经常发生？')
        st.write('对方没有马上回复时，你通常会怎样理解，后来会怎么做？')
        st.caption('可以回到对话补充，也可以跳过。当前情绪不能证明固定性格。')
