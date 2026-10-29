import logging

_allowed = {'model_id','input_tokens','output_tokens','elapsed_ms','action','status','error_code','run_id','attempts'}
_events = {'turn','model_error','session_clear'}


def record_event(event_type, metrics):
    if event_type not in _events or not set(metrics) <= _allowed:
        raise ValueError('invalid_metric')
    if any(not (v is None or isinstance(v,(str,int,float))) for v in metrics.values()):
        raise ValueError('invalid_metric')
    # Values such as model_id/error_code can come from untrusted systems: log no values.
    logging.getLogger('support_agent').info('%s fields=%s',event_type,','.join(sorted(metrics)))
