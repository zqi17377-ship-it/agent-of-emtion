"""Monitor refreshes outside status after a job starts, without provider calls."""

from inspect import unwrap
from types import SimpleNamespace

import pytest


class AppRerun(Exception):
    """Stop execution like Streamlit's app rerun without starting a runtime."""


def monitor_context(monkeypatch):
    import support_agent.observation_ui as ui

    state = SimpleNamespace(pending_job=None)
    conversation = SimpleNamespace(
        id='synthetic-monitor-conversation', gateway_mode='live',
        state=SimpleNamespace(messages=[], previous_decision=None),
        exploration=SimpleNamespace(observation=state),
    )
    monkeypatch.setattr(ui.st, 'session_state', {
        'workspace': SimpleNamespace(active=conversation),
        'workspace_view': 'chat',
        'research_confirmed': True,
        'api_consent': True,
    })
    snapshot = object()
    monkeypatch.setattr(ui, 'get_session_settings', lambda: snapshot)
    monkeypatch.setattr(ui, 'make_gateway', lambda **_: pytest.fail('No provider call'))
    reruns = []

    def rerun(*, scope):
        reruns.append(scope)
        raise AppRerun

    monkeypatch.setattr(ui.st, 'rerun', rerun)
    readiness = SimpleNamespace(ready=True)
    return ui, state, readiness, reruns


def test_started_automatic_job_refreshes_external_status_once(monkeypatch):
    ui, state, readiness, reruns = monitor_context(monkeypatch)
    monkeypatch.setattr(ui, 'poll_observation', lambda *a, **k: False)
    starts = []

    def start(current, messages, conversation_id, gateway_factory, **options):
        assert options == {
            'manual': False, 'authorized': True, 'live': True, 'paused': False,
        }
        if current.pending_job is not None:
            return False
        current.pending_job = object()
        starts.append(conversation_id)
        return True

    monkeypatch.setattr(ui, 'start_observation', start)
    monitor = unwrap(ui.render_observation_monitor)

    with pytest.raises(AppRerun):
        monitor(readiness)
    assert reruns == ['app']
    assert state.pending_job is not None

    # A still-running job is rejected by the scheduler. The monitor must not
    # request another app rerun just because a pending job already exists.
    monitor(readiness)
    assert starts == ['synthetic-monitor-conversation']
    assert reruns == ['app']


def test_completed_poll_keeps_existing_app_refresh_before_starting_more_work(monkeypatch):
    ui, state, readiness, reruns = monitor_context(monkeypatch)
    state.pending_job = object()

    def completed(current, *args, **kwargs):
        current.pending_job = None
        return True

    monkeypatch.setattr(ui, 'poll_observation', completed)
    monkeypatch.setattr(
        ui, 'start_observation',
        lambda *a, **k: pytest.fail('Completion must refresh the app first'),
    )

    with pytest.raises(AppRerun):
        unwrap(ui.render_observation_monitor)(readiness)
    assert state.pending_job is None
    assert reruns == ['app']
