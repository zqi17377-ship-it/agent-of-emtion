from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest


def launch(monkeypatch):
    from support_agent import config
    monkeypatch.setattr(config,'load_configuration',lambda:(_ for _ in ()).throw(AssertionError('Web must not load host credentials')))
    return AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=10).run()


def open_settings(app):
    app.button(key='open_api_settings').click().run()
    assert not app.exception


def saved_settings(app):
    return app.session_state['connection_settings'] if 'connection_settings' in app.session_state else None


def save(app, key='synthetic-visitor-key', model='deepseek-flash'):
    next(item for item in app.text_input if item.label=='API Key').set_value(key).run()
    app.text_input(key='api_settings_model').set_value(model).run()
    app.button(key='api_settings_save').click().run()
    assert not app.exception


def test_new_web_visitor_has_settings_entry_and_no_host_credentials(monkeypatch):
    app=launch(monkeypatch)
    assert not app.exception
    open_settings(app)
    assert next(item for item in app.text_input if item.label=='API Key').value==''
    assert next(item for item in app.text_input if item.label=='API Key').proto.type==1  # PASSWORD enum
    assert app.button(key='api_settings_test').disabled
    assert saved_settings(app) is None


def test_save_is_local_clears_password_and_isolates_visitors(monkeypatch):
    import support_agent.model_client as model_client
    monkeypatch.setattr(model_client,'make_gateway',lambda *a,**k:(_ for _ in ()).throw(AssertionError('Save must not send a request')))
    app=launch(monkeypatch);open_settings(app);save(app)
    assert app.session_state['connection_settings'].api_key=='synthetic-visitor-key'
    assert next(item for item in app.text_input if item.label=='API Key').value==''
    assert not app.session_state['api_consent']
    assert 'synthetic-visitor-key' not in '\n'.join(x.value for x in app.markdown)
    assert 'synthetic-visitor-key' not in app.session_state['workspace'].export_markdown()
    other=launch(monkeypatch);open_settings(other)
    assert next(item for item in other.text_input if item.label=='API Key').value==''
    assert saved_settings(other) is None
    assert app.session_state['connection_settings'].api_key=='synthetic-visitor-key'


def test_chat_setup_returns_to_same_step_after_saving_and_clear_blocks_send(monkeypatch):
    app=launch(monkeypatch)
    app.button(key='home_chat').click().run()
    app.checkbox(key='chat_setup_research').check().run()
    app.button(key='chat_setup_next').click().run()
    app.button(key='api_setup_settings').click().run()
    save(app)
    app.button(key='api_settings_back').click().run()
    assert app.session_state['workspace_view']=='chat_setup'
    assert app.button(key='chat_setup_finish').disabled
    app.checkbox(key='chat_setup_api').check().run()
    app.button(key='chat_setup_finish').click().run()
    assert not app.chat_input[0].disabled
    open_settings(app)
    app.button(key='api_settings_clear').click().run()
    assert saved_settings(app) is None
    assert app.button(key='api_settings_test').disabled
    app.button(key='api_settings_back').click().run()
    assert app.chat_input[0].disabled


def test_connection_test_uses_only_saved_settings_and_normalizes_failures(monkeypatch):
    app=launch(monkeypatch);open_settings(app);save(app)
    import support_agent.api_settings_ui as ui
    calls=[]
    def check(settings):
        calls.append(settings)
        return SimpleNamespace(success=True,error_code=None,elapsed_ms=10,input_tokens=1,output_tokens=1)
    monkeypatch.setattr(ui,'check_connection',check)
    next(item for item in app.text_input if item.label=='API Key').set_value('unsaved-other-key').run()
    app.button(key='api_settings_test').click().run()
    assert len(calls)==1 and calls[0].api_key=='synthetic-visitor-key'
    assert any('连接测试成功' in item.value for item in app.success)
    monkeypatch.setattr(ui,'check_connection',lambda *_:(_ for _ in ()).throw(RuntimeError('sensitive-provider-error')))
    app.button(key='api_settings_test').click().run()
    assert not app.exception
    assert app.error and all('sensitive-provider-error' not in item.value for item in app.error)


def test_model_only_edit_reuses_own_key_and_empty_first_key_is_rejected(monkeypatch):
    app=launch(monkeypatch);open_settings(app)
    app.button(key='api_settings_save').click().run()
    assert app.error and saved_settings(app) is None
    save(app)
    save(app,key='',model='another-model')
    assert app.session_state['connection_settings'].api_key=='synthetic-visitor-key'
    assert app.session_state['connection_settings'].model=='another-model'


def test_save_and_clear_replace_password_widget_to_remove_frontend_secret(monkeypatch):
    app=launch(monkeypatch);open_settings(app)
    original=next(item for item in app.text_input if item.label=='API Key').proto.id
    save(app)
    after_save=next(item for item in app.text_input if item.label=='API Key').proto.id
    assert after_save!=original
    next(item for item in app.text_input if item.label=='API Key').set_value('unsaved-replacement-key').run()
    app.button(key='api_settings_clear').click().run()
    assert next(item for item in app.text_input if item.label=='API Key').proto.id!=after_save
    assert next(item for item in app.text_input if item.label=='API Key').value==''
