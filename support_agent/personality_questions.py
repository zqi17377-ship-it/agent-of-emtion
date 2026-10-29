"""Original daily-preference reflection items, not an official or validated test.

Answers describe the user's own choices. They do not measure personality,
mental health, ability, or confidence, and must not be filled from chat inference.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    id: str
    axis: str
    prompt: str
    left_label: str
    right_label: str
    left_pole: str
    right_pole: str


CHOICE_UNSURE = "不确定 / 看情况"

QUESTION_ITEMS: tuple[Question, ...] = (
    Question(
        "ei_1", "EI", "日常忙碌过后，如果可以自由安排休息，你通常更想怎样恢复精力？",
        "和熟悉的人聊聊或一起活动", "独处，做些自己的事", "E", "I",
    ),
    Question(
        "ei_2", "EI", "遇到一个想讨论的新点子时，你平时更习惯怎样整理想法？",
        "边和别人交流边梳理", "先独自想一想，再决定怎样分享", "E", "I",
    ),
    Question(
        "sn_1", "SN", "了解一项不熟悉的日常活动时，你通常更想先接触哪类信息？",
        "具体例子、步骤和实际细节", "整体思路、关联和可能的变化", "S", "N",
    ),
    Question(
        "sn_2", "SN", "接触一个新话题时，哪类内容通常更容易吸引你的注意？",
        "已有的事实和可观察到的细节", "这些信息能延伸出的联系和可能性", "S", "N",
    ),
    Question(
        "tf_1", "TF", "当几个日常选项各有取舍时，你通常先用什么来比较？",
        "可一致运用的标准和各自的理由", "自己和相关的人重视什么", "T", "F",
    ),
    Question(
        "tf_2", "TF", "和他人一起作普通决定时，你通常先从哪个角度组织自己的建议？",
        "各个方案的依据和一致的判断原则", "各个方案与相关人的价值取向是否契合", "T", "F",
    ),
    Question(
        "jp_1", "JP", "安排一个自由的休息日时，你平时更偏好怎样开始？",
        "先选定主要安排和大致顺序", "先保留选择，再随当时兴趣展开", "J", "P",
    ),
    Question(
        "jp_2", "JP", "处理几件时间宽裕的日常小事时，你通常更喜欢怎样安排？",
        "先定下顺序，按安排推进", "边做边看情况，随时调整顺序", "J", "P",
    ),
)

_AXIS_POLES = {"EI": ("E", "I"), "SN": ("S", "N"), "TF": ("T", "F"), "JP": ("J", "P")}
_QUESTIONS_BY_ID = {question.id: question for question in QUESTION_ITEMS}


def score_self_report(answers: dict[str, str]) -> dict[str, str]:
    """Summarize explicit answers without numeric scores or filling gaps.

    An axis needs both answers and agreement to return a pole. Two different
    poles return ``mixed``; missing or explicitly unsure answers return
    ``unknown``. Unknown question IDs and choices outside an item's poles or
    ``unknown`` raise ValueError. Display labels are not answer values.
    """
    for question_id, answer in answers.items():
        question = _QUESTIONS_BY_ID.get(question_id)
        if question is None:
            raise ValueError(f"Unknown question ID: {question_id!r}")
        if answer not in (question.left_pole, question.right_pole, "unknown"):
            raise ValueError(f"Invalid answer for question {question_id!r}: {answer!r}")

    result = {}
    for axis in _AXIS_POLES:
        choices = [answers.get(question.id, "unknown") for question in QUESTION_ITEMS if question.axis == axis]
        if "unknown" in choices:
            result[axis] = "unknown"
        elif choices[0] == choices[1]:
            result[axis] = choices[0]
        else:
            result[axis] = "mixed"
    return result


def confirmed_type(preferences: dict[str, str]) -> str | None:
    """Format four explicit self-confirmed choices; never infer missing poles.

    Callers must supply the user's confirmed preferences, rather than chat
    estimates or an automatically accepted self-report summary.
    """
    choices = []
    for axis, poles in _AXIS_POLES.items():
        choice = preferences.get(axis)
        if choice not in poles:
            return None
        choices.append(choice)
    return "".join(choices)


def describe_self_report(answers: dict[str, str]) -> str:
    """Describe explicit original-question choices without assigning a type."""
    descriptions = {
        'EI': ('社交能量', {'E': '你在这两题都选择了交流中梳理或与熟悉的人一起活动。', 'I': '你在这两题都选择了先独自整理想法或独处中恢复。'}, '回想最近一次休息：什么活动实际让你恢复了精力？'),
        'SN': ('信息关注', {'S': '你在这两题都优先选择具体例子、步骤与已有事实。', 'N': '你在这两题都优先选择整体关联与新的可能性。'}, '遇到新任务时，先看具体例子还是整体思路更能帮助你开始？'),
        'TF': ('决策偏好', {'T': '你在这两题都优先选择一致标准和理由。', 'F': '你在这两题都优先考虑相关人的价值与感受。'}, '回顾一个实际决定：你如何兼顾判断理由与相关人的需要？'),
        'JP': ('安排方式', {'J': '你在这两题都更喜欢先定安排和大致顺序。', 'P': '你在这两题都更喜欢保留选择并随情况调整。'}, '哪些安排需要提前确定，哪些部分保留弹性更适合你？'),
    }
    lines = ['### 本次偏好解读', '', '以下依据八题原创问答中你明确选择的内容，供核对日常习惯；不能据此确定稳定人格类型。']
    for axis, pole in score_self_report(answers).items():
        label, texts, prompt = descriptions[axis]
        explanation = texts.get(pole, '两题选择了不同方向，可能随不同情境变化，先保留两种线索。' if pole == 'mixed' else '信息不足：存在未回答或不确定选项，暂不归类。')
        lines.extend(['', '**'+label+'**：'+explanation, '可以想一想：'+prompt])
    return '\n'.join(lines)
