import hashlib
import json
from pydantic import ValidationError
from .config import ROOT
from .schemas import Assessment, Message, ModelCallError


def assess(messages, previous, gateway, budget):
    instructions = (ROOT / 'prompts/assess.md').read_text(encoding='utf-8')
    data = {'conversation': [m.model_dump() for m in messages], 'previous_decision': previous.model_dump() if previous else None}
    inputs = [Message(role='user', content=json.dumps(data, ensure_ascii=False))]
    for attempt in range(2):
        try:
            result = gateway.generate(inputs, instructions, Assessment.model_json_schema(), budget)
            a = Assessment.model_validate_json(result.text)
            users = {m.id: m.content for m in messages if m.role == 'user'}
            positions = {m.id: i for i,m in enumerate(messages) if m.role == 'user'}
            replacements = {}
            if len({e.id for e in a.evidence}) != len(a.evidence):
                raise ValueError('duplicate_evidence')
            for e in a.evidence:
                if e.message_id not in users or e.quote not in users[e.message_id]:
                    raise ValueError('invalid_evidence')
                stable = hashlib.sha256((e.message_id + ':' + str(users[e.message_id].index(e.quote)) + ':' + e.quote).encode()).hexdigest()[:20]
                replacements[e.id] = stable
                e.id = stable
                e.message_index = positions[e.message_id]
            quotes = '\n'.join(e.quote for e in a.evidence)
            for fact in (a.duration, a.daily_impact):
                if fact is not None and (not fact.strip() or fact not in quotes):
                    raise ValueError('unsupported_fact')
            for s in a.safety_signals:
                s.evidence_ids = [replacements[eid] for eid in s.evidence_ids]
            for c in a.clarifications:
                c.new_evidence_ids = [replacements[eid] for eid in c.new_evidence_ids]
            return a
        except ModelCallError:
            return Assessment(status='failed', missing_information=['模型服务或请求预算不可用'])
        except (ValidationError, ValueError, KeyError, TypeError):
            instructions += '\n上次结构或原文引用无效。重新返回符合 schema 且全部证据可定位的 JSON；不补造事实。'
    return Assessment(status='failed', missing_information=['模型输出未通过字段或原文证据校验'])
