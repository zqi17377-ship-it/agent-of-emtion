from tests.test_app import launch


def test_exploration_entry_and_incomplete_survey_never_invent_result():
    from tests.test_questionnaire_wizard import questionnaire_app, start
    app=start(questionnaire_app())
    assert app.button(key='survey_next').disabled
    assert not app.session_state['conversation'].exploration.survey_results


def test_survey_scores_locally_without_model_calls(monkeypatch):
    import support_agent.model_client as client
    from tests.test_questionnaire_wizard import questionnaire_app, start, complete
    def forbidden(*a,**k): raise AssertionError('Questionnaires must not request a model')
    monkeypatch.setattr(client,'make_gateway',forbidden)
    app=complete(start(questionnaire_app()))
    assert not app.exception
    assert app.session_state['conversation'].exploration.survey_results['test:v1'].dimensions['life_satisfaction'].total==20


def test_mbti_analysis_requires_consent_and_keeps_composer_available():
    app=launch()
    app.button(key='home_test').click().run()
    app.button(key='feature_mbti').click().run()
    c=app.session_state['workspace'].active
    app.button(key='personality_'+c.id+'_open_scope').click().run()
    assert not any(b.key=='analyze_personality' for b in app.button)
    app.button(key='open_exploration').click().run()
    # The composer stays mounted but hidden to preserve the frontend draft.
    assert len(app.chat_input)==1
    assert not app.session_state['workspace'].active.state.messages
