"""IPIP public-domain factor markers; project research translation, not validated Chinese."""
from dataclasses import replace
from .psychometrics import Questionnaire, TestItem
from .research_wellbeing_tests import SWLS

# Grouped in official factor-key order; each tuple lists positive then negative items.
_FACTOR_ITEMS = (
    ('extraversion', '外向性', 5, (
        '在聚会中，我是活跃气氛的人。','与人相处时，我感到自在。','我会主动开始交谈。','聚会时，我会和许多不同的人交谈。','我不介意成为注意力的中心。',
        '我不太爱说话。','我倾向于待在不引人注意的位置。','我没有多少话可说。','我不喜欢让别人注意到自己。','在陌生人身边，我很安静。')),
    ('agreeableness', '宜人性', 6, (
        '我对他人感兴趣。','我能体谅他人的感受。','我心肠柔软。','我会抽出时间给他人。','我能感受到他人的情绪。','我让他人感到自在。',
        '我对他人并不怎么感兴趣。','我会侮辱他人。','我对他人的困扰不感兴趣。','我很少关心他人。')),
    ('conscientiousness', '尽责性', 6, (
        '我总是做好准备。','我注意细节。','我会及时做完日常杂事。','我喜欢井然有序。','我按日程安排做事。','我对自己的工作要求严格。',
        '我把自己的东西随处乱放。','我常把事情弄得一团糟。','我经常忘记把东西放回原处。','我会逃避自己的职责。')),
    ('emotional_stability', '情绪稳定性', 2, (
        '大多数时候，我感到放松。','我很少感到忧郁低落。',
        '我很容易感到压力过大。','我会担心各种事情。','我很容易受到困扰。','我很容易心烦或难过。','我的心情经常变化。','我的情绪经常大起大落。','我很容易烦躁。','我经常感到忧郁低落。')),
    ('intellect_imagination', '智性/想象力', 7, (
        '我的词汇丰富。','我的想象力生动丰富。','我有很出色的想法。','我能很快理解事情。','我会使用难懂的词。','我会花时间反思事情。','我有很多点子。',
        '我觉得理解抽象概念有困难。','我对抽象概念不感兴趣。','我的想象力不太丰富。')),
)

IPIP50 = Questionnaire(
    id='ipip50', title='大五人格 · IPIP Factor Markers 50题（研究自译）',
    description='判断每个描述在多大程度上符合平时的你；五个宽维分别呈现。题目按作者计分键分组。',
    items=tuple(TestItem(f'ipip50_{factor_index*10+item_index}', text, dimension, item_index>positive)
        for factor_index,(dimension,label,positive,texts) in enumerate(_FACTOR_ITEMS)
        for item_index,text in enumerate(texts,1)),
    options=('非常不符合','比较不符合','介于符合与不符合之间','比较符合','非常符合'), min_score=1,
    dimension_labels={dimension:label for dimension,label,_,_ in _FACTOR_ITEMS},
    source_name='International Personality Item Pool: Big-Five Factor Markers, five 10-item scales (50 items)',
    source_url='https://ipip.ori.org/newBigFive5broadKey.htm',
    license_notice='IPIP题项与量表属公共领域，可复制、编辑、翻译及用于商业或非商业用途，无需费用或另行许可。https://ipip.ori.org/newPermission.htm；本项目仍限本地非商业研究。',
    translation_note='本项目依据公共领域英文题项制作的研究自译，未经中文信效度验证，不是已验证中文版。来源与计分键于2026-10-29核对。',
    display='mean',
    interpretation='按官方1—5正反向计分，各维10题，原始总分10—50，并列呈现均分1—5。第四维是情绪稳定性：高分代表更稳定，与Mini-IPIP负性情绪倾向方向相反，不能直接混比。智性/想象力不等于智商。不计算人格总分、类型、诊断或百分位。计分：https://ipip.ori.org/newScoringInstructions.htm。',
)

SWLS3 = replace(
    SWLS, id='swls3', title='生活满意度 · SWLS 三题缩略版（研究自译）', items=SWLS.items[:3],
    source_name=SWLS.source_name+'; Kjell & Diener (2021), abbreviated three-item version, doi:10.1080/00223891.2020.1737093',
    interpretation='固定使用原SWLS第1、2、3题，1—7计分，3题求和范围3—21。不能套用5题版5—35的阈值、总分或常模；未验证本项目中文译文。较高分表示本次自报生活满意度较高，不提供诊断或百分位。',
)
