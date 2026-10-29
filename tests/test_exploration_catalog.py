def test_catalog_contains_multiple_distinct_tools_with_provenance():
    from support_agent.exploration_catalog import SURVEYS
    assert {'attachment_exploration','mini_ipip','tipi','rses','swls'} <= {q.id for q in SURVEYS}
    assert all(q.source_url.startswith('https://') and q.license_notice and q.translation_note for q in SURVEYS)
    assert len({q.id for q in SURVEYS})==len(SURVEYS)


def test_swls_uses_all_five_items_and_research_license():
    from support_agent.research_wellbeing_tests import SWLS
    from support_agent.psychometrics import score_questionnaire
    result=score_questionnaire(SWLS,{q.id:4 for q in SWLS.items})
    assert result.dimensions['life_satisfaction'].total==20
    assert '非商业' in SWLS.license_notice
    assert not any(q.reverse for q in SWLS.items)
