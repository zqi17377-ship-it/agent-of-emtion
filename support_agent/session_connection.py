"""Per-visitor connection settings, kept only in Streamlit session memory.

Web callers never fall back to the process or local file configuration. Workers
must capture the returned immutable settings on the UI thread before dispatch.
"""
from dataclasses import is_dataclass
from uuid import uuid4
import streamlit as st

from .config import ConnectionSettings

SESSION_SETTINGS_KEY = 'connection_settings'


def get_session_settings() -> ConnectionSettings | None:
    # Streamlit can reload config while retaining an instance of its old class.
    from .config import ConnectionSettings as current_type, ModelCallError
    settings = st.session_state.get(SESSION_SETTINGS_KEY)
    if isinstance(settings, current_type):
        return settings
    old_type = type(settings)
    if not is_dataclass(settings) or (
        old_type.__module__, old_type.__qualname__
    ) != (current_type.__module__, current_type.__qualname__):
        return None
    try:
        normalized = current_type(
            api_key=settings.api_key, model=settings.model, base_url=settings.base_url,
        )
    except (AttributeError, TypeError, ModelCallError):
        return None
    # Identity migration keeps the same connection and must not revoke consent.
    st.session_state[SESSION_SETTINGS_KEY] = normalized
    return normalized


def session_readiness():
    from .config import readiness_for_settings
    return readiness_for_settings(get_session_settings())


def _invalidate_connection():
    """Stop future work with prior credentials while retaining saved records."""
    st.session_state['connection_revision'] = st.session_state.get('connection_revision', 0) + 1
    st.session_state['api_consent'] = False
    st.session_state.pop('chat_setup_api', None)
    workspace = st.session_state.get('workspace')
    if workspace is None:
        return
    for conversation in workspace.items:
        exploration = conversation.exploration
        observation = exploration.observation
        with observation.lock:
            observation.mode = 'off'
            observation.consent_revision += 1
            observation.generation = uuid4().hex
            observation.pending_job = None
            observation.error_code = None
        setup = exploration.flows.get('observation_setup')
        if setup is not None:
            page=setup.get('page')
            if page not in ('report','relations','annotations'):
                page='done' if observation.report is not None else 'setup'
            setup.update(page=page, step=0, consent=False)
        personality = exploration.flows.get('personality')
        if personality is not None:
            local_pages=('results','menu','questions','self_review','confirm','confirm_review','self_intro','confirm_intro')
            personality.update(page=personality.get('page') if personality.get('page') in local_pages else 'scope',consent=False)
        prefix = 'explore_' + conversation.id + '_observe_'
        for key in list(st.session_state):
            if isinstance(key, str) and (
                key in ('personality_' + conversation.id + '_api',
                        'personality_' + conversation.id + '_consent')
                or key.startswith(prefix) and (key.endswith('consent') or key.endswith('_api'))
            ):
                st.session_state.pop(key, None)


def save_session_settings(settings: ConnectionSettings) -> bool:
    """Save a validated snapshot; return whether the effective settings changed."""
    from .config import ConnectionSettings as current_type
    if not isinstance(settings, current_type):
        raise TypeError('invalid_settings')
    if get_session_settings() == settings:
        return False
    st.session_state[SESSION_SETTINGS_KEY] = settings
    _invalidate_connection()
    return True


def clear_session_settings() -> bool:
    """Forget this visitor's settings without restoring any server credentials."""
    present = get_session_settings() is not None
    st.session_state.pop(SESSION_SETTINGS_KEY, None)
    _invalidate_connection()
    return present
