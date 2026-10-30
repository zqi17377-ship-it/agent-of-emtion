"""Construct-specific presentation of the newly sourced questionnaire forms."""

from dataclasses import replace
from xml.etree import ElementTree as ET

import pytest

from support_agent.additional_personality_tests import IPIP100
from support_agent.psychometrics import score_questionnaire
from support_agent.relationship_risk_tests import DOSPERT30, ECR_R36, ECR_RS9
from support_agent.self_care_tests import MAAS15, SCS12, SCS26
from support_agent.survey_presentation import build_survey_presentation


def score_responses(definition, responses):
    return score_questionnaire(definition, {
        f'{definition.id}_{number}': value
        for number, value in enumerate(responses, 1)
    })


def circles(svg):
    return [element for element in ET.fromstring(svg).iter()
            if element.tag.endswith('circle')]


def test_ipip100_uses_the_five_axis_radar_and_its_original_directions():
    responses = (
        (5,) * 10 + (1,) * 10
        + (5,) * 14 + (1,) * 6
        + (5,) * 11 + (1,) * 9
        + (5,) * 5 + (1,) * 15
        + (5,) * 13 + (1,) * 7
    )
    presentation = build_survey_presentation(IPIP100, score_responses(IPIP100, responses))

    assert '雷达' in presentation.chart_label
    assert len(circles(presentation.svg)) == 5
    assert '情绪稳定性' in presentation.svg
    assert '智性/想象力' in presentation.svg
    assert '放松、沉着和情绪较稳定' in presentation.markdown
    assert '不等于智商' in presentation.markdown
    assert '五个维度分别理解' in presentation.markdown


def test_scs26_shows_six_axes_and_the_equal_weighted_composite_separately():
    # Kindness has five scores of 5; all five other subscale means are 1.
    # Their equal-weighted mean is 10/6=1.6667; the 26-item mean is 46/26.
    responses = (
        5, 5, 1, 5, 5, 5, 1, 5, 1, 1, 5, 5, 5,
        1, 1, 5, 1, 5, 5, 5, 5, 1, 5, 5, 5, 5,
    )
    presentation = build_survey_presentation(SCS26, score_responses(SCS26, responses))

    assert '雷达' not in presentation.chart_label
    assert len(circles(presentation.svg)) == 6
    assert '自我关怀总均分' not in presentation.svg
    assert '自我关怀总均分' in presentation.markdown
    assert '均分 1.67，原始范围 1—5' in presentation.markdown
    assert '1.77' not in presentation.markdown
    for label in SCS26.dimension_labels.values():
        assert label in presentation.svg and label in presentation.markdown


def test_scs26_reversed_axes_describe_less_negative_responding_at_high_scores():
    # All raw answers of 1 produce a score of 5 on each negative subscale.
    presentation = build_survey_presentation(SCS26, score_responses(SCS26, (1,) * 26))

    for label, meaning in (
        ('较少自我批评（反向计分）', '较少自我批评'),
        ('较少孤立感（反向计分）', '较少孤立感'),
        ('较少过度认同（反向计分）', '较少过度认同'),
    ):
        section = presentation.markdown.split('#### ' + label, 1)[1].split('#### ', 1)[0]
        assert '均分 5.00' in section
        assert '较高一侧' in section
        assert meaning in section
        assert '已经反向计分' in section


def test_scs12_chart_and_interpretation_only_expose_the_overall_mean():
    # Short-form source order: kindness 2,6 score 5; other ten items score 1.
    responses = (5, 5, 1, 5, 1, 5, 1, 5, 5, 1, 5, 5)
    presentation = build_survey_presentation(SCS12, score_responses(SCS12, responses))

    assert len(circles(presentation.svg)) == 1
    assert '自我关怀总均分' in presentation.svg
    assert '均分 1.67，原始范围 1—5' in presentation.markdown
    for label in SCS12.dimension_labels.values():
        assert label not in presentation.svg
        assert label not in presentation.markdown
    assert '六个分量表' not in presentation.markdown


def test_maas_uses_its_frequency_direction_and_own_six_point_range():
    low = build_survey_presentation(MAAS15, score_responses(MAAS15, (1,) * 15))
    high = build_survey_presentation(MAAS15, score_responses(MAAS15, (6,) * 15))

    assert '较多走神' in low.markdown
    assert '较少走神' in high.markdown
    assert '自动驾驶' in low.markdown and '自动驾驶' in high.markdown
    assert '均分 6.00，原始范围 1—6' in high.markdown
    assert len(circles(high.svg)) == 1


@pytest.mark.parametrize('definition,raw', [(MAAS15, 3), (DOSPERT30, 4)])
def test_forward_only_midrange_results_do_not_invent_reverse_key_cancellation(definition, raw):
    presentation = build_survey_presentation(
        definition, score_responses(definition, (raw,) * len(definition.items)),
    )

    assert '在本量程中间一带' in presentation.markdown
    assert '正反方向相互抵消' not in presentation.markdown


@pytest.mark.parametrize('raw,total', [(1, 6), (7, 42)])
def test_dospert_uses_five_independent_sum_ranges(raw, total):
    presentation = build_survey_presentation(
        DOSPERT30, score_responses(DOSPERT30, (raw,) * 30),
    )

    assert '雷达' not in presentation.chart_label
    assert len(circles(presentation.svg)) == 5
    assert presentation.markdown.count(f'{total} 分，原始范围 6—42') == 5
    for label in DOSPERT30.dimension_labels.values():
        assert label in presentation.svg and label in presentation.markdown
    assert '行为意向' in presentation.markdown
    assert '不计算跨领域总分' in presentation.markdown
    assert '不表示应该尝试' in presentation.markdown


@pytest.mark.parametrize('definition', [ECR_R36, ECR_RS9])
def test_ecr_profiles_do_not_use_the_original_attachment_heuristic(monkeypatch, definition):
    import support_agent.attachment_questions as original
    import support_agent.survey_presentation as presentation_module

    def original_heuristic_must_not_run(*args, **kwargs):
        raise AssertionError('ECR must not use the original attachment heuristic')

    monkeypatch.setattr(original, 'attachment_pattern', original_heuristic_must_not_run)
    monkeypatch.setattr(presentation_module, 'attachment_dimension_band', original_heuristic_must_not_run)
    # Raw 4 is unchanged by reversal on a 1—7 scale: both ECR dimensions = 4.
    result = score_responses(definition, (4,) * len(definition.items))
    presentation = build_survey_presentation(definition, result)

    assert len(circles(presentation.svg)) == 2
    assert presentation.markdown.count('在本量程中间一带') == 2
    for forbidden in ('中点启发式', '2.5—3.5', '较接近安全的应答倾向', '并存的应答倾向'):
        assert forbidden not in presentation.markdown
    if definition.id == 'ecr_r36':
        assert '平时亲密伴侣关系' in presentation.markdown
        assert '所选关系' not in presentation.markdown
        assert '选定关系' not in presentation.markdown
    else:
        assert '所选关系' in presentation.markdown


@pytest.mark.parametrize('composite_change', [
    {'key': 'wrong_key'},
    {'mean': float('nan')},
    {'mean': float('inf')},
    {'mean': 0},
    {'mean': 6},
    {'min_value': 0},
    {'max_value': 6},
    {'min_value': 5, 'max_value': 1},
])
def test_presentation_rejects_mismatched_or_out_of_range_composites(composite_change):
    result = score_responses(SCS12, (3,) * 12)
    malformed = replace(result.composites['self_compassion'], **composite_change)
    result = replace(result, composites={'self_compassion': malformed})

    with pytest.raises(ValueError, match='[Cc]omposite'):
        build_survey_presentation(SCS12, result)


@pytest.mark.parametrize('change', ['missing', 'extra'])
def test_presentation_requires_exactly_the_declared_composite_keys(change):
    result = score_responses(SCS26, (3,) * 26)
    composites = {} if change == 'missing' else {
        **result.composites,
        'extra': replace(result.composites['self_compassion'], key='extra'),
    }

    with pytest.raises(ValueError, match='[Cc]omposite'):
        build_survey_presentation(SCS26, replace(result, composites=composites))
