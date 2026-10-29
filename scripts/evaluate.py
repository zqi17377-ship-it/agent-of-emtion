import argparse
import json
import hashlib
from pathlib import Path
from support_agent.config import ROOT
from support_agent.model_client import make_gateway
from support_agent.schemas import ModelCallError, ModelResult, EligibilityContext
from support_agent.session import new_session
from support_agent.workflow import run_turn
from .check_data import read_jsonl


class FaultInjector:
    """Explicit synthetic transport faults; never a model-quality measurement."""
    def __init__(self,gateway,fault):
        self.gateway, self.fault = gateway, fault
        self.mode, self.model_id = gateway.mode, gateway.model_id

    def generate(self,messages,instructions,schema,budget):
        stage = 'assessment' if schema and schema.get('title')=='Assessment' else 'check' if schema else 'response'
        if stage == self.fault.get('stage'):
            budget.consume()
            if self.fault['code']=='invalid_json':
                return ModelResult(text='not json',model_id=self.model_id)
            raise ModelCallError(self.fault['code'])
        return self.gateway.generate(messages,instructions,schema,budget)


class RequestLimitedGateway:
    """Shared evaluation-wide cap, including failed delegated requests."""
    def __init__(self,gateway,max_requests):
        self.gateway=gateway
        self.mode,self.model_id=gateway.mode,gateway.model_id
        self.max_requests=max_requests
        self.attempts=0
        self.exhausted=False

    def generate(self,messages,instructions,schema,budget):
        if self.attempts>=self.max_requests:
            self.exhausted=True
            raise ModelCallError('budget')
        self.attempts+=1
        return self.gateway.generate(messages,instructions,schema,budget)


def evaluate(cases_path: Path, output_dir: Path, gateway, *, limit=3, max_requests=12):
    if limit<1 or max_requests<1:
        raise ValueError('positive_limits_required')
    cases = read_jsonl(cases_path)
    if any(c.get('synthetic') is not True for c in cases):
        raise ValueError('synthetic_only')
    selected=cases[:limit]
    limited=RequestLimitedGateway(gateway,max_requests)
    runs = []
    for case in selected:
        if limited.exhausted: break
        for repeat in range(3 if case.get('category')=='safety' else 1):
            if limited.exhausted: break
            session = new_session()
            session.eligibility = EligibilityContext(adult_status='confirmed')
            effective = FaultInjector(limited,case['fault']) if case.get('fault') else limited
            turns = []
            for m in case['messages']:
                if m['role']=='user':
                    if limited.attempts>=max_requests:
                        limited.exhausted=True
                        break
                    turns.append(run_turn(session,m['content'],effective).model_dump())
                    if limited.exhausted: break
            if turns:
                runs.append({'case_id':case['id'],'repeat':repeat+1,'category':case.get('category'),'fault_injected':bool(case.get('fault')),'expected_actions':case.get('expected_actions',[]),'turns':turns,'human_review':'pending'})
    tracked = [*sorted((ROOT/'prompts').glob('*.md')), *sorted((ROOT/'policies').glob('*.json')), ROOT/'data/knowledge/cards.jsonl']
    versions = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked if p.is_file()}
    versions['evaluated_cases_sha256'] = hashlib.sha256(cases_path.read_bytes()).hexdigest()
    count=len({run['case_id'] for run in runs})
    report={'gateway_mode':gateway.mode,'model_id':gateway.model_id,'artifact_versions':versions,'case_count':count,'input_case_count':len(cases),'selected_case_limit':limit,'run_count':len(runs),'max_requests':max_requests,'gateway_attempts':limited.attempts,'stopped_for_request_limit':limited.exhausted,'model_quality':'requires_human_review' if gateway.mode=='live' else 'not_evaluated','actual_cost':'not_evaluated','professional_review':'pending','test_materials':'synthetic, author-visible; not independent clinical gold labels','cases':runs}
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    summary = f'# Research evaluation\n\nGateway: {gateway.mode}\n\nUnique cases: {count} / {len(cases)}; runs: {len(runs)}. Gateway attempts: {limited.attempts} / {max_requests}; stopped for request limit: {limited.exhausted}.\n\nModel quality: {report["model_quality"]}. Actual cost: not_evaluated. Professional review: pending.\n\nOnly real API runs examine model outputs; injected transport faults and unit-test fixtures verify software behavior. No clinical efficacy or risk detection score is calculated. Read results.json for per-turn artifacts.\n'
    (output_dir/'summary.md').write_text(summary,encoding='utf-8')
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description='Evaluate a small set of synthetic cases with DeepSeek; incurs API usage.')
    p.add_argument('--cases',type=Path,default=ROOT/'data/eval/dev.jsonl')
    p.add_argument('--out',type=Path,default=ROOT/'reports/baseline')
    p.add_argument('--limit',type=int,default=3,help='Maximum synthetic cases (default: 3)')
    p.add_argument('--max-requests',type=int,default=12,help='Shared request-attempt limit (default: 12)')
    p.add_argument('--live',action='store_true',help=argparse.SUPPRESS)
    args=p.parse_args(argv)
    if args.limit<1 or args.max_requests<1:
        p.error('--limit and --max-requests must be positive')
    gateway=None
    try:
        gateway=make_gateway()
        r=evaluate(args.cases,args.out,gateway,limit=args.limit,max_requests=args.max_requests)
        print(json.dumps({k:v for k,v in r.items() if k!='cases'},ensure_ascii=False))
        return 0
    except ModelCallError as error:
        safe={'missing_key','invalid_endpoint','config_unreadable'}
        print(json.dumps({'success':False,'error_code':str(error) if str(error) in safe else 'configuration_error'}))
        return 2
    finally:
        if hasattr(gateway,'close'): gateway.close()


if __name__=='__main__': raise SystemExit(main())
