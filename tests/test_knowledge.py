from support_agent.schemas import KnowledgeCard, EligibilityContext


def card(**changes):
    d = dict(id='k1', title='睡眠', content='示例', tags=['睡眠'],source_url='local://original/k1', source_date='2026-10-29', permission_status='permitted',permission_evidence='original',review_status='pending',applicability={'adult_status':'confirmed'},exclusions=[])
    d.update(changes)
    return KnowledgeCard(**d)


def test_unapproved_card_excluded_from_eligible_mode():
    from support_agent.knowledge import retrieve
    assert not retrieve('睡眠', [], [card()], EligibilityContext(adult_status='confirmed'), 'eligible_pilot')


def test_unknown_applicability_excludes_restricted_card():
    from support_agent.knowledge import retrieve
    assert not retrieve('睡眠', [], [card()], EligibilityContext(), 'synthetic_research')


def test_exclusion_overrides_keyword_match():
    from support_agent.knowledge import retrieve
    assert not retrieve('睡眠', [], [card(exclusions=['special'])], EligibilityContext(adult_status='confirmed',reported_conditions=['special']), 'synthetic_research')


def test_empty_retrieval_and_unauthorized_card():
    from support_agent.knowledge import retrieve
    eligibility = EligibilityContext(adult_status='confirmed')
    assert retrieve('关系', [], [card()], eligibility, 'synthetic_research') == []
    assert retrieve('睡眠', [], [card(permission_status='unknown')], eligibility, 'synthetic_research') == []
    assert len(retrieve('睡眠', [], [card()], eligibility, 'synthetic_research')) == 1
