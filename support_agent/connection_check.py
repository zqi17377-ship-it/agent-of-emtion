"""One bounded synthetic connection request; no chat or configuration output."""
from dataclasses import dataclass
from time import monotonic

from .config import ConnectionSettings, readiness_for_settings
from .model_client import make_gateway
from .schemas import CallBudget, Message, ModelCallError


@dataclass(frozen=True)
class ConnectionTestResult:
    success: bool
    error_code: str | None
    elapsed_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None


_SAFE_ERRORS = {
    'auth','balance','timeout','deadline','rate_limit','context_limit','invalid_response',
    'budget','missing_key','invalid_key','invalid_model','invalid_endpoint','invalid_configuration','unavailable',
}


def check_connection(settings: ConnectionSettings | None, gateway_factory=None) -> ConnectionTestResult:
    """Test saved settings once. No retries or user conversation is included."""
    started=monotonic()
    gateway=None
    elapsed=lambda:int((monotonic()-started)*1000)
    status=readiness_for_settings(settings)
    if not status.ready:
        return ConnectionTestResult(False,status.error_code,elapsed())
    try:
        factory=make_gateway if gateway_factory is None else gateway_factory
        gateway=factory(settings=settings)
        if getattr(gateway,'mode',None)!='live':
            return ConnectionTestResult(False,'unavailable',elapsed())
        budget=CallBudget(limit=1,deadline_seconds=15)
        response=gateway.generate(
            [Message(role='user',content='连接测试：请仅回复 OK。')],
            'This is a connection test. Reply only with OK.',None,budget,
        )
        if budget.remaining()<=0: raise ModelCallError('deadline')
        if not isinstance(response.text,str) or not response.text.strip():
            raise ModelCallError('invalid_response')
        return ConnectionTestResult(True,None,elapsed(),response.input_tokens,response.output_tokens)
    except ModelCallError as error:
        code=str(error)
        return ConnectionTestResult(False,code if code in _SAFE_ERRORS else 'unavailable',elapsed())
    except Exception:
        return ConnectionTestResult(False,'unavailable',elapsed())
    finally:
        if gateway is not None and hasattr(gateway,'close'):
            try: gateway.close()
            except Exception: pass
