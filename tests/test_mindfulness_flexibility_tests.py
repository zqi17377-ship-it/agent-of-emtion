import pytest


@pytest.mark.parametrize(
    "responses, expected_total, expected_mean",
    [
        ((1, 1, 1, 1, 1, 1, 1), 7, 1),
        ((7, 7, 7, 7, 7, 7, 7), 49, 7),
        ((1, 2, 3, 4, 5, 6, 7), 28, 4),
    ],
)
def test_final_seven_item_aaqii_sums_inflexibility_without_reversing(
    responses, expected_total, expected_mean,
):
    from support_agent.mindfulness_flexibility_tests import AAQII7
    from support_agent.psychometrics import score_questionnaire

    answers = dict(zip(
        ("aaqii7_1", "aaqii7_2", "aaqii7_3", "aaqii7_4", "aaqii7_5", "aaqii7_6", "aaqii7_7"),
        responses,
    ))
    result = score_questionnaire(AAQII7, answers)
    inflexibility = result.dimensions["psychological_inflexibility"]

    assert AAQII7.id == "aaqii7"
    assert AAQII7.display == "sum"
    assert set(result.dimensions) == {"psychological_inflexibility"}
    assert inflexibility.count == 7
    assert inflexibility.total == expected_total
    assert inflexibility.mean == expected_mean
    assert (inflexibility.min_total, inflexibility.max_total) == (7, 49)
    assert (inflexibility.min_value, inflexibility.max_value) == (1, 7)
    assert result.composites == {}
    assert result.answers == answers


@pytest.mark.parametrize(
    "item_id",
    ("aaqii7_1", "aaqii7_2", "aaqii7_3", "aaqii7_4", "aaqii7_5", "aaqii7_6", "aaqii7_7"),
)
def test_every_final_aaqii_item_increases_inflexibility(item_id):
    from support_agent.mindfulness_flexibility_tests import AAQII7
    from support_agent.psychometrics import score_questionnaire

    answers = {
        "aaqii7_1": 1, "aaqii7_2": 1, "aaqii7_3": 1, "aaqii7_4": 1,
        "aaqii7_5": 1, "aaqii7_6": 1, "aaqii7_7": 1,
    }
    answers[item_id] = 7
    result = score_questionnaire(AAQII7, answers)

    assert result.dimensions["psychological_inflexibility"].total == 13
    assert result.dimensions["psychological_inflexibility"].mean == pytest.approx(13 / 7)


def test_final_aaqii_rejects_incomplete_answers_instead_of_imputing():
    from support_agent.mindfulness_flexibility_tests import AAQII7
    from support_agent.psychometrics import score_questionnaire

    answers = {
        "aaqii7_1": 1, "aaqii7_2": 1, "aaqii7_3": 1,
        "aaqii7_4": 1, "aaqii7_5": 1, "aaqii7_6": 1,
    }

    with pytest.raises(ValueError, match="exactly all"):
        score_questionnaire(AAQII7, answers)


@pytest.mark.parametrize("invalid_value", [0, 8, True, 1.0])
def test_final_aaqii_rejects_values_outside_its_seven_integer_choices(invalid_value):
    from support_agent.mindfulness_flexibility_tests import AAQII7
    from support_agent.psychometrics import score_questionnaire

    answers = {
        "aaqii7_1": invalid_value, "aaqii7_2": 1, "aaqii7_3": 1,
        "aaqii7_4": 1, "aaqii7_5": 1, "aaqii7_6": 1, "aaqii7_7": 1,
    }

    with pytest.raises(ValueError, match="integer within"):
        score_questionnaire(AAQII7, answers)
