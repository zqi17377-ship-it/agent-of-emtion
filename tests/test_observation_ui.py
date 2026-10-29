from tests.test_observation_wizard import launch,ready,advance
from support_agent.schemas import Message


def test_conversation_observation_is_off_and_intro_only_by_default():
    app=launch()
    assert app.session_state['workspace'].active.exploration.observation.mode=='off'
    assert len(app.checkbox)==1 and not app.selectbox and not app.multiselect


def test_observation_cannot_switch_existing_mock_messages_to_live():
    app=launch()
    c=app.session_state['workspace'].active
    c.state.messages=[Message(role='user',content='已有演示消息')]
    p='explore_'+c.id+'_observe_wizard_'
    app.checkbox(key=p+'research').check().run();advance(app)
    app.checkbox(key=p+'api').check().run()
    assert app.button(key='observation_next').disabled
    assert c.gateway_mode=='mock' and c.exploration.observation.mode=='off'


def test_observation_settings_are_separate_for_each_conversation():
    app=launch();c,p=ready(app)
    app.checkbox(key=p+'consent').check().run()
    app.button(key='observation_confirm').click().run()
    app.session_state['workspace'].new_conversation()
    app.run()
    assert app.session_state['workspace'].active.exploration.observation.mode=='off'
    assert len(app.session_state['workspace'].items)==2
    assert c.exploration.observation.mode=='auto'


def test_report_button_cannot_bypass_shared_observation_budget():
    app=launch();c,p=ready(app)
    app.checkbox(key=p+'consent').check().run()
    app.button(key='observation_confirm').click().run()
    c.state.messages=[Message(role='user',content='我平时喜欢独自散步休息。'),Message(role='user',content='周末我也喜欢独自在家读书。')]
    c.exploration.observation.ledger.spent=6
    app.button(key='observation_report').click().run()
    assert app.button(key='analyze_observations').disabled

def enabled_panel():
    app=launch();c,p=ready(app)
    app.checkbox(key=p+'consent').check().run()
    app.button(key='observation_confirm').click().run()
    return app,c


def test_relations_and_message_annotations_have_separate_pages(monkeypatch):
    import support_agent.observation_ui as ui
    monkeypatch.setattr(ui,'make_gateway',lambda **kw: (_ for _ in ()).throw(AssertionError('unexpected API')))
    app,c=enabled_panel()
    c.state.messages=[Message(role='user',content='我和朋友一起散步。')]
    prefix='explore_'+c.id+'_observe_'
    app.button(key='observation_relations').click().run()
    app.button(key=prefix+'add_relation').click().run()
    assert len(app.selectbox)==1
    assert c.exploration.observation.relations=={'partner_1':'partner'}
    assert app.button(key='observation_revoke')
    app.button(key='observation_done').click().run()
    app.button(key='observation_annotations').click().run()
    assert len(app.selectbox)==2
    assert not any(b.key==prefix+'add_relation' for b in app.button)
    app.selectbox(key=prefix+'relation_object').select('partner_1').run()
    app.button(key=prefix+'save_relation').click().run()
    assert c.exploration.observation.message_relations[c.state.messages[0].id]=='partner_1'
    app.button(key='observation_done').click().run()
    assert app.button(key='observation_relations')
    app.button(key='observation_annotations').click().run()
    app.button(key='observation_revoke').click().run()
    assert c.exploration.observation.mode=='off'
    assert not c.exploration.flows['observation_setup']['consent']


def test_empty_annotations_explain_prerequisites_and_allow_return():
    app,c=enabled_panel()
    app.button(key='observation_annotations').click().run()
    assert not app.selectbox
    assert any('关系对象' in item.value for item in app.info)
    assert app.button(key='observation_revoke')
    app.button(key='observation_done').click().run()
    app.button(key='observation_relations').click().run()
    app.button(key='explore_'+c.id+'_observe_add_relation').click().run()
    app.button(key='observation_done').click().run()
    app.button(key='observation_annotations').click().run()
    assert not app.selectbox
    assert any('消息' in item.value for item in app.info)
    app.button(key='observation_done').click().run()
    assert not app.exception
