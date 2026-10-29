import pytest
from support_agent.schemas import CallBudget, ModelResult


@pytest.mark.parametrize('missing_attempts',[1,2])
def test_missing_usage_after_success_makes_aggregate_unknown(missing_attempts):
    budget=CallBudget()
    budget.consume(); budget.record(ModelResult(text='ok',model_id='test',input_tokens=10,output_tokens=5))
    assert budget.input_tokens==10
    for _ in range(missing_attempts): budget.consume()
    assert budget.input_tokens is None and budget.output_tokens is None
    budget.consume(); budget.record(ModelResult(text='ok',model_id='test',input_tokens=8,output_tokens=3))
    assert budget.input_tokens is None and budget.output_tokens is None
