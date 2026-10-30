from dataclasses import replace

import pytest


def definition():
    from support_agent.psychometrics import CompositeSpec,Questionnaire,TestItem
    return Questionnaire(
        id='unequal',title='Independent scoring fixture',description='Fixture',
        items=(TestItem('a1','A1','a'),TestItem('a2','A2','a'),TestItem('b1','B1','b'),TestItem('r1','R1','r',True)),
        options=('1','2','3','4','5'),min_score=1,
        dimension_labels={'a':'A','b':'B','r':'R'},source_name='Test',source_url='https://example.org',
        license_notice='Fixture',translation_note='Fixture',
        composites=(CompositeSpec('overall','Overall',('a','b','r')),),
    )


def test_composite_equally_weights_dimension_means_with_unequal_item_counts():
    from support_agent.psychometrics import score_questionnaire
    answers={'a1':1,'a2':1,'b1':5,'r1':1}
    result=score_questionnaire(definition(),answers)
    assert result.dimensions['a'].mean==1
    assert result.dimensions['b'].mean==5
    assert result.dimensions['r'].mean==5
    assert result.composites['overall'].mean==pytest.approx(11/3)
    assert result.composites['overall'].min_value==1
    assert result.composites['overall'].max_value==5
    assert result.answers==answers
    ordinary=score_questionnaire(replace(definition(),composites=()),answers)
    assert ordinary.composites=={}
    assert ordinary.dimensions==result.dimensions


@pytest.mark.parametrize('members',[(),('a','missing'),('a','a')])
def test_invalid_composite_members_are_rejected_before_scoring(members):
    from support_agent.psychometrics import CompositeSpec,score_questionnaire
    with pytest.raises(ValueError):
        score_questionnaire(replace(definition(),composites=(CompositeSpec('overall','Overall',members),)),{'a1':1,'a2':1,'b1':5,'r1':1})


def test_hidden_dimensions_require_a_visible_composite_result():
    from support_agent.psychometrics import score_questionnaire
    with pytest.raises(ValueError):
        score_questionnaire(replace(definition(),show_dimensions=False,composites=()),{'a1':1,'a2':1,'b1':5,'r1':1})
