from dataclasses import replace
import importlib.util
import pytest
from support_agent.psychometrics import score_questionnaire


def registry():
    assert importlib.util.find_spec('support_agent.survey_registry') is not None, 'Version registry is missing'
    from support_agent import survey_registry
    return survey_registry


def test_registry_has_distinct_versions_and_legacy_ids():
    r=registry()
    enabled=[v for v in r.list_versions() if v.enabled]
    assert len(enabled)==8
    assert len({v.id for v in r.SURVEY_VERSIONS})==len(r.SURVEY_VERSIONS)
    assert {v.definition.id for v in enabled}=={'tipi','mini_ipip','rses','swls','swls3','ipip50','attachment_exploration','coping_confidence'}
    assert len(r.list_versions('big_five'))>=4
    with pytest.raises(KeyError): r.get_version('unknown')
    for v in enabled:
        assert r.get_version(v.id) is v
        assert v.language_version and v.scoring_key_version and v.license_notice and v.validation_population


def test_candidates_never_supply_unverified_items():
    candidates=[v for v in registry().list_versions() if not v.enabled]
    assert {'ipip100','bfi2','ecr_r','ecr_rs','ecr_s'} <= {v.instrument_id for v in candidates}
    assert all(v.definition is None and v.notes for v in candidates)


def test_swls_three_uses_first_three_items_and_distinct_range():
    enabled={v.definition.id:v for v in registry().list_versions() if v.enabled}
    short,long=enabled['swls3'],enabled['swls']
    assert short.definition.items==long.definition.items[:3]
    for v,limits in ((short,(3,21)),(long,(5,35))):
        result=score_questionnaire(v.definition,{i.id:4 for i in v.definition.items})
        d=result.dimensions['life_satisfaction']
        assert (d.min_total,d.max_total)==limits
        assert result.version_id is None
        assert replace(result,version_id=v.id).test_id==v.definition.id
        assert '未经' in v.definition.translation_note


def test_ipip50_official_key_and_direction():
    v=next(v for v in registry().list_versions() if v.instrument_id=='ipip50')
    q=v.definition
    assert len(q.items)==50 and q.min_score==1 and q.max_score==5
    assert [sum(i.reverse for i in q.items if i.dimension==d) for d in q.dimension_labels]==[5,4,4,8,3]
    # Answer the positive pole of every official factor, including stability.
    result=score_questionnaire(q,{i.id:1 if i.reverse else 5 for i in q.items})
    assert all(d.mean==5 and d.total==50 for d in result.dimensions.values())
    assert '情绪稳定' in q.interpretation and '负性情绪' in q.interpretation
    assert '公共领域' in q.license_notice and '未经' in q.translation_note

def test_ui_shared_items_keep_versions_and_relationship_widgets_separate(monkeypatch):
    from streamlit.testing.v1 import AppTest
    import support_agent.questionnaire_ui as ui
    downloads=[]
    original=ui.st.download_button
    def capture(*args,**kwargs):
        downloads.append(kwargs['data'])
        return original(*args,**kwargs)
    monkeypatch.setattr(ui.st,'download_button',capture)
    app=AppTest.from_string('''
import streamlit as st
from types import SimpleNamespace
from support_agent.exploration_state import ExplorationState
from support_agent.research_wellbeing_tests import SWLS
from support_agent.questionnaire_ui import render_questionnaire
if 'conversation' not in st.session_state:
    st.session_state.conversation=SimpleNamespace(id='test', exploration=ExplorationState())
version=st.selectbox('version',['zh-v1:key-v1','zh-v2:key-v2'],key='version')
render_questionnaire(st.session_state.conversation,SWLS,True,version_id=version)
''').run()
    assert not app.exception
    first_keys=[s.key for s in app.selectbox if '_item_swls_' in s.key]
    for key in first_keys: app.selectbox(key=key).select(4)
    app.button(key='calculate_survey').click().run()
    assert not app.exception
    state=app.session_state['conversation'].exploration
    assert state.survey_results['zh-v1:key-v1'].version_id=='zh-v1:key-v1'
    app.selectbox(key='version').select('zh-v2:key-v2').run()
    second_keys=[s.key for s in app.selectbox if '_item_swls_' in s.key]
    assert set(first_keys).isdisjoint(second_keys)
    assert all(app.selectbox(key=k).value is None for k in second_keys)
    for key in second_keys: app.selectbox(key=key).select(2)
    app.button(key='calculate_survey').click().run()
    state=app.session_state['conversation'].exploration
    assert state.survey_results['zh-v1:key-v1'].dimensions['life_satisfaction'].total==20
    assert state.survey_results['zh-v2:key-v2'].dimensions['life_satisfaction'].total==10
    assert state.survey_contexts=={'zh-v1:key-v1':'','zh-v2:key-v2':''}
    assert any('zh-v2:key-v2' in c.value for c in app.caption)
    assert '版本：zh-v2:key-v2' in downloads[-1]
    assert '版本：zh-v1:key-v1' in downloads[0]

def test_ui_attachment_relationship_switch_clears_new_answers():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string('''
import streamlit as st
from types import SimpleNamespace
from support_agent.exploration_state import ExplorationState
from support_agent.attachment_questions import ATTACHMENT_EXPLORATION
from support_agent.questionnaire_ui import render_questionnaire
if 'conversation' not in st.session_state:
    st.session_state.conversation=SimpleNamespace(id='test', exploration=ExplorationState())
render_questionnaire(st.session_state.conversation,ATTACHMENT_EXPLORATION,True,version_id='attachment:v1')
''').run()
    app.selectbox(key='explore_test_attachment_context_attachment:v1').select('亲密伴侣').run()
    first=[s.key for s in app.selectbox if '_item_' in s.key]
    for key in first: app.selectbox(key=key).select(4)
    app.button(key='calculate_survey').click().run()
    app.selectbox(key='explore_test_attachment_context_attachment:v1').select('亲近朋友').run()
    second=[s.key for s in app.selectbox if '_item_' in s.key]
    assert not app.exception and set(first).isdisjoint(second)
    assert all(app.selectbox(key=k).value is None for k in second)
    assert app.session_state['conversation'].exploration.survey_contexts['attachment:v1']=='亲密伴侣'
    assert any('关系对象已切换' in w.value for w in app.warning)

def test_attachment_context_does_not_leak_between_conversations():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string('''
import streamlit as st
from types import SimpleNamespace
from support_agent.exploration_state import ExplorationState
from support_agent.attachment_questions import ATTACHMENT_EXPLORATION
from support_agent.questionnaire_ui import render_questionnaire
if 'conversations' not in st.session_state:
    st.session_state.conversations={k:SimpleNamespace(id=k,exploration=ExplorationState()) for k in ('first','second')}
active=st.selectbox('Conversation',['first','second'],key='active')
render_questionnaire(st.session_state.conversations[active],ATTACHMENT_EXPLORATION,True,version_id='attachment:v1')
''').run()
    relation=next(s for s in app.selectbox if s.label=='这次想到哪段关系？')
    first_key=relation.key
    relation.select('亲密伴侣').run()
    app.selectbox(key='active').select('second').run()
    relation=next(s for s in app.selectbox if s.label=='这次想到哪段关系？')
    assert relation.value is None
    assert relation.key!=first_key
    assert relation.key.startswith('explore_second_')
