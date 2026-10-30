"""Primary-source keys and hand-calculated scores for relationship/risk forms."""

import pytest

from support_agent.psychometrics import score_questionnaire
from support_agent.relationship_risk_tests import DOSPERT30, ECR_R36, ECR_RS9


@pytest.mark.parametrize('form,count,dimension_counts', [
    (ECR_R36, 36, {'anxiety': 18, 'avoidance': 18}),
    (ECR_RS9, 9, {'avoidance': 6, 'anxiety': 3}),
    (DOSPERT30, 30, {
        'risk_ethical': 6, 'risk_financial': 6, 'risk_health_safety': 6,
        'risk_recreational': 6, 'risk_social': 6,
    }),
])
def test_complete_seven_point_forms_score_only_their_separate_dimensions(
    form, count, dimension_counts,
):
    result = score_questionnaire(form, {item.id: 4 for item in form.items})

    assert form.min_score == 1
    assert form.max_score == 7
    assert len(form.items) == count
    assert len({item.id for item in form.items}) == count
    assert len({item.text for item in form.items}) == count
    assert all(item.text.strip() for item in form.items)
    assert {key: value.count for key, value in result.dimensions.items()} == dimension_counts
    assert all(value.mean == 4 for value in result.dimensions.values())
    assert not hasattr(result, 'overall')


@pytest.mark.parametrize('form', [ECR_R36, ECR_RS9])
def test_ecr_agreement_scale_has_a_neutral_midpoint_between_opposite_endpoints(form):
    assert form.options[0] == '非常不同意'
    assert form.options[3] == '既不赞同也不反对'
    assert form.options[6] == '非常同意'


def test_dospert_response_values_represent_likelihood_with_an_uncertain_midpoint():
    assert DOSPERT30.options == (
        '极不可能', '较不可能', '有些不可能', '不确定', '有些可能', '较可能', '极有可能',
    )


def test_ecr_r36_preserves_the_official_administration_order_and_reverse_key():
    assert {number for number, item in enumerate(ECR_R36.items, 1)
            if item.dimension == 'anxiety'} == set(range(1, 19))
    assert {number for number, item in enumerate(ECR_R36.items, 1)
            if item.dimension == 'avoidance'} == set(range(19, 37))
    assert {number for number, item in enumerate(ECR_R36.items, 1)
            if item.reverse} == {9, 11, 20, 22, 26, 27, 28, 29, 30, 31, 33, 34, 35, 36}
    assert ECR_R36.display == 'mean'
    assert ECR_R36.context_options == ()


def test_ecr_r36_reproduces_the_authors_worked_example():
    # Fraley FAQ: anxiety 42/18; avoidance 39/18 (rounded there to 2.33/2.17).
    values = (
        1, 2, 2, 1, 3, 2, 2, 2, 1, 1, 6, 2, 2, 2, 3, 2, 5, 1,
        2, 5, 2, 5, 2, 4, 2, 6, 6, 7, 7, 5, 6, 2, 6, 6, 6, 6,
    )
    result = score_questionnaire(
        ECR_R36, {item.id: value for item, value in zip(ECR_R36.items, values, strict=True)},
    )

    assert result.dimensions['anxiety'].total == 42
    assert result.dimensions['anxiety'].mean == pytest.approx(2.333333333333333)
    assert result.dimensions['avoidance'].total == 39
    assert result.dimensions['avoidance'].mean == pytest.approx(2.1666666666666665)


@pytest.mark.parametrize('value,anxiety_total,avoidance_total', [
    (1, 30, 90), (7, 114, 54),
])
def test_ecr_r36_constant_raw_answers_keep_both_reverse_item_sets(
    value, anxiety_total, avoidance_total,
):
    result = score_questionnaire(ECR_R36, {item.id: value for item in ECR_R36.items})
    assert result.dimensions['anxiety'].total == anxiety_total
    assert result.dimensions['avoidance'].total == avoidance_total


def test_ecr_rs9_scores_one_selected_relationship_with_the_original_key():
    assert ECR_RS9.context_options == ('母亲', '父亲', '亲密伴侣', '最亲近的朋友')
    assert {number for number, item in enumerate(ECR_RS9.items, 1)
            if item.dimension == 'avoidance'} == {1, 2, 3, 4, 5, 6}
    assert {number for number, item in enumerate(ECR_RS9.items, 1)
            if item.dimension == 'anxiety'} == {7, 8, 9}
    assert {number for number, item in enumerate(ECR_RS9.items, 1)
            if item.reverse} == {1, 2, 3, 4}
    assert ECR_RS9.display == 'mean'

    values = (7, 6, 5, 4, 3, 2, 1, 5, 6)
    result = score_questionnaire(
        ECR_RS9, {item.id: value for item, value in zip(ECR_RS9.items, values, strict=True)},
    )
    assert result.dimensions['avoidance'].total == 15
    assert result.dimensions['avoidance'].mean == 2.5
    assert result.dimensions['anxiety'].total == 12
    assert result.dimensions['anxiety'].mean == 4


@pytest.mark.parametrize('value,avoidance_total,anxiety_total', [
    (1, 30, 3), (7, 18, 21),
])
def test_ecr_rs9_constant_raw_answers_keep_reverse_items(
    value, avoidance_total, anxiety_total,
):
    result = score_questionnaire(ECR_RS9, {item.id: value for item in ECR_RS9.items})
    assert result.dimensions['avoidance'].total == avoidance_total
    assert result.dimensions['anxiety'].total == anxiety_total


@pytest.mark.parametrize('number,dimension', [
    (1, 'risk_social'), (2, 'risk_recreational'), (3, 'risk_financial'),
    (4, 'risk_financial'), (5, 'risk_health_safety'), (6, 'risk_ethical'),
    (7, 'risk_social'), (8, 'risk_financial'), (9, 'risk_ethical'),
    (10, 'risk_ethical'), (11, 'risk_recreational'), (12, 'risk_financial'),
    (13, 'risk_recreational'), (14, 'risk_financial'), (15, 'risk_health_safety'),
    (16, 'risk_ethical'), (17, 'risk_health_safety'), (18, 'risk_financial'),
    (19, 'risk_recreational'), (20, 'risk_health_safety'), (21, 'risk_social'),
    (22, 'risk_social'), (23, 'risk_health_safety'), (24, 'risk_recreational'),
    (25, 'risk_recreational'), (26, 'risk_health_safety'), (27, 'risk_social'),
    (28, 'risk_social'), (29, 'risk_ethical'), (30, 'risk_ethical'),
])
def test_dospert30_each_item_changes_only_its_primary_source_domain(number, dimension):
    answers = {item.id: 1 for item in DOSPERT30.items}
    answers[DOSPERT30.items[number - 1].id] = 7
    result = score_questionnaire(DOSPERT30, answers)

    assert result.dimensions[dimension].total == 12
    assert all(value.total == 6 for key, value in result.dimensions.items() if key != dimension)


@pytest.mark.parametrize('value,total', [(1, 6), (7, 42)])
def test_dospert30_uses_unreversed_sums_on_the_six_to_forty_two_scale(value, total):
    result = score_questionnaire(DOSPERT30, {item.id: value for item in DOSPERT30.items})

    assert DOSPERT30.display == 'sum'
    assert not any(item.reverse for item in DOSPERT30.items)
    assert DOSPERT30.context_options == ()
    assert all(value.total == total for value in result.dimensions.values())
    assert all(value.min_total == 6 and value.max_total == 42 for value in result.dimensions.values())

