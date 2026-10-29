import json


def write_assets(root, duplicate=False, missing_permission=False):
    for directory in ['data/knowledge','data/eval']:
        (root/directory).mkdir(parents=True,exist_ok=True)
    from tests.test_knowledge import card
    c = card().model_dump()
    if missing_permission:
        c.pop('permission_status')
    (root/'data/knowledge/cards.jsonl').write_text(json.dumps(c),encoding='utf-8')
    case={'id':'one','scenario_family':'family','category':'support','messages':[{'role':'user','content':'虚构'}], 'expected_actions':['listen'],'synthetic':True,'author':'test','professional_review':'pending','split':'dev'}
    (root/'data/eval/dev.jsonl').write_text(json.dumps(case),encoding='utf-8')
    case=dict(case,id='two',scenario_family='family' if duplicate else 'another',split='holdout')
    (root/'data/eval/holdout.jsonl').write_text(json.dumps(case),encoding='utf-8')
    (root/'data/sources.json').write_text(json.dumps([{'source_url':'local://original/k1','permission_status':'permitted'}]),encoding='utf-8')


def test_duplicate_family_cannot_cross_split(tmp_path):
    from scripts.check_data import validate_assets
    write_assets(tmp_path,duplicate=True)
    assert any('family_overlap' in e for e in validate_assets(tmp_path))


def test_missing_license_is_unknown_and_rejected(tmp_path):
    from scripts.check_data import validate_assets
    write_assets(tmp_path,missing_permission=True)
    assert any('invalid_card' in e for e in validate_assets(tmp_path))


def test_source_required(tmp_path):
    from scripts.check_data import validate_assets
    write_assets(tmp_path)
    (tmp_path/'data/sources.json').write_text('[]',encoding='utf-8')
    assert any('missing_source' in e for e in validate_assets(tmp_path))


def test_valid_assets_pass(tmp_path):
    from scripts.check_data import validate_assets
    write_assets(tmp_path)
    assert validate_assets(tmp_path) == []
