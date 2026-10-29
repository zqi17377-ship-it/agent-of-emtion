import json


def test_mock_report_has_no_model_performance_claim_and_missing_usage_stays_unknown(tmp_path):
    from scripts.evaluate import evaluate
    from support_agent.model_client import FakeGateway
    case={'id':'demo','scenario_family':'demo','category':'support','messages':[{'role':'user','content':'我是成年人，这是一段虚构对话。'}],'expected_actions':['support'],'synthetic':True,'author':'test','professional_review':'pending','split':'dev'}
    path=tmp_path/'cases.jsonl'; path.write_text(json.dumps(case),encoding='utf-8')
    report=evaluate(path,tmp_path/'report',FakeGateway())
    assert report['gateway_mode']=='mock'
    assert report['model_quality']=='not_evaluated'
    assert report['actual_cost']=='not_evaluated'
    assert report['professional_review']=='pending'
    assert report['cases'][0]['turns'][0]['metrics']['input_tokens'] is None


def test_evaluation_rejects_non_synthetic_data(tmp_path):
    import pytest
    from scripts.evaluate import evaluate
    from support_agent.model_client import FakeGateway
    path=tmp_path/'cases.jsonl'; path.write_text(json.dumps({'id':'real','synthetic':False,'messages':[]}),encoding='utf-8')
    with pytest.raises(ValueError,match='synthetic_only'):
        evaluate(path,tmp_path/'report',FakeGateway())
