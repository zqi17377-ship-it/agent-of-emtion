from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from support_agent.observation_scheduler import ObservationState, snapshot_fingerprint
from support_agent.schemas import Message


def messages(count, size=50):
    """Each distinct user message has exactly size non-whitespace characters."""
    return [
        Message(id=str(i), role='user', content=f'{i:03d}' + '甲' * (size - 3))
        for i in range(count)
    ]


def progress(state, items, **overrides):
    from support_agent.observation_progress import observation_progress

    settings = dict(authorized=True, live=True, paused=False)
    settings.update(overrides)
    return observation_progress(state, items, **settings)


@pytest.mark.parametrize('count,fraction,reason', [
    (0, 0.0, 'insufficient'),
    (1, 0.5, 'insufficient'),
    (2, 1.0, None),
    (3, 1.0, None),
])
def test_manual_progress_reaches_content_threshold_at_two_candidates(count, fraction, reason):
    state = ObservationState(mode='manual', domains=('mbti',))

    result = progress(state, messages(count))

    assert result.fraction == fraction
    assert result.reason == reason
    assert result.candidate_count == count
    assert result.candidate_chars == count * 50
    assert str(count) in result.detail
    assert result.title


@pytest.mark.parametrize('count,size,fraction,reason,chars', [
    (0, 50, 0.0, 'insufficient', 0),
    (10, 50, 0.5, 'insufficient', 500),
    (19, 60, 0.95, 'insufficient', 1140),
    (20, 49, 0.98, 'insufficient', 980),
    (20, 50, 1.0, None, 1000),
    (25, 60, 1.0, None, 1500),
])
def test_first_automatic_progress_requires_both_twenty_messages_and_thousand_chars(
    count, size, fraction, reason, chars,
):
    state = ObservationState(mode='auto', domains=('mbti',))

    result = progress(state, messages(count, size))

    assert result.fraction == fraction
    assert result.reason == reason
    assert result.candidate_count == count
    assert result.candidate_chars == chars
    assert '20' in result.detail and '1000' in result.detail
    assert str(count) in result.detail and str(chars) in result.detail


def test_candidate_progress_excludes_assistant_short_duplicate_and_whitespace():
    state = ObservationState(mode='manual', domains=('mbti',))
    text = '今天我在工作中有些难以说清楚的感受'
    items = [
        Message(role='user', content=text),
        Message(role='user', content=' \n'.join(text)),
        Message(role='assistant', content='回复' * 100),
        Message(role='user', content='嗯嗯'),
        Message(role='user', content='😀' * 100),
    ]

    result = progress(state, items)

    assert result.candidate_count == 1
    assert result.candidate_chars == 17
    assert result.fraction == 0.5
    assert '重复' in result.detail and '短' in result.detail
    assert text not in result.detail


@pytest.mark.parametrize('count,fraction,reason,new_count', [
    (18, 0.0, 'insufficient_new', 0),
    (20, 0.0, 'insufficient_new', 0),
    (29, 0.9, 'insufficient_new', 9),
    (30, 1.0, None, 10),
    (40, 1.0, None, 20),
])
def test_next_automatic_progress_uses_ten_new_candidates_since_last_trigger(
    count, fraction, reason, new_count,
):
    state = ObservationState(
        mode='auto', domains=('mbti',), automatic_count=1, last_auto_candidate_count=20,
    )

    result = progress(state, messages(count))

    assert result.fraction == fraction
    assert result.reason == reason
    assert '10' in result.detail and str(new_count) in result.detail
    assert '新增' in result.detail


def test_new_conversation_uses_first_threshold_with_retained_automatic_spend():
    state = ObservationState(
        mode='auto', domains=('mbti',), automatic_count=1, last_auto_candidate_count=0,
    )

    result = progress(state, messages(10))

    assert result.reason == 'insufficient'
    assert result.fraction == 0.5
    assert '20' in result.detail and '1000' in result.detail


@pytest.mark.parametrize('mode,domains,authorized,live,paused,pending,spent,reserved,attempted,automatic,reason', [
    ('off', (), False, False, True, True, 6, 0, True, 3, 'off'),
    ('auto', (), False, False, True, True, 6, 0, True, 3, 'no_domains'),
    ('auto', ('mbti',), False, False, True, True, 6, 0, True, 3, 'unauthorized'),
    ('auto', ('mbti',), True, False, True, True, 6, 0, True, 3, 'offline'),
    ('auto', ('mbti',), True, True, True, True, 6, 0, True, 3, 'paused'),
    ('auto', ('mbti',), True, True, False, True, 6, 0, True, 3, 'pending'),
    ('auto', ('mbti',), True, True, False, False, 4, 2, True, 3, 'budget'),
    ('auto', ('mbti',), True, True, False, False, 0, 0, True, 3, 'unchanged'),
    ('auto', ('mbti',), True, True, False, False, 0, 0, False, 3, 'auto_limit'),
])
def test_blocked_status_follows_scheduler_priority_and_hides_fraction(
    mode, domains, authorized, live, paused, pending, spent, reserved, attempted, automatic, reason,
):
    state = ObservationState(mode=mode, domains=domains, automatic_count=automatic)
    state.pending_job = object() if pending else None
    state.ledger.spent, state.ledger.reserved = spent, reserved
    items = messages(20)
    if attempted:
        state.attempted_fingerprints.add(snapshot_fingerprint(state, items))

    result = progress(state, items, authorized=authorized, live=live, paused=paused)

    assert result.reason == reason
    assert result.fraction is None
    assert result.candidate_count == 20
    assert result.candidate_chars == 1000
    assert result.title and result.detail
    assert '20' in result.detail and '1000' in result.detail


def test_manual_content_progress_is_available_after_automatic_limit():
    state = ObservationState(mode='manual', domains=('mbti',), automatic_count=3)

    result = progress(state, messages(2))

    assert result.reason is None
    assert result.fraction == 1.0


def test_rendering_progress_is_read_only_and_result_is_immutable():
    state = ObservationState(
        mode='auto', domains=('mbti',), automatic_count=1, last_auto_candidate_count=20,
        relations={'r1': 'partner'}, message_relations={'0': 'r1'}, excluded_keys={'deleted'},
    )
    state.ledger.spent, state.ledger.reserved = 1, 2
    items = messages(29)
    before_state = {
        key: deepcopy(value) for key, value in vars(state).items() if key not in ('ledger', 'lock')
    }
    before_ledger = (state.ledger.spent, state.ledger.reserved, state.ledger.input_tokens, state.ledger.output_tokens)
    before_messages = deepcopy(items)

    first = progress(state, items)
    second = progress(state, items)

    assert first == second
    assert {key: value for key, value in vars(state).items() if key not in ('ledger', 'lock')} == before_state
    assert (state.ledger.spent, state.ledger.reserved, state.ledger.input_tokens, state.ledger.output_tokens) == before_ledger
    assert items == before_messages
    with pytest.raises(FrozenInstanceError):
        first.fraction = 1.0
