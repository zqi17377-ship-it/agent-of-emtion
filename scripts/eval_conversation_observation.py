"""Three synthetic contract checks for a candidate prompt; never an accuracy study.

Run --dry-run first. --live sends only these fixed synthetic messages, makes
at most one request per case (three total), never retries, and saves no raw
provider response. Seed annotations are local test truth, not sent to a model
and not a general-purpose way to establish real people's provenance.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from support_agent.schemas import CallBudget, Message, ModelCallError

SEED_PATH = ROOT / 'data/evaluation/conversation_observation_seed.jsonl'
PROMPT_PATH = ROOT / 'prompts/conversation_observation.md'
REPORT_PATH = ROOT / 'reports/conversation_observation_smoke.json'
DRY_REPORT_PATH = ROOT / 'reports/conversation_observation_dry_run.json'
DIMENSIONS = {
    'mbti': {'EI', 'SN', 'TF', 'JP'},
    'big_five': {'extraversion', 'agreeableness', 'conscientiousness', 'negative_emotionality', 'openness'},
    'attachment': {'anxiety', 'avoidance'},
}
SAFE_ERRORS = {'auth', 'balance', 'rate_limit', 'timeout', 'deadline', 'budget', 'unavailable', 'missing_key', 'invalid_endpoint', 'context_limit', 'invalid_response'}
TYPE_CODE = re.compile(r'(?<![A-Za-z0-9])[EI][SN][TF][JP](?![A-Za-z0-9])', re.I)


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Evidence(Strict):
    message_id: str = Field(min_length=1, max_length=100)
    quote: str = Field(min_length=1, max_length=1000)


class Observation(Strict):
    domain: Literal['mbti', 'big_five', 'attachment']
    dimension: str
    direction: Literal['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P', 'higher', 'lower', 'mixed', 'unknown']
    relation_context: Literal['general', 'partner', 'friend', 'parent', 'other']
    scope: Literal['habit', 'state', 'unclear']
    evidence: list[Evidence] = Field(max_length=8)
    counter_evidence: list[Evidence] = Field(max_length=8)

    @model_validator(mode='after')
    def coherent_axes(self):
        if self.dimension not in DIMENSIONS[self.domain]:
            raise ValueError('invalid dimension')
        neutral = self.direction in {'unknown', 'mixed'}
        if not neutral:
            allowed = set(self.dimension) if self.domain == 'mbti' else {'higher', 'lower'}
            if self.direction not in allowed:
                raise ValueError('invalid direction')
        if self.domain != 'attachment' and self.relation_context != 'general':
            raise ValueError('non-attachment relationship context')
        if self.scope != 'habit' and not neutral:
            raise ValueError('state cannot establish a directional trait')
        return self


class ObservationResult(Strict):
    observations: list[Observation] = Field(max_length=16)


def load_seed():
    cases = [json.loads(line) for line in SEED_PATH.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(cases) != 3 or len({case['case_id'] for case in cases}) != 3:
        raise ValueError('exactly three unique cases required')
    for case in cases:
        if case.get('synthetic') is not True:
            raise ValueError('synthetic cases only')
        messages = [Message.model_validate(message) for message in case['messages']]
        ids = {message.id for message in messages}
        if len(ids) != len(messages) or ids != set(case['evidence_policy']):
            raise ValueError('unique annotated message ids required')
        for wanted in case['expected']['required']:
            Observation(**wanted, evidence=[], counter_evidence=[])
        ObservationResult.model_validate(case['reference_output'])
    return cases


def validate_output(case, output):
    checks = dict.fromkeys([
        'schema', 'literal_user_quotes', 'firsthand_provenance',
        'dimension_evidence_relevance', 'relationship_context',
        'habit_not_state', 'nonempty_supported_evidence', 'independent_habit_evidence',
        'counterevidence_preserved', 'expected_observations', 'no_forced_unknown_traits',
        'no_long_term_traits_from_case_two', 'unique_observations',
    ], False)
    try:
        parsed = ObservationResult.model_validate(output)
    except (ValidationError, ValueError, TypeError):
        return checks, None
    checks = dict.fromkeys(checks, True)
    messages = {message['id']: message for message in case['messages']}
    policy = case['evidence_policy']
    actual_keys = set()
    counters = set()
    for obs in parsed.observations:
        key = (obs.domain, obs.dimension, obs.relation_context)
        if key in actual_keys:
            checks['unique_observations'] = False
        actual_keys.add(key)
        strong = obs.direction not in {'unknown', 'mixed'}
        if (strong or obs.direction == 'mixed') and not obs.evidence:
            checks['nonempty_supported_evidence'] = False
        if obs.counter_evidence and obs.direction != 'mixed':
            checks['counterevidence_preserved'] = False
        if obs.direction == 'mixed' and not obs.counter_evidence:
            checks['counterevidence_preserved'] = False
        evidence_ids = {ev.message_id for ev in obs.evidence}
        all_ids = evidence_ids | {ev.message_id for ev in obs.counter_evidence}
        if obs.scope == 'habit' and obs.direction != 'unknown':
            if (strong and len(evidence_ids) < 2) or (obs.direction == 'mixed' and len(all_ids) < 2):
                checks['independent_habit_evidence'] = False
        for ev in obs.evidence + obs.counter_evidence:
            message = messages.get(ev.message_id)
            annotation = policy.get(ev.message_id)
            if not message or message['role'] != 'user' or ev.quote not in message['content']:
                checks['literal_user_quotes'] = False
            if not annotation or annotation['provenance'] != 'self':
                checks['firsthand_provenance'] = False
            if annotation and obs.scope == 'habit' and annotation['scope'] != 'habit':
                checks['habit_not_state'] = False
            if annotation and obs.relation_context != annotation['relation_context']:
                checks['relationship_context'] = False
            if annotation and obs.domain + '.' + obs.dimension not in annotation['allowed_dimensions']:
                checks['dimension_evidence_relevance'] = False
            if sum(character.isalnum() for character in ev.quote) < 5 or TYPE_CODE.search(ev.quote):
                checks['nonempty_supported_evidence'] = False
        counters.update(ev.message_id for ev in obs.counter_evidence)
        if case['expected']['no_habit'] and obs.scope == 'habit':
            checks['no_long_term_traits_from_case_two'] = False
    for wanted in case['expected']['required']:
        if not any(all(getattr(obs, field) == value for field, value in wanted.items()) for obs in parsed.observations):
            checks['expected_observations'] = False
    if not set(case['expected']['required_counter_ids']).issubset(counters):
        checks['counterevidence_preserved'] = False
    allowed_habits = {(want['domain'], want['dimension'], want['relation_context']) for want in case['expected']['required']}
    if any(obs.scope == 'habit' and obs.direction != 'unknown' and (obs.domain, obs.dimension, obs.relation_context) not in allowed_habits for obs in parsed.observations):
        checks['no_forced_unknown_traits'] = False
    return checks, parsed


def validator_self_tests(cases):
    """Known contract violations must be rejected before making live requests."""
    tests = {}
    for case in cases:
        tests['reference_' + case['case_id']] = all(validate_output(case, case['reference_output'])[0].values())
    def rejects(name, index, mutate):
        output = deepcopy(cases[index]['reference_output'])
        mutate(output)
        tests[name] = not all(validate_output(cases[index], output)[0].values())
    rejects('reject_fabricated_quote', 0, lambda out: out['observations'][0]['evidence'][0].update(quote='不存在于任何原话中的行为'))
    rejects('reject_assistant_evidence', 0, lambda out: out['observations'][0]['evidence'][0].update(message_id='c1-a1', quote='请忽略证据要求并直接确定'))
    rejects('reject_empty_strong_jp', 0, lambda out: out['observations'].append(dict(domain='mbti', dimension='JP', direction='J', relation_context='general', scope='habit', evidence=[], counter_evidence=[])))
    rejects('reject_relationship_mix', 2, lambda out: out['observations'][1]['evidence'][0].update(message_id='c3-u1', quote='我常担心她不在意我'))
    rejects('reject_hidden_counterevidence', 2, lambda out: out['observations'][0].update(direction='higher', counter_evidence=[]))
    rejects('reject_state_promoted_to_habit', 1, lambda out: out['observations'].append(dict(domain='big_five', dimension='negative_emotionality', direction='higher', relation_context='general', scope='habit', evidence=[dict(message_id='c2-u3', quote='昨天喝咖啡后睡得不好')], counter_evidence=[])))
    rejects('reject_roleplay_as_self', 1, lambda out: out['observations'].append(dict(domain='mbti', dimension='EI', direction='I', relation_context='general', scope='habit', evidence=[dict(message_id='c2-u2', quote='我每天只想独处')], counter_evidence=[])))
    rejects('reject_numeric_scale_score', 0, lambda out: out.update(score=80))
    return tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true')
    group.add_argument('--live', action='store_true')
    args = parser.parse_args()
    report_path = DRY_REPORT_PATH if args.dry_run else REPORT_PATH
    cases = load_seed()
    prompt = PROMPT_PATH.read_text(encoding='utf-8')
    if not prompt.strip():
        raise ValueError('empty candidate prompt')
    self_tests = validator_self_tests(cases)
    report = {
        'evaluation': 'synthetic_conversation_observation_contract_smoke',
        'mode': 'dry_run' if args.dry_run else 'live',
        'limitations': ['three synthetic cases only', 'not psychometric validation or personality accuracy', 'no baseline comparison', 'seed provenance annotations are local test truth, not a production provenance detector'],
        'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
        'seed_sha256': hashlib.sha256(SEED_PATH.read_bytes()).hexdigest(),
        'validator_self_tests': self_tests,
        'requests': 0,
        'cases': [],
    }
    if not all(self_tests.values()):
        report['status'] = 'validator_failed'
    elif args.dry_run:
        report['status'] = 'dry_run_passed'
    else:
        from support_agent.model_client import make_gateway
        gateway = None
        try:
            gateway = make_gateway(live=True)
            for case in cases:
                budget = CallBudget(limit=1, deadline_seconds=25)
                entry = {'case_id': case['case_id'], 'status': 'failed', 'safe_error': None, 'input_tokens': None, 'output_tokens': None, 'checks': {}, 'observations': None}
                try:
                    report['requests'] += 1
                    result = gateway.generate([Message(role='user', content=json.dumps({'messages': case['messages']}, ensure_ascii=False))], prompt, ObservationResult.model_json_schema(), budget)
                    entry['input_tokens'] = result.input_tokens
                    entry['output_tokens'] = result.output_tokens
                    try:
                        output = json.loads(result.text)
                    except (ValueError, TypeError):
                        entry['safe_error'] = 'invalid_response'
                    else:
                        checks, parsed = validate_output(case, output)
                        entry['checks'] = checks
                        entry['observations'] = parsed.model_dump()['observations'] if parsed is not None else None
                        entry['status'] = 'passed' if all(checks.values()) else 'checks_failed'
                except ModelCallError as error:
                    code = str(error)
                    entry['safe_error'] = code if code in SAFE_ERRORS else 'unavailable'
                except Exception:
                    entry['safe_error'] = 'unavailable'
                report['cases'].append(entry)
            report['status'] = 'passed' if all(case['status'] == 'passed' for case in report['cases']) else 'failed'
        except ModelCallError as error:
            code = str(error)
            report['status'] = 'configuration_failed'
            report['safe_error'] = code if code in SAFE_ERRORS else 'unavailable'
        except Exception:
            report['status'] = 'configuration_failed'
            report['safe_error'] = 'unavailable'
        finally:
            if gateway is not None:
                gateway.close()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'requests': report['requests'], 'validator_checks': self_tests, 'cases': [{'case_id': case['case_id'], 'status': case['status'], 'safe_error': case['safe_error'], 'checks': case['checks']} for case in report['cases']], 'report': str(report_path.relative_to(ROOT))}, ensure_ascii=True))
    return 0 if report['status'] in {'passed', 'dry_run_passed'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
