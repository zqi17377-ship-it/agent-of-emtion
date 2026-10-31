import json
from time import monotonic
from .assessment import assess
from .config import ROOT
from .guardrails import check_reply
from .knowledge import load_cards, retrieve
from .policy import choose_action
from .response import draft_reply
from .schemas import Assessment, CallBudget, Message, ModelCallError, TurnResult
from .telemetry import record_event
from .dialogue_exploration import exploration_payload, plan_inquiry, advance_inquiry_state,honor_inquiry_pause
from .schemas import InquiryState


def fallback_text(action, failed=False):
    data = json.loads((ROOT / 'policies/fallbacks.json').read_text(encoding='utf-8'))
    return data['urgent_support' if action == 'urgent_support' else 'service_error' if failed else action]


def run_turn(session, text, gateway, *, exploration_context=None):
    if session.mode != 'synthetic_research':
        return TurnResult(text='真实用户试用尚未启用。',action='clarify',status='error',error_code='pilot_disabled')
    if not text.strip():
        return TurnResult(text='请输入一个虚构场景。',action='clarify',status='error',error_code='empty_input')
    budget = CallBudget()
    inquiry_state = getattr(session, 'inquiry_state', InquiryState())
    inquiry_plan = None
    oversized = sum(len(m.content) for m in session.messages) + len(text) > 18000
    if not oversized:
        session.messages.append(Message(role='user',content=text))
        if exploration_payload(exploration_context) is not None:
            a = assess(session.messages,session.previous_decision,gateway,budget,
                       exploration_context=exploration_context,inquiry_state=inquiry_state)
        else:
            a = assess(session.messages,session.previous_decision,gateway,budget)
    else:
        a = Assessment(status='failed',missing_information=['上下文超出研究原型限制，未静默截断'])
    decision = choose_action(a,session.previous_decision)
    session.previous_decision = decision
    paused_state=honor_inquiry_pause(exploration_context,inquiry_state,a,session.messages)
    if paused_state is not inquiry_state:
        inquiry_state=paused_state
        session.inquiry_state=paused_state
    status, sources, code = 'ok', [], None
    if a.status == 'failed' or decision.action == 'urgent_support':
        reply = fallback_text(decision.action,failed=a.status=='failed')
        status = 'fallback'
        code = 'context_limit' if oversized else 'assessment_failed' if a.status=='failed' else None
    else:
        try:
            cards = retrieve(text,a.concerns,load_cards(),session.eligibility,session.mode)
            inquiry_plan = plan_inquiry(exploration_context,session.messages,a,decision,inquiry_state)
            draft = draft_reply(session.messages,a,decision,cards,gateway,budget,inquiry_plan=inquiry_plan)
            checked = check_reply(draft,session.messages,a,decision,cards,gateway,budget,inquiry_plan=inquiry_plan)
            if not checked.allowed or budget.remaining() <= 0:
                raise ModelCallError('output_not_approved')
            reply = draft
            sources = [c.id for c in cards if f'[[{c.id}]]' in draft]
        except (ModelCallError, ValueError, OSError):
            reply = fallback_text(decision.action,failed=True)
            status, code = 'fallback', 'generation_or_check_failed'
    if oversized:
        reply = '上下文过长，本轮未发送。请保留重要信息另开会话；清除前请自行确认仍需处理的求助信息。\n\n' + reply
    else:
        assistant_message = Message(role='assistant',content=reply)
        session.messages.append(assistant_message)
        if status == 'ok':
            session.inquiry_state = advance_inquiry_state(
                inquiry_state,exploration_context,inquiry_plan,a,session.messages,
                assistant_message_id=assistant_message.id,
            )
    metrics = {'model_id':gateway.model_id,'attempts':budget.attempts,'input_tokens':budget.input_tokens,'output_tokens':budget.output_tokens,'elapsed_ms':int((monotonic()-budget.started)*1000),'action':decision.action,'status':status,'error_code':code}
    record_event('turn',metrics)
    return TurnResult(text=reply,action=decision.action,source_ids=sources,status=status,error_code=code,metrics=metrics)
