from tests.test_app import launch


def test_exploration_entry_and_incomplete_survey_never_invent_result():
    app=launch()
    app.button(key='open_exploration').click().run()
    assert not app.exception
    assert app.selectbox(key='exploration_tool').value=='attachment_exploration'
    app.checkbox(key='research_confirmed').check().run()
    context=next(s for s in app.selectbox if s.key and '_attachment_context_' in s.key)
    context.select('亲密伴侣').run()
    app.button(key='calculate_survey').click().run()
    assert app.warning
    assert not app.session_state['workspace'].active.exploration.survey_results


def test_survey_scores_locally_without_model_calls(monkeypatch):
    import support_agent.model_client as client
    def forbidden(*a,**k): raise AssertionError('Questionnaires must not request a model')
    monkeypatch.setattr(client,'make_gateway',forbidden)
    app=launch(); app.button(key='open_exploration').click().run()
    app.checkbox(key='research_confirmed').check().run()
    app.selectbox(key='exploration_tool').select('swls').run()
    for element in app.selectbox:
        if element.key and '_item_swls_' in element.key:
            element.select(4)
    app.button(key='calculate_survey').click().run()
    assert not app.exception
    result=next(r for r in app.session_state['workspace'].active.exploration.survey_results.values() if r.test_id=='swls')
    assert result.dimensions['life_satisfaction'].total==20


def test_mbti_analysis_requires_consent_and_keeps_composer_available():
    app=launch()
    app.button(key='starter_pressure').click().run()
    app.button(key='open_exploration').click().run()
    app.selectbox(key='exploration_tool').select('mbti').run()
    assert app.button(key='analyze_personality').disabled
    app.button(key='open_exploration').click().run()
    # ChatInput.value is a transient submission/prefill event in AppTest,
    # not the browser's unsent draft. Browser persistence is checked in UI QA.
    assert len(app.chat_input)==1
    assert not app.session_state['workspace'].active.state.messages
