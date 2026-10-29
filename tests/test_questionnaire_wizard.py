from streamlit.testing.v1 import AppTest


def questionnaire_app(instrument='SWLS', module='research_wellbeing_tests', versions=False):
    selector="version=st.selectbox('version',['zh-v1:key-v1','zh-v2:key-v2'],key='version')" if versions else "version='test:v1'"
    return AppTest.from_string(f'''
import streamlit as st
from types import SimpleNamespace
from support_agent.exploration_state import ExplorationState
from support_agent.{module} import {instrument}
from support_agent.questionnaire_ui import render_questionnaire
if 'conversation' not in st.session_state:
    st.session_state.conversation=SimpleNamespace(id='test',exploration=ExplorationState())
{selector}
render_questionnaire(st.session_state.conversation,{instrument},False,version_id=version)
''').run()


def start(app):
    app.checkbox(key='survey_research').check().run()
    app.button(key='survey_start').click().run()
    return app


def complete(app, value=4):
    while any(b.key=='survey_next' for b in app.button):
        app.radio[0].set_value(value).run()
        app.button(key='survey_next').click().run()
    app.button(key='calculate_survey').click().run()
    return app


def test_one_question_navigation_restores_answer_and_requires_choice():
    app=questionnaire_app()
    assert len(app.selectbox)==0
    start(app)
    assert len(app.radio)==1 and len(app.selectbox)==0
    assert app.radio[0].value is None
    assert len(app.radio[0].options)==7
    assert app.button(key='survey_next').disabled
    app.radio[0].set_value(4).run()
    app.button(key='survey_next').click().run()
    assert app.radio[0].value is None
    app.button(key='survey_prev').click().run()
    assert app.radio[0].value==4
    assert not app.session_state['conversation'].exploration.survey_results


def test_review_is_read_only_and_only_submit_saves_result():
    app=start(questionnaire_app())
    for _ in range(5):
        app.radio[0].set_value(4).run()
        app.button(key='survey_next').click().run()
    assert not app.radio and not app.selectbox
    assert not app.session_state['conversation'].exploration.survey_results
    app.button(key='calculate_survey').click().run()
    assert not app.exception and not app.selectbox
    assert app.session_state['conversation'].exploration.survey_results['test:v1'].dimensions['life_satisfaction'].total==20
    assert not any('test:v1' in c.value for c in app.caption)
    app.button(key='survey_edit').click().run()
    app.radio[0].set_value(2).run()
    assert app.session_state['conversation'].exploration.survey_results['test:v1'].dimensions['life_satisfaction'].total==20


def test_fifty_items_still_render_one_question():
    app=start(questionnaire_app('IPIP50','long_personality_tests'))
    assert len(app.radio)==1 and len(app.selectbox)==0



def test_result_displays_score_chart_and_exports_same_local_interpretation(monkeypatch):
    import support_agent.questionnaire_ui as ui
    downloads=[]
    original=ui.st.download_button
    def capture(*args,**kwargs):
        downloads.append(kwargs['data'])
        return original(*args,**kwargs)
    monkeypatch.setattr(ui.st,'download_button',capture)
    app=complete(start(questionnaire_app()))
    assert not app.exception
    import base64
    images=app.get('image')
    assert len(images)==1
    image_url=images[0].proto.imgs[0].url
    assert image_url.startswith('data:image/svg+xml;base64,')
    rendered_svg=base64.b64decode(image_url.split(',',1)[1]).decode('utf-8')
    assert '<svg' in rendered_svg and '</svg>' in rendered_svg
    from support_agent.survey_presentation import build_survey_presentation
    from support_agent.research_wellbeing_tests import SWLS
    result=app.session_state['conversation'].exploration.survey_results['test:v1']
    presentation=build_survey_presentation(SWLS,result)
    assert rendered_svg==presentation.svg
    assert any(presentation.markdown==m.value for m in app.markdown)
    assert any(presentation.chart_label==c.value for c in app.caption)
    assert any('20 / 35' in m.value for m in app.markdown)
    assert presentation.markdown in downloads[-1]

