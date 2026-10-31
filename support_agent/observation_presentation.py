"""Shared, authored descriptions of guarded conversational observations."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObservationView:
    level_label: str
    direction_label: str
    summary: str
    alternatives: tuple[str, ...]
    next_question: str


@dataclass(frozen=True)
class _Dimension:
    title: str
    poles: tuple[str, str]
    labels: tuple[str, str]
    meanings: tuple[str, str]
    alternatives: tuple[str, str]
    question: str


_DIMENSIONS = {
    ('mbti', 'EI'): _Dimension(
        '互动与精力恢复', ('E', 'I'), ('E：互动后恢复精力', 'I：独处后恢复精力'),
        ('较常通过与人互动恢复精力、在交流中整理想法', '较常通过独处或安静活动恢复精力、先自行整理想法'),
        ('当时精力不足或临时压力较大，使叙述者需要安静恢复', '交往对象的熟悉程度或场合中的角色要求，改变了叙述者的互动方式'),
        '请对照两次互动结束后的经历：本次案例叙述者之后做了什么、精力怎样变化，哪些条件影响了这些选择？',
    ),
    ('mbti', 'SN'): _Dimension(
        '理解信息的方式', ('S', 'N'), ('S：先留意具体经验', 'N：先联系整体可能性'),
        ('理解事情时较先留意具体事实和已有经验', '理解事情时较先连接可能性、整体联系与意义'),
        ('任务需要准确执行已有步骤，使叙述者更关注具体细节', '问题仍处于探索阶段或涉及熟悉领域，使叙述者更容易联想新的可能性'),
        '面对一个不熟悉的问题时，本次案例叙述者先注意到了哪些信息、怎样理解它，在另一件类似事情中有哪些不同？',
    ),
    ('mbti', 'TF'): _Dimension(
        '取舍时优先考虑的依据', ('T', 'F'), ('T：先核对规则与一致性', 'F：先考虑价值与人的处境'),
        ('取舍时较先核对规则、一致性和可预期结果', '取舍时较先考虑个人重视的事与对人的影响'),
        ('当时的工作或照顾角色要求叙述者优先考虑特定责任', '决定牵涉的对象或后果不同，使叙述者采用了不同的取舍依据'),
        '最近一次两种方案都有得失时，本次案例叙述者怎样取舍、最在意什么，与另一回取舍相比有哪些不同？',
    ),
    ('mbti', 'JP'): _Dimension(
        '安排与应对变化的方式', ('J', 'P'), ('J：先形成计划', 'P：保留调整余地'),
        ('较常先形成计划与节点，再依照安排推进', '较常保留调整余地，随新信息改变安排'),
        ('外部期限或角色要求叙述者提前确定安排', '信息仍在变化或临时压力增加，使叙述者需要保持灵活'),
        '请对照一件提前安排的事和一件临时变化的事：本次案例叙述者怎样决定下一步，哪些安排有用、哪些需要调整？',
    ),
    ('big_five', 'extraversion'): _Dimension(
        '人际参与与活跃程度', ('higher', 'lower'), ('较多主动互动与表达', '较少互动或偏好安静活动'),
        ('较多主动参与互动、表达想法或投入外部活动', '较常选择互动较少或较安静的活动方式'),
        ('活动对象的熟悉程度或场合中的角色要求影响了叙述者的参与', '当时精力、可用时间或临时压力影响了叙述者的活跃程度'),
        '在两次可自行选择参加方式的活动中，本次案例叙述者实际怎样参与、当时想获得什么，熟悉程度有何影响？',
    ),
    ('big_five', 'agreeableness'): _Dimension(
        '分歧中的协调与立场表达', ('higher', 'lower'), ('较先寻求协调', '较先坚持与检视立场'),
        ('分歧中较先寻求协调、照顾双方需要', '分歧中较先坚持立场、检视他人提出的要求'),
        ('关系中的角色要求或权力差异影响了叙述者表达分歧的方式', '当时涉及重要边界或不同利益，使叙述者选择了不同的回应'),
        '最近一次意见不同的经历里，本次案例叙述者如何表达自己的需要并回应分歧，与另一回经历相比有哪些不同？',
    ),
    ('big_five', 'conscientiousness'): _Dimension(
        '计划、跟进与履约方式', ('higher', 'lower'), ('较常规划并持续跟进', '较少依靠固定计划与跟进'),
        ('较常提前规划、跟进进度并完成约定', '较少依靠固定计划或持续的进度追踪来推进事情'),
        ('工作量、可用资源或临时压力影响了叙述者的持续执行', '外部时间表、他人协作或角色要求帮助叙述者保持了进度'),
        '请对照一件按期完成与一件中途调整的任务：本次案例叙述者怎样安排、跟进，哪些条件影响了过程？',
    ),
    ('big_five', 'neuroticism'): _Dimension(
        '压力下的情绪反应与恢复', ('higher', 'lower'), ('压力下感受较易波动', '压力下较平稳或恢复较快'),
        ('压力情境下较易出现担忧、感受波动或较久才恢复', '压力情境下感受较平稳或恢复较快'),
        ('近期睡眠、精力或临时压力影响了叙述者当时的感受', '事件的实际后果与可获得的支持不同，影响了叙述者的恢复过程'),
        '面对两次程度相近的压力时，本次案例叙述者当时有什么感受、多久后发生变化，哪些条件帮助或妨碍了恢复？',
    ),
    ('big_five', 'openness'): _Dimension(
        '接触新想法与经验的方式', ('higher', 'lower'), ('较愿意探索新想法与体验', '较偏好熟悉经验与可用做法'),
        ('较愿意探索新想法、不同体验或抽象联系', '较偏好熟悉经验与具体可用的做法'),
        ('可用资源、尝试成本或当时的角色要求影响了叙述者探索新事物的空间', '主题的熟悉程度或实际兴趣不同，影响了叙述者是否愿意尝试'),
        '面对一次陌生做法或新观点时，本次案例叙述者怎样了解并决定是否尝试，另一次作出不同选择的经历是什么？',
    ),
    ('attachment', 'anxiety'): _Dimension(
        '关系联系不明确时的反应', ('higher', 'lower'), ('较多担心连接并寻求确认', '较能等待并安顿关系担忧'),
        ('联系不明确时较容易担心被忽略、希望获得确认', '联系暂不明确时较能等待，并自行安顿关系中的担忧'),
        ('这段关系的联系安排确实尚不明确，影响了叙述者的反应', '叙述者近期的临时压力或既往经历影响了当时对连接的在意程度'),
        '在这段已明确的关系中，两次联系暂不明确时，本次案例叙述者各自怎样理解、表达需要并照顾自己，哪些具体互动让反应不同？',
    ),
    ('attachment', 'avoidance'): _Dimension(
        '关系中的亲近与求助方式', ('higher', 'lower'), ('较常拉开距离并自行处理', '较能接受亲近并表达需要'),
        ('面对亲近、表达需要或求助时较倾向拉开距离、自己处理', '较能接受亲近、表达需要或寻求支持'),
        ('叙述者当时需要隐私、休息或维护具体边界，影响了亲近方式', '支持是否合适、可用精力或临时压力不同，影响了叙述者是否求助'),
        '在这段已明确的关系中，最近一次需要支持或谈及亲近时，本次案例叙述者实际怎样回应，与另一回不同反应相比有哪些条件不同？',
    ),
}


def _citations(items):
    """Count existing guarded citations, without publishing their raw text."""
    return {
        (item.message_id, item.quote, item.event_id, item.context_kind)
        for item in items
        if all(getattr(item, name, '') for name in ('message_id', 'quote', 'event_id', 'context_kind'))
    }


def _counts(citations):
    return len(citations), len({c[2] for c in citations}), len({c[3] for c in citations})


def _legacy_coverage(observation, dimension, support, counter):
    # Older reports have no guarded case-narrator scope or tentative pole.
    # An old unknown must stay unknown even when many citations are present.
    if getattr(observation, 'subject', 'unknown') != 'self':
        return 'out_of_scope'
    scope = getattr(observation, 'scope', 'unclear')
    direction = getattr(observation, 'direction', 'unknown')
    if scope == 'state' and support:
        return 'state'
    if scope != 'habit':
        return 'none'
    if direction == 'mixed' and support and counter:
        return 'conflicting'
    _, events, contexts = _counts(support)
    if (direction in dimension.poles and len({c[0] for c in support}) >= 3
            and events >= 3 and contexts >= 2):
        return 'supported'
    return 'none'


def _limited_gap(observation, support):
    if getattr(observation, 'scope', 'unclear') != 'habit':
        return '还需确认这些反应是平时习惯还是当次变化。'
    _, events, contexts = _counts(support)
    gaps = []
    if events < 3:
        gaps.append('其他独立事件的对比')
    if contexts < 2:
        gaps.append('不同情境的对照')
    if len({c[0] for c in support}) < 3:
        gaps.append('在其他时间回顾同类经历的材料')
    return '还缺少' + '、'.join(gaps) + '。' if gaps else '还需核对反例与行为背后的考虑。'


def describe_observation(observation) -> ObservationView:
    """Describe a guarded dimension using the same text for UI and export.

    Provider explanations and coverage_reason are deliberately not interpolated.
    The backend owns provenance and coverage; this module owns their wording.
    """
    domain = getattr(observation, 'domain', '')
    dimension = _DIMENSIONS.get((domain, getattr(observation, 'dimension', '')))
    if dimension is None:
        return ObservationView(
            '暂不可用', '维度尚未明确',
            '本次案例叙述者的材料缺少可识别的观察主题与维度，暂时无法作具体解释。', (),
            '请补充本次案例叙述者的一件具体经历：当时发生了什么、实际怎样回应，与另一回经历有什么不同？',
        )

    support = _citations(getattr(observation, 'evidence', ()) or ())
    counter = _citations(getattr(observation, 'counter_evidence', ()) or ())
    quotes, events, contexts = _counts(support | counter)
    counts = f'已核对{quotes}处引文，涉及{events}个事件、{contexts}类情境。'
    coverage = getattr(observation, 'coverage', None)
    if coverage is None:
        coverage = _legacy_coverage(observation, dimension, support, counter)
    if getattr(observation, 'subject', 'unknown') not in ('self', 'case_narrator'):
        coverage = 'out_of_scope'
    if domain == 'attachment' and not getattr(observation, 'relation_id', ''):
        coverage = 'out_of_scope'

    if coverage == 'out_of_scope':
        if domain == 'attachment':
            gap = '还需把本次案例叙述者的具体经历绑定到同一段已明确的关系，并确认叙述对象和互动范围。'
        else:
            gap = '还需确认材料描述的是本次案例叙述者实际经历的行为，而非转述、他人经历或假设。'
        return ObservationView('范围待确认', '暂不解释方向', gap + counts, (), dimension.question)

    subject = '本次案例叙述者在这段已明确的关系中' if domain == 'attachment' else '本次案例叙述者在所述经历中'
    alternatives = tuple(f'一种待核对的可能性是：{value}；目前未证实。' for value in dimension.alternatives)
    if quotes and (coverage == 'state' or getattr(observation, 'scope', 'unclear') == 'state'):
        return ObservationView(
            '当次感受', '不据此判断稳定倾向',
            f'{subject}呈现的是当次感受或反应，关于{dimension.title}仍需其他经历作对比，不能据此解释为稳定倾向。' + counts,
            alternatives, dimension.question,
        )
    if quotes and coverage == 'conflicting':
        return ObservationView(
            '情境差异', '尚不归为单一方向',
            f'{subject}既有{dimension.meanings[0]}的描述，也有{dimension.meanings[1]}的描述；需区分各自发生的条件。' + counts,
            alternatives, dimension.question,
        )

    direction = getattr(observation, 'direction', 'unknown')
    tentative = getattr(observation, 'tentative_direction', 'unknown')
    if quotes and coverage == 'supported' and direction in dimension.poles:
        pole = dimension.poles.index(direction)
        return ObservationView(
            '多次经历支持', dimension.labels[pole],
            f'{subject}，这些经历多次支持{dimension.meanings[pole]}的观察；仍需结合发生条件理解。' + counts,
            alternatives, dimension.question,
        )
    if quotes and coverage == 'limited':
        if getattr(observation, 'scope', 'unclear') == 'habit' and tentative in dimension.poles:
            pole = dimension.poles.index(tentative)
            label = dimension.labels[pole] + '（初步，待核对）'
            meaning = f'显现出{dimension.meanings[pole]}的初步线索'
        else:
            label = '倾向尚不明确'
            meaning = f'有与{dimension.title}相关的具体反应，但方向尚未明确'
        return ObservationView(
            '初步线索', label,
            f'{subject}，{meaning}。' + counts + _limited_gap(observation, support) + '这些材料尚不能解释为稳定倾向。',
            alternatives, dimension.question,
        )

    gap = ('尚缺可核对的具体行为原话，需要补充发生了什么、实际怎样回应。' if not quotes
           else f'关于{dimension.title}的方向尚未明确，需要补充其他经历、反例及当时的考虑。')
    return ObservationView('线索不足', '倾向尚不明确', f'{subject}，{gap}' + counts, (), dimension.question)
