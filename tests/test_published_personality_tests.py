import pytest


@pytest.mark.parametrize(
    "responses, expected_total",
    [
        ((3, 3, 0, 3, 0, 3, 3, 0, 0, 0), 30),
        ((0, 0, 3, 0, 3, 0, 0, 3, 3, 3), 0),
        ((3, 3, 3, 3, 3, 3, 3, 3, 3, 3), 15),
    ],
)
def test_rosenberg_scores_the_published_ten_item_key(responses, expected_total):
    from support_agent.psychometrics import score_questionnaire
    from support_agent.published_personality_tests import RSES

    answers = {f"rses_{number}": value for number, value in enumerate(responses, 1)}
    result = score_questionnaire(RSES, answers)

    assert len(RSES.items) == 10
    assert RSES.min_score == 0
    assert len(RSES.options) == 4
    assert RSES.display == "sum"
    assert set(result.dimensions) == {"self_esteem"}
    assert result.dimensions["self_esteem"].total == expected_total


@pytest.mark.parametrize(
    "responses, expected_totals",
    [
        (
            (5, 5, 1, 1, 5, 5, 1, 1, 5, 5, 1, 1, 5, 5, 1, 1, 5, 1, 1, 1),
            (20, 20, 20, 20, 20),
        ),
        (
            (1, 1, 5, 5, 1, 1, 5, 5, 1, 1, 5, 5, 1, 1, 5, 5, 1, 5, 5, 5),
            (4, 4, 4, 4, 4),
        ),
        (
            (5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5),
            (12, 12, 12, 12, 8),
        ),
    ],
)
def test_mini_ipip_preserves_five_separate_published_scales(responses, expected_totals):
    from support_agent.psychometrics import score_questionnaire
    from support_agent.published_personality_tests import MINI_IPIP

    answers = {f"mini_ipip_{number}": value for number, value in enumerate(responses, 1)}
    result = score_questionnaire(MINI_IPIP, answers)
    dimensions = (
        "extraversion", "agreeableness", "conscientiousness", "neuroticism",
        "intellect_imagination",
    )

    assert len(MINI_IPIP.items) == 20
    assert MINI_IPIP.min_score == 1
    assert len(MINI_IPIP.options) == 5
    assert MINI_IPIP.display == "mean"
    assert set(result.dimensions) == set(dimensions)
    assert tuple(result.dimensions[key].total for key in dimensions) == expected_totals
    assert tuple(result.dimensions[key].mean for key in dimensions) == tuple(
        total / 4 for total in expected_totals
    )


@pytest.mark.parametrize("questionnaire_name", ["RSES", "MINI_IPIP"])
def test_published_scales_require_complete_answers(questionnaire_name):
    from support_agent import published_personality_tests
    from support_agent.psychometrics import score_questionnaire

    questionnaire = getattr(published_personality_tests, questionnaire_name)
    answers = {item.id: questionnaire.min_score for item in questionnaire.items[:-1]}

    with pytest.raises(ValueError):
        score_questionnaire(questionnaire, answers)
