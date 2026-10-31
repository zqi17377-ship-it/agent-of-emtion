"""Opt-in settings, finite background monitoring and correctable observations."""
import streamlit as st
from .model_client import make_gateway
from .observation_scheduler import configure_observation,correct_observation,count_candidates,eligibility_reason,AUTO_FIRST_MESSAGES,AUTO_FIRST_CHARS,AUTO_NEW_MESSAGES
from .observation_jobs import start_observation,poll_observation
from .exploration_state import exploration_paused
from .session_connection import get_session_settings
from .observation_presentation import describe_observation

DOMAIN_LABELS={'mbti':'MBTI风格偏好','big_five':'大五人格线索','attachment':'关系中的依恋倾向'}
DOMAIN_DESCRIPTIONS={'mbti':'从日常例子中探索社交恢复、关注信息、做决定和安排事情的偏好。','big_five':'了解外向性、宜人性、尽责性、负性情绪倾向和经验开放性的线索。','attachment':'围绕同一段关系，探索对回应和亲近距离的感受；聊天后可标注匿名关系对象。'}
DIMENSION_LABELS={'EI':'社交恢复方式','SN':'信息关注','TF':'决策偏好','JP':'安排方式','extraversion':'外向性','agreeableness':'宜人性','conscientiousness':'尽责性','neuroticism':'负性情绪倾向','openness':'经验开放性','anxiety':'关系焦虑','avoidance':'亲近回避'}
RELATIONS={'partner':'伴侣','friend':'朋友','parent':'家人','other':'其他重要关系'}
MODE_LABELS={'off':'关闭','manual':'仅在我点击时整理','auto':'达到门槛后自动整理'}
DIRECTION_LABELS={'higher':'有较多相关线索','lower':'有较少相关线索','mixed':'不同方向的线索并存','unknown':'信息不足'}


def open_observation():
    st.session_state['workspace_view']='exploration'
    st.session_state['exploration_tool']='conversation_observation'
    st.session_state['feature_flow_active']=True


def _setup_draft(c):
    state=c.exploration.observation
    return c.exploration.flows.setdefault('observation_setup',{'step':0,'domains':list(state.domains or DOMAIN_LABELS),'mode':state.mode if state.mode!='off' else 'manual','consent':False,'page':'done' if state.mode!='off' else 'setup'})


def open_observation_report():
    c=st.session_state['workspace'].active
    _setup_draft(c)['page']='report'
    open_observation()


def open_observation_relations():
    c=st.session_state['workspace'].active
    _setup_draft(c)['page']='relations'
    open_observation()


def return_to_chat():
    st.session_state['workspace_view']='chat'
    st.session_state['feature_flow_active']=False


def revoke_observation_consents():
    workspace=st.session_state.get('workspace')
    if workspace:
        for c in workspace.items:
            configure_observation(c.exploration.observation,'off',())
            prefix='explore_'+c.id+'_observe_'
            st.session_state[prefix+'consent']=False
            draft=c.exploration.flows.get('observation_setup')
            if draft: draft.update(consent=False,page='setup',step=0)
            personality=c.exploration.flows.get('personality')
            if personality: personality.update(consent=False,page='scope')
            st.session_state.pop('personality_'+c.id+'_consent',None)
            for key in list(st.session_state):
                if key.startswith(prefix) and key.endswith('consent'): st.session_state[key]=False


def _authorized(c,readiness):
    return bool(st.session_state.get('research_confirmed')) and bool(st.session_state.get('api_consent')) and readiness.ready and c.gateway_mode=='live'


def export_observation_report(c):
    state=c.exploration.observation
    lines=['# 对话中的性格与关系观察','','分析对象：本次成年人虚构案例中的叙述者。探索性线索，不是官方施测、量表得分或心理诊断。']
    if not state.report: return '\n'.join(lines)
    for observation in state.report.observations:
        view=describe_observation(observation)
        lines.extend(['','## '+DIMENSION_LABELS.get(observation.dimension,observation.dimension),
                      view.level_label+' · '+view.direction_label,view.summary])
        if getattr(observation,'coverage_reason',''): lines.append(observation.coverage_reason)
        if observation.relation_id: lines.append('本次匿名关系：'+observation.relation_id)
        for item in observation.evidence: lines.append('依据：'+item.quote)
        for item in observation.counter_evidence: lines.append('不同线索：'+item.quote)
        for alternative in view.alternatives: lines.append(alternative)
        lines.append('下一步可以聊：'+view.next_question)
    return '\n'.join(lines)


def render_observation_entry(c,readiness):
    state=c.exploration.observation
    mode=MODE_LABELS.get(state.mode,'关闭')
    if state.mode=='off':
        with st.container(key='observation_entry',horizontal=True,vertical_alignment='center'):
            st.caption('性格探索未开启')
            st.button('设置对话探索',key='open_conversation_observation',icon=':material/psychology:',type='tertiary',on_click=open_observation)
        return
    from .observation_progress import observation_progress
    status=observation_progress(state,c.state.messages,authorized=_authorized(c,readiness),live=c.gateway_mode=='live',paused=exploration_paused(c.state.previous_decision))
    with st.container(key='observation_entry',horizontal=True,vertical_alignment='center'):
        st.caption('性格探索 · '+status.title)
        st.button('打开观察报告',key='open_conversation_report',type='tertiary',on_click=open_observation_report)
        with st.popover('探索详情',icon=':material/tune:',type='tertiary',key='observation_details'):
            st.caption(mode+' · '+'、'.join(DOMAIN_LABELS[x] for x in state.domains))
            if status.fraction is not None:
                st.progress(status.fraction)
            st.write(status.detail)
            st.caption('进度仅表示聊天资料量，不代表性格分数或判断准确度。')
            st.button('设置对话探索',key='open_conversation_observation',icon=':material/psychology:',type='tertiary',on_click=open_observation)
            if 'attachment' in state.domains:
                st.button('管理匿名关系对象',key='open_conversation_relations',type='tertiary',on_click=open_observation_relations)


@st.fragment(run_every='1s')
def render_observation_monitor(readiness):
    c=st.session_state['workspace'].active
    state=c.exploration.observation
    authorized=_authorized(c,readiness)
    paused=exploration_paused(c.state.previous_decision)
    accepted=poll_observation(state,c.state.messages,authorized=authorized,live=c.gateway_mode=='live',paused=paused)
    if accepted:
        st.rerun(scope='app')
    settings=get_session_settings()
    started=start_observation(state,c.state.messages,c.id,lambda:make_gateway(settings=settings,purpose='observation'),manual=False,authorized=authorized,live=c.gateway_mode=='live',paused=paused)
    if started:
        st.rerun(scope='app')
    if state.pending_job is not None and st.session_state.get('workspace_view')!='chat':
        st.caption('正在后台整理对话线索，你可以继续聊天。')


def render_observation_panel(c,allowed,readiness):
    from .flow_ui import step_header,research_checkbox,api_checkbox
    state=c.exploration.observation
    prefix='explore_'+c.id+'_observe_'
    widget=prefix+'wizard_'
    draft=_setup_draft(c)
    if state.mode!='off':
        if st.button('暂停并撤回对话观察同意',key='observation_revoke'):
            configure_observation(state,'off',())
            draft.update(consent=False,page='setup',step=0)
            st.session_state.pop(widget+'consent',None)
            st.rerun()
    page=draft.get('page','setup')
    if page!='setup':
        if page=='done':
            st.markdown('### 对话探索已启用' if state.mode!='off' else '### 对话探索已暂停')
            st.write('当前方式：'+MODE_LABELS[state.mode])
            st.caption(f'额外请求 {state.request_count} / 6 · 已报告token {state.total_tokens}')
            for target,key,label in [('setup','observation_modify','修改设置'),('relations','observation_relations','管理关系对象'),('annotations','observation_annotations','逐条消息标注'),('report','observation_report','查看观察报告')]:
                if st.button(label,key=key):
                    draft['page']=target
                    if target=='setup': draft['step']=0;draft['consent']=False;st.session_state.pop(widget+'consent',None)
                    st.rerun()
        else:
            if st.button('返回探索状态',key='observation_done'):
                draft['page']='done';st.rerun()
            if page=='relations': _render_relations(c,allowed,prefix)
            elif page=='annotations': _render_annotations(c,prefix)
            else: _render_report(c,readiness,prefix)
        return
    steps=['了解范围','连接与API费用','选择主题','选择整理方式','同意并确认启用']
    index=draft['step']
    step_header('从对话探索自己',steps,index)
    valid=True
    if index==0:
        st.write('围绕本次成年人虚构案例，一次聊一个具体问题，再整理行为、动机、情境和不同做法。已有线索会分层展示，不必等所有维度都充分。')
        valid=research_checkbox(widget+'research')
    elif index==1:
        st.write('此功能使用 DeepSeek 分析你允许的用户文字，会产生额外调用费用。使用本次会话中保存的API配置。')
        st.caption('连接配置已就绪' if readiness.ready else '连接配置尚未就绪，请先打开API设置。')
        if st.button('打开API设置',key='observation_api_settings'):
            from .api_settings_ui import open_api_settings
            open_api_settings()
            st.rerun()
        mixed=c.gateway_mode!='live' and bool(c.state.messages)
        if mixed: st.info('这段历史对话来自旧版连接，请先新开API对话。')
        valid=api_checkbox(widget+'api') and readiness.ready and not mixed
        if valid and c.gateway_mode!='live':
            c.gateway_mode='live'
    elif index==2:
        st.write('你想从聊天中了解哪些方面？可以选择一个或多个主题。')
        selected=[]
        for domain,label in DOMAIN_LABELS.items():
            with st.container(key='observe_domain_card_'+domain,border=True):
                checked=st.checkbox(label,value=domain in draft['domains'],key=widget+'domain_'+domain)
                st.caption(DOMAIN_DESCRIPTIONS[domain])
            if checked: selected.append(domain)
        draft['domains']=selected
        st.caption(f'已选择 {len(selected)} 个主题。你可以稍后在聊天页修改。')
        if not selected: st.info('至少选择一个主题，才能继续。')
        valid=bool(draft['domains'])
    elif index==3:
        st.write('选择什么时候整理聊天中的线索。两种方式都可以先自由聊天。')
        draft['mode']=st.radio('分析方式',['manual','auto'],index=1 if draft['mode']=='auto' else 0,format_func=MODE_LABELS.get,key=widget+'mode',captions=['由你决定整理时机。至少积累2条有效用户消息后，在观察报告页点击整理。',f'先自由聊天；{AUTO_FIRST_MESSAGES}条有效表达且累计至少{AUTO_FIRST_CHARS}字后初步整理，之后每新增{AUTO_NEW_MESSAGES}条复查，最多3次。'])
        st.caption('手动、自动和格式修复合计最多6次额外请求；支持对话的请求另计。')
    else:
        st.write('主题：'+'、'.join(DOMAIN_LABELS[x] for x in draft['domains']))
        st.write('整理方式：'+MODE_LABELS[draft['mode']])
        st.caption('确认后将直接进入当前聊天，可以从一件具体的日常小事说起。设置与报告可随时从聊天页打开。')
        draft['consent']=st.checkbox('同意分析本对话的用户文字，知悉会额外调用 DeepSeek',value=draft['consent'],key=widget+'consent')
        if st.button('启用并开始对话',key='observation_confirm',type='primary',disabled=not draft['consent'] or not _authorized(c,readiness)):
            configure_observation(state,draft['mode'],tuple(draft['domains']))
            draft['page']='done'
            st.session_state['workspace_view']='chat'
            st.session_state['feature_flow_active']=False
            st.rerun()
    with st.container(key='observation_navigation',horizontal=True):
        if index>0 and st.button('上一步',key='observation_back'):
            draft['step']-=1;st.rerun()
        if index<4 and st.button('下一步',key='observation_next',type='primary',disabled=not valid):
            draft['step']+=1;st.rerun()


def _render_relations(c,allowed,prefix):
    state=c.exploration.observation
    st.markdown('### 管理关系对象')
    st.caption('依恋观察需要明确是哪段关系。这里使用匿名代号；两位朋友分别建立对象。')
    st.caption('新建对象后，会选为下一条消息的对象；可以在聊天页更改。')
    kind=st.selectbox('新增关系类别',list(RELATIONS),format_func=RELATIONS.get,key=prefix+'new_relation_kind')
    if st.button('添加匿名关系',key=prefix+'add_relation',disabled=not allowed or len(state.relations)>=12):
        index=1
        while f'{kind}_{index}' in state.relations: index+=1
        state.relations[f'{kind}_{index}']=kind
        state.observation_revision+=1
        st.session_state[prefix+'next_relation']=f'{kind}_{index}'
        st.rerun()
    if state.relations:
        for relation_id,kind in state.relations.items():
            st.write(RELATIONS.get(kind,'关系')+' · '+relation_id)
        st.caption('对象已保留。返回探索状态后，可进入逐条消息标注。')
        st.button('返回聊天并继续',key=prefix+'relations_chat',on_click=return_to_chat,type='primary')
    else: st.info('先添加一个匿名关系对象，再返回探索状态进入逐条消息标注。')


def _render_annotations(c,prefix):
    state=c.exploration.observation
    st.markdown('### 逐条消息标注')
    users=[m for m in c.state.messages if m.role=='user']
    if not state.relations:
        st.info('还没有关系对象。请返回探索状态，进入管理关系对象添加匿名对象。')
        return
    if not users:
        st.info('当前还没有你的消息。请先回到对话，说说与这段关系有关的日常例子，再来标注。')
        return
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


def _render_report(c,readiness,prefix):
    state=c.exploration.observation
    st.markdown('### 观察报告')
    count,chars=count_candidates(c.state.messages)
    st.caption(f'当前候选消息 {count} 条 · 非空白内容 {chars} 字 · 额外请求 {state.request_count} / 6')
    reason=eligibility_reason(state,c.state.messages,manual=True,live=c.gateway_mode=='live',authorized=_authorized(c,readiness),paused=exploration_paused(c.state.previous_decision))
    if st.button('整理当前对话线索',key='analyze_observations',type='primary',disabled=reason is not None):
        settings=get_session_settings()
        start_observation(state,c.state.messages,c.id,lambda:make_gateway(settings=settings,purpose='observation'),manual=True,authorized=_authorized(c,readiness),live=c.gateway_mode=='live',paused=exploration_paused(c.state.previous_decision))
        st.rerun()
    if reason=='unchanged': st.caption('当前资料已尝试整理；补充新例子后可再次查看。')
    if reason=='budget': st.info('本对话的额外请求额度已用完。仍可查看已有观察。')
    if state.error_code:
        error_text={'context_limit':'当前分析材料超过16,000字符上限，这不是性格信息不足。请导出后选取一段完整案例另开对话。',
                    'invalid_response':'这次分析的结构或原话引用未通过校验，保留上次结果。',
                    'timeout':'这次后台分析等待超时，保留上次结果。',
                    'deadline':'这次后台分析已达到等待时限，保留上次结果。',
                    'budget':'本次分析的请求额度已用完，仍可查看已有观察。'}
        st.warning(error_text.get(state.error_code,'这次整理未完成，已有观察保留；没有自动无限重试。'))
    if state.report is None: st.info('尚未生成观察报告。')
    report=state.report
    if report:
        if state.is_stale(c.state.messages): st.warning('对话或标注已更新；下面保留上次快照的观察，等待下一次整理。')
        st.markdown('#### 本次对话观察')
        st.caption('本次案例的初步线索、多次经历支持和情境差异分开呈现；可展开核对原话。')
        if not report.observations: st.info('目前没有足够的本人日常例子，暂不形成观察。')
        for observation in report.observations:
            view=describe_observation(observation)
            with st.container(border=True):
                st.markdown('**'+DIMENSION_LABELS.get(observation.dimension,observation.dimension)+'** · '+view.level_label)
                st.write(view.direction_label)
                st.write(view.summary)
                if getattr(observation,'coverage_reason',''): st.caption(observation.coverage_reason)
                if observation.relation_id: st.caption('匿名关系：'+observation.relation_id)
                with st.expander('查看原话与待核对解释'):
                    for item in observation.evidence: st.write('依据：'+item.quote)
                    for item in observation.counter_evidence: st.write('不同线索：'+item.quote)
                    for alternative in view.alternatives: st.write(alternative)
                st.write('下一步可以聊：'+view.next_question)
                columns=st.columns(3)
                for column,action,label in zip(columns,('disagree','state','delete'),('不认同','暂不讨论此面向','删除观察')):
                    column.button(label,key=prefix+action+'_'+observation.key,on_click=correct_observation,args=(state,observation.key,action),type='tertiary')
        st.download_button('导出对话观察记录',data=export_observation_report(c),file_name='conversation-observations.md',mime='text/markdown',key='download_observations',on_click='ignore')
