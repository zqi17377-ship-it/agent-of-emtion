import json
from .config import ROOT
from .schemas import Message


def draft_reply(messages, assessment, decision, cards, gateway, budget):
    instructions = (ROOT / 'prompts/respond.md').read_text(encoding='utf-8')
    data = {'assessment': assessment.model_dump(), 'decision': decision.model_dump(), 'knowledge': [c.model_dump() for c in cards]}
    # Retrieved instructions stay inside user data, never in the trusted system prompt.
    return gateway.generate(messages + [Message(role='user',content=json.dumps(data, ensure_ascii=False))], instructions, None, budget).text
