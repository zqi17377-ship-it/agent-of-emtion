import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .schemas import ModelCallError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS = {
    'LLM_API_KEY': '',
    'LLM_BASE_URL': 'https://api.deepseek.com',
    'LLM_MODEL': 'deepseek-flash',
}

OFFICIAL_ENDPOINTS = ('https://api.deepseek.com', 'https://api.deepseek.com/v1')


@dataclass(frozen=True)
class ConnectionSettings:
    """One explicit credential snapshot; never load or write process settings."""
    api_key: str = field(repr=False)
    model: str = 'deepseek-flash'
    base_url: str = 'https://api.deepseek.com'

    def __post_init__(self):
        if not isinstance(self.api_key,str): raise ModelCallError('invalid_key')
        key=self.api_key.strip()
        if not key: raise ModelCallError('missing_key')
        if len(key)>4096 or not key.isascii() or any(c.isspace() or ord(c)<32 or ord(c)==127 for c in key):
            raise ModelCallError('invalid_key')
        model=self.model.strip() if isinstance(self.model,str) else ''
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,99}',model):
            raise ModelCallError('invalid_model')
        endpoint=self.base_url.strip().rstrip('/') if isinstance(self.base_url,str) else ''
        if endpoint not in OFFICIAL_ENDPOINTS: raise ModelCallError('invalid_endpoint')
        object.__setattr__(self,'api_key',key)
        object.__setattr__(self,'model',model)
        object.__setattr__(self,'base_url',endpoint)


@dataclass(frozen=True)
class ConfigurationReadiness:
    ready: bool
    key_present: bool
    endpoint_valid: bool
    error_code: str | None


def readiness_for_settings(settings: ConnectionSettings | None) -> ConfigurationReadiness:
    """Inspect only an explicit snapshot; None never borrows local credentials."""
    if settings is None:
        return ConfigurationReadiness(False,False,False,'missing_key')
    if not isinstance(settings,ConnectionSettings):
        return ConfigurationReadiness(False,False,False,'invalid_configuration')
    return ConfigurationReadiness(True,True,True,None)


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
    endpoint_valid = settings['LLM_BASE_URL'].rstrip('/') in OFFICIAL_ENDPOINTS
    error_code = 'missing_key' if not key_present else 'invalid_endpoint' if not endpoint_valid else None
    return ConfigurationReadiness(error_code is None, key_present, endpoint_valid, error_code)
