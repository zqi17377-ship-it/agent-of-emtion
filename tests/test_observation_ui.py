from tests.test_app import launch


def test_conversation_observation_is_visible_but_off_by_default():
    app = launch()
    assert any(b.key == 'open_conversation_observation' for b in app.button)
    assert app.session_state['workspace'].active.exploration.observation.mode == 'off'


def test_observation_requires_explicit_consent_and_live_mode():
    app = launch()
    app.button(key='open_conversation_observation').click().run()
    assert not app.exception
    assert app.selectbox(key='exploration_tool').value == 'conversation_observation'
    assert app.button(key='analyze_observations').disabled
    assert any('20' in text.value for text in app.caption)


def test_observation_settings_are_separate_for_each_conversation():
    app = launch()
    app.button(key='open_conversation_observation').click().run()
    c = app.session_state['workspace'].active
    c.exploration.observation.mode = 'manual'
    app.button(key='new_sidebar').click().run()
    assert app.session_state['workspace'].active.exploration.observation.mode == 'off'
    assert len(app.session_state['workspace'].items) == 2


def test_old_personality_button_cannot_bypass_shared_observation_budget(monkeypatch):
    import support_agent.ui as ui
    from support_agent.config import ConfigurationReadiness
    from support_agent.schemas import Message
    monkeypatch.setattr(ui,'configuration_readiness',lambda:ConfigurationReadiness(True,True,True,None))
    app=launch()
    app.checkbox(key='research_confirmed').check().run()
    app.radio(key='mode_selector').set_value('DeepSeek API').run()
    app.checkbox(key='api_consent').check().run()
    c=app.session_state['workspace'].active
    c.state.messages=[Message(role='user',content='我平时喜欢独自散步休息。'),Message(role='user',content='周末我也喜欢独自在家读书。')]
    c.exploration.observation.ledger.spent=6
    app.button(key='open_exploration').click().run()
    app.selectbox(key='exploration_tool').select('mbti').run()
    app.checkbox(key='explore_'+c.id+'_personality_consent').check().run()
    assert app.button(key='analyze_personality').disabled
