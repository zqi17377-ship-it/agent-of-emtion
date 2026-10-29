import pytest


def test_every_question_can_be_answered_from_its_displayed_poles():
    from support_agent.personality_questions import QUESTION_ITEMS, score_self_report

    assert len(QUESTION_ITEMS) == 8
    assert len({question.id for question in QUESTION_ITEMS}) == 8
    assert [question.axis for question in QUESTION_ITEMS] == [
        "EI", "EI", "SN", "SN", "TF", "TF", "JP", "JP"
    ]
    left_answers = {question.id: question.left_pole for question in QUESTION_ITEMS}
    right_answers = {question.id: question.right_pole for question in QUESTION_ITEMS}
    assert score_self_report(left_answers) == {"EI": "E", "SN": "S", "TF": "T", "JP": "J"}
    assert score_self_report(right_answers) == {"EI": "I", "SN": "N", "TF": "F", "JP": "P"}
    assert all(question.prompt and question.left_label and question.right_label for question in QUESTION_ITEMS)


@pytest.mark.parametrize(
    "answers, expected",
    [
        ({}, {"EI": "unknown", "SN": "unknown", "TF": "unknown", "JP": "unknown"}),
        ({"ei_1": "E"}, {"EI": "unknown", "SN": "unknown", "TF": "unknown", "JP": "unknown"}),
        ({"ei_1": "E", "ei_2": "unknown"}, {"EI": "unknown", "SN": "unknown", "TF": "unknown", "JP": "unknown"}),
        ({"ei_1": "unknown", "ei_2": "I"}, {"EI": "unknown", "SN": "unknown", "TF": "unknown", "JP": "unknown"}),
        ({"ei_1": "unknown", "ei_2": "unknown"}, {"EI": "unknown", "SN": "unknown", "TF": "unknown", "JP": "unknown"}),
        ({"ei_1": "E", "ei_2": "I"}, {"EI": "mixed", "SN": "unknown", "TF": "unknown", "JP": "unknown"}),
        ({"sn_1": "N", "sn_2": "S"}, {"EI": "unknown", "SN": "mixed", "TF": "unknown", "JP": "unknown"}),
        ({"tf_1": "T", "tf_2": "F"}, {"EI": "unknown", "SN": "unknown", "TF": "mixed", "JP": "unknown"}),
        ({"jp_1": "P", "jp_2": "J"}, {"EI": "unknown", "SN": "unknown", "TF": "unknown", "JP": "mixed"}),
    ],
)
def test_incomplete_unsure_and_split_answers_preserve_uncertainty(answers, expected):
    from support_agent.personality_questions import score_self_report

    original = answers.copy()
    assert score_self_report(answers) == expected
    assert answers == original


@pytest.mark.parametrize(
    "answers",
    [
        {"missing_question": "E"},
        {"ei_1": "S"},
        {"sn_1": "E"},
        {"tf_1": "J"},
        {"jp_1": "T"},
        {"ei_1": "e"},
        {"ei_1": ""},
        {"ei_1": "不确定 / 看情况"},
        {"ei_1": 1},
    ],
)
def test_invalid_answers_are_rejected_instead_of_becoming_preferences(answers):
    from support_agent.personality_questions import score_self_report

    with pytest.raises(ValueError):
        score_self_report(answers)


@pytest.mark.parametrize(
    "preferences, expected",
    [
        ({"EI": "I", "SN": "N", "TF": "F", "JP": "P"}, "INFP"),
        ({"JP": "J", "TF": "T", "SN": "S", "EI": "E"}, "ESTJ"),
        ({}, None),
        ({"EI": "I", "SN": "N", "TF": "F"}, None),
        ({"EI": "unknown", "SN": "N", "TF": "F", "JP": "P"}, None),
        ({"EI": "I", "SN": "mixed", "TF": "F", "JP": "P"}, None),
        ({"EI": "I", "SN": "N", "TF": "T/F", "JP": "P"}, None),
        ({"EI": "I", "SN": "N", "TF": "F", "JP": "j"}, None),
        ({"EI": "E", "SN": "I", "TF": "F", "JP": "P"}, None),
    ],
)
def test_only_complete_explicit_preferences_form_a_type(preferences, expected):
    from support_agent.personality_questions import confirmed_type

    assert confirmed_type(preferences) == expected
