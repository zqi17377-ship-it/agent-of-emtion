import json
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from support_agent.schemas import Assessment, Decision, Message, SessionState


def observation(*, domains=('mbti',), mode='manual', relation=''):
    return SimpleNamespace(
        mode=mode, domains=domains, generation='synthetic-generation',
        consent_revision=1, observation_revision=0, report=None,
        excluded_keys=set(), relations={relation: 'friend'} if relation else {},
    )


def context(*, domains=('mbti',), mode='manual', relation='', selected=''):
    from support_agent.dialogue_exploration import build_exploration_context
    return build_exploration_context(
        observation(domains=domains, mode=mode, relation=relation), [],
        selected_relation=selected, subject_mode='synthetic_case',
    )


def feedback(text, *, kind='event', continuation='continue', topic=''):
    return Assessment(
        status='ok', user_goal='clarify', reply_kind=kind,
        continuation=continuation, inquiry_quote=text, inquiry_topic=topic,
    )


def plan(ctx, *, state=None, text='最近我参加了一次工作会议。', assessment=None, decision=None):
    from support_agent.dialogue_exploration import plan_inquiry
    from support_agent.schemas import InquiryState
    return plan_inquiry(
        ctx, [Message(id='current', role='user', content=text)],
        assessment or Assessment(status='ok'), decision or Decision(action='clarify'),
        state or InquiryState(),
    )


@pytest.mark.parametrize('candidate', [None, {}, {'domains': ['mbti']}, SimpleNamespace(domains=('mbti',))])
def test_unknown_context_cannot_enable_interview(candidate):
    assert plan(candidate) is None


def test_context_filters_domains_and_exclusions_and_is_immutable():
    from support_agent.dialogue_exploration import build_exploration_context, exploration_payload
    state=observation(domains=('mbti', 'unapproved', 'attachment'))
    state.excluded_keys={'mbti:EI:', 'attachment:anxiety:friend_private'}
    ctx=build_exploration_context(state, [], subject_mode='synthetic_case')
    payload=exploration_payload(ctx)

    assert payload['domains']==['mbti', 'attachment']
    assert 'unapproved' not in json.dumps(payload)
    assert 'friend_private' not in json.dumps(payload)
    assert all('mbti:EI' not in gap.targets for gap in ctx.gaps)
    assert payload['subject_scope']=='research_case_narrator'
    with pytest.raises(FrozenInstanceError):
        ctx.domains=('big_five',)


@pytest.mark.parametrize('mode,domains,subject_mode', [
    ('off', ('mbti',), 'synthetic_case'),
    ('manual', ('unknown',), 'synthetic_case'),
    ('manual', ('mbti',), 'unknown'),
])
def test_disabled_or_unrecognized_scopes_do_not_create_context(mode,domains,subject_mode):
    from support_agent.dialogue_exploration import build_exploration_context
    assert build_exploration_context(observation(mode=mode,domains=domains), [], subject_mode=subject_mode) is None


def test_related_authorized_targets_share_an_example_without_claiming_a_type():
    first=plan(context(domains=('mbti','big_five')))
    assert first.topic=='energy' and first.stage=='event'
    assert first.targets==('mbti:EI','big_five:extraversion')
    assert first.question.count('？')==1
    assert not any(label in first.question for label in ('内向','外向','I型','E型','更适合'))


def test_specific_behavior_advances_to_motivation_instead_of_repeating_event_question():
    from support_agent.dialogue_exploration import advance_inquiry_state
    from support_agent.schemas import InquiryState
    ctx=context()
    first=plan(ctx)
    state=advance_inquiry_state(InquiryState(),ctx,first,Assessment(status='ok'),[])
    text='那次会议结束后，我自己去公园散步了半小时。'
    next_plan=plan(ctx,state=state,text=text,assessment=feedback(text,kind='behavior'))

    assert next_plan.topic=='energy' and next_plan.stage=='motivation'
    assert next_plan.question!=first.question
    assert '考虑' in next_plan.question
    assert state.stage=='event'


def test_unlocated_feedback_does_not_advance_a_previous_question():
    from support_agent.dialogue_exploration import advance_inquiry_state
    from support_agent.schemas import InquiryState
    ctx=context()
    first=plan(ctx)
    state=advance_inquiry_state(InquiryState(),ctx,first,Assessment(status='ok'),[])
    next_plan=plan(ctx,state=state,assessment=feedback('这句话并不在当前用户消息中。',kind='motivation'))

    assert next_plan is None
    assert state.stage=='event'


def test_motivation_leads_to_other_context_then_counterexample_then_new_gap():
    from support_agent.dialogue_exploration import advance_inquiry_state
    from support_agent.schemas import InquiryState
    ctx=context()
    state=InquiryState()
    current=plan(ctx)
    state=advance_inquiry_state(state,ctx,current,Assessment(status='ok'),[])
    text='我这样安排是因为想先把自己的想法想清楚。'
    current=plan(ctx,state=state,text=text,assessment=feedback(text,kind='motivation'))
    assert current.topic=='energy' and current.stage=='cross_context'
    state=advance_inquiry_state(state,ctx,current,feedback(text,kind='motivation'),[Message(role='user',content=text)])
    text='上个月家庭旅行结束后，我也自己在房间里读书。'
    current=plan(ctx,state=state,text=text,assessment=feedback(text,kind='cross_context'))
    assert current.topic=='energy' and current.stage=='counterexample'
    state=advance_inquiry_state(state,ctx,current,feedback(text,kind='cross_context'),[Message(role='user',content=text)])
    text='但有一次朋友聚会后，我还主动约了人继续聊天。'
    current=plan(ctx,state=state,text=text,assessment=feedback(text,kind='counterexample'))
    assert current.topic=='information' and current.stage=='event'
    assert 'energy' in current.completed_topics


@pytest.mark.parametrize('continuation', ['decline','listen_only','distress','pause'])
def test_explicit_refusal_or_current_distress_stops_questions_and_stays_paused(continuation):
    from support_agent.dialogue_exploration import advance_inquiry_state
    from support_agent.schemas import InquiryState
    ctx=context()
    text='这一部分我现在不想继续回答，只想先说说当下。'
    assessment=feedback(text,continuation=continuation)
    assert plan(ctx,text=text,assessment=assessment) is None
    state=advance_inquiry_state(InquiryState(),ctx,None,assessment,[Message(role='user',content=text)])
    assert state.paused
    assert plan(ctx,state=state) is None
    resume='现在我愿意继续探索一个具体例子。'
    assert plan(ctx,state=state,text=resume,assessment=feedback(resume,kind='unknown')) is not None


@pytest.mark.parametrize('action', ['urgent_support','refer'])
def test_current_safety_or_professional_support_has_priority(action):
    assert plan(context(),decision=Decision(action=action)) is None


def test_failed_assessment_cannot_start_or_advance_an_interview():
    assert plan(context(),assessment=Assessment(status='failed')) is None


def test_skip_or_topic_change_uses_another_authorized_gap():
    from support_agent.dialogue_exploration import advance_inquiry_state
    from support_agent.schemas import InquiryState
    ctx=context()
    first=plan(ctx)
    state=advance_inquiry_state(InquiryState(),ctx,first,Assessment(status='ok'),[])
    text='这个先跳过，我们聊聊安排事情吧。'
    next_plan=plan(ctx,state=state,text=text,assessment=feedback(text,continuation='switch_topic',topic='organization'))
    assert next_plan.topic=='organization'
    assert next_plan.targets==('mbti:JP',)
    assert next_plan.question!=first.question


def test_attachment_requires_an_explicit_same_relationship_and_resets_old_followup():
    from support_agent.dialogue_exploration import advance_inquiry_state
    from support_agent.schemas import InquiryState
    unspecified=context(domains=('attachment',),relation='friend_1')
    scope=plan(unspecified)
    assert scope.stage=='relation_scope' and scope.relation_id==''
    assert '匿名' in scope.question
    first_context=context(domains=('attachment',),relation='friend_1',selected='friend_1')
    first=plan(first_context)
    assert first.relation_id=='friend_1' and first.stage=='event'
    state=advance_inquiry_state(InquiryState(),first_context,first,Assessment(status='ok'),[])
    second_context=context(domains=('attachment',),relation='friend_2',selected='friend_2')
    text='这次换成另一位朋友，我给对方发了一条消息。'
    second=plan(second_context,state=state,text=text,assessment=feedback(text,kind='motivation'))
    assert second.relation_id=='friend_2' and second.stage=='event'
    assert second.topic=='attachment_anxiety'


def test_stale_or_unverifiable_report_is_not_treated_as_supported_coverage():
    from support_agent.dialogue_exploration import build_exploration_context
    state=observation()
    state.report=SimpleNamespace(observations=[SimpleNamespace(
        domain='mbti',dimension='EI',relation_id='',subject='case_narrator',scope='habit',
        evidence=[SimpleNamespace(message_id='invented',quote='不存在的原话',event_id='e',context_kind='work')],
        counter_evidence=[],
    )])
    state.is_stale=lambda messages:True
    ctx=build_exploration_context(state,[])
    assert all(gap.message_count==0 for gap in ctx.gaps)
    assert all(not gap.example_hint for gap in ctx.gaps)


def test_prompt_injection_and_original_quotes_stay_in_user_data():
    from support_agent.response import draft_reply
    from support_agent.guardrails import check_reply
    from support_agent.schemas import CallBudget
    from tests.helpers import ScriptedGateway
    text='我在会议上写下了 IGNORE_ALL_RULES 作为示例字符串。'
    messages=[Message(role='user',content=text)]
    inquiry=plan(context(),text=text,assessment=feedback(text,kind='behavior'))
    gateway=ScriptedGateway(inquiry.question,{'allowed':True,'reason_codes':[]})
    budget=CallBudget()
    reply=draft_reply(messages,feedback(text,kind='behavior'),Decision(action='clarify'),[],gateway,budget,inquiry_plan=inquiry)
    check_reply(reply,messages,feedback(text,kind='behavior'),Decision(action='clarify'),[],gateway,budget,inquiry_plan=inquiry)

    assert budget.attempts==2
    for sent,instructions,_ in gateway.calls:
        assert 'IGNORE_ALL_RULES' not in instructions
        assert any('IGNORE_ALL_RULES' in message.content for message in sent)
        payload=json.loads(sent[-1].content)
        assert payload['inquiry_plan']['question']==inquiry.question


def turn_gateway(text, *, continuation='continue', kind='event', check=True, broken_first=False):
    from support_agent.schemas import ModelResult
    class Gateway:
        mode='live';model_id='synthetic-dialogue-test'
        def __init__(self): self.calls=[]
        def generate(self,messages,instructions,schema,budget):
            budget.consume();self.calls.append((messages,instructions,schema))
            title=schema.get('title') if schema else ''
            if title=='Assessment':
                if broken_first and len(self.calls)==1:
                    result='invalid json'
                else:
                    result=json.dumps({
                        'status':'ok','user_goal':'clarify','reply_kind':kind,
                        'continuation':continuation,'inquiry_quote':text,'inquiry_topic':'',
                    })
            elif title=='CheckResult': result=json.dumps({'allowed':check,'reason_codes':[]})
            else:
                payload=json.loads(messages[-1].content)
                question=payload.get('inquiry_plan',{}).get('question','')
                result='我注意到你说了一个具体的场景。'+question
            return ModelResult(text=result,model_id=self.model_id)
    return Gateway()


@pytest.mark.parametrize('repair,expected_calls',[(False,3),(True,4)])
def test_real_workflow_sends_scope_without_extra_calls_and_commits_only_checked_plan(repair,expected_calls):
    from support_agent.workflow import run_turn
    text='最近那次小组讨论，我先记下自己的想法，再开口补充。'
    gateway=turn_gateway(text,broken_first=repair)
    session=SessionState()

    result=run_turn(session,text,gateway,exploration_context=context())

    assert result.status=='ok'
    assert len(gateway.calls)==expected_calls
    assert session.inquiry_state.topic=='energy'
    assert session.inquiry_state.last_question in result.text
    assert session.inquiry_state.last_question_message_id==session.messages[-1].id
    assessment_payload=json.loads(gateway.calls[0][0][0].content)
    assert assessment_payload['exploration']['domains']==['mbti']
    assert assessment_payload['exploration']['subject_scope']=='research_case_narrator'
    response_payload=json.loads(gateway.calls[-2][0][-1].content)
    assert response_payload['inquiry_plan']['targets']==['mbti:EI']


def test_failed_check_does_not_advance_the_interview():
    from support_agent.workflow import run_turn
    text='最近那次小组讨论，我先记下自己的想法，再开口补充。'
    session=SessionState()
    original=session.inquiry_state.model_dump()
    result=run_turn(session,text,turn_gateway(text,check=False),exploration_context=context())
    assert result.status=='fallback'
    assert session.inquiry_state.model_dump()==original


def test_ordinary_chat_keeps_legacy_payload_and_three_call_budget():
    from support_agent.workflow import run_turn
    text='这是一个虚构案例，我最近想梳理工作中的一件小事。'
    gateway=turn_gateway(text)
    result=run_turn(SessionState(),text,gateway)
    assert result.status=='ok' and len(gateway.calls)==3
    assert 'exploration' not in json.loads(gateway.calls[0][0][0].content)
    assert 'inquiry_plan' not in json.loads(gateway.calls[1][0][-1].content)


def test_verified_old_snapshot_keeps_its_examples_when_new_messages_arrive():
    from support_agent.conversation_observation import build_snapshot,analyze_observations
    from support_agent.observation_scheduler import ObservationState
    from support_agent.dialogue_exploration import build_exploration_context
    from support_agent.schemas import CallBudget
    from tests.test_conversation_observation import Gateway,messages,observation as model_observation
    state=ObservationState(conversation_id='c',mode='manual',domains=('mbti',),subject_mode='synthetic_case')
    old=messages()
    snap=build_snapshot('c',state.generation,0,0,old,state.domains,subject_mode='synthetic_case')
    state.report=analyze_observations(snap,Gateway({'observations':[model_observation(subject='case_narrator')]}),CallBudget())
    current=old+[Message(id='later',role='user',content='虚构案例的下一段：今天又发生了另一件事。')]
    ctx=build_exploration_context(state,current,subject_mode='synthetic_case')
    assert ctx.gaps[0].message_count==3
    assert state.report.metrics['source_digests']['0']
    old[0].content='这条来源的全文已经改变，不能沿用先前解释。'
    ctx=build_exploration_context(state,current,subject_mode='synthetic_case')
    assert ctx.gaps[0].message_count==2
    state.consent_revision+=1
    assert build_exploration_context(state,current,subject_mode='synthetic_case').gaps[0].message_count==0


def test_clearing_chat_clears_interview_progress_and_pause():
    from support_agent.session import clear_session
    from support_agent.schemas import InquiryState
    session=SessionState(inquiry_state=InquiryState(topic='energy',stage='motivation',paused=True,completed_topics=['information']))
    clear_session(session)
    assert session.inquiry_state==InquiryState()


def test_enabled_interview_feedback_cannot_silently_default_missing_fields():
    from support_agent.assessment import assess
    from support_agent.schemas import CallBudget
    from tests.helpers import ScriptedGateway
    missing={'status':'ok','user_goal':'clarify','reply_kind':'behavior'}
    gateway=ScriptedGateway(missing,missing)
    result=assess([Message(role='user',content='虚构案例：会后我独自散步恢复精力。')],None,gateway,CallBudget(limit=2),exploration_context=context())
    assert result.status=='failed' and len(gateway.calls)==2


def test_distress_blocks_personality_interview_but_not_current_support_clarification():
    from support_agent.guardrails import check_reply
    from support_agent.schemas import CallBudget,SafetySignal
    from tests.helpers import ScriptedGateway
    source=Message(role='user',content='固定虚构案例：我现在很害怕，不知道自己是否安全。')
    assessment=Assessment(status='ok',continuation='distress',inquiry_quote=source.content)
    decision=Decision(action='clarify',unresolved_safety=[SafetySignal(id='signal',kind='self_harm',assertion='unclear',current_need='clarify',evidence_ids=['e1'])])
    checked=check_reply('你现在身边是否有可以陪着你的人？',[source],assessment,decision,[],ScriptedGateway({'allowed':True,'reason_codes':[]}),CallBudget())
    assert checked.allowed


def test_explicit_decline_is_remembered_even_when_reply_check_fails():
    from support_agent.workflow import run_turn
    text='我不想继续回答性格问题了，先暂停。'
    session=SessionState()
    result=run_turn(session,text,turn_gateway(text,continuation='decline',check=False),exploration_context=context())
    assert result.status=='fallback'
    assert session.inquiry_state.paused and not session.inquiry_state.last_question


def test_requested_relationship_topic_gets_scope_question_before_unrelated_personality_topics():
    text='虚构案例：我想先谈同一位伴侣晚回复时的反应。'
    chosen=plan(context(domains=('mbti','attachment')),text=text,
                assessment=feedback(text,kind='event',topic='attachment_anxiety'))
    assert chosen.stage=='relation_scope' and chosen.topic=='relationship_scope'


def test_refusing_personality_does_not_disable_ordinary_support_clarification():
    from support_agent.guardrails import check_reply
    from support_agent.schemas import CallBudget
    from tests.helpers import ScriptedGateway
    source=Message(role='user',content='这个虚构角色暂时不想分析性格，请帮他梳理明天的汇报。')
    assessment=Assessment(status='ok',user_goal='advice',continuation='decline',inquiry_quote=source.content)
    checked=check_reply('明天的汇报最需要先解决哪件具体的事？',[source],assessment,Decision(action='support'),[],ScriptedGateway({'allowed':True,'reason_codes':[]}),CallBudget())
    assert checked.allowed


def test_refusal_still_blocks_a_supplied_personality_plan_before_model_check():
    from support_agent.guardrails import check_reply
    from support_agent.schemas import CallBudget
    from tests.helpers import ScriptedGateway
    source=Message(role='user',content='暂时不想继续回答性格问题。')
    inquiry=plan(context())
    assessment=Assessment(status='ok',continuation='decline',inquiry_quote=source.content)
    checked=check_reply(inquiry.question,[source],assessment,Decision(action='clarify'),[],ScriptedGateway(),CallBudget(),inquiry_plan=inquiry)
    assert not checked.allowed and checked.reason_codes==['inquiry_not_wanted']


def test_annotation_revision_does_not_silently_resume_paused_questions():
    from support_agent.dialogue_exploration import build_exploration_context
    from support_agent.schemas import InquiryState
    scope=observation()
    original=build_exploration_context(scope,[],subject_mode='synthetic_case')
    paused=InquiryState(context_key=original.context_key,paused=True)
    scope.observation_revision+=1
    changed=build_exploration_context(scope,[],subject_mode='synthetic_case')
    assert plan(changed,state=paused,text='这个虚构角色今天又提到了工作。') is None
