import json
import re
from .config import ROOT
from .schemas import CheckResult, Message, ModelCallError


def check_reply(text, messages, assessment, decision, cards, gateway, budget):
    forbidden = [r'你(?:已经|确实)?(?:患有|得了)(?:抑郁症|焦虑症|双相|精神分裂)', r'(?:已(?:经)?为你转接|已通知(?:医生|家属)|救援正在赶来)', r'(?:保证|百分之百|一定能)(?:治好|治愈)', r'(?:立即|马上|自行)停药']
    if any(re.search(p,text) for p in forbidden):
        return CheckResult(allowed=False,reason_codes=['forbidden_claim'])
    ids = set(re.findall(r'\[\[([^\]]+)\]\]',text))
    if not ids <= {c.id for c in cards}:
        return CheckResult(allowed=False,reason_codes=['invented_source'])
    instructions = (ROOT / 'prompts/check.md').read_text(encoding='utf-8')
    data = {'conversation':[m.model_dump() for m in messages], 'assessment':assessment.model_dump(), 'decision':decision.model_dump(), 'knowledge':[c.model_dump() for c in cards], 'draft':text}
    try:
        result = gateway.generate([Message(role='user',content=json.dumps(data,ensure_ascii=False))],instructions,CheckResult.model_json_schema(),budget)
        return CheckResult.model_validate_json(result.text)
    except (ModelCallError, ValueError, TypeError):
        return CheckResult(allowed=False,reason_codes=['checker_unavailable'])
