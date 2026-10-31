from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from support_agent.conversation_observation import Observation, ObservationEvidence


def evidence(index=1, *, event=None, context='work'):
    return ObservationEvidence(
        message_id=f'm{index}', quote=f'第{index}次经历中，我先安静休息再作决定。',
        event_id=event or f'event-{index}', context_kind=context,
    )


def observation(**changes):
    values = dict(
        domain='mbti', dimension='EI', subject='case_narrator', scope='habit',
        direction='unknown', tentative_direction='I', coverage='limited',
        evidence=[evidence()], counter_evidence=[],
    )
    values.update(changes)
    return Observation(**values)


def describe(item):
    from support_agent.observation_presentation import describe_observation
    return describe_observation(item)


def text(view):
    return ' '.join((view.level_label, view.direction_label, view.summary, *view.alternatives, view.next_question))


def test_limited_case_clue_explains_tentative_direction_and_concrete_evidence_gaps():
    item = observation(coverage_reason='UNTRUSTED_MODEL_DIAGNOSIS')
    view = describe(item)
    assert view.level_label == '初步线索'
    assert 'I' in view.direction_label
    assert '独处' in view.summary and '恢复精力' in view.summary
    assert '本次案例叙述者' in view.summary
    assert '1处引文' in view.summary and '1个事件' in view.summary and '1类情境' in view.summary
    assert '其他独立事件' in view.summary and '不同情境' in view.summary
    assert '稳定倾向' in view.summary
    assert 'UNTRUSTED_MODEL_DIAGNOSIS' not in text(view)
    assert 1 <= len(view.alternatives) <= 2
    assert all('可能' in alternative and '未证实' in alternative for alternative in view.alternatives)
    assert item.direction == 'unknown'


def test_supported_direction_uses_repeated_cross_context_evidence_without_type_synthesis():
    view = describe(observation(
        coverage='supported', direction='I', tentative_direction='unknown',
        evidence=[evidence(1), evidence(2), evidence(3, context='friends')],
    ))
    assert view.level_label == '多次经历支持'
    assert 'I' in view.direction_label and '待核对' not in view.direction_label
    assert '独处' in view.summary
    assert '3处引文' in view.summary and '3个事件' in view.summary and '2类情境' in view.summary
    assert '本次案例叙述者' in view.summary and '这些经历' in view.summary
    assert 'INFP' not in text(view) and '%' not in text(view)


def test_state_describes_only_current_feeling_even_if_input_carries_a_tentative_pole():
    view = describe(observation(coverage='state', scope='state', tentative_direction='I'))
    assert view.level_label == '当次感受'
    assert 'I' not in view.direction_label
    assert '独处后恢复精力' not in view.summary
    assert '当次' in view.summary and '稳定倾向' in view.summary
    assert '1处引文' in view.summary


def test_conflicting_evidence_keeps_both_sides_and_offers_contextual_explanations():
    view = describe(observation(
        coverage='conflicting', direction='mixed', tentative_direction='unknown',
        counter_evidence=[evidence(2, context='friends')],
    ))
    assert view.level_label == '情境差异'
    assert '单一方向' in view.direction_label
    assert '独处' in view.summary and '互动' in view.summary
    assert '2处引文' in view.summary and '2个事件' in view.summary
    alternatives = ' '.join(view.alternatives)
    assert '精力' in alternatives and '对象' in alternatives
    assert all('未证实' in value for value in view.alternatives)


def test_coverage_counts_do_not_count_same_quote_twice_across_support_and_counter():
    quote = evidence()
    view = describe(observation(coverage='conflicting', direction='mixed', counter_evidence=[quote]))
    assert '1处引文' in view.summary and '1个事件' in view.summary


def test_legacy_unknown_is_not_upgraded_from_evidence_or_tentative_field():
    legacy = SimpleNamespace(
        domain='mbti', dimension='EI', subject='self', scope='habit', direction='unknown',
        tentative_direction='I', evidence=[evidence(1), evidence(2), evidence(3, context='friends')],
        counter_evidence=[], relation_id='',
    )
    view = describe(legacy)
    assert view.level_label == '线索不足'
    assert 'I' not in view.direction_label
    assert '方向尚未明确' in view.summary
    assert '独处后恢复精力' not in view.summary


def test_legacy_case_narrator_requires_new_verified_scope_before_any_direction():
    legacy = SimpleNamespace(
        domain='mbti', dimension='EI', subject='case_narrator', scope='habit', direction='I',
        evidence=[evidence(1), evidence(2), evidence(3, context='friends')],
        counter_evidence=[], relation_id='',
    )
    view = describe(legacy)
    assert view.level_label == '范围待确认'
    assert 'I' not in view.direction_label


def test_legacy_verified_self_direction_can_still_be_read():
    legacy = SimpleNamespace(
        domain='mbti', dimension='EI', subject='self', scope='habit', direction='I',
        evidence=[evidence(1), evidence(2), evidence(3, context='friends')],
        counter_evidence=[], relation_id='',
    )
    view = describe(legacy)
    assert view.level_label == '多次经历支持'
    assert 'I' in view.direction_label


@pytest.mark.parametrize('subject', ['other', 'quoted', 'hypothetical', 'unknown'])
def test_unusable_subject_cannot_display_a_tentative_personality_direction(subject):
    view = describe(observation(subject=subject))
    assert view.level_label == '范围待确认'
    assert 'I' not in view.direction_label and '独处后恢复精力' not in view.summary
    assert view.alternatives == ()


def test_missing_attachment_relationship_has_a_specific_scope_gap():
    view = describe(observation(
        domain='attachment', dimension='anxiety', coverage='out_of_scope',
        tentative_direction='unknown', relation_id='',
    ))
    assert view.level_label == '范围待确认'
    assert '同一段已明确的关系' in view.summary
    assert '对方' not in view.direction_label


def test_attachment_explains_only_the_narrators_reactions_in_the_bound_relationship():
    view = describe(observation(
        domain='attachment', dimension='anxiety', relation_id='relation-1',
        tentative_direction='higher',
    ))
    assert '本次案例叙述者' in view.summary and '这段已明确的关系' in view.summary
    assert '担心' in view.summary and '确认' in view.summary
    assert all(term not in text(view) for term in ('对方不爱', '对方回避', '对方内心', '依恋障碍'))
    assert '叙述者' in view.next_question


def test_no_quotes_identifies_missing_behavior_without_a_personality_interpretation():
    view = describe(observation(coverage='none', tentative_direction='unknown', evidence=[]))
    assert view.level_label == '线索不足'
    assert '可核对的具体行为原话' in view.summary
    assert '0处引文' in view.summary
    assert view.alternatives == ()


def test_unclear_scope_limited_clue_does_not_invent_a_direction():
    view = describe(observation(scope='unclear', tentative_direction='unknown'))
    assert view.level_label == '初步线索'
    assert 'I' not in view.direction_label
    assert '习惯' in view.summary and '当次' in view.summary


@pytest.mark.parametrize('domain,dimension,pole,meaning', [
    ('mbti', 'EI', 'E', '互动'), ('mbti', 'EI', 'I', '独处'),
    ('mbti', 'SN', 'S', '具体事实'), ('mbti', 'SN', 'N', '可能性'),
    ('mbti', 'TF', 'T', '一致性'), ('mbti', 'TF', 'F', '对人的影响'),
    ('mbti', 'JP', 'J', '计划'), ('mbti', 'JP', 'P', '调整余地'),
    ('big_five', 'extraversion', 'higher', '主动参与'),
    ('big_five', 'extraversion', 'lower', '较安静'),
    ('big_five', 'agreeableness', 'higher', '协调'),
    ('big_five', 'agreeableness', 'lower', '坚持立场'),
    ('big_five', 'conscientiousness', 'higher', '跟进'),
    ('big_five', 'conscientiousness', 'lower', '固定计划'),
    ('big_five', 'neuroticism', 'higher', '担忧'),
    ('big_five', 'neuroticism', 'lower', '恢复较快'),
    ('big_five', 'openness', 'higher', '新想法'),
    ('big_five', 'openness', 'lower', '熟悉经验'),
    ('attachment', 'anxiety', 'higher', '确认'),
    ('attachment', 'anxiety', 'lower', '等待'),
    ('attachment', 'avoidance', 'higher', '自己处理'),
    ('attachment', 'avoidance', 'lower', '表达需要'),
])
def test_each_dimension_explains_the_selected_pole_in_concrete_behavior(domain, dimension, pole, meaning):
    view = describe(observation(
        domain=domain, dimension=dimension, tentative_direction=pole,
        relation_id='relation-1' if domain == 'attachment' else '',
    ))
    assert meaning in view.summary
    assert view.level_label == '初步线索'


def test_each_dimension_has_its_own_open_behavior_and_comparison_question():
    cases = [
        ('mbti', 'EI', '精力'), ('mbti', 'SN', '信息'),
        ('mbti', 'TF', '取舍'), ('mbti', 'JP', '安排'),
        ('big_five', 'extraversion', '参与'), ('big_five', 'agreeableness', '分歧'),
        ('big_five', 'conscientiousness', '任务'), ('big_five', 'neuroticism', '压力'),
        ('big_five', 'openness', '新观点'),
        ('attachment', 'anxiety', '联系'), ('attachment', 'avoidance', '支持'),
    ]
    questions = []
    for domain, dimension, topic in cases:
        view = describe(observation(
            domain=domain, dimension=dimension, tentative_direction='unknown',
            relation_id='r' if domain == 'attachment' else '',
        ))
        assert topic in view.next_question
        assert view.next_question.endswith('？')
        assert '叙述者' in view.next_question
        assert all(term not in view.next_question for term in ('内向吗', '焦虑吗', '你是否', '你是'))
        questions.append(view.next_question)
    assert len(set(questions)) == 11


def test_view_and_alternatives_are_immutable():
    view = describe(observation())
    with pytest.raises(FrozenInstanceError):
        view.summary = 'changed'
    assert isinstance(view.alternatives, tuple)
