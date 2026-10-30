"""Behavioral checks for deterministic, local questionnaire scoring."""

from dataclasses import FrozenInstanceError, asdict, replace

import pytest

import support_agent.psychometrics as scoring
import support_agent.attachment_questions as attachment


def definition():
    return scoring.Questionnaire(
        id='example', title='示例', description='仅用于验证计算。',
        items=(
            scoring.TestItem('a1', '第一题', 'a'),
            scoring.TestItem('a2', '第二题', 'a', reverse=True),
            scoring.TestItem('b1', '第三题', 'b'),
        ),
        options=('很不符合', '不太符合', '一般', '比较符合', '很符合'),
        min_score=1, dimension_labels={'a': '维度甲', 'b': '维度乙'},
        source_name='测试夹具', source_url='', license_notice='原创测试题。',
        translation_note='不涉及翻译。',
    )


def test_scores_each_dimension_and_retains_raw_answers_for_export():
    answers = {'a1': 4, 'a2': 2, 'b1': 3}
    result = scoring.score_questionnaire(definition(), answers)

    assert asdict(result) == {
        'test_id': 'example',
        'version_id': None,
        'composites': {},
        'dimensions': {
            'a': {
                'key': 'a', 'label': '维度甲', 'total': 8, 'mean': 4.0,
                'count': 2, 'min_total': 2, 'max_total': 10,
                'min_value': 1, 'max_value': 5,
            },
            'b': {
                'key': 'b', 'label': '维度乙', 'total': 3, 'mean': 3.0,
                'count': 1, 'min_total': 1, 'max_total': 5,
                'min_value': 1, 'max_value': 5,
            },
        },
        'answers': {'a1': 4, 'a2': 2, 'b1': 3},
    }
    answers['a1'] = 1
    assert result.answers['a1'] == 4
    with pytest.raises(FrozenInstanceError):
        result.test_id = 'changed'
    with pytest.raises(FrozenInstanceError):
        result.dimensions['a'].mean = 0


@pytest.mark.parametrize('answers,want_total', [
    ({'a1': 1, 'a2': 5, 'b1': 1}, 2),
    ({'a1': 5, 'a2': 1, 'b1': 5}, 10),
])
def test_reverse_item_uses_inclusive_scale_extrema(answers, want_total):
    result = scoring.score_questionnaire(definition(), answers)
    assert result.dimensions['a'].total == want_total


def test_reverse_item_works_with_a_zero_based_response_scale():
    form = replace(definition(), min_score=0)
    result = scoring.score_questionnaire(form, {'a1': 0, 'a2': 0, 'b1': 4})
    assert form.max_score == 4
    assert result.dimensions['a'].total == 4
    assert result.dimensions['a'].mean == 2.0
    assert result.dimensions['a'].min_total == 0
    assert result.dimensions['a'].max_total == 8


@pytest.mark.parametrize('answers', [
    {}, {'a1': 1, 'a2': 2},
    {'a1': 1, 'a2': 2, 'b1': 3, 'foreign': 4},
    {'a1': 1, 'a2': 2, 'foreign': 3},
])
def test_rejects_missing_or_extra_answers(answers):
    with pytest.raises(ValueError):
        scoring.score_questionnaire(definition(), answers)


@pytest.mark.parametrize('value', [True, False, 1.0, 3.5, '3', None, 0, 6])
def test_rejects_non_integer_or_out_of_range_answers(value):
    with pytest.raises(ValueError):
        scoring.score_questionnaire(
            definition(), {'a1': value, 'a2': 2, 'b1': 3},
        )


@pytest.mark.parametrize('change', [
    {'options': ('只有一个选项',)},
    {'items': ()},
    {'dimension_labels': {'a': '甲'}},
    {'dimension_labels': {'a': '甲', 'b': '乙', 'unused': '丙'}},
    {'min_score': True},
    {'min_score': 1.5},
])
def test_rejects_invalid_definitions(change):
    with pytest.raises(ValueError):
        form = replace(definition(), **change)
        scoring.score_questionnaire(form, {'a1': 1, 'a2': 2, 'b1': 3})


def test_rejects_duplicate_item_ids_before_scoring():
    with pytest.raises(ValueError):
        form = replace(definition(), items=(
            scoring.TestItem('same', '甲', 'a'),
            scoring.TestItem('same', '乙', 'b'),
        ))
        scoring.score_questionnaire(form, {'same': 3})


def test_questionnaire_and_items_are_frozen():
    form = definition()
    with pytest.raises(FrozenInstanceError):
        form.title = 'changed'
    with pytest.raises(FrozenInstanceError):
        form.items[0].reverse = True


def test_original_attachment_exercise_scores_two_six_item_dimensions():
    form = attachment.ATTACHMENT_EXPLORATION
    result = scoring.score_questionnaire(
        form, {item.id: 1 for item in form.items},
    )
    assert len(form.items) == 12
    assert len({item.id for item in form.items}) == 12
    assert form.min_score == 1
    assert form.max_score == 5
    assert set(result.dimensions) == {'anxiety', 'avoidance'}
    assert result.dimensions['anxiety'].count == 6
    assert result.dimensions['avoidance'].count == 6
    assert result.dimensions['anxiety'].min_total == 6
    assert result.dimensions['anxiety'].max_total == 30


def attachment_result(anxiety, avoidance):
    form = attachment.ATTACHMENT_EXPLORATION
    answers = {}
    for dimension, values in (('anxiety', anxiety), ('avoidance', avoidance)):
        items = [item for item in form.items if item.dimension == dimension]
        for item, score in zip(items, values, strict=True):
            answers[item.id] = 6 - score if item.reverse else score
    return scoring.score_questionnaire(form, answers)


@pytest.mark.parametrize('anxiety,avoidance,want_label', [
    ([1] * 6, [1] * 6, '较接近安全的应答倾向'),
    ([5] * 6, [1] * 6, '较多关系焦虑的应答倾向'),
    ([1] * 6, [5] * 6, '较多亲近回避的应答倾向'),
    ([5] * 6, [5] * 6, '关系焦虑与亲近回避并存的应答倾向'),
    ([2, 2, 2, 3, 3, 3], [1] * 6, '混合或暂不清晰的应答倾向'),
    ([3, 3, 3, 4, 4, 4], [5] * 6, '混合或暂不清晰的应答倾向'),
    ([1] * 6, [2, 2, 2, 3, 3, 3], '混合或暂不清晰的应答倾向'),
    ([5] * 6, [3, 3, 3, 4, 4, 4], '混合或暂不清晰的应答倾向'),
])
def test_attachment_pattern_is_tentative_and_neutral_at_both_boundaries(
    anxiety, avoidance, want_label,
):
    label, explanation = attachment.attachment_pattern(
        attachment_result(anxiety, avoidance),
    )
    assert label == want_label
    assert '原创练习' in explanation
    assert '中点' in explanation
    assert '未经验证' in explanation
    assert '诊断' in explanation
    assert '稳定类型' in explanation


def test_attachment_pattern_does_not_accept_results_from_other_tests():
    result = scoring.score_questionnaire(definition(), {'a1': 1, 'a2': 2, 'b1': 3})
    with pytest.raises(ValueError):
        attachment.attachment_pattern(result)
