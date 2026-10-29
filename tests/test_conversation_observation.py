import json
import pytest
from support_agent.schemas import Message, CallBudget, ModelResult, ModelCallError


class Gateway:
    mode = 'live'
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []
    def generate(self, messages, instructions, schema, budget):
        budget.consume()
        self.calls.append((messages, instructions, schema))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return ModelResult(text=json.dumps(response), model_id='test')


def messages():
    return [Message(id=str(i), role='user', content=text) for i, text in enumerate([
        '上周聚会结束后，我独自在公园散步恢复精力。',
        '周一工作会议结束，我自己在房间安静休息。',
        '上个月家庭旅行后，我习惯自己看书放松。'])]


def observation(ms=None, **changes):
    ms = ms or messages()
    data = dict(domain='mbti', dimension='EI', direction='I', subject='self', scope='habit', relation_id='',
                evidence=[dict(message_id=m.id, quote=m.content, event_id='e'+m.id,
                               context_kind='work' if m.id == '1' else 'social') for m in ms], counter_evidence=[])
    data.update(changes)
    return data


def run(data, ms=None, domains=('mbti',), **kwargs):
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    snap = build_snapshot('c', 'g', 1, 0, ms or messages(), domains, **kwargs)
    gateway = Gateway({'observations': [data]})
    return analyze_observations(snap, gateway, CallBudget(limit=2, deadline_seconds=40))


def test_three_events_support_direction():
    report = run(observation())
    assert report.status == 'ok'
    assert report.observations[0].direction == 'I'


@pytest.mark.parametrize('change', [dict(subject='other'), dict(subject='unknown'), dict(scope='state'), dict(scope='unclear')])
def test_nonself_or_state_cannot_be_strong(change):
    assert run(observation(**change)).observations[0].direction == 'unknown'


def test_one_event_split_into_three_messages_is_insufficient():
    data = observation()
    for e in data['evidence']:
        e['event_id'] = 'same'
    assert run(data).observations[0].direction == 'unknown'


def test_repeated_text_does_not_accumulate():
    ms = [Message(id=str(i), role='user', content=messages()[0].content) for i in range(3)]
    assert run(observation(ms), ms).observations[0].direction == 'unknown'


def test_verified_counter_evidence_remains_mixed():
    data = observation(counter_evidence=[observation()['evidence'][0]])
    assert run(data).observations[0].direction == 'mixed'


@pytest.mark.parametrize('bad', ['quote', 'message_id'])
def test_false_quote_and_assistant_source_are_repaired_then_rejected(bad):
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    data = observation()
    data['evidence'][0][bad] = 'PRIVATE_UNVERIFIED'
    gateway = Gateway({'observations': [data]}, {'observations': [data]})
    result = analyze_observations(build_snapshot('c', 'g', 1, 0, messages(), ('mbti',)), gateway, CallBudget(limit=2))
    assert result.error_code == 'invalid_response'
    assert len(gateway.calls) == 2
    assert 'PRIVATE_UNVERIFIED' not in gateway.calls[1][1]


def test_only_authorized_schema_and_prompt_and_reject_other_domain():
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    gateway = Gateway({'observations': [observation(domain='attachment', dimension='anxiety', direction='higher')]})
    result = analyze_observations(build_snapshot('c', 'g', 1, 0, messages(), ('mbti',)), gateway, CallBudget(limit=2))
    assert result.status == 'failed'
    assert len(gateway.calls) == 1
    sent = json.dumps(gateway.calls[0][2]) + gateway.calls[0][1]
    assert 'attachment' not in sent and 'big_five' not in sent


@pytest.mark.parametrize('relations,bindings,rid', [({}, {}, ''), ({'friend_1':'friend'}, {'0':'friend_1','1':'friend_2','2':'friend_1'}, 'friend_1')])
def test_unknown_relationship_or_two_friends_cannot_merge(relations, bindings, rid):
    result = run(observation(domain='attachment', dimension='anxiety', direction='higher', relation_id=rid),
                 domains=('attachment',), relations=relations, message_relations=bindings)
    assert result.observations[0].direction == 'unknown'


def test_snapshot_copies_and_fingerprints_content_permissions_relations_and_exclusions():
    from support_agent.conversation_observation import build_snapshot
    ms = messages()
    snap = build_snapshot('c', 'g', 1, 0, ms, ('mbti',))
    ms[0].content = 'changed'
    assert snap.messages[0].content != 'changed'
    assert snap.fingerprint != build_snapshot('c','g',1,0,ms,('mbti',)).fingerprint
    assert snap.fingerprint != build_snapshot('c','g',1,0,messages(),('mbti',), excluded_keys=('mbti:EI:',)).fingerprint
    assert run(observation(), excluded_keys=('mbti:EI:',)).observations == []


def test_input_limits_fail_without_call_and_mock_has_no_traits():
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    for ms, code in [([messages()[0]]*2,'invalid_input'), ([Message(role='user',content='x'*16001)],'context_limit')]:
        gateway = Gateway()
        result = analyze_observations(build_snapshot('c','g',1,0,ms,('mbti',)),gateway,CallBudget())
        assert result.error_code == code and not gateway.calls
    gateway.mode='mock'
    result = analyze_observations(build_snapshot('c','g',1,0,messages(),('mbti',)),gateway,CallBudget())
    assert result.observations == []


def test_repeated_quote_with_different_surrounding_text_cannot_accumulate():
    ms = [Message(id=str(i), role='user', content=f'第{i}条记录：我平时喜欢独自安静休息。') for i in range(3)]
    data = observation(ms)
    for e in data['evidence']:
        e['quote'] = '我平时喜欢独自安静休息。'
    assert run(data, ms).observations[0].direction == 'unknown'


def test_type_label_fragment_is_not_behavior_evidence():
    ms = [Message(id=str(i),role='user',content='我觉得我是INFP。') for i in range(3)]
    assert run(observation(ms),ms).observations[0].direction == 'unknown'


def test_structure_repair_uses_shared_budget_and_reports_usage():
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    snap = build_snapshot('c','g',1,0,messages(),('mbti',))
    gateway = Gateway({'bad':'unverified private body'}, {'observations':[observation()]})
    budget = CallBudget(limit=2)
    result = analyze_observations(snap, gateway, budget)
    assert result.status == 'ok' and result.metrics['attempts'] == 2
    assert 'unverified private body' not in gateway.calls[1][1]
    gateway = Gateway({'bad':'body'})
    result = analyze_observations(snap,gateway,CallBudget(limit=1))
    assert result.error_code == 'budget' and len(gateway.calls) == 1


@pytest.mark.parametrize('error,code', [(ModelCallError('timeout'),'timeout'),(RuntimeError('PRIVATE_PROVIDER_BODY'),'unavailable')])
def test_provider_errors_are_safe_without_retry(error, code):
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    gateway = Gateway(error)
    result = analyze_observations(build_snapshot('c','g',1,0,messages(),('mbti',)),gateway,CallBudget())
    assert result.error_code == code and len(gateway.calls) == 1
    assert 'PRIVATE' not in result.model_dump_json()


def test_known_explicit_relationship_can_support_direction():
    result = run(observation(domain='attachment',dimension='anxiety',direction='higher',relation_id='friend_1'),
                 domains=('attachment',),relations={'friend_1':'friend'},message_relations={str(i):'friend_1' for i in range(3)})
    assert result.observations[0].direction == 'higher'


def test_oversized_report_is_repaired_not_truncated_silently():
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    gateway = Gateway({'observations':[observation()]*17}, {'observations':[]})
    result = analyze_observations(build_snapshot('c','g',1,0,messages(),('mbti',)),gateway,CallBudget(limit=2))
    assert result.observations == [] and result.metrics['attempts'] == 2


def test_unrecognized_unauthorized_domain_is_rejected_without_repair():
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    gateway = Gateway({'observations':[observation(domain='clinical')]}, {'observations':[observation()]})
    result = analyze_observations(build_snapshot('c','g',1,0,messages(),('mbti',)),gateway,CallBudget(limit=2))
    assert result.error_code == 'invalid_response' and len(gateway.calls) == 1


def test_snapshot_nested_values_are_immutable_and_still_serialize():
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    snap = build_snapshot('c','g',1,0,messages(),('attachment',),
                          relations={'friend_1':'friend'}, message_relations={'0':'friend_1'})
    with pytest.raises((ValueError, TypeError, AttributeError)):
        snap.messages[0].content = 'changed after identity computed'
    with pytest.raises(TypeError):
        snap.relations['friend_1'] = 'partner'
    with pytest.raises(TypeError):
        snap.message_relations['0'] = 'friend_2'
    assert snap.messages[0].model_dump()['content'] == messages()[0].content
    gateway = Gateway({'observations':[]})
    assert analyze_observations(snap,gateway,CallBudget()).error_code is None
    payload = json.loads(gateway.calls[0][0][0].content)
    assert payload['relations'] == {'friend_1':'friend'}


def test_snapshot_and_payload_omit_unauthorized_correction_metadata():
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    snap = build_snapshot('c','g',1,0,messages(),('mbti',),relations={'friend_private':'friend'},
                          message_relations={'0':'friend_private'},
                          excluded_keys=('attachment:anxiety:friend_private','mbti:EI:'))
    assert snap.excluded_keys == ('mbti:EI:',)
    gateway = Gateway({'observations':[]})
    assert analyze_observations(snap,gateway,CallBudget()).error_code is None
    sent = gateway.calls[0][0][0].content
    assert 'attachment' not in sent and 'friend_private' not in sent


@pytest.mark.parametrize('domain,dimension,direction', [('mbti','EI','I'),('big_five','extraversion','lower')])
def test_nonrelationship_observation_cannot_produce_relation_scoped_key(domain, dimension, direction):
    from support_agent.conversation_observation import build_snapshot, analyze_observations
    invalid = observation(domain=domain, dimension=dimension, direction=direction, relation_id='friend_1')
    gateway = Gateway({'observations':[invalid]}, {'observations':[invalid]})
    snap = build_snapshot('c','g',1,0,messages(),(domain,),excluded_keys=(f'{domain}:{dimension}:',))
    result = analyze_observations(snap,gateway,CallBudget(limit=2))
    assert result.status == 'failed' and result.error_code == 'invalid_response'
    assert result.observations == []
