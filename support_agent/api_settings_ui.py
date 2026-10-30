"""Independent, per-visitor DeepSeek connection settings page."""
import streamlit as st

from .config import ConnectionSettings, DEFAULT_SETTINGS
from .connection_check import check_connection
from .schemas import ModelCallError
from .session_connection import get_session_settings, save_session_settings, clear_session_settings


ERROR_MESSAGES = {
    'missing_key':'请先填写你自己的 API Key。',
    'invalid_key':'API Key 格式有误，请检查是否包含空格、换行或多余内容。',
    'invalid_model':'请填写有效的模型名称，例如 deepseek-flash。',
    'invalid_endpoint':'当前只支持 DeepSeek 官方接口。',
    'auth':'密钥验证失败，请检查密钥是否正确、是否仍然有效。',
    'balance':'该 API 账号余额不足，请在 DeepSeek 平台检查。',
    'rate_limit':'请求过于频繁，请稍后再试。',
    'timeout':'连接测试超时，请稍后再试。',
    'deadline':'连接测试超时，请稍后再试。',
    'unavailable':'暂时无法完成连接，请检查网络和模型名称，稍后再试。',
}


def open_api_settings():
    current=st.session_state.get('workspace_view','home')
    if current!='api_settings':
        st.session_state['api_settings_return']=current
    st.session_state['workspace_view']='api_settings'


def back_from_api_settings():
    target=st.session_state.pop('api_settings_return','home')
    st.session_state['workspace_view']=target if target in ('home','chat','chat_setup','exploration') else 'home'
    st.session_state.pop(_password_widget_key(),None)


def _password_widget_key():
    return f"api_settings_key_{st.session_state.get('api_settings_form_revision',0)}"


def render_api_settings():
    current=get_session_settings()
    if st.session_state.pop('api_settings_reset_form',False):
        # A new identity also removes a submitted or unsaved password in the browser.
        st.session_state.pop(_password_widget_key(),None)
        st.session_state['api_settings_form_revision']=st.session_state.get('api_settings_form_revision',0)+1
        st.session_state.pop('api_settings_model',None)
    st.markdown('## 连接你自己的 DeepSeek')
    st.write('填写你自己的 API Key 和模型名称，保存后即可用于本次会话中的对话与分析。')
    st.caption('密钥会由运行此应用的服务器处理，仅保存在当前浏览器会话对应的内存中；不写入配置文件。刷新或关闭后可能需要重新填写。')
    st.caption('服务商：DeepSeek · 官方地址：https://api.deepseek.com')
    if current:
        st.info('本次会话已保存 API 配置。修改模型时可以把密钥栏留空，沿用本次已保存的密钥。')
    else:
        st.info('本次会话尚未设置 API。每位使用者需要填写自己的密钥。')
    with st.form('api_settings_form',clear_on_submit=True):
        key=st.text_input('API Key',type='password',key=_password_widget_key(),max_chars=4096,autocomplete='off',placeholder='已保存；留空可保留原密钥' if current else '在这里填写你的 DeepSeek API Key')
        model=st.text_input('模型名称',value=current.model if current else DEFAULT_SETTINGS['LLM_MODEL'],key='api_settings_model',max_chars=100)
        submitted=st.form_submit_button('保存 API 配置',key='api_settings_save',type='primary')
    if submitted:
        try:
            snapshot=ConnectionSettings(key if key.strip() else current.api_key if current else '',model)
            changed=save_session_settings(snapshot)
        except ModelCallError as error:
            st.error(ERROR_MESSAGES.get(str(error),'配置格式有误，请重新检查。'))
        else:
            st.session_state.pop('api_settings_test_result',None)
            st.session_state['api_settings_saved']=changed
            st.session_state['api_settings_reset_form']=True
            st.rerun()
    if 'api_settings_saved' in st.session_state:
        changed=st.session_state.pop('api_settings_saved')
        st.success('配置已保存，没有发送 API 请求。' if changed else '配置未变，没有发送 API 请求。')
        if changed: st.caption('连接配置已更新；对话发送与自动观察需要重新确认。已有聊天和测试记录保留。')
    st.markdown('#### 检查连接')
    st.caption('只测试已保存的配置。点击后发送一次简短连接测试，可能产生少量 API 用量，不包含你的聊天记录。')
    if st.button('测试连接',key='api_settings_test',disabled=current is None):
        try:
            with st.spinner('正在检查 DeepSeek 连接…'):
                result=check_connection(current)
        except Exception:
            # Never display an exception or provider response containing secrets.
            result=None
        st.session_state['api_settings_test_result']=result if result is not None else False
    if 'api_settings_test_result' in st.session_state:
        result=st.session_state['api_settings_test_result']
        if result and result.success:
            st.success('连接测试成功，可以返回继续使用。')
            st.caption(f'本次测试 1 次请求 · {result.elapsed_ms} 毫秒')
        else:
            code=result.error_code if result else 'unavailable'
            st.error(ERROR_MESSAGES.get(code,'连接测试未完成，请核对配置后重试。'))
    if st.button('清除本次 API 配置',key='api_settings_clear',disabled=current is None,type='tertiary'):
        clear_session_settings()
        st.session_state.pop('api_settings_test_result',None)
        st.session_state['api_settings_reset_form']=True
        st.rerun()
    st.button('返回继续使用',key='api_settings_back',on_click=back_from_api_settings)
    st.markdown('[获取 DeepSeek API Key](https://platform.deepseek.com/api_keys) · [官方接入说明](https://api-docs.deepseek.com/)')
