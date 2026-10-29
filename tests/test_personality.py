import json

import httpx
import pytest

from support_agent.model_client import DeepSeekGateway
from support_agent.schemas import Message, ModelCallError


FIRST = Message(id='u1', role='user', content='我平时在聚会后喜欢独处。学新东西时，我常先想整体可能性。做决定我会顾及人的感受。旅行我习惯留出临时调整的空间。')
SECOND = Message(id='u2', role='user', content='工作之外，我也习惯一个人安静恢复精力。处理家庭问题，我先想未来的不同可能。和朋友商量时，我通常先考虑彼此的感受。周末安排，我经常临时决定。')


def evidence(message, quote=None):
    return {'message_id': message.id, 'quote': quote or message.content}


def axis_data(axis='EI', leaning='I', evidence_items=None, counter_items=None, explanation='这些日常例子中出现了相似偏好。'):
    return {
        'axis': axis,
        'leaning': leaning,
        'evidence': evidence_items if evidence_items is not None else [evidence(FIRST), evidence(SECOND)],
        'counter_evidence': counter_items or [],
        'explanation': explanation,
        'coverage': 'supported',
    }


def output(*axes):
    by_axis = {axis['axis']: axis for axis in axes}
    return {'axes': [by_axis.get(name, {
        'axis': name, 'leaning': 'unknown', 'evidence': [], 'counter_evidence': [],
        'explanation': '尚无足够的日常例子。', 'coverage': 'none',
    }) for name in ('EI', 'SN', 'TF', 'JP')]}


class RecordingGateway(DeepSeekGateway):
    def __init__(self, responses, mode='live'):
        self.responses = iter(responses)
        self.requests = []
        self.budgets = []
        self.mode = mode

        def respond(request):
            self.requests.append(json.loads(request.content))
            response = next(self.responses)
            if isinstance(response, Exception):
                raise response
            if isinstance(response, int):
                return httpx.Response(response, json={'private': 'SECRET_PROVIDER_BODY'})
            text = response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)
            return httpx.Response(200, json={
                'choices': [{'message': {'content': text}, 'finish_reason': 'stop'}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 10},
            })

        super().__init__('test-only-placeholder', client=httpx.Client(transport=httpx.MockTransport(respond)))

    def generate(self, messages, instructions, schema, budget):
        self.budgets.append(budget)
        return super().generate(messages, instructions, schema, budget)


def analyze(messages, gateway):
    from support_agent.personality import analyze_personality
    return analyze_personality(messages, gateway)


def test_supported_axes_produce_ordered_partial_type_hint():
    gateway = RecordingGateway([output(axis_data(), axis_data('TF', 'F'))])
    result = analyze([FIRST, SECOND], gateway)
    assert result.status == 'ok'
    assert [axis.axis for axis in result.axes] == ['EI', 'SN', 'TF', 'JP']
    assert result.type_hint == 'I?F?'
    assert result.axes[0].coverage == 'supported'
    assert result.message_count == 2
    assert result.error_code is None


def test_full_type_is_derived_only_from_four_supported_axes():
    gateway = RecordingGateway([output(*(axis_data(name, pole) for name, pole in [('EI', 'I'), ('SN', 'N'), ('TF', 'F'), ('JP', 'P')]))])
    result = analyze([FIRST, SECOND], gateway)
    assert result.type_hint == 'INFP'


def test_payload_contains_only_serialized_user_ids_and_content():
    assistant = Message(id='a1', role='assistant', content='ASSISTANT_SECRET_TEXT')
    gateway = RecordingGateway([output(axis_data())])
    analyze([FIRST, assistant, SECOND], gateway)
    sent = gateway.requests[0]['messages']
    assert len(sent) == 2
    assert sent[1]['role'] == 'user'
    assert json.loads(sent[1]['content']) == [
        {'id': 'u1', 'content': FIRST.content}, {'id': 'u2', 'content': SECOND.content},
    ]
    assert 'ASSISTANT_SECRET_TEXT' not in json.dumps(gateway.requests, ensure_ascii=False)
    assert gateway.budgets[0].limit == 2
    assert gateway.budgets[0].deadline_seconds == 40


def test_fingerprint_ignores_assistant_and_changes_for_user_edits():
    from support_agent.personality import user_fingerprint
    assistant = Message(id='a1', role='assistant', content='回复')
    fingerprint = user_fingerprint([FIRST, SECOND])
    assert len(fingerprint) == 64
    assert user_fingerprint([FIRST, assistant, SECOND]) == fingerprint
    assert user_fingerprint([FIRST, SECOND.model_copy(update={'content': '改变了'})]) != fingerprint
    assert user_fingerprint([SECOND, FIRST]) != fingerprint
    assert analyze([FIRST, SECOND], RecordingGateway([output()])).fingerprint == fingerprint


@pytest.mark.parametrize('messages,mode,want_status,want_error', [
    ([], 'live', 'insufficient', None),
    ([Message(role='assistant', content='只有助手')], 'live', 'insufficient', None),
    ([Message(role='user', content='   ')], 'live', 'insufficient', None),
    ([FIRST, SECOND], 'mock', 'insufficient', None),
    ([Message(role='user', content='字' * 16001)], 'live', 'failed', 'context_limit'),
])
def test_unusable_or_offline_input_never_calls_model(messages, mode, want_status, want_error):
    gateway = RecordingGateway([], mode=mode)
    result = analyze(messages, gateway)
    assert result.status == want_status
    assert result.error_code == want_error
    assert result.type_hint == '????'
    assert not gateway.requests
    assert not gateway.budgets


def test_exact_input_character_limit_is_accepted():
    message = Message(id='limit', role='user', content='字' * 16000)
    gateway = RecordingGateway([output()])
    assert analyze([message], gateway).status == 'insufficient'
    assert len(gateway.requests) == 1


def test_a_single_supporting_message_cannot_establish_a_preference():
    axis = axis_data(evidence_items=[evidence(FIRST), evidence(FIRST, '我平时在聚会后喜欢独处。')])
    result = analyze([FIRST, SECOND], RecordingGateway([output(axis)]))
    assert result.status == 'insufficient'
    assert result.axes[0].leaning == 'unknown'
    assert result.axes[0].coverage == 'limited'
    assert result.type_hint == '????'


def test_claimed_coverage_without_evidence_is_removed():
    result = analyze([FIRST, SECOND], RecordingGateway([output(axis_data(evidence_items=[]))]))
    assert result.axes[0].leaning == 'unknown'
    assert result.axes[0].coverage == 'none'


def test_counterevidence_takes_precedence_and_is_retained():
    other = Message(id='u3', role='user', content='但在熟悉的小组里，我平时会主动组织大家一起活动，也从中恢复精力。')
    axis = axis_data(evidence_items=[evidence(FIRST)], counter_items=[evidence(other)])
    result = analyze([FIRST, SECOND, other], RecordingGateway([output(axis)]))
    assert result.axes[0].leaning == 'mixed'
    assert result.axes[0].coverage == 'conflicting'
    assert result.axes[0].counter_evidence[0].quote == other.content
    assert result.type_hint == '????'


@pytest.mark.parametrize('type_text', ['我是INFP', '我是 infp。', '测出来是 ENFJ-T。'])
def test_self_declared_type_labels_do_not_support_axes(type_text):
    label = Message(id='label', role='user', content=type_text)
    axis = axis_data(evidence_items=[evidence(label), evidence(FIRST)])
    result = analyze([label, FIRST], RecordingGateway([output(axis)]))
    assert result.axes[0].leaning == 'unknown'
    assert result.axes[0].coverage == 'limited'
    assert [item.message_id for item in result.axes[0].evidence] == ['u1']


@pytest.mark.parametrize('bad_evidence', [
    {'message_id': 'assistant', 'quote': '助手说你内向'},
    {'message_id': 'u1', 'quote': '虚构的用户原话'},
    {'message_id': 'missing', 'quote': FIRST.content},
    {'message_id': 'u1', 'quote': ' '},
])
def test_invalid_evidence_fails_closed_after_one_repair(bad_evidence):
    assistant = Message(id='assistant', role='assistant', content='助手说你内向')
    invalid = output(axis_data(evidence_items=[bad_evidence, evidence(SECOND)]))
    gateway = RecordingGateway([invalid, invalid])
    result = analyze([FIRST, assistant, SECOND], gateway)
    assert result.status == 'failed'
    assert result.error_code == 'invalid_response'
    assert result.type_hint == '????'
    assert len(gateway.requests) == 2


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'foreign_axis', 'wrong_pole', 'extra_axis'])
def test_axis_structure_is_strictly_validated(mutation):
    invalid = output(axis_data())
    if mutation == 'missing':
        invalid['axes'].pop()
    elif mutation == 'duplicate':
        invalid['axes'][1] = invalid['axes'][0]
    elif mutation == 'foreign_axis':
        invalid['axes'][1]['axis'] = 'XX'
    elif mutation == 'wrong_pole':
        invalid['axes'][0]['leaning'] = 'F'
    else:
        invalid['axes'].append(axis_data())
    result = analyze([FIRST, SECOND], RecordingGateway([invalid, invalid]))
    assert result.status == 'failed'
    assert result.error_code == 'invalid_response'


def test_axis_order_is_normalized():
    candidate = output(axis_data())
    candidate['axes'].reverse()
    result = analyze([FIRST, SECOND], RecordingGateway([candidate]))
    assert [item.axis for item in result.axes] == ['EI', 'SN', 'TF', 'JP']
    assert result.type_hint == 'I???'


def test_invalid_json_gets_only_one_repair_with_same_budget():
    gateway = RecordingGateway(['broken json', output(axis_data())])
    result = analyze([FIRST, SECOND], gateway)
    assert result.status == 'ok'
    assert len(gateway.requests) == 2
    assert gateway.budgets[0] is gateway.budgets[1]
    assert gateway.budgets[0].attempts == 2
    assert 'broken json' not in json.dumps(gateway.requests[1], ensure_ascii=False)


def test_repeated_invalid_json_returns_finite_error():
    gateway = RecordingGateway(['broken', 'still broken'])
    result = analyze([FIRST, SECOND], gateway)
    assert result.status == 'failed'
    assert result.error_code == 'invalid_response'
    assert len(gateway.requests) == 2


@pytest.mark.parametrize('response,want_error', [
    (401, 'auth'), (402, 'balance'), (413, 'context_limit'), (429, 'rate_limit'),
    (500, 'unavailable'), (httpx.TimeoutException('SECRET_TIMEOUT_TEXT'), 'timeout'),
    (ModelCallError('SECRET_UNKNOWN_ERROR'), 'unavailable'),
])
def test_provider_errors_are_safe_and_are_not_retried(response, want_error, capsys):
    gateway = RecordingGateway([response])
    result = analyze([FIRST, SECOND], gateway)
    assert result.status == 'failed'
    assert result.error_code == want_error
    assert result.type_hint == '????'
    assert len(gateway.requests) == 1
    assert 'SECRET' not in result.model_dump_json()
    captured = capsys.readouterr()
    assert 'SECRET' not in captured.out + captured.err


@pytest.mark.parametrize('explanation', [
    '你患有抑郁症，所以更内向。',
    '这说明存在 bipolar disorder，应考虑 medication。',
    '建议服用舍曲林治疗，你有焦虑障碍。',
    '你的内向概率为80%。这是官方MBTI测试结果。',
])
def test_unsafe_or_overconfident_explanations_are_replaced(explanation):
    result = analyze([FIRST, SECOND], RecordingGateway([output(axis_data(explanation=explanation))]))
    assert result.axes[0].leaning == 'I'
    assert result.axes[0].explanation != explanation
    assert '%' not in result.axes[0].explanation
    assert '抑郁症' not in result.axes[0].explanation


def test_duplicate_user_ids_fail_before_network():
    duplicate = FIRST.model_copy(update={'content': '另一条不同内容'})
    gateway = RecordingGateway([])
    result = analyze([FIRST, duplicate], gateway)
    assert result.status == 'failed'
    assert result.error_code == 'invalid_input'
    assert not gateway.requests


@pytest.mark.parametrize('explanation', [
    '你的高血压是因为你属于内向型。',
    '你需要每天20mg escitalopram。',
])
def test_medical_claims_cannot_bypass_explanation_sanitizing(explanation):
    result = analyze([FIRST, SECOND], RecordingGateway([output(axis_data(explanation=explanation))]))
    assert result.axes[0].leaning == 'I'
    assert result.axes[0].explanation != explanation


def test_model_authored_mixed_without_counterevidence_stays_unknown():
    result = analyze([FIRST, SECOND], RecordingGateway([output(axis_data(leaning='mixed'))]))
    assert result.status == 'insufficient'
    assert result.axes[0].leaning == 'unknown'
    assert result.axes[0].coverage == 'limited'


def test_invalid_counterevidence_is_also_rejected():
    invalid = output(axis_data(counter_items=[{'message_id': 'u1', 'quote': '未曾说过的反例'}]))
    result = analyze([FIRST, SECOND], RecordingGateway([invalid, invalid]))
    assert result.status == 'failed'
    assert result.error_code == 'invalid_response'


def test_self_label_letters_cannot_be_reassembled_into_supported_type():
    first = Message(id='label1', role='user', content='我是INFP')
    second = Message(id='label2', role='user', content='测出来是INFP')
    candidate = output(*(axis_data(name, pole, evidence_items=[evidence(first, pole), evidence(second, pole)])
                         for name, pole in [('EI', 'I'), ('SN', 'N'), ('TF', 'F'), ('JP', 'P')]))
    result = analyze([first, second], RecordingGateway([candidate]))
    assert result.status == 'insufficient'
    assert result.type_hint == '????'
    assert all(axis.coverage == 'none' and not axis.evidence for axis in result.axes)


def test_partial_quote_overlapping_type_code_is_not_behavioral_evidence():
    first = Message(id='label1', role='user', content='我以前测出来是INFP。')
    second = Message(id='label2', role='user', content='我以前测出来是INFP，有点好奇。')
    fragment = '我以前测出来是IN'
    candidate = output(axis_data(evidence_items=[evidence(first, fragment), evidence(second, fragment)]))
    result = analyze([first, second], RecordingGateway([candidate]))
    assert result.status == 'insufficient'
    assert result.axes[0].coverage == 'none'


@pytest.mark.parametrize('fragment', ['我', '独处'])
def test_tiny_literal_fragments_do_not_count_as_behavioral_examples(fragment):
    second = Message(id='other', role='user', content='我平时独处时可以安静地恢复精力。')
    candidate = output(axis_data(evidence_items=[evidence(FIRST, fragment), evidence(second, fragment)]))
    result = analyze([FIRST, second], RecordingGateway([candidate]))
    assert result.status == 'insufficient'
    assert result.axes[0].coverage == 'none'


def test_behavioral_quotes_remain_usable_when_source_also_mentions_a_type():
    first_quote = '我平时在聚会后喜欢独处。'
    second_quote = '我在周末也习惯一个人安静恢复精力。'
    first = Message(id='mixed1', role='user', content='网上测过INFP，但想再探索一下。' + first_quote)
    second = Message(id='mixed2', role='user', content=second_quote + '朋友说我像INFP。')
    candidate = output(axis_data(evidence_items=[evidence(first, first_quote), evidence(second, second_quote)]))
    result = analyze([first, second], RecordingGateway([candidate]))
    assert result.status == 'ok'
    assert result.type_hint == 'I???'
    assert [item.quote for item in result.axes[0].evidence] == [first_quote, second_quote]


def test_tiny_type_fragment_cannot_create_counterevidence():
    label = Message(id='label', role='user', content='我是INFP')
    candidate = output(axis_data(counter_items=[evidence(label, 'I')]))
    result = analyze([FIRST, SECOND, label], RecordingGateway([candidate]))
    assert result.axes[0].leaning == 'I'
    assert result.axes[0].coverage == 'supported'
    assert not result.axes[0].counter_evidence
