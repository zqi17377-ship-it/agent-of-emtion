"""Opt-in exploration records scoped to one in-memory conversation."""
from dataclasses import dataclass,field
from .personality import PersonalityProfile,user_fingerprint
from .personality_questions import score_self_report,confirmed_type,describe_self_report
from .psychometrics import QuestionnaireResult
from .observation_scheduler import ObservationState

AXIS_LABELS={'EI':('社交能量','E · 互动中充电','I · 独处中恢复'),'SN':('信息关注','S · 具体与经验','N · 关联与可能'),'TF':('决策偏好','T · 原则与理由','F · 价值与感受'),'JP':('安排方式','J · 计划与确定','P · 弹性与探索')}


@dataclass
class ExplorationState:
    flows: dict[str,dict] = field(default_factory=dict)
    observation: ObservationState = field(default_factory=ObservationState)
    profile: PersonalityProfile | None = None
    profile_error: str | None = None
    self_answers: dict[str,str] = field(default_factory=dict)
    confirmations: dict[str,str] = field(default_factory=dict)
    survey_answers: dict[str,dict[str,int]] = field(default_factory=dict)
    survey_results: dict[str,QuestionnaireResult] = field(default_factory=dict)
    survey_contexts: dict[str,str] = field(default_factory=dict)

    def is_stale(self,messages):
        return self.profile is not None and self.profile.fingerprint!=user_fingerprint(messages)

    def record_profile(self,profile):
        if profile.status=='failed':
            self.profile_error=profile.error_code or 'invalid_response'
        else:
            self.profile=profile
            self.profile_error=None


def exploration_paused(decision):
    if decision is None: return False
    if decision.action=='urgent_support': return True
    return any(s.kind in ('self_harm','harm_to_others','other_urgent') and s.current_need in ('immediate_support','clarify') for s in decision.unresolved_safety)


def export_personality_report(state,messages):
    lines=['# 性格倾向观察 · MBTI 风格','','这是探索性记录，不是官方 MBTI 施测、心理诊断或稳定的人格结论。','']
    own=confirmed_type(state.confirmations)
    lines.append('自行确认的偏好：'+(own or '尚未完整确认'))
    if state.profile:
        lines.extend(['','对话参考：'+state.profile.type_hint, '对话已更新，以下保留上次观察。' if state.is_stale(messages) else '以下依据本次分析时的用户文字。'])
        for axis in state.profile.axes:
            lines.extend(['',f'## {AXIS_LABELS[axis.axis][0]}：{axis.leaning}',axis.explanation])
            for evidence in axis.evidence: lines.append('依据：'+evidence.quote)
            for evidence in axis.counter_evidence: lines.append('不同线索：'+evidence.quote)
    if state.self_answers:
        lines.extend(['','## 原创偏好自述（非标准化量表）'])
        for axis,pole in score_self_report(state.self_answers).items(): lines.append(f'{AXIS_LABELS[axis][0]}：{pole}')
        lines.extend(['',describe_self_report(state.self_answers)])
    return '\n'.join(lines)
