from support_agent.schemas import Message


def samples(count, width=40):
    return [Message(id=f'm{i}', role='user', content=f'{i:02d}'+'我'*(width-2)) for i in range(count)]


def test_early_automatic_review_requires_both_examples_and_content():
    from support_agent.observation_scheduler import ObservationState,eligibility_reason
    state=ObservationState(mode='auto',domains=('mbti',))
    def reason(items):
        return eligibility_reason(state,items,manual=False,live=True,authorized=True,paused=False)
    assert reason(samples(5,100))=='insufficient'
    assert reason(samples(6,39))=='insufficient'
    assert reason(samples(6,40)) is None
    state.automatic_count=1;state.last_auto_candidate_count=6
    assert reason(samples(11))=='insufficient_new'
    assert reason(samples(12)) is None


def test_short_behavior_answers_count_but_assent_duplicates_and_types_do_not():
    from support_agent.observation_scheduler import count_candidates
    texts=['我会先独处。','我先查资料。','我会先独处。','嗯嗯','好的，谢谢','INFP','😀'*30]
    items=[Message(role='user',content=t) for t in texts]
    assert count_candidates(items)==(2,len(texts[0])+len(texts[1]))


def test_subject_mode_is_preserved_by_scheduler_snapshot_identity():
    from support_agent.observation_scheduler import ObservationState,snapshot_fingerprint
    from support_agent.conversation_observation import build_snapshot
    state=ObservationState(mode='manual',domains=('mbti',))
    state.subject_mode='synthetic_case'
    items=samples(2)
    expected=build_snapshot(state.conversation_id,state.generation,state.consent_revision,state.observation_revision,items,state.domains,subject_mode='synthetic_case')
    assert snapshot_fingerprint(state,items)==expected.fingerprint


def test_root_chat_passes_only_enabled_topics_and_selected_anonymous_relation(monkeypatch):
    from tests.test_app import launch,prepare
    import support_agent.ui as ui
    from support_agent.config import ConfigurationReadiness
    from support_agent.schemas import TurnResult
    monkeypatch.setattr(ui,'configuration_readiness',lambda:ConfigurationReadiness(True,True,True,None))
    monkeypatch.setattr(ui,'make_gateway',lambda **_:object())
    contexts=[]
    def rejected(session,text,gateway,*,exploration_context=None):
        contexts.append(exploration_context)
        return TurnResult(text='用于验证参数，不发送消息。',action='clarify',status='error')
    monkeypatch.setattr(ui.workflow,'run_turn',rejected)
    app=prepare(launch());c=app.session_state['workspace'].active
    state=c.exploration.observation
    state.mode='manual';state.domains=('attachment',)
    state.relations={'friend_1':'friend','friend_2':'friend'}
    app.run()
    app.selectbox(key='explore_'+c.id+'_observe_next_relation').select('friend_1').run()
    app.chat_input[0].set_value('固定成年人虚构案例：我想说说和这位朋友相处的经历。').run()
    assert not app.exception
    assert contexts[0].domains==('attachment',) and contexts[0].relation_id=='friend_1'
    assert c.state.messages==[] and state.message_relations=={}
    state.mode='off';app.run()
    app.chat_input[0].set_value('固定成年人虚构案例：现在只想普通聊天。').run()
    assert contexts[-1] is None


def test_report_and_export_show_tentative_pattern_and_next_question_without_strong_type():
    from tests.test_app import launch
    from support_agent.conversation_observation import Observation,ObservationEvidence,ObservationReport
    from support_agent.observation_ui import export_observation_report
    from support_agent.observation_scheduler import snapshot_fingerprint
    app=launch();c=app.session_state['workspace'].active
    message=Message(id='example',role='user',content='成年人虚构案例：上周聚会后，我独自散步恢复精力。')
    c.state.messages=[message]
    state=c.exploration.observation
    state.mode='manual';state.domains=('mbti',);state.subject_mode='synthetic_case'
    evidence=ObservationEvidence(message_id='example',quote='上周聚会后，我独自散步恢复精力。',event_id='gathering',context_kind='social')
    item=Observation(domain='mbti',dimension='EI',subject='case_narrator',scope='habit',direction='unknown',coverage='limited',tentative_direction='I',coverage_reason='还需不同情境的独立经历。',evidence=[evidence])
    state.report=ObservationReport(status='insufficient',observations=[item],fingerprint=snapshot_fingerprint(state,c.state.messages))
    c.exploration.flows['observation_setup']={'page':'report','step':0,'consent':True}
    app.session_state['workspace_view']='exploration'
    app.session_state['feature_flow_active']=True
    app.session_state['exploration_tool']='conversation_observation'
    app.run()
    assert not app.exception
    visible='\n'.join(str(m.value) for m in app.markdown)
    assert '初步线索' in visible and '下一步' in visible
    exported=export_observation_report(c)
    assert '初步线索' in exported and '下一步' in exported
    assert '还需不同情境' in exported
    assert 'INFP' not in exported and 'INTJ' not in exported


def test_relation_scope_has_direct_setup_and_new_object_returns_to_chat_without_binding_old_messages(monkeypatch):
    from tests.test_app import launch,prepare
    import support_agent.ui as ui
    from support_agent.config import ConfigurationReadiness
    monkeypatch.setattr(ui,'configuration_readiness',lambda:ConfigurationReadiness(True,True,True,None))
    app=prepare(launch());c=app.session_state['workspace'].active
    c.state.inquiry_state.stage='relation_scope'
    state=c.exploration.observation
    state.mode='manual';state.domains=('attachment',)
    app.run()
    app.button(key='setup_chat_relation').click().run()
    assert app.session_state['workspace_view']=='exploration'
    prefix='explore_'+c.id+'_observe_'
    app.button(key=prefix+'add_relation').click().run()
    assert state.relations=={'partner_1':'partner'} and state.message_relations=={}
    app.button(key=prefix+'relations_chat').click().run()
    assert app.session_state['workspace_view']=='chat'
    assert app.selectbox(key=prefix+'next_relation').value=='partner_1'
