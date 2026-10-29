from dataclasses import replace
import streamlit as st
from .attachment_questions import attachment_pattern
from .psychometrics import score_questionnaire
from .exploration_catalog import export_survey_report


def show_result(definition,result,context):
    st.markdown('#### 本次记录')
    if result.version_id: st.caption('版本：'+result.version_id)
    if context: st.caption('想到的关系：'+context)
    for dimension in result.dimensions.values():
        value=f'{dimension.total} / {dimension.max_total}' if definition.display=='sum' else f'{dimension.mean:.2f} / {dimension.max_value}'
        st.markdown(f'**{dimension.label}**　{value}')
        st.progress((dimension.mean-dimension.min_value)/(dimension.max_value-dimension.min_value))
    st.caption('条形仅表示原始量程中的位置，不是概率或人群百分位。修改答案后，请重新计算。')
    if definition.id=='attachment_exploration':
        label,explanation=attachment_pattern(result)
        st.info('在这段关系中的本次参考：'+label)
        with st.expander('依恋参考是如何得到的？'): st.write(explanation)
    st.write(definition.interpretation)
    st.download_button('导出这份探索记录',data=export_survey_report(definition,result,context)+(('\n\n版本：'+result.version_id) if result.version_id else ''),file_name=f'{(result.version_id or definition.id).replace(chr(58), chr(45))}-research.md',mime='text/markdown',key='download_survey',on_click='ignore')


def render_questionnaire(conversation,definition,allowed,version_id=None):
    identity=version_id or definition.id
    state=conversation.exploration
    st.markdown('### '+definition.title)
    st.write(definition.description)
    if '非商业' in definition.license_notice: st.caption('使用范围：仅限非商业研究。')
    else: st.caption(definition.translation_note)
    with st.expander('来源、计分与使用说明'):
        st.markdown(f'[{definition.source_name}]({definition.source_url})')
        st.write(definition.license_notice)
        st.write(definition.translation_note)
        st.write(definition.interpretation)
    context=''
    if definition.id=='attachment_exploration':
        context=st.selectbox('这次想到哪段关系？',['亲密伴侣','亲近朋友','父母或家人','其他重要关系'],index=None,key=('explore_'+conversation.id+'_attachment_context_'+version_id if version_id else 'attachment_context'),placeholder='选择关系，不需要填写任何人的姓名') or ''
        st.caption('同一次作答始终围绕这一段关系，不把不同对象混在一起。')
    old_result=state.survey_results.get(identity)
    old_context=state.survey_contexts.get(identity,'')
    if old_result:
        if old_context!=context: st.warning('关系对象已切换，下面仍是上次“'+old_context+'”的结果；新关系需要重新作答。')
        show_result(definition,old_result,old_context)
    enabled=allowed and (definition.id!='attachment_exploration' or bool(context))
    if not allowed: st.caption('请先在上方确认研究使用范围；这些问卷在本机计分，不会发给模型。')
    prior=state.survey_answers.get(identity,{}) if context==old_context else {}
    context_suffix=str(['','亲密伴侣','亲近朋友','父母或家人','其他重要关系'].index(context))
    with st.form('explore_'+conversation.id+'_form_'+identity+'_'+context_suffix):
        answers={}
        for index,item in enumerate(definition.items,1):
            values=list(range(definition.min_score,definition.max_score+1))
            previous=prior.get(item.id)
            answers[item.id]=st.selectbox(f'{index}. {item.text}',values,index=values.index(previous) if previous in values else None,format_func=lambda value:definition.options[value-definition.min_score],key=f'explore_{conversation.id}_item_{item.id}_{identity}_{context_suffix}',placeholder='请选择；暂不作答可留空',disabled=not enabled)
        submitted=st.form_submit_button('计算并保存本次记录',key='calculate_survey',type='primary',disabled=not enabled)
    if submitted:
        missing=sum(v is None for v in answers.values())
        if missing:
            st.warning(f'还有 {missing} 题未作答，暂不计算；不会替你填补答案。')
        else:
            result=replace(score_questionnaire(definition,answers),version_id=version_id)
            state.survey_answers[identity]=dict(answers)
            state.survey_results[identity]=result
            state.survey_contexts[identity]=context
            st.rerun()
