import pytest


KEYS={
    'erq30_behavioral_activation':{4,14,23},
    'erq30_problem_solving':{6,16,25},
    'erq30_situational_avoidance':{5,15,24},
    'erq30_social_withdrawal':{11,21,30},
    'erq30_distraction':{9,19,28},
    'erq30_rumination':{8,18,27},
    'erq30_acceptance':{10,20,29},
    'erq30_cognitive_reappraisal':{1,3,12},
    'erq30_expressive_suppression':{2,13,22},
    'erq30_social_sharing':{7,17,26},
}


def test_english_erq30_preserves_author_key_and_unlabeled_intermediate_options():
    from support_agent.emotion_regulation_tests import ERQ30_EN
    assert len(ERQ30_EN.items)==30
    assert [item.id for item in ERQ30_EN.items]==[f'erq30_{n}' for n in range(1,31)]
    for key,numbers in KEYS.items():
        assert {int(item.id.split('_')[-1]) for item in ERQ30_EN.items if item.dimension==key}==numbers
    assert not any(item.reverse for item in ERQ30_EN.items)
    assert ERQ30_EN.options==('1 · Strongly disagree','2','3','4 · Neither agree nor disagree','5','6','7 · Strongly agree')
    assert ERQ30_EN.items[1].text=='I keep my emotions to myself.'
    assert not any('\u4e00'<=c<='\u9fff' for item in ERQ30_EN.items for c in item.text)


@pytest.mark.parametrize('value,total',[(1,3),(7,21)])
def test_erq30_subscales_have_their_own_original_sum_range(value,total):
    from support_agent.emotion_regulation_tests import ERQ30_EN
    from support_agent.psychometrics import score_questionnaire
    result=score_questionnaire(ERQ30_EN,{item.id:value for item in ERQ30_EN.items})
    assert len(result.dimensions)==10 and result.composites=={}
    assert all(d.total==total and d.min_total==3 and d.max_total==21 for d in result.dimensions.values())


def test_erq30_mixed_vector_matches_independently_calculated_subscale_sums():
    from support_agent.emotion_regulation_tests import ERQ30_EN
    from support_agent.psychometrics import score_questionnaire
    raw=[1,2,3,4,5,6,7,1,2,3,4,5,6,7,1,2,3,4,5,6,7,1,2,3,4,5,6,7,1,2]
    result=score_questionnaire(ERQ30_EN,{f'erq30_{n}':v for n,v in enumerate(raw,1)})
    assert {k:d.total for k,d in result.dimensions.items()}=={
        'erq30_behavioral_activation':13,'erq30_problem_solving':12,
        'erq30_situational_avoidance':9,'erq30_social_withdrawal':13,
        'erq30_distraction':14,'erq30_rumination':11,'erq30_acceptance':10,
        'erq30_cognitive_reappraisal':9,'erq30_expressive_suppression':9,'erq30_social_sharing':15,
    }


def test_erq30_incomplete_responses_are_not_imputed():
    from support_agent.emotion_regulation_tests import ERQ30_EN
    from support_agent.psychometrics import score_questionnaire
    with pytest.raises(ValueError):
        score_questionnaire(ERQ30_EN,{f'erq30_{n}':4 for n in range(1,30)})
