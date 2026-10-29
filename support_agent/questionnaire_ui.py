from dataclasses import replace
import streamlit as st
from .attachment_questions import attachment_pattern
from .psychometrics import score_questionnaire
from .exploration_catalog import export_survey_report
from .flow_ui import step_header, research_checkbox, back_to_tools


def show_result(definition,result,context):
    from .survey_presentation import build_survey_presentation
    presentation=build_survey_presentation(definition,result)
    st.markdown('#### 本次记录')
    if context: st.caption('想到的关系：'+context)
    st.image(presentation.svg,width='stretch')
    st.caption(presentation.chart_label)
    with st.expander('查看原始分数'):
        for dimension in result.dimensions.values():
            value=f'{dimension.total} / {dimension.max_total}' if definition.display=='sum' else f'{dimension.mean:.2f} / {dimension.max_value}'
            st.markdown(f'**{dimension.label}**　{value}')
    st.markdown(presentation.markdown)
    if definition.id=='attachment_exploration':
        label,explanation=attachment_pattern(result)
        st.info('在这段关系中的本次参考：'+label)
        with st.expander('依恋参考是如何得到的？'): st.write(explanation)
    with st.expander('计分与研究限制'):
        st.write(definition.interpretation)
    st.download_button('导出这份探索记录',data=export_survey_report(definition,result,context)+'\n\n'+presentation.markdown+(('\n\n版本：'+result.version_id) if result.version_id else ''),file_name=f'{(result.version_id or definition.id).replace(chr(58), chr(45))}-research.md',mime='text/markdown',key='download_survey',on_click='ignore')


def render_questionnaire(conversation,definition,allowed,version_id=None):
    identity=version_id or definition.id
    state=conversation.exploration
    prefix=f'explore_{conversation.id}_{identity}'
    flow=state.flows.setdefault('survey:'+prefix,{'page':'intro','context':'','drafts':{},'index':0})
    context=flow['context']
    draft_key=f'{prefix}:{context}'
    prior=state.survey_answers.get(identity,{}) if state.survey_contexts.get(identity,'')==context else {}
    answers=flow['drafts'].setdefault(draft_key,dict(prior))
    enabled=bool(st.session_state.get('research_confirmed',allowed))
    attachment=definition.id=='attachment_exploration'
    page=flow['page']
    steps=['使用说明']+(['选择关系'] if attachment else [])+['逐题填写','核对答案','查看结果']
    step_index={'intro':0,'context':1,'questions':1+attachment,'review':2+attachment,'result':3+attachment}[page]
    step_header(definition.title,steps,step_index,show_progress=page not in ('questions','review'))
    if st.button('返回功能选择',key='survey_exit'):
        back_to_tools()
        st.rerun()
    def go(target):
        flow['page']=target
        st.rerun()
    if page=='intro':
        st.write(definition.description)
        st.caption(f'共 {len(definition.items)} 题，每页只填写一题；可随时返回修改。本机计分，不发送给模型。')
        with st.expander('来源、计分与使用说明'):
            st.markdown(f'[{definition.source_name}]({definition.source_url})')
            st.write(definition.license_notice)
            st.write(definition.translation_note)
            st.write(definition.interpretation)
        confirmed=research_checkbox('survey_research')
        if st.button('开始填写',key='survey_start',disabled=not confirmed,type='primary'):
            go('context' if attachment else 'questions')
        if identity in state.survey_results and st.button('查看上次结果',key='survey_show_saved'):
            go('result')
        return
    if page=='context':
        options=['亲密伴侣','亲近朋友','父母或家人','其他重要关系']
        selected=st.radio('这次想到哪段关系？',options,index=options.index(context) if context in options else None,key=prefix+'_attachment_context')
        if selected: flow['context']=selected
        st.caption('同一次作答始终围绕这一段关系，不把不同对象混在一起。')
        if st.button('上一步',key='survey_prev'): go('intro')
        if st.button('下一步',key='survey_next',disabled=not selected or not enabled):
            flow['index']=0
            go('questions')
        return
    if page=='result':
        if identity in state.survey_results:
            show_result(definition,state.survey_results[identity],state.survey_contexts.get(identity,''))
        if st.button('修改答案',key='survey_edit'):
            flow['index']=0
            go('context' if attachment else 'questions')
        return
    def answer_progress():
        count=len(answers)
        st.caption(f'已答 {count} / {len(definition.items)} 题 · 剩余 {len(definition.items)-count} 题')
        st.progress(count/len(definition.items))
    if not enabled: st.warning('请返回使用说明，确认研究使用范围后继续。')
    if page=='questions':
        index=flow['index']
        item=definition.items[index]
        values=list(range(definition.min_score,definition.max_score+1))
        previous=answers.get(item.id)
        value=st.radio(f'{index+1}. {item.text}',values,index=values.index(previous) if previous in values else None,format_func=lambda value:definition.options[value-definition.min_score],key=f'{prefix}_item_{item.id}_{context}',disabled=not enabled)
        if value is not None: answers[item.id]=value
        answer_progress()
        if st.button('上一步',key='survey_prev'):
            if index: flow['index']-=1
            else: flow['page']='context' if attachment else 'intro'
            st.rerun()
        if st.button('下一步' if index<len(definition.items)-1 else '核对答案',key='survey_next',disabled=value is None or not enabled):
            if index<len(definition.items)-1: flow['index']+=1
            else: flow['page']='review'
            st.rerun()
        return
    answer_progress()
    st.write('请核对本次答案，确认提交后才会保存计分结果。')
    with st.expander('查看本次答案（只读）'):
        for index,item in enumerate(definition.items,1):
            value=answers.get(item.id)
            st.write(f'{index}. {item.text}：'+(definition.options[value-definition.min_score] if value in range(definition.min_score,definition.max_score+1) else '尚未回答'))
    if st.button('上一步',key='survey_prev'):
        flow['index']=len(definition.items)-1
        go('questions')
    complete=all(answers.get(item.id) in range(definition.min_score,definition.max_score+1) for item in definition.items)
    if st.button('确认提交并保存结果',key='calculate_survey',disabled=not enabled or not complete,type='primary'):
        state.survey_answers[identity]=dict(answers)
        state.survey_results[identity]=replace(score_questionnaire(definition,answers),version_id=version_id)
        state.survey_contexts[identity]=context
        go('result')
