"""Per-browser, in-memory chat workspace. No file or network persistence."""
from dataclasses import dataclass,field
from uuid import uuid4
from .schemas import SessionState,TurnResult
from .session import new_session,clear_session
from .exploration_state import ExplorationState
from .observation_scheduler import fresh_observation_state, configure_observation

MAX_TITLE_LENGTH = 40


@dataclass
class Conversation:
    id: str = field(default_factory=lambda:uuid4().hex)
    title: str = '新的对话'
    title_is_custom: bool = False
    state: SessionState = field(default_factory=new_session)
    last_result: TurnResult | None = None
    results: dict[str,TurnResult] = field(default_factory=dict)
    feedback: dict[str,str] = field(default_factory=dict)
    gateway_mode: str = 'live'
    exploration: ExplorationState = field(default_factory=ExplorationState)


class Workspace:
    def __init__(self):
        first=Conversation()
        self.items=[first]
        self.active_id=first.id

    @property
    def active(self):
        return next(c for c in self.items if c.id==self.active_id)

    def new_conversation(self,gateway_mode=None):
        if len(self.items)>=10:
            raise ValueError('conversation_limit')
        c=Conversation(gateway_mode=gateway_mode or 'live')
        self.items.append(c)
        self.active_id=c.id
        return c

    def select(self,conversation_id):
        if not any(c.id==conversation_id for c in self.items):
            raise KeyError(conversation_id)
        self.active_id=conversation_id
        return self.active

    def rename_conversation(self,conversation_id,title):
        conversation=next((c for c in self.items if c.id==conversation_id),None)
        if conversation is None:
            raise KeyError(conversation_id)
        if not isinstance(title,str):
            raise ValueError('invalid_title')
        normalized=' '.join(title.split())
        if not normalized or len(normalized)>MAX_TITLE_LENGTH:
            raise ValueError('invalid_title')
        conversation.title=normalized
        conversation.title_is_custom=True

    def clear_active(self):
        c=self.active
        clear_session(c.state)
        c.title='新的对话'
        c.title_is_custom=False
        c.results.clear()
        c.feedback.clear()
        c.last_result=None
        previous=c.exploration.observation
        c.exploration=ExplorationState(observation=fresh_observation_state(previous))
        c.exploration.observation.last_auto_candidate_count=0

    def remove_active(self):
        configure_observation(self.active.exploration.observation,'off',())
        self.items=[c for c in self.items if c.id!=self.active_id]
        if not self.items:
            self.items=[Conversation()]
        self.active_id=self.items[-1].id
        return self.active

    def record_turn(self,result):
        c=self.active
        c.last_result=result
        first_user=next((m.content for m in c.state.messages if m.role=='user'),None)
        if first_user and not getattr(c,'title_is_custom',False):
            title=' '.join(first_user.split())
            c.title=title[:18]+('…' if len(title)>18 else '')
        if c.state.messages and c.state.messages[-1].role=='assistant':
            last=c.state.messages[-1]
            if last.id not in c.results and last.content==result.text:
                c.results[last.id]=result

    def set_feedback(self,message_id,rating):
        if not any(m.id==message_id and m.role=='assistant' for m in self.active.state.messages):
            raise ValueError('assistant_message_required')
        if rating not in (None,'helpful','not_helpful'):
            raise ValueError('invalid_feedback')
        if rating is None:
            self.active.feedback.pop(message_id,None)
        else:
            self.active.feedback[message_id]=rating

    def export_markdown(self):
        lines=['# 知心 · 虚构案例研究对话','','仅导出当前对话中的可见文本；不构成诊断或治疗意见。','']
        for m in self.active.state.messages:
            lines.extend(['## '+('你' if m.role=='user' else '知心'),'',m.content,''])
        return '\n'.join(lines)
