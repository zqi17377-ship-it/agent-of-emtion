import os
from dataclasses import dataclass
from pathlib import Path

from .schemas import ModelCallError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS = {
    'LLM_API_KEY': '',
    'LLM_BASE_URL': 'https://api.deepseek.com',
    'LLM_MODEL': 'deepseek-flash',
}


@dataclass(frozen=True)
class ConfigurationReadiness:
    ready: bool
    key_present: bool
    endpoint_valid: bool
    error_code: str | None


def load_local_env(path: Path | None = None) -> dict[str, str]:
    """Read local values literally without changing the process environment."""
    path = path if path is not None else ROOT / '.env'
    try:
        content = path.read_text(encoding='utf-8-sig')
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError):
        raise ModelCallError('config_unreadable') from None
    settings = {}
    for line in content.splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key, value = key.strip(), value.strip()
            if key in DEFAULT_SETTINGS:
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                settings[key] = value
    return settings


def load_configuration() -> dict[str, str]:
    """Resolve a fresh snapshot: explicit environment, local file, defaults."""
    settings = {**DEFAULT_SETTINGS, **load_local_env()}
    for key in DEFAULT_SETTINGS:
        if key in os.environ:
            settings[key] = os.environ[key]
    return settings


def configuration_readiness() -> ConfigurationReadiness:
    """Return safe readiness state without retaining credentials or endpoints."""
    try:
        settings = load_configuration()
    except ModelCallError:
        return ConfigurationReadiness(False, False, False, 'config_unreadable')
    key_present = bool(settings['LLM_API_KEY'].strip())
    endpoint_valid = settings['LLM_BASE_URL'].rstrip('/') in (
        'https://api.deepseek.com', 'https://api.deepseek.com/v1',
    )
    error_code = 'missing_key' if not key_present else 'invalid_endpoint' if not endpoint_valid else None
    return ConfigurationReadiness(error_code is None, key_present, endpoint_valid, error_code)
