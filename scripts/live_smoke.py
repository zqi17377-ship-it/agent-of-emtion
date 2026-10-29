"""One fixed synthetic-case live check. Never prints configuration or keys."""
import json
from pathlib import Path
from time import monotonic
from uuid import uuid4
from support_agent.config import ROOT
from support_agent.model_client import make_gateway
from support_agent.schemas import EligibilityContext, ModelCallError
from support_agent.session import new_session
from support_agent.workflow import run_turn

SYNTHETIC_TEXT='我是一名成年人。这是虚构研究案例：最近工作任务多，想先有人听我说，不需要建议。'
SAFE_CODES={'auth','balance','timeout','unavailable','rate_limit','context_limit','invalid_response','budget','deadline','missing_key','invalid_endpoint'}


class StageRecorder:
    def __init__(self,gateway):
        self.gateway=gateway
        self.mode,self.model_id=gateway.mode,gateway.model_id
        self.stages=[]

    def generate(self,messages,instructions,schema,budget):
        stage='assessment' if schema and schema.get('title')=='Assessment' else 'check' if schema else 'response'
        started=monotonic()
        try:
            result=self.gateway.generate(messages,instructions,schema,budget)
            self.stages.append({'stage':stage,'status':'ok','elapsed_ms':int((monotonic()-started)*1000)})
            return result
        except ModelCallError as error:
            code=str(error) if str(error) in SAFE_CODES else 'request_failed'
            self.stages.append({'stage':stage,'status':'error','error_code':code,'elapsed_ms':int((monotonic()-started)*1000)})
            raise


def run_smoke(gateway,output_dir:Path):
    recorder=StageRecorder(gateway)
    session=new_session()
    session.eligibility=EligibilityContext(adult_status='confirmed')
    result=run_turn(session,SYNTHETIC_TEXT,recorder)
    passed={s['stage'] for s in recorder.stages if s['status']=='ok'}
    report={'gateway_mode':gateway.mode,'synthetic':True,'success':gateway.mode=='live' and result.status=='ok' and passed=={'assessment','response','check'},'stages':recorder.stages,'result':result.model_dump(),'professional_review':'pending','scope':'One fixed synthetic case verifies connectivity and workflow only, not clinical quality.'}
    output_dir.mkdir(parents=True,exist_ok=True)
    path=output_dir/f'smoke-{uuid4().hex[:8]}.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    report['report_path']=str(path)
    return report


def main():
    gateway=None
    try:
        gateway=make_gateway(live=True)
        report=run_smoke(gateway,ROOT/'reports/live')
        print(json.dumps(report,ensure_ascii=False))
        return 0 if report['success'] else 1
    except ModelCallError as error:
        print(json.dumps({'configuration_ready':False,'error_code':str(error) if str(error) in SAFE_CODES else 'configuration_error'}))
        return 2
    except Exception as error:
        # Do not expose configuration values via a traceback/error body.
        print(json.dumps({'success':False,'error_code':'local_configuration_error','exception_type':type(error).__name__}))
        return 2
    finally:
        if gateway is not None and hasattr(gateway,'close'): gateway.close()


if __name__=='__main__': raise SystemExit(main())
