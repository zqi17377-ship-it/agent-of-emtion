import json


def synthetic_cases(path, count):
    path.write_text('\n'.join(json.dumps({'id':str(i),'category':'support','synthetic':True,'messages':[{'role':'user','content':'这是成年人虚构研究案例，我想先聊聊。'}]}) for i in range(count)), encoding='utf-8')


def test_api_evaluation_stops_before_exceeding_shared_request_limit(tmp_path):
    from scripts.evaluate import evaluate
    from tests.helpers import FakeGateway
    class CountingGateway(FakeGateway):
        calls=0
        def generate(self,*args):
            self.calls+=1
            return super().generate(*args)
    cases=tmp_path/'cases.jsonl'
    synthetic_cases(cases,3)
    gateway=CountingGateway()
    report=evaluate(cases,tmp_path/'report',gateway,limit=3,max_requests=1)
    assert gateway.calls==1
    assert report['gateway_attempts']==1
    assert report['stopped_for_request_limit'] is True


def test_evaluation_selects_only_requested_number_of_synthetic_cases(tmp_path):
    from scripts.evaluate import evaluate
    from tests.helpers import FakeGateway
    cases=tmp_path/'cases.jsonl'
    synthetic_cases(cases,3)
    report=evaluate(cases,tmp_path/'report',FakeGateway(),limit=1,max_requests=4)
    assert report['case_count']==1
    assert report['input_case_count']==3
    assert report['stopped_for_request_limit'] is False


def test_evaluation_command_defaults_to_api_and_small_explicit_limits(tmp_path,monkeypatch):
    from scripts import evaluate as module
    seen={}
    class Gateway:
        mode='live'
        model_id='test'
    def factory(live=True):
        seen['live']=live
        return Gateway()
    def run(cases,out,gateway,**kwargs):
        seen.update(kwargs)
        return {'case_count':0,'cases':[]}
    monkeypatch.setattr(module,'make_gateway',factory)
    monkeypatch.setattr(module,'evaluate',run)
    assert module.main([])==0
    assert seen=={'live':True,'limit':3,'max_requests':12}


def test_mock_report_has_no_model_performance_claim_and_missing_usage_stays_unknown(tmp_path):
    from scripts.evaluate import evaluate
    from tests.helpers import FakeGateway
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
    from tests.helpers import FakeGateway
    path=tmp_path/'cases.jsonl'; path.write_text(json.dumps({'id':'real','synthetic':False,'messages':[]}),encoding='utf-8')
    with pytest.raises(ValueError,match='synthetic_only'):
        evaluate(path,tmp_path/'report',FakeGateway())
