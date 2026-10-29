import pytest


@pytest.mark.parametrize(
    'responses, expected_means',
    [
        (
            [1, 5, 4, 6, 7, 6, 2, 5, 7, 4],
            {
                'extraversion': 1.5,
                'agreeableness': 2.5,
                'conscientiousness': 3.5,
                'emotional_stability': 4.5,
                'openness': 5.5,
            },
        ),
        (
            [7, 1, 7, 1, 7, 1, 7, 1, 7, 1],
            {
                'extraversion': 7.0,
                'agreeableness': 7.0,
                'conscientiousness': 7.0,
                'emotional_stability': 7.0,
                'openness': 7.0,
            },
        ),
        (
            [1, 7, 1, 7, 1, 7, 1, 7, 1, 7],
            {
                'extraversion': 1.0,
                'agreeableness': 1.0,
                'conscientiousness': 1.0,
                'emotional_stability': 1.0,
                'openness': 1.0,
            },
        ),
    ],
)
def test_tipi_scores_original_item_pairs_with_reverse_scoring(responses, expected_means):
    from support_agent.psychometrics import score_questionnaire
    from support_agent.wellbeing_tests import TIPI

    answers = {f'tipi_{number}': response for number, response in enumerate(responses, 1)}
    result = score_questionnaire(TIPI, answers)

    assert {key: score.mean for key, score in result.dimensions.items()} == expected_means
