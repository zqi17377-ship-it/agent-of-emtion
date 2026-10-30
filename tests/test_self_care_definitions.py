"""Author-keyed scoring checks for self-compassion and adult trait mindfulness."""

from importlib import import_module

import pytest

from support_agent.psychometrics import score_questionnaire


# Hand-checked against the author's SCS information PDF, scoring-key page.
FULL_KEY = {
    'self_kindness': ({5, 12, 19, 23, 26}, False),
    'self_judgment_reversed': ({1, 8, 11, 16, 21}, True),
    'common_humanity': ({3, 7, 10, 15}, False),
    'isolation_reversed': ({4, 13, 18, 25}, True),
    'scs_mindfulness': ({9, 14, 17, 22}, False),
    'over_identification_reversed': ({2, 6, 20, 24}, True),
}
SHORT_KEY = {
    'self_kindness': ({2, 6}, False),
    'self_judgment_reversed': ({11, 12}, True),
    'common_humanity': ({5, 10}, False),
    'isolation_reversed': ({4, 8}, True),
    'scs_mindfulness': ({3, 7}, False),
    'over_identification_reversed': ({1, 9}, True),
}


@pytest.mark.parametrize('export,prefix,count,key', [
    ('SCS26', 'scs26', 26, FULL_KEY),
    ('SCS12', 'scs12', 12, SHORT_KEY),
])
def test_scs_item_changes_follow_author_dimension_and_reversal_keys(export, prefix, count, key):
    form = getattr(import_module('support_agent.self_care_tests'), export)
    assert [item.id for item in form.items] == [f'{prefix}_{n}' for n in range(1, count + 1)]
    assert (form.min_score, form.max_score) == (1, 5)
    baseline = {item.id: 3 for item in form.items}

    # Each individual response must move only its keyed dimension, with the
    # keyed direction; aggregate weighting is equal across the six means.
    for dimension, (numbers, reverse) in key.items():
        for number in numbers:
            answers = {**baseline, f'{prefix}_{number}': 5}
            result = score_questionnaire(form, answers)
            change = (-2 if reverse else 2) / len(numbers)
            assert result.dimensions[dimension].mean == pytest.approx(3 + change)
            assert result.dimensions[dimension].count == len(numbers)
            for other in key.keys() - {dimension}:
                assert result.dimensions[other].mean == 3
            assert result.composites['self_compassion'].mean == pytest.approx(3 + change / 6)
            assert result.answers[f'{prefix}_{number}'] == 5


def test_scs26_composite_uses_six_means_rather_than_26_item_average():
    form = import_module('support_agent.self_care_tests').SCS26
    # Five self-kindness answers = 5; all other keyed answers = 3.
    # Six-mean average = (5 + 3 + 3 + 3 + 3 + 3) / 6 = 10/3.
    answers = {f'scs26_{n}': (5 if n in {5, 12, 19, 23, 26} else 3) for n in range(1, 27)}
    result = score_questionnaire(form, answers)
    assert result.composites['self_compassion'].mean == pytest.approx(10 / 3)
    assert result.composites['self_compassion'].min_value == 1
    assert result.composites['self_compassion'].max_value == 5
    assert form.show_dimensions is True


def test_scs12_is_official_reordered_subset_and_suppresses_subscale_reporting():
    definitions = import_module('support_agent.self_care_tests')
    # Author's short-to-long mapping, not the first twelve full-scale items.
    full_numbers = (6, 26, 14, 13, 15, 12, 9, 25, 2, 10, 1, 11)
    for short_item, full_number in zip(definitions.SCS12.items, full_numbers, strict=True):
        full_item = definitions.SCS26.items[full_number - 1]
        assert short_item.text == full_item.text
        assert short_item.dimension == full_item.dimension
        assert short_item.reverse == full_item.reverse
    assert definitions.SCS12.show_dimensions is False


@pytest.mark.parametrize('response,expected', [(1, 1.0), (6, 6.0)])
def test_adult_trait_maas_uses_15_direct_scores_with_six_point_frequency_direction(response, expected):
    form = import_module('support_agent.self_care_tests').MAAS15
    assert [item.id for item in form.items] == [f'maas15_{n}' for n in range(1, 16)]
    assert (form.min_score, form.max_score) == (1, 6)
    assert form.options[0] == '几乎总是'
    assert form.options[-1] == '几乎从不'
    result = score_questionnaire(form, {item.id: response for item in form.items})
    assert set(result.dimensions) == {'mindful_attention'}
    assert result.dimensions['mindful_attention'].count == 15
    assert result.dimensions['mindful_attention'].mean == expected
    assert result.composites == {}


def test_adult_trait_maas_averages_the_raw_responses_without_double_reversal():
    form = import_module('support_agent.self_care_tests').MAAS15
    # Raw sum = 48, so the original six-point mean is 48/15 = 3.2.
    responses = (1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6, 1, 2, 3)
    result = score_questionnaire(form, dict(zip((item.id for item in form.items), responses, strict=True)))
    assert result.dimensions['mindful_attention'].mean == 3.2
