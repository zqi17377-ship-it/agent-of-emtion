import pytest


def test_cli_defaults_to_api_and_rejects_removed_demo(monkeypatch):
    from support_agent import cli
    calls=[]
    class Gateway:
        mode='live'
        model_id='test'
    def factory(live=True):
        calls.append(live)
        return Gateway()
    monkeypatch.setattr(cli,'make_gateway',factory)
    monkeypatch.setattr('builtins.input',lambda prompt:'/quit')
    monkeypatch.setattr('sys.argv',['cli'])
    assert cli.main()==0
    assert calls==[True]
    calls.clear()
    monkeypatch.setattr('sys.argv',['cli','--mock'])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code==2
    assert calls==[]
