import json
from pathlib import Path
from support_agent.config import ROOT
from support_agent.schemas import KnowledgeCard, Message


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def validate_assets(root: Path):
    errors = []
    try:
        sources = json.loads((root/'data/sources.json').read_text(encoding='utf-8'))
        source_urls = {s['source_url'] for s in sources}
        ids = set()
        for raw in read_jsonl(root/'data/knowledge/cards.jsonl'):
            try:
                c = KnowledgeCard.model_validate(raw)
            except ValueError:
                errors.append('invalid_card'); continue
            if c.id in ids:
                errors.append('duplicate_card')
            ids.add(c.id)
            if c.source_url not in source_urls:
                errors.append('missing_source:'+c.id)
        families = {}; case_ids = set()
        for split in ('dev','holdout'):
            families[split] = set()
            for c in read_jsonl(root/f'data/eval/{split}.jsonl'):
                if c.get('synthetic') is not True or c.get('split') != split or not c.get('scenario_family'):
                    errors.append('invalid_case')
                families[split].add(c.get('scenario_family'))
                if c.get('id') in case_ids:
                    errors.append('duplicate_case')
                case_ids.add(c.get('id'))
                for m in c.get('messages',[]):
                    Message.model_validate(m)
        if families['dev'] & families['holdout']:
            errors.append('family_overlap')
    except (OSError, ValueError, KeyError, TypeError):
        errors.append('invalid_assets')
    return errors


if __name__ == '__main__':
    issues = validate_assets(ROOT)
    print(json.dumps({'valid':not issues,'errors':issues},ensure_ascii=False))
    raise SystemExit(bool(issues))
