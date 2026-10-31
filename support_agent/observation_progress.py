"""Read-only presentation of the existing conversation-observation scheduler."""
from __future__ import annotations

from dataclasses import dataclass

from .observation_scheduler import count_candidates, eligibility_reason,AUTO_FIRST_MESSAGES,AUTO_FIRST_CHARS,AUTO_NEW_MESSAGES


@dataclass(frozen=True)
class ObservationProgress:
    title: str
    detail: str
    fraction: float | None
    candidate_count: int
    candidate_chars: int
    reason: str | None


_BLOCKED_COPY = {
    'off': ('对话观察尚未开启', '可在探索设置中开启对话观察，再继续聊天。'),
    'no_domains': ('先选择观察方向', '在观察设置中选择想探索的方向，再继续聊天。'),
    'unauthorized': ('先完成连接与使用确认', '在 API 设置中核对配置，并完成对话准备与探索同意后继续。'),
    'offline': ('等待连接就绪', '在连接设置中完成连接，再回到聊天。'),
    'paused': ('观察已暂停', '当前先专注于支持对话，暂不整理性格与关系线索。'),
    'pending': ('正在整理已有聊天线索', '已有一项整理正在进行，可继续聊天并稍后查看结果。'),
    'budget': ('本对话观察额度已用完', '可继续聊天，也可查看已有观察。'),
    'unchanged': ('这部分聊天已尝试整理', '继续补充新的具体表达后，再查看观察进展。'),
    'auto_limit': ('本对话自动观察已达上限', '已达到 3 次自动观察上限；可继续聊天、查看已有观察或选择手动整理。'),
}


def observation_progress(state, messages, *, authorized: bool, live: bool, paused: bool) -> ObservationProgress:
    """Describe data accumulation without starting work or changing session state."""
    count, chars = count_candidates(messages)
    manual = state.mode != 'auto'
    reason = eligibility_reason(
        state, messages, manual=manual, authorized=authorized, live=live, paused=paused,
    )
    counts = f'当前有 {count} 条有效表达、{chars} 个非空白字符。'
    if reason in _BLOCKED_COPY:
        title, action = _BLOCKED_COPY[reason]
        return ObservationProgress(title, counts + action, None, count, chars, reason)

    filtering = '过短或重复的消息不计入，继续聊具体的经历和想法即可。'
    if manual:
        fraction = min(count / 2, 1.0)
        title = '已达到手动整理的内容门槛' if reason is None else '正在积累聊天线索'
        detail = f'手动整理需要 2 条有效表达；当前 {count}/2 条、{chars} 个非空白字符。'
        action = '点击“打开观察报告”，再选择“整理当前对话线索”。' if reason is None else filtering
    elif state.automatic_count and state.last_auto_candidate_count > 0:
        new_count = max(0, count - state.last_auto_candidate_count)
        fraction = min(new_count / AUTO_NEW_MESSAGES, 1.0)
        title = '已达到下次自动整理的内容门槛' if reason is None else '继续积累新的聊天线索'
        detail = counts + f'距上次自动整理新增 {new_count}/{AUTO_NEW_MESSAGES} 条有效表达。'
        action = '已满足本次内容触发条件。' if reason is None else filtering
    else:
        fraction = min(count / AUTO_FIRST_MESSAGES, chars / AUTO_FIRST_CHARS, 1.0)
        title = '已达到首次自动整理的内容门槛' if reason is None else '正在积累聊天线索'
        detail = f'首次自动整理需要 {AUTO_FIRST_MESSAGES} 条有效表达且至少 {AUTO_FIRST_CHARS} 个非空白字符；当前 {count}/{AUTO_FIRST_MESSAGES} 条、{chars}/{AUTO_FIRST_CHARS} 字符。'
        action = '已满足本次内容触发条件。' if reason is None else filtering
    return ObservationProgress(title, detail + action, fraction, count, chars, reason)
