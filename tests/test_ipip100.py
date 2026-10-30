"""IPIP's five official 20-item factor keys, independently transcribed."""

from collections import Counter

import pytest


# The official 20-item keys are grouped by factor, positive items first.
# These IDs are transcribed from the source, not obtained from the definition.
KEYS = {
    'extraversion': (
        {1, 2, 3, 4, 5, 6, 7, 8, 9, 10},
        {11, 12, 13, 14, 15, 16, 17, 18, 19, 20},
    ),
    'agreeableness': (
        {21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34},
        {35, 36, 37, 38, 39, 40},
    ),
    'conscientiousness': (
        {41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51},
        {52, 53, 54, 55, 56, 57, 58, 59, 60},
    ),
    'emotional_stability': (
        {61, 62, 63, 64, 65},
        {66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80},
    ),
    'intellect_imagination': (
        {81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93},
        {94, 95, 96, 97, 98, 99, 100},
    ),
}


def test_ipip100_preserves_all_five_twenty_item_keys_and_order():
    from support_agent.additional_personality_tests import IPIP100

    assert IPIP100.id == 'ipip100'
    assert [item.id for item in IPIP100.items] == [
        f'ipip100_{number}' for number in range(1, 101)
    ]
    assert len({item.id for item in IPIP100.items}) == 100
    assert Counter(item.dimension for item in IPIP100.items) == {
        'extraversion': 20,
        'agreeableness': 20,
        'conscientiousness': 20,
        'emotional_stability': 20,
        'intellect_imagination': 20,
    }
    assert tuple(IPIP100.dimension_labels) == tuple(KEYS)
    for dimension, (positive, negative) in KEYS.items():
        assert {item.id for item in IPIP100.items
                if item.dimension == dimension and not item.reverse} == {
            f'ipip100_{number}' for number in positive
        }
        assert {item.id for item in IPIP100.items
                if item.dimension == dimension and item.reverse} == {
            f'ipip100_{number}' for number in negative
        }


@pytest.mark.parametrize('responses, totals', [
    # Endorse every + item and reject every - item: 20 * 5 = 100 each.
    (
        (5,) * 10 + (1,) * 10
        + (5,) * 14 + (1,) * 6
        + (5,) * 11 + (1,) * 9
        + (5,) * 5 + (1,) * 15
        + (5,) * 13 + (1,) * 7,
        (100, 100, 100, 100, 100),
    ),
    # The opposite responses produce 20 * 1 = 20 in every factor.
    (
        (1,) * 10 + (5,) * 10
        + (1,) * 14 + (5,) * 6
        + (1,) * 11 + (5,) * 9
        + (1,) * 5 + (5,) * 15
        + (1,) * 13 + (5,) * 7,
        (20, 20, 20, 20, 20),
    ),
    # All endorsements expose the unequal + and - item counts per factor.
    ((5,) * 100, (60, 76, 64, 40, 72)),
    ((1,) * 100, (60, 44, 56, 80, 48)),
])
def test_ipip100_scores_hand_calculated_factor_extremes(responses, totals):
    from support_agent.additional_personality_tests import IPIP100
    from support_agent.psychometrics import score_questionnaire

    answers = {f'ipip100_{number}': value
               for number, value in enumerate(responses, 1)}
    result = score_questionnaire(IPIP100, answers)

    assert len(responses) == 100
    assert IPIP100.min_score == 1
    assert IPIP100.max_score == 5
    assert IPIP100.display == 'mean'
    assert tuple(result.dimensions) == tuple(KEYS)
    assert tuple(part.total for part in result.dimensions.values()) == totals
    assert tuple(part.mean for part in result.dimensions.values()) == tuple(
        total / 20 for total in totals
    )
    assert all((part.count, part.min_total, part.max_total) == (20, 20, 100)
               for part in result.dimensions.values())
    assert result.answers == answers


def test_ipip100_rejects_a_missing_answer_instead_of_imputing():
    from support_agent.additional_personality_tests import IPIP100
    from support_agent.psychometrics import score_questionnaire

    answers = {f'ipip100_{number}': 3 for number in range(1, 100)}
    with pytest.raises(ValueError, match='exactly all'):
        score_questionnaire(IPIP100, answers)
