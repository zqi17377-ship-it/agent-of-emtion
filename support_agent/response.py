import json
from .config import ROOT
from .schemas import Message
from .dialogue_exploration import inquiry_plan_payload


def draft_reply(messages, assessment, decision, cards, gateway, budget, *, inquiry_plan=None):
    instructions = (ROOT / 'prompts/respond.md').read_text(encoding='utf-8')
    data = {'assessment': assessment.model_dump(), 'decision': decision.model_dump(), 'knowledge': [c.model_dump() for c in cards]}
    plan = inquiry_plan_payload(inquiry_plan)
    if plan is not None:
        data['inquiry_plan'] = plan
    # Retrieved instructions stay inside user data, never in the trusted system prompt.
    return gateway.generate(messages + [Message(role='user',content=json.dumps(data, ensure_ascii=False))], instructions, None, budget).text
