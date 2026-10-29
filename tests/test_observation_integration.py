"""AppTest integration of real consent widgets, scheduler, worker and report UI.

No environment configuration or provider requests are used by these tests.
"""
import pytest
from tests.test_app import launch
from support_agent.schemas import Message,ModelResult
from support_agent.conversation_observation import Observation,ObservationReport
from support_agent.observation_scheduler import fresh_observation_state


@pytest.fixture
def live_app(monkeypatch):
    import support_agent.ui as ui
    import support_agent.observation_ui as observation_ui
    from support_agent.config import ConfigurationReadiness
    monkeypatch.setattr(ui,'configuration_readiness',lambda:ConfigurationReadiness(True,True,True,None))
    calls=[]
    class Gateway:
        mode='live';model_id='integration-fake'
        def generate(self,messages,instructions,schema,budget):
            budget.consume();calls.append(messages)
            result=ModelResult(text='{"observations":[]}',model_id=self.model_id,input_tokens=11,output_tokens=3)
            budget.record(result);return result
        def close(self): pass
    monkeypatch.setattr(observation_ui,'make_gateway',lambda **_:Gateway())
    app=launch()
    app.checkbox(key='research_confirmed').check().run()
    app.radio(key='mode_selector').set_value('DeepSeek API').run()
    app.checkbox(key='api_consent').check().run()
    app.button(key='open_conversation_observation').click().run()
    c=app.session_state['workspace'].active
    prefix='explore_'+c.id+'_observe_'
    app.checkbox(key=prefix+'consent').check().run()
    app.selectbox(key=prefix+'mode').select('auto').run()
    app.multiselect(key=prefix+'domains').set_value(['mbti']).run()
    assert not app.exception
    return app,c,prefix,calls


def synthetic_messages():
    return [Message(id='event_'+str(i),role='user',content=f'成年人虚构案例，独立事件{i}：我在工作学习和休息时发现自己需要先独立想清楚，再与大家商量下一步安排。'+ '这是我对自己当时经历的详细叙述。'*2) for i in range(20)]


def analyze(app,c):
    c.state.messages=synthetic_messages()
    app.run()
    state=c.exploration.observation
    if state.pending_job is not None: state.pending_job.future.result(timeout=3)
    app.run()
    assert not app.exception
    assert state.report is not None
    return state


def test_real_auto_flow_accepts_report_and_rerun_never_repeats_request(live_app):
    app,c,prefix,calls=live_app
    state=analyze(app,c)
    assert state.mode=='auto' and state.domains==('mbti',)
    assert state.report.status=='insufficient' and state.request_count==1 and state.total_tokens==14
    assert len(calls)==1 and not state.is_stale(c.state.messages)
    app.run();app.run()
    assert len(calls)==1 and state.automatic_count==1
    assert any('没有足够' in item.value for item in app.info)


@pytest.mark.parametrize('key',['api_consent','research_confirmed'])
def test_top_level_consent_withdrawal_clears_independent_consent(live_app,key):
    app,c,prefix,calls=live_app
    state=analyze(app,c)
    app.checkbox(key=key).uncheck().run()
    assert not app.exception
    assert state.mode=='off' and state.report is None
    assert app.session_state[prefix+'consent'] is False
    app.run()
    assert len(calls)==1 and state.request_count==1


def test_clear_current_and_fresh_state_preserve_shared_spent_ledger(live_app):
    app,c,prefix,calls=live_app
    previous=analyze(app,c)
    app.button(key='open_exploration').click().run()
    app.button(key='clear_current').click().run()
    assert not app.exception
    clean=c.exploration.observation
    assert clean is not previous and clean.mode=='off' and clean.report is None
    assert c.state.messages==[] and clean.request_count==1
    assert clean.ledger is previous.ledger
    assert fresh_observation_state(clean).request_count==1
    app.run();assert len(calls)==1


def test_relationship_annotation_and_observation_deletion_survive_rerun(live_app):
    app,c,prefix,calls=live_app
    state=analyze(app,c)
    app.selectbox(key=prefix+'new_relation_kind').select('friend').run()
    app.button(key=prefix+'add_relation').click().run()
    app.selectbox(key=prefix+'relation_message').select('event_0').run()
    app.selectbox(key=prefix+'relation_object').select('friend_1').run()
    app.button(key=prefix+'save_relation').click().run()
    assert state.relations=={'friend_1':'friend'} and state.message_relations=={'event_0':'friend_1'}
    state.report=ObservationReport(status='insufficient',observations=[Observation(domain='mbti',dimension='EI')])
    app.run()
    app.button(key=prefix+'delete_mbti:EI:').click().run()
    assert 'mbti:EI:' in state.excluded_keys and state.report.observations==[]
    app.run();app.run()
    assert not app.exception and state.report.observations==[] and len(calls)==1


def test_rejected_chat_does_not_rebind_previous_user_to_new_relation(monkeypatch):
    import support_agent.ui as ui
    from support_agent.schemas import TurnResult
    app=launch()
    app.checkbox(key='research_confirmed').check().run()
    c=app.session_state['workspace'].active
    c.state.messages=[Message(id='previous_user',role='user',content='这段历史消息谈到第一位朋友。'),Message(id='previous_assistant',role='assistant',content='我在听。')]
    state=c.exploration.observation
    state.mode='manual';state.domains=('attachment',)
    state.relations={'friend_1':'friend','friend_2':'friend'}
    state.message_relations={'previous_user':'friend_1'}
    def rejected_turn(*args,**kwargs):
        return TurnResult(text='上下文超出限制',action='clarify',status='error',error_code='context_limit')
    monkeypatch.setattr(ui.workflow,'run_turn',rejected_turn)
    app.run()
    relation=next(item for item in app.selectbox if item.label=='本条消息谈到的关系对象（可留空）')
    relation.select('friend_2').run()
    app.chat_input[0].set_value('这一条新消息本来谈到第二位朋友，但因超限被拒绝。').run()
    assert not app.exception
    assert [m.id for m in c.state.messages]==['previous_user','previous_assistant']
    assert state.message_relations=={'previous_user':'friend_1'}
