from support_agent.psychometrics import score_questionnaire


def test_seven_new_versions_are_runnable_with_independent_identities():
    from support_agent.survey_registry import list_versions,get_version
    enabled={v.definition.id:v for v in list_versions() if v.enabled}
    assert {key:len(enabled[key].definition.items) for key in ('ipip100','scs26','scs12','maas15','ecr_r36','ecr_rs9','dospert30')}=={
        'ipip100':100,'scs26':26,'scs12':12,'maas15':15,'ecr_r36':36,'ecr_rs9':9,'dospert30':30,
    }
    for version in enabled.values():
        assert get_version(version.id) is version
        q=version.definition
        result=score_questionnaire(q,{item.id:q.min_score for item in q.items})
        assert result.test_id==q.id and len(result.answers)==len(q.items)


def test_short_self_compassion_export_exposes_only_overall_not_subscale_profile():
    from support_agent.self_care_tests import SCS12
    from support_agent.exploration_catalog import export_survey_report
    result=score_questionnaire(SCS12,{item.id:3 for item in SCS12.items})
    report=export_survey_report(SCS12,result)
    assert '自我关怀总均分' in report and '3.00' in report
    for label in SCS12.dimension_labels.values():
        assert label+'：' not in report


def test_short_self_compassion_result_ui_shows_overall_and_keeps_subscales_hidden():
    from tests.test_questionnaire_wizard import questionnaire_app,start,complete
    from support_agent.self_care_tests import SCS12
    app=complete(start(questionnaire_app('SCS12','self_care_tests')),value=3)
    assert not app.exception
    assert any(m.label=='自我关怀总均分' and '3.00' in m.value for m in app.metric)
    raw=next(section for section in app.expander if section.label=='查看原始分数')
    assert any('自我关怀总均分' in item.value for item in raw.get('markdown'))
    rendered='\n'.join(m.value for m in app.markdown)
    for label in SCS12.dimension_labels.values():
        assert '**'+label+'**' not in rendered


def test_relationship_structures_selects_one_target_and_keeps_drafts_separate():
    from tests.test_questionnaire_wizard import questionnaire_app,start
    app=start(questionnaire_app('ECR_RS9','relationship_risk_tests'))
    assert app.radio[0].options==['母亲','父亲','亲密伴侣','最亲近的朋友']
    assert app.radio[0].value is None and app.button(key='survey_next').disabled
    app.radio[0].set_value('母亲').run();app.button(key='survey_next').click().run()
    app.radio[0].set_value(2).run();app.button(key='survey_prev').click().run()
    app.radio[0].set_value('父亲').run();app.button(key='survey_next').click().run()
    assert app.radio[0].value is None
    app.radio[0].set_value(6).run();app.button(key='survey_prev').click().run()
    app.radio[0].set_value('母亲').run();app.button(key='survey_next').click().run()
    assert app.radio[0].value==2


def test_new_test_catalog_routes_through_the_existing_sequential_form():
    from tests.test_app import launch
    app=launch();app.button(key='home_test').click().run()
    for tool in ('scs26','maas15','dospert30'):
        assert app.button(key='feature_'+tool)
    app.button(key='feature_scs26').click().run()
    assert len(app.radio[0].options)==2
    app.radio[0].set_value('scs_sf:12:zh-project-v1:key-v1').run();app.button(key='feature_begin').click().run()
    app.checkbox(key='survey_research').check().run();app.button(key='survey_start').click().run()
    assert len(app.radio)==1 and len(app.radio[0].options)==5
    assert app.button(key='survey_next').disabled


def test_two_completed_relationship_results_remain_independent_and_retrievable():
    from tests.test_questionnaire_wizard import questionnaire_app,start,complete
    app=start(questionnaire_app('ECR_RS9','relationship_risk_tests'))
    app.radio[0].set_value('母亲').run();app.button(key='survey_next').click().run()
    complete(app,value=2)
    app.button(key='survey_edit').click().run()
    app.radio[0].set_value('父亲').run();app.button(key='survey_next').click().run()
    complete(app,value=6)
    state=app.session_state['conversation'].exploration
    saved={state.survey_contexts[key]:result for key,result in state.survey_results.items()}
    assert set(saved)=={'母亲','父亲'}
    assert saved['母亲'].dimensions['anxiety'].mean==2
    assert saved['父亲'].dimensions['anxiety'].mean==6
    app.button(key='survey_edit').click().run()
    app.radio[0].set_value('母亲').run()
    app.button(key='survey_show_context_saved').click().run()
    assert not app.exception
    assert any('想到的关系：母亲' in item.value for item in app.caption)
    assert any('2.00 / 7' in item.value for item in app.markdown)
    assert len(state.survey_results)==2
