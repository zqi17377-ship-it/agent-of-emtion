from support_agent.psychometrics import score_questionnaire


def test_original_english_forms_have_explicit_language_id_and_old_ids_still_work():
    from support_agent.survey_registry import list_versions,get_version
    english={v.definition.id:v for v in list_versions() if v.enabled and v.language_version=='en-original'}
    assert set(english)=={'erq30_en','aaqii7'}
    assert {v.item_count for v in english.values()}=={7,30}
    assert get_version('scs:26:zh-project-v1:key-v1').definition.id=='scs26'
    assert get_version('erq30:30:en-original:key-v1').definition.id=='erq30_en'
    assert get_version('aaq_ii:7:en-original:key-v1').definition.id=='aaqii7'
    assert all('中文译文' not in v.validation_population for v in english.values())


def test_pending_beq_and_ffmq_do_not_supply_questions_or_runnable_buttons():
    from support_agent.survey_registry import list_versions
    from tests.test_app import launch
    pending={v.instrument_id:v for v in list_versions() if v.instrument_id in ('beq','ffmq')}
    assert set(pending)=={'beq','ffmq'}
    assert all(not v.enabled and v.definition is None for v in pending.values())
    app=launch();app.button(key='home_test').click().run()
    assert not app.exception
    assert any(e.label=='待接入的测试与来源' for e in app.expander)
    assert not any(b.key in ('feature_beq','feature_ffmq') for b in app.button)
    assert not app.radio


def test_english_aaqii_uses_the_local_sequential_flow_and_saves_twenty_eight(monkeypatch):
    from tests.test_app import launch
    import support_agent.model_client as client
    monkeypatch.setattr(client,'make_gateway',lambda *a,**k:(_ for _ in ()).throw(AssertionError('No model request for questionnaires')))
    app=launch();app.button(key='home_test').click().run()
    app.button(key='feature_aaqii7').click().run()
    app.checkbox(key='survey_research').check().run();app.button(key='survey_start').click().run()
    assert len(app.radio)==1 and app.radio[0].options==['never true','very seldom true','seldom true','sometimes true','frequently true','almost always true','always true']
    for _ in range(7):
        app.radio[0].set_value(4).run();app.button(key='survey_next').click().run()
    app.button(key='calculate_survey').click().run()
    assert not app.exception
    state=app.session_state['workspace'].active.exploration
    result=state.survey_results['aaq_ii:7:en-original:key-v1']
    assert result.dimensions['psychological_inflexibility'].total==28
    assert app.get('download_button')


def test_erq30_english_first_question_and_original_anchor_choices_are_visible():
    from tests.test_app import launch
    app=launch();app.button(key='home_test').click().run()
    app.button(key='feature_erq30_en').click().run()
    app.checkbox(key='survey_research').check().run();app.button(key='survey_start').click().run()
    assert len(app.radio)==1 and 'When I want to feel more positive emotion' in app.radio[0].label
    assert app.radio[0].options==['1 · Strongly disagree','2','3','4 · Neither agree nor disagree','5','6','7 · Strongly agree']
    assert app.button(key='survey_next').disabled


def test_new_results_explain_their_own_constructs_without_combining_strategies():
    from support_agent.emotion_regulation_tests import ERQ30_EN
    from support_agent.mindfulness_flexibility_tests import AAQII7
    from support_agent.survey_presentation import build_survey_presentation
    erq=score_questionnaire(ERQ30_EN,{item.id:4 for item in ERQ30_EN.items})
    erq_view=build_survey_presentation(ERQ30_EN,erq)
    assert len(erq.dimensions)==10 and all(d.total==12 for d in erq.dimensions.values())
    assert erq.composites=={}
    assert 'Consider a recent' in erq_view.markdown
    assert 'Behavioral activation' in erq_view.svg
    result=score_questionnaire(AAQII7,{item.id:7 for item in AAQII7.items})
    view=build_survey_presentation(AAQII7,result)
    assert '49' in view.svg and '心理不灵活' in view.markdown
    assert '妨碍' in view.markdown
