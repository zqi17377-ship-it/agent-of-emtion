import os
from dataclasses import FrozenInstanceError, asdict

import pytest

from support_agent import config
from support_agent.model_client import FakeGateway, make_gateway
from support_agent.schemas import ModelCallError


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    for key in ('LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(config, 'ROOT', tmp_path)


def test_live_gateway_picks_up_edits_to_local_config(tmp_path, monkeypatch):
    local_env = tmp_path / '.env'
    local_env.write_text('LLM_API_KEY=synthetic-first\nLLM_MODEL=first-model\n', encoding='utf-8')
    first = make_gateway(live=True)
    local_env.write_text('LLM_API_KEY=synthetic-second\nLLM_MODEL=second-model\n', encoding='utf-8')
    second = make_gateway(live=True)

    assert first.api_key == 'synthetic-first'
    assert second.api_key == 'synthetic-second'
    assert second.model_id == 'second-model'


def test_loading_local_config_never_changes_process_environment(tmp_path):
    local_env = tmp_path / '.env'
    local_env.write_text('LLM_API_KEY=synthetic-local\nLLM_MODEL=local-model\n', encoding='utf-8')

    make_gateway(live=True)

    key_was_exported = 'LLM_API_KEY' in os.environ
    model_was_exported = 'LLM_MODEL' in os.environ
    assert key_was_exported is False
    assert model_was_exported is False


def test_explicit_process_settings_override_local_settings(tmp_path, monkeypatch):
    (tmp_path / '.env').write_text(
        'LLM_API_KEY=synthetic-local\nLLM_MODEL=local-model\nLLM_BASE_URL=https://invalid.example\n',
        encoding='utf-8',
    )
    monkeypatch.setenv('LLM_API_KEY', 'synthetic-process')
    monkeypatch.setenv('LLM_BASE_URL', 'https://api.deepseek.com/v1')

    gateway = make_gateway(live=True)

    assert gateway.api_key == 'synthetic-process'
    assert gateway.model_id == 'local-model'
    assert gateway.url == 'https://api.deepseek.com/v1/chat/completions'


def test_empty_process_key_overrides_local_key(tmp_path, monkeypatch):
    (tmp_path / '.env').write_text('LLM_API_KEY=synthetic-local\n', encoding='utf-8')
    monkeypatch.setenv('LLM_API_KEY', '')

    with pytest.raises(ModelCallError, match='missing_key'):
        make_gateway(live=True)


def test_local_reader_keeps_values_literal_and_ignores_unrelated_settings(tmp_path):
    local_env = tmp_path / '.env'
    local_env.write_text(
        '\ufeff# local settings\nLLM_API_KEY="synthetic-${NO_EXPANSION}=literal"\n'
        "LLM_MODEL='local-model'\nUNRELATED_SETTING=ignored\n",
        encoding='utf-8',
    )

    assert config.load_local_env(local_env) == {
        'LLM_API_KEY': 'synthetic-${NO_EXPANSION}=literal',
        'LLM_MODEL': 'local-model',
    }


def test_readiness_refreshes_after_a_missing_key_is_filled_in(tmp_path):
    local_env = tmp_path / '.env'
    local_env.write_text('LLM_API_KEY=\n', encoding='utf-8')
    assert config.configuration_readiness().error_code == 'missing_key'
    local_env.write_text('LLM_API_KEY=synthetic-added\n', encoding='utf-8')

    assert asdict(config.configuration_readiness()) == {
        'ready': True,
        'key_present': True,
        'endpoint_valid': True,
        'error_code': None,
    }


def test_readiness_is_immutable_and_contains_no_credentials(tmp_path):
    (tmp_path / '.env').write_text('LLM_API_KEY=synthetic-private-value\n', encoding='utf-8')

    status = config.configuration_readiness()

    assert 'synthetic-private-value' not in repr(status)
    assert set(asdict(status)) == {'ready', 'key_present', 'endpoint_valid', 'error_code'}
    with pytest.raises(FrozenInstanceError):
        status.ready = False


def test_deleting_local_config_removes_previously_loaded_credentials(tmp_path):
    local_env = tmp_path / '.env'
    local_env.write_text('LLM_API_KEY=synthetic-removed\n', encoding='utf-8')
    assert config.configuration_readiness().ready is True
    local_env.unlink()

    assert config.configuration_readiness().error_code == 'missing_key'
    with pytest.raises(ModelCallError, match='missing_key'):
        make_gateway(live=True)


@pytest.mark.parametrize('endpoint, valid', [
    ('https://api.deepseek.com', True),
    ('https://api.deepseek.com/v1/', True),
    ('http://api.deepseek.com', False),
    ('https://api.deepseek.com.example', False),
    ('https://api.deepseek.com/path', False),
    ('https://api.deepseek.com?redirect=other', False),
])
def test_readiness_matches_gateway_endpoint_validation(tmp_path, endpoint, valid):
    (tmp_path / '.env').write_text(
        f'LLM_API_KEY=synthetic-key\nLLM_BASE_URL={endpoint}\n', encoding='utf-8',
    )

    status = config.configuration_readiness()

    assert status.ready is valid
    assert status.endpoint_valid is valid
    assert status.key_present is True
    assert status.error_code == (None if valid else 'invalid_endpoint')
    if valid:
        assert make_gateway(live=True).mode == 'live'
    else:
        with pytest.raises(ModelCallError, match='invalid_endpoint'):
            make_gateway(live=True)


def test_readiness_returns_only_safe_state_when_config_is_unreadable(tmp_path):
    (tmp_path / '.env').write_bytes(b'LLM_API_KEY=\xff\xfe')

    assert asdict(config.configuration_readiness()) == {
        'ready': False,
        'key_present': False,
        'endpoint_valid': False,
        'error_code': 'config_unreadable',
    }
    with pytest.raises(ModelCallError, match='config_unreadable'):
        make_gateway(live=True)


def test_offline_gateway_does_not_require_readable_config(tmp_path):
    (tmp_path / '.env').write_bytes(b'LLM_API_KEY=\xff\xfe')

    assert isinstance(make_gateway(live=False), FakeGateway)
