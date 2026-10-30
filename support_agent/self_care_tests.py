"""Author-sourced SCS forms and adult trait MAAS, with project Chinese translations.

The translations below have not been validated. Source PDFs provide permission,
item order and scoring keys; no existing Chinese validation is claimed. SCS-SF
is the author's reordered 12-item subset, and is reported only as an overall mean.
"""

from .psychometrics import CompositeSpec, Questionnaire, TestItem


_SCS_DIMENSIONS = {
    'self_kindness': '善待自己',
    'self_judgment_reversed': '较少自我批评（反向计分）',
    'common_humanity': '共同人性',
    'isolation_reversed': '较少孤立感（反向计分）',
    'scs_mindfulness': '平衡觉察',
    'over_identification_reversed': '较少过度认同（反向计分）',
}
_SCS_COMPOSITES = (
    CompositeSpec('self_compassion', '自我关怀总均分', tuple(_SCS_DIMENSIONS)),
)
_SCS_OPTIONS = (
    '几乎从不', '较少（项目补充锚点）', '有时（项目补充锚点）',
    '经常（项目补充锚点）', '几乎总是',
)
_SCS_DESCRIPTION = (
    '请根据你在困难时期通常如何对待自己，回答每种情况出现的频率。'
    '按真实经历作答，不必选择你认为自己应该有的表现。'
    '原量表只为1和5提供“几乎从不／几乎总是”文字锚点；'
    '2—4的频率用语由本项目补充，未经过验证。'
)
_SCS_TRANSLATION = (
    '依据作者公开英文题项制作的本项目中文研究自译，未经信效度验证，'
    '不是已验证中文版。原作者要求新译本按 Neff 等（2019）的双因素探索性'
    '结构方程模型（bifactor ESEM）检验因子结构；本项目尚未完成该验证。'
    '原量表仅标注1和5两个端点，2—4的中文频率锚点为本项目补充。'
)


SCS26 = Questionnaire(
    id='scs26',
    title='自我关怀 · SCS（26题）',
    description=_SCS_DESCRIPTION,
    items=(
        TestItem('scs26_1', '我对自己的缺点和不足持否定、批评的态度。', 'self_judgment_reversed', True),
        TestItem('scs26_2', '情绪低落时，我往往会反复纠结于所有不如意之处。', 'over_identification_reversed', True),
        TestItem('scs26_3', '事情不顺利时，我把遇到的困难看作每个人在生活中都会经历的一部分。', 'common_humanity'),
        TestItem('scs26_4', '想到自己的不足时，我往往会感到自己与周围的人和世界更加隔绝。', 'isolation_reversed', True),
        TestItem('scs26_5', '感到情感上的痛苦时，我会试着温柔地关爱自己。', 'self_kindness'),
        TestItem('scs26_6', '在对自己重要的事情上失败时，我会被自己不够好的感受淹没。', 'over_identification_reversed', True),
        TestItem('scs26_7', '情绪低落时，我会提醒自己，世界上还有许多人正有着和我相似的感受。', 'common_humanity'),
        TestItem('scs26_8', '处境十分艰难时，我往往会对自己很苛刻。', 'self_judgment_reversed', True),
        TestItem('scs26_9', '遇到让我难受的事时，我会试着保持情绪平衡。', 'scs_mindfulness'),
        TestItem('scs26_10', '当我觉得自己在某方面不够好时，我会试着提醒自己，大多数人也有过这种感受。', 'common_humanity'),
        TestItem('scs26_11', '对自己性格中不喜欢的部分，我会缺乏包容和耐心。', 'self_judgment_reversed', True),
        TestItem('scs26_12', '度过非常艰难的时期时，我会给予自己所需要的关怀和温柔。', 'self_kindness'),
        TestItem('scs26_13', '情绪低落时，我往往觉得大多数其他人可能都比我幸福。', 'isolation_reversed', True),
        TestItem('scs26_14', '遇到令人痛苦的事时，我会试着用平衡的眼光看待当时的处境。', 'scs_mindfulness'),
        TestItem('scs26_15', '我会试着把自己的失败看作身为人都会经历的一部分。', 'common_humanity'),
        TestItem('scs26_16', '看到自己身上不喜欢的部分时，我会贬低自己。', 'self_judgment_reversed', True),
        TestItem('scs26_17', '在对自己重要的事情上失败时，我会试着把事情放在更全面的背景下看待。', 'scs_mindfulness'),
        TestItem('scs26_18', '我十分挣扎时，往往会觉得其他人的日子一定比我轻松。', 'isolation_reversed', True),
        TestItem('scs26_19', '经历痛苦时，我会善待自己。', 'self_kindness'),
        TestItem('scs26_20', '遇到让我难受的事时，我会被自己的情绪裹挟。', 'over_identification_reversed', True),
        TestItem('scs26_21', '经历痛苦时，我对自己可能会有些冷漠。', 'self_judgment_reversed', True),
        TestItem('scs26_22', '情绪低落时，我会试着以好奇和开放的态度面对自己的感受。', 'scs_mindfulness'),
        TestItem('scs26_23', '我能包容自己的缺点和不足。', 'self_kindness'),
        TestItem('scs26_24', '遇到令人痛苦的事时，我往往会把事情夸大。', 'over_identification_reversed', True),
        TestItem('scs26_25', '在对自己重要的事情上失败时，我往往觉得只有自己在承受这样的失败。', 'isolation_reversed', True),
        TestItem('scs26_26', '对自己性格中不喜欢的部分，我会试着给予理解和耐心。', 'self_kindness'),
    ),
    options=_SCS_OPTIONS,
    min_score=1,
    dimension_labels=dict(_SCS_DIMENSIONS),
    source_name='Neff (2003), Self-Compassion Scale；作者信息、许可及计分文件',
    source_url='https://self-compassion.org/wp-content/uploads/2021/03/SCS-information.pdf',
    license_notice=(
        '作者 Kristin Neff 的许可函允许 SCS 用于任何目的，并要求引用 Neff (2003), '
        'Development and validation of a scale to measure self-compassion, Self and Identity, 2, 223–250。'
        '作者也允许翻译，要求按 Neff 等（2019）的分析方法验证因子结构；'
        '本项目提供未验证的中文研究自译，尚未完成所要求的验证。'
    ),
    translation_note=_SCS_TRANSLATION,
    interpretation=(
        '先将自我批评、孤立感、过度认同题目按6减原始分反向计分，再计算六个维度各自的题均分；'
        '自我关怀总均分是六个维度均分的等权平均，不是26道题直接平均，范围1—5。'
        '本报告所有维度均按较高分表示更多自我关怀的方向呈现；'
        '三个反向维度的高分分别表示较少自我批评、较少孤立感、较少过度认同。'
        '总均分与六个维度分别展示，不使用临床阈值、百分位或诊断标签。'
    ),
    composites=_SCS_COMPOSITES,
    show_dimensions=True,
)


# Author's SCS-SF information PDF, final page: short-form number → full number.
_SCS12_FULL_NUMBERS = (6, 26, 14, 13, 15, 12, 9, 25, 2, 10, 1, 11)

SCS12 = Questionnaire(
    id='scs12',
    title='自我关怀简版 · SCS-SF（12题）',
    description=(
        _SCS_DESCRIPTION + '此简版只报告整体自我关怀均分。'
        '作者指出每个分量表只有两题、可靠性较低，因此不单独解释六个维度。'
    ),
    items=tuple(
        TestItem(f'scs12_{short_number}', item.text, item.dimension, item.reverse)
        for short_number, full_number in enumerate(_SCS12_FULL_NUMBERS, 1)
        for item in (SCS26.items[full_number - 1],)
    ),
    options=_SCS_OPTIONS,
    min_score=1,
    dimension_labels=dict(_SCS_DIMENSIONS),
    source_name='Raes, Pommier, Neff & Van Gucht (2011), SCS-SF；作者信息、许可及计分文件',
    source_url='https://self-compassion.org/wp-content/uploads/2021/03/SCS-SF-information.pdf',
    license_notice=(
        '作者 Kristin Neff 的许可函允许 SCS-SF 用于任何目的，并要求引用 Raes, Pommier, '
        'Neff & Van Gucht (2011), Construction and factorial validation of a short form of '
        'the Self-Compassion Scale, Clinical Psychology & Psychotherapy, 18, 250–255。'
        '作者也允许翻译，要求按 Neff 等（2019）的分析方法验证因子结构；'
        '本项目提供未验证的中文研究自译，尚未完成所要求的验证。'
    ),
    translation_note=_SCS_TRANSLATION + '12题依作者短版到长版的对应表选取并重新排序。',
    interpretation=(
        '负向题按6减原始分计分后，先计算内部六维度的题均分，再等权平均得到自我关怀总均分（1—5）。'
        '较高分表示本次回答反映更多自我关怀。'
        '简版每个维度只有两题，作者不推荐用其分量表作解释，因此只报告总均分并保留原始作答。'
        '不使用临床阈值、百分位或诊断标签。'
    ),
    composites=_SCS_COMPOSITES,
    show_dimensions=False,
)


MAAS15 = Questionnaire(
    id='maas15',
    title='正念注意觉察 · MAAS（成人特质版15题）',
    description=(
        '以下描述涉及你当前日常生活中的体验，请逐题独立判断出现的频率，按实际经历作答。'
        '此处使用成人特质版15题。1表示“几乎总是”，6表示“几乎从不”；'
        '题目描述走神或缺少觉察的体验，因此数字较高表示这些体验出现较少。'
        '若某题情境不适用，可退出，不必勉强选择。'
    ),
    items=tuple(
        TestItem(f'maas15_{number}', text, 'mindful_attention')
        for number, text in enumerate((
            '我可能正经历某种情绪，却要过一段时间才察觉到。',
            '我会因为粗心、没有留意或想着别的事情，而打坏或打翻东西。',
            '我觉得很难把注意力持续放在此刻正在发生的事情上。',
            '我往往只顾快步赶往目的地，没有留意沿途的体验。',
            '身体的紧绷或不适常要强烈到引起我的注意，我才会察觉。',
            '第一次听到别人介绍自己的名字后，我几乎马上就忘了。',
            '我仿佛处在“自动运行”中，不太清楚自己正在做什么。',
            '我匆忙完成各种活动，没有真正留心正在做的事。',
            '我过于专注想达成的目标，以至于忽略此刻为目标正在做的事。',
            '我会自动地完成工作或任务，没有觉察自己正在做什么。',
            '我发现自己一边只分出部分注意力听别人说话，一边做着其他事情。',
            '我会像开了“自动驾驶”一样开车到某处，之后才纳闷自己为什么来到这里。',
            '我发现自己满脑子都在想着未来或过去。',
            '我发现自己在做事时没有用心留意。',
            '我吃零食时，没有觉察自己正在吃东西。',
        ), 1)
    ),
    options=('几乎总是', '非常频繁', '比较频繁', '不太频繁', '很少', '几乎从不'),
    min_score=1,
    dimension_labels={'mindful_attention': '正念注意觉察'},
    source_name='Brown & Ryan (2003), MAAS adult trait version；作者研究工具页所链原始文件',
    source_url='https://kirkwarrenbrown.com/s/MAAS-trait-research-ready-intro-3cd9.pdf',
    license_notice=(
        'Kirk Warren Brown 在作者研究工具页所链成人特质版文件中明确说明 trait MAAS 属于公共领域'
        '（public domain），研究或临床用途不需要特别许可。'
        '引用 Brown & Ryan (2003), The benefits of being present: Mindfulness and its role in '
        'psychological well-being, Journal of Personality and Social Psychology, 84, 822–848。'
        '本项目中文研究自译尚未经信效度验证，不代表作者验证或认可。'
    ),
    translation_note=(
        '依据作者公开的成人特质版15题英文原文制作的本项目中文研究自译，'
        '未经信效度验证，不冒称已验证中文版。题项、顺序和六级频率方向依原版保留。'
        '来源入口：https://kirkwarrenbrown.com/tools-for-researchers 。'
    ),
    interpretation=(
        '15个原始作答直接求均值，范围1—6；所有题目均不再反向计分。'
        '原选项已按1“几乎总是”至6“几乎从不”排列，因此较高均分表示较多正念注意与觉察。'
        '只描述本次日常体验，不将分数转为临床结论、诊断阈值或百分位。'
    ),
)
