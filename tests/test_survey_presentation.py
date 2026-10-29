from dataclasses import replace
from xml.etree import ElementTree as ET

import pytest

from support_agent.psychometrics import score_questionnaire
from support_agent.published_personality_tests import MINI_IPIP, RSES
from support_agent.wellbeing_tests import TIPI
from support_agent.long_personality_tests import IPIP50, SWLS3
from support_agent.research_wellbeing_tests import SWLS, COPING_CONFIDENCE
from support_agent.attachment_questions import ATTACHMENT_EXPLORATION
from support_agent.survey_presentation import build_survey_presentation


def at_score(definition, value):
    return score_questionnaire(definition, {
        item.id: definition.min_score+definition.max_score-value if item.reverse else value
        for item in definition.items
    })


def vertices(svg):
    root=ET.fromstring(svg)
    polygon=next(e for e in root.iter() if e.attrib.get('data-series')=='answers')
    return [tuple(map(float,p.split(','))) for p in polygon.attrib['points'].split()]


@pytest.mark.parametrize('definition',[TIPI,MINI_IPIP,IPIP50])
def test_big_five_chart_preserves_each_instrument_axes_and_scale_endpoints(definition):
    low=build_survey_presentation(definition,at_score(definition,definition.min_score))
    high=build_survey_presentation(definition,at_score(definition,definition.max_score))
    assert '雷达' in low.chart_label
    assert len(vertices(high.svg))==5
    assert len(set(vertices(low.svg)))==1  # minimum belongs at the common centre
    assert len(set(vertices(high.svg)))==5
    for label in definition.dimension_labels.values():
        assert label in high.svg and label in high.markdown
    assert '百分位' in high.markdown and '不' in high.markdown
    assert low.markdown!=high.markdown


def test_midpoint_is_not_a_claimed_type_and_radar_is_half_radius():
    mid=build_survey_presentation(MINI_IPIP,at_score(MINI_IPIP,3))
    high=build_survey_presentation(MINI_IPIP,at_score(MINI_IPIP,5))
    low=build_survey_presentation(MINI_IPIP,at_score(MINI_IPIP,1))
    centre=vertices(low.svg)[0]
    for middle,outer in zip(vertices(mid.svg),vertices(high.svg)):
        assert middle[0]-centre[0]==pytest.approx((outer[0]-centre[0])/2,abs=.01)
        assert middle[1]-centre[1]==pytest.approx((outer[1]-centre[1])/2,abs=.01)
    assert '中间' in mid.markdown and '暂不' in mid.markdown


def test_emotional_axes_keep_opposite_scoring_directions():
    negative=build_survey_presentation(MINI_IPIP,at_score(MINI_IPIP,5)).markdown
    stable=build_survey_presentation(IPIP50,at_score(IPIP50,5)).markdown
    assert '烦扰' in negative
    assert '放松' in stable
    assert '负性情绪倾向' in negative and '情绪稳定性' in stable
    assert '智商' in stable


@pytest.mark.parametrize('definition',[SWLS3,SWLS,RSES,COPING_CONFIDENCE,ATTACHMENT_EXPLORATION])
def test_other_constructs_use_own_range_and_do_not_fabricate_personality(definition):
    result=at_score(definition,definition.max_score)
    presentation=build_survey_presentation(definition,result)
    ET.fromstring(presentation.svg)
    assert '雷达' not in presentation.chart_label
    assert 'MBTI' not in presentation.markdown
    assert '反思' in presentation.markdown
    for dimension in result.dimensions.values():
        assert dimension.label in presentation.markdown
        assert str(dimension.max_total) in presentation.markdown or f'{dimension.max_value}' in presentation.markdown
    assert presentation.markdown!=build_survey_presentation(definition,at_score(definition,definition.min_score)).markdown


def test_swls_three_and_five_item_versions_show_their_own_totals():
    three=build_survey_presentation(SWLS3,at_score(SWLS3,7))
    five=build_survey_presentation(SWLS,at_score(SWLS,7))
    assert '21' in three.markdown and '35' in five.markdown
    assert '生活满意度' in three.markdown


def test_svg_is_accessible_responsive_and_escapes_untrusted_labels():
    result=at_score(RSES,3)
    label='<script>alert("x")</script>&名字'
    definition=replace(RSES,dimension_labels={'self_esteem':label})
    result=replace(result,dimensions={'self_esteem':replace(result.dimensions['self_esteem'],label=label)})
    presentation=build_survey_presentation(definition,result)
    root=ET.fromstring(presentation.svg)
    assert root.attrib['role']=='img' and root.attrib['viewBox']
    assert 'width:100%' in presentation.svg
    assert '<script>' not in presentation.svg
    assert '&lt;script&gt;' in presentation.svg
    assert any(e.tag.endswith('title') for e in root.iter())
    assert any(e.tag.endswith('desc') for e in root.iter())


def test_wrong_questionnaire_or_missing_dimensions_is_rejected():
    with pytest.raises(ValueError):
        build_survey_presentation(SWLS3,at_score(SWLS,4))
    result=at_score(MINI_IPIP,3)
    with pytest.raises(ValueError):
        build_survey_presentation(MINI_IPIP,replace(result,dimensions={}))


def attachment_at_means(anxiety_values,avoidance_values):
    values={'anxiety':iter(anxiety_values),'avoidance':iter(avoidance_values)}
    answers={}
    for item in ATTACHMENT_EXPLORATION.items:
        value=next(values[item.dimension])
        answers[item.id]=6-value if item.reverse else value
    return score_questionnaire(ATTACHMENT_EXPLORATION,answers)


@pytest.mark.parametrize('anxiety_values,expected_band',[
    ([5,5,1,1,1,1],'较低一侧'),
    ([1,2,3,3,3,3],'中间一带'),
    ([2,3,4,4,4,4],'中间一带'),
    ([5,5,5,3,2,2],'较高一侧'),
])
def test_attachment_interpretation_agrees_with_existing_midpoint_rule(anxiety_values,expected_band):
    from support_agent.attachment_questions import attachment_pattern
    result=attachment_at_means(anxiety_values,[4]*6)
    presentation=build_survey_presentation(ATTACHMENT_EXPLORATION,result)
    anxiety_section=presentation.markdown.split('#### 关系焦虑',1)[1].split('#### 亲近回避',1)[0]
    assert expected_band in anxiety_section
    label,_=attachment_pattern(result)
    if expected_band=='中间一带':
        assert '暂不清晰' in label
    elif expected_band=='较低一侧':
        assert '较多亲近回避' in label
    else:
        assert '并存' in label
    assert '2.5—3.5' in presentation.markdown
    assert '含边界' in presentation.markdown
    assert '未经验证' in presentation.markdown
