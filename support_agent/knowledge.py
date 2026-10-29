import json
from .config import ROOT
from .schemas import KnowledgeCard


def load_cards():
    path = ROOT / 'data/knowledge/cards.jsonl'
    if not path.exists():
        return []
    return [KnowledgeCard.model_validate_json(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def retrieve(query, concerns, cards, eligibility, mode, limit=3):
    if mode not in ('synthetic_research', 'eligible_pilot'):
        return []
    scored = []
    for card in cards:
        if card.permission_status != 'permitted' or card.review_status == 'rejected':
            continue  # research-only rights must first be resolved to the exact permitted purpose.
        if mode == 'eligible_pilot' and (card.review_status != 'approved' or not card.reviewer or not card.review_date):
            continue
        context = eligibility.model_dump()
        if any(context.get(k) != v for k,v in card.applicability.items()):
            continue
        if set(card.exclusions).intersection(eligibility.reported_conditions):
            continue
        score = sum(1 for tag in card.tags if tag in query or tag in concerns)
        if score:
            scored.append((score, card.id, card))
    return [c for _,_,c in sorted(scored,key=lambda item:(-item[0],item[1]))[:max(0,min(limit,3))]]
