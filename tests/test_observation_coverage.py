"""Code-derived evidence levels retain useful, bounded conversational clues."""

import pytest

from support_agent.conversation_observation import analyze_observations, build_snapshot
from support_agent.schemas import CallBudget, Message
from tests.test_conversation_observation import Gateway, messages, observation, run


@pytest.mark.parametrize('count', [1, 2])
def test_fewer_than_three_habit_messages_preserve_a_limited_candidate(count):
    ms = messages()[:count]
    result = run(observation(ms), ms)
    item = result.observations[0]

    assert item.direction == 'unknown'
    assert result.status == 'insufficient'
    assert item.coverage == 'limited'
    assert item.tentative_direction == 'I'
    assert len(item.evidence) == count
    assert all(word in item.coverage_reason for word in ('消息', '事件', '情境'))


def test_supported_level_keeps_the_existing_three_message_event_context_rule():
    item = run(observation()).observations[0]
    assert item.direction == 'I'
    assert item.coverage == 'supported'
    assert item.tentative_direction == 'unknown'
    assert '3' in item.coverage_reason and '2' in item.coverage_reason


@pytest.mark.parametrize('field,value,missing', [
    ('event_id', 'one_event', '事件'),
    ('context_kind', 'work', '情境'),
])
def test_limited_reason_names_the_unmet_independence_requirement(field, value, missing):
    data = observation()
    for citation in data['evidence']:
        citation[field] = value
    item = run(data).observations[0]
    assert item.direction == 'unknown' and item.tentative_direction == 'I'
    assert item.coverage == 'limited' and missing in item.coverage_reason


def test_one_message_can_retain_three_distinct_quotes_without_becoming_supported():
    parts = [message.content for message in messages()]
    ms = [Message(id='one', role='user', content='\n'.join(parts))]
    data = observation()
    data['evidence'] = [dict(
        message_id='one', quote=text, event_id=f'event_{number}', context_kind=context,
    ) for number, (text, context) in enumerate(zip(parts, ('social', 'work', 'family')))]

    item = run(data, ms).observations[0]
    assert [citation.quote for citation in item.evidence] == parts
    assert item.direction == 'unknown' and item.tentative_direction == 'I'
    assert item.coverage == 'limited'


@pytest.mark.parametrize('counter_quote', [
    '上周聚会结束后，我独自在公园散步恢复精力。',
    '我独自在公园散步恢复精力。',
])
def test_duplicate_or_overlapping_quote_cannot_be_its_own_counterexample(counter_quote):
    data = observation(counter_evidence=[dict(
        message_id='0', quote=counter_quote, event_id='counter', context_kind='other',
    )])
    item = run(data).observations[0]
    assert item.counter_evidence == []
    assert item.direction == item.tentative_direction == 'unknown'
    assert item.coverage == 'limited' and '重叠' in item.coverage_reason


def test_repeated_quote_in_another_message_is_not_an_independent_counterexample():
    ms = messages()
    repeated = Message(id='repeat', role='user', content='再说一次：' + ms[0].content)
    data = observation(counter_evidence=[dict(
        message_id='repeat', quote=ms[0].content, event_id='not_new', context_kind='other',
    )])
    item = run(data, ms + [repeated]).observations[0]
    assert item.counter_evidence == [] and item.coverage == 'limited'
    assert item.direction == item.tentative_direction == 'unknown'
    assert '重叠' in item.coverage_reason


def test_broad_support_quote_containing_real_counter_clause_cannot_gain_support():
    ms = messages()
    contrary = '有些周末我又会主动邀请朋友聚会，见面后更有精神。'
    ms[0].content += contrary
    data = observation(ms, counter_evidence=[dict(
        message_id='0', quote=contrary, event_id='e0', context_kind='social',
    )])
    result = run(data, ms)
    item = result.observations[0]
    assert result.status == 'insufficient'
    assert item.direction == item.tentative_direction == 'unknown'
    assert item.coverage == 'limited' and '重叠' in item.coverage_reason
    assert item.evidence[0].quote == ms[0].content


def test_mixed_without_a_counterexample_cannot_claim_a_successful_finding():
    result = run(observation(direction='mixed'))
    item = result.observations[0]
    assert result.status == 'insufficient'
    assert item.direction == 'unknown' and item.tentative_direction == 'unknown'
    assert item.coverage == 'limited' and '反例' in item.coverage_reason


def test_independent_opposing_examples_remain_conflicting_without_choosing_a_pole():
    ms = messages() + [Message(
        id='counter', role='user',
        content='周末和熟悉的朋友见面后，我经常更有精神，还想继续找人聊天。',
    )]
    data = observation(counter_evidence=[dict(
        message_id='counter', quote=ms[-1].content,
        event_id='weekend_with_friends', context_kind='friends',
    )])
    item = run(data, ms).observations[0]
    assert item.coverage == 'conflicting' and item.direction == 'mixed'
    assert item.tentative_direction == 'unknown'
    assert len(item.counter_evidence) == 1
    assert '情境' in item.coverage_reason


def test_current_state_is_preserved_without_becoming_a_personality_candidate():
    item = run(observation(scope='state')).observations[0]
    assert item.direction == 'unknown' and item.tentative_direction == 'unknown'
    assert item.coverage == 'state' and item.evidence
    assert '当前' in item.coverage_reason or '当次' in item.coverage_reason


def test_unclear_habit_scope_has_a_specific_gap_without_a_tentative_pole():
    item = run(observation(scope='unclear')).observations[0]
    assert item.coverage == 'limited'
    assert item.direction == item.tentative_direction == 'unknown'
    assert '习惯' in item.coverage_reason


@pytest.mark.parametrize('subject', ['other', 'quoted', 'hypothetical', 'unknown', 'case_narrator'])
def test_untrusted_subjects_cannot_become_candidates_in_self_mode(subject):
    item = run(observation(subject=subject)).observations[0]
    assert item.coverage == 'out_of_scope'
    assert item.direction == item.tentative_direction == 'unknown'
    assert item.coverage_reason


def test_no_usable_behavior_quotes_is_none_rather_than_a_limited_direction():
    ms = [Message(id=str(number), role='user', content='我觉得我是INFP。') for number in range(3)]
    item = run(observation(ms), ms).observations[0]
    assert item.coverage == 'none' and item.evidence == []
    assert item.direction == item.tentative_direction == 'unknown'


def test_unbound_relationship_explains_scope_gap_without_a_tentative_trait():
    item = run(
        observation(domain='attachment', dimension='anxiety', direction='higher', relation_id='friend_1'),
        domains=('attachment',),
    ).observations[0]
    assert item.coverage == 'out_of_scope'
    assert item.direction == item.tentative_direction == 'unknown'
    assert '关系' in item.coverage_reason


def test_model_cannot_promote_coverage_or_supply_the_code_authored_reason():
    ms = messages()[:1]
    data = observation(ms)
    data.update(coverage='supported', tentative_direction='E', coverage_reason='MODEL_AUTHORED_REASON')
    item = run(data, ms).observations[0]
    assert item.coverage == 'limited' and item.tentative_direction == 'I'
    assert item.direction == 'unknown'
    assert 'MODEL_AUTHORED_REASON' not in item.coverage_reason


def test_model_schema_requires_complete_fields_and_omits_derived_coverage():
    gateway = Gateway({'observations': [observation()]})
    snapshot = build_snapshot('c', 'g', 1, 0, messages(), ('mbti',))
    assert analyze_observations(snapshot, gateway, CallBudget()).status == 'ok'
    definition = gateway.calls[0][2]['$defs']['Observation']
    assert set(definition['required']) == {
        'domain', 'dimension', 'direction', 'scope', 'subject', 'relation_id',
        'evidence', 'counter_evidence',
    }
    assert not {'coverage', 'tentative_direction', 'coverage_reason'} & set(definition['properties'])


def test_missing_model_subject_and_scope_are_repaired_instead_of_defaulting_silently():
    incomplete = observation()
    incomplete.pop('subject')
    incomplete.pop('scope')
    gateway = Gateway({'observations': [incomplete]}, {'observations': [observation()]})
    snapshot = build_snapshot('c', 'g', 1, 0, messages(), ('mbti',))
    result = analyze_observations(snapshot, gateway, CallBudget(limit=2))
    assert len(gateway.calls) == 2
    assert result.status == 'ok' and result.observations[0].coverage == 'supported'


def test_subject_mode_is_explicit_in_snapshot_fingerprint_and_provider_payload():
    default = build_snapshot('c', 'g', 1, 0, messages(), ('mbti',))
    explicit = build_snapshot('c', 'g', 1, 0, messages(), ('mbti',), subject_mode='self')
    synthetic = build_snapshot('c', 'g', 1, 0, messages(), ('mbti',), subject_mode='synthetic_case')
    assert default.subject_mode == explicit.subject_mode == 'self'
    assert default.fingerprint == explicit.fingerprint != synthetic.fingerprint
    gateway = Gateway({'observations': [observation(subject='case_narrator')]})
    result = analyze_observations(synthetic, gateway, CallBudget())
    assert result.status == 'ok' and result.observations[0].coverage == 'supported'
    import json
    assert json.loads(gateway.calls[0][0][0].content)['subject_mode'] == 'synthetic_case'


@pytest.mark.parametrize('subject', ['other', 'quoted', 'hypothetical', 'unknown'])
def test_synthetic_mode_does_not_relabel_other_or_ambiguous_subjects(subject):
    item = run(observation(subject=subject), subject_mode='synthetic_case').observations[0]
    assert item.coverage == 'out_of_scope'
    assert item.direction == item.tentative_direction == 'unknown'


def test_unsupported_subject_mode_is_rejected_before_building_a_trusted_snapshot():
    with pytest.raises(ValueError):
        build_snapshot('c', 'g', 1, 0, messages(), ('mbti',), subject_mode='untrusted_other')


def test_report_metadata_binds_immutable_user_sources_and_permission_identity():
    ms = [
        Message(id='source', role='user', content='abc'),
        Message(id='assistant', role='assistant', content='Not a source'),
    ]
    snapshot = build_snapshot(
        'c', 'test-generation', 4, 9, ms, ('mbti',), subject_mode='synthetic_case',
    )
    ms[0].content = 'changed after snapshot'
    gateway = Gateway({'observations': []})
    result = analyze_observations(snapshot, gateway, CallBudget())

    assert result.metrics['source_digests'] == {
        'source': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
    }
    assert result.metrics['subject_mode'] == 'synthetic_case'
    assert result.metrics['generation'] == 'test-generation'
    assert result.metrics['consent_revision'] == 4
    assert result.metrics['observation_revision'] == 9
    assert 'messages' not in result.metrics and 'content' not in result.metrics
