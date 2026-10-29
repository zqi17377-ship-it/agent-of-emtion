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


def evaluate(cases_path: Path, output_dir: Path, gateway):
    cases = read_jsonl(cases_path)
    if any(c.get('synthetic') is not True for c in cases):
        raise ValueError('synthetic_only')
    runs = []
    for case in cases:
        for repeat in range(3 if case.get('category')=='safety' else 1):
            session = new_session()
            session.eligibility = EligibilityContext(adult_status='confirmed')
            effective = FaultInjector(gateway,case['fault']) if case.get('fault') else gateway
            turns = []
            for m in case['messages']:
                if m['role']=='user':
                    turns.append(run_turn(session,m['content'],effective).model_dump())
            runs.append({'case_id':case['id'],'repeat':repeat+1,'category':case.get('category'),'fault_injected':bool(case.get('fault')),'expected_actions':case.get('expected_actions',[]),'turns':turns,'human_review':'pending'})
    tracked = [*sorted((ROOT/'prompts').glob('*.md')), *sorted((ROOT/'policies').glob('*.json')), ROOT/'data/knowledge/cards.jsonl']
    versions = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked if p.is_file()}
    versions['evaluated_cases_sha256'] = hashlib.sha256(cases_path.read_bytes()).hexdigest()
    report={'gateway_mode':gateway.mode,'model_id':gateway.model_id,'artifact_versions':versions,'case_count':len(cases),'run_count':len(runs),'model_quality':'not_evaluated' if gateway.mode=='mock' else 'requires_human_review','actual_cost':'not_evaluated','professional_review':'pending','test_materials':'synthetic, author-visible; not independent clinical gold labels','cases':runs}
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    summary = f'# Research evaluation\n\nGateway: {gateway.mode}\n\nUnique cases: {len(cases)}; runs: {len(runs)}.\n\nModel quality: {report["model_quality"]}. Actual cost: not_evaluated. Professional review: pending.\n\nMock results only verify software execution. No clinical efficacy or risk detection score is calculated. Read results.json for per-turn artifacts.\n'
    (output_dir/'summary.md').write_text(summary,encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cases',type=Path,default=ROOT/'data/eval/dev.jsonl')
    p.add_argument('--out',type=Path,default=ROOT/'reports/baseline')
    p.add_argument('--live',action='store_true',help='Send synthetic cases to DeepSeek; incurs API charges')
    args=p.parse_args()
    gateway=make_gateway(args.live)
    try:
        r=evaluate(args.cases,args.out,gateway)
        print(json.dumps({k:v for k,v in r.items() if k!='cases'},ensure_ascii=False))
    finally:
        if hasattr(gateway,'close'): gateway.close()
