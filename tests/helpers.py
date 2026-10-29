import json
from support_agent.schemas import CallBudget, Message, ModelResult, ModelCallError


class ScriptedGateway:
    """Only replaces external model outputs; workflow remains real."""
    mode = 'mock'
    model_id = 'test-fixture'

    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls = []

    def generate(self, messages, instructions, schema, budget):
        budget.consume()
        self.calls.append((messages, instructions, schema))
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        result = ModelResult(text=json.dumps(output, ensure_ascii=False) if isinstance(output, dict) else output, model_id=self.model_id)
        budget.record(result)
        return result


def assessment(message, **changes):
    base = {'concerns': [], 'duration': None, 'daily_impact': None, 'user_goal': 'advice', 'evidence': [{'id': 'e1', 'message_id': message.id, 'quote': message.content}], 'safety_signals': [], 'clarifications': [], 'missing_information': [], 'status': 'ok'}
    base.update(changes)
    return base


def signal(kind='self_harm', need='immediate_support'):
    return {'id': 's1', 'kind': kind, 'subject': 'self', 'timeframe': 'current', 'assertion': 'reported', 'current_need': need, 'evidence_ids': ['e1']}
