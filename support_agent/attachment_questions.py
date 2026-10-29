"""Original relationship reflection items; not a validated attachment scale.

These Chinese items were written for this project. They are neither ECR-R nor
ECR-RS items or translations, and must not be presented under either scale name.
The linked research page supplies theoretical background only.
"""

from __future__ import annotations

from .psychometrics import Questionnaire, QuestionnaireResult, TestItem


ATTACHMENT_EXPLORATION = Questionnaire(
    id='attachment_exploration',
    title='关系中的依恋倾向探索（原创练习）',
    description=(
        '请先选定一位与你有重要情感联系的人，例如伴侣、家人或亲近朋友。'
        '以下所有题目中的“对方”都指同一个人；请根据最近一个月你在这段特定关系中的通常感受作答。'
        '不要把不同关系混在一起。若没有合适的关系情境或题目不适用，可以退出，不必勉强选择。'
        '这是未经信效度验证的原创自我反思练习，不是正式心理量表。'
    ),
    items=(
        TestItem(
            'attachment_anxiety_1',
            '对方结束一次见面却没提下次安排时，我会反复猜测这段关系是不是变淡了。',
            'anxiety',
        ),
        TestItem(
            'attachment_anxiety_2',
            '对方因为自己的事情忙碌时，我容易把这种忙碌理解为自己不再重要。',
            'anxiety',
        ),
        TestItem(
            'attachment_anxiety_3',
            '即使刚得到肯定，我仍会很快想再次确认自己在对方心里的位置。',
            'anxiety',
        ),
        TestItem(
            'attachment_anxiety_4',
            '我们对同一件事看法不一致时，我仍能相信这段关系不会因此马上失去。',
            'anxiety', reverse=True,
        ),
        TestItem(
            'attachment_anxiety_5',
            '等待对方回应一件重要的事时，担心被冷落会挤占我处理其他事情的注意力。',
            'anxiety',
        ),
        TestItem(
            'attachment_anxiety_6',
            '对方暂时需要自己的空间时，我通常能安心等到双方合适的时候再联系。',
            'anxiety', reverse=True,
        ),
        TestItem(
            'attachment_avoidance_1',
            '遇到难处而对方想陪我一起面对时，我的第一反应是把事情收回去自己处理。',
            'avoidance',
        ),
        TestItem(
            'attachment_avoidance_2',
            '一次深入交谈之后，即使交流很愉快，我也常想刻意拉开一些距离。',
            'avoidance',
        ),
        TestItem(
            'attachment_avoidance_3',
            '当对方想了解我的脆弱或顾虑时，我会把话题转向不那么私人的内容。',
            'avoidance',
        ),
        TestItem(
            'attachment_avoidance_4',
            '我可以把尚未想明白的烦恼告诉对方，允许对方参与我的感受。',
            'avoidance', reverse=True,
        ),
        TestItem(
            'attachment_avoidance_5',
            '即使希望得到安慰，我也常选择让对方以为我不需要支持。',
            'avoidance',
        ),
        TestItem(
            'attachment_avoidance_6',
            '做涉及我们两个人的重要决定时，我愿意把自己的需要摊开来一起商量。',
            'avoidance', reverse=True,
        ),
    ),
    options=('很不符合', '不太符合', '介于两者之间', '比较符合', '很符合'),
    min_score=1,
    dimension_labels={'anxiety': '关系焦虑', 'avoidance': '亲近回避'},
    source_name='本项目原创题目；依恋双维度理论背景参考 Fraley 的关系结构研究页面',
    source_url='https://labs.psychology.illinois.edu/~rcfraley/measures/relstructures.htm',
    license_notice=(
        '这 12 道中文题目由本项目原创，可随项目使用与修改；'
        '未复制或翻译 ECR-R、ECR-RS 题项，不是上述量表的官方或授权版本。'
        '尚未经信效度验证。所链接页面仅提供理论背景，不代表其作者认可本练习。'
    ),
    translation_note='本项目直接撰写的原创中文题目，不是任何现有量表的中文译本。',
    display='mean',
    interpretation=(
        '分别查看关系焦虑与亲近回避的题均分（1—5）。分数只描述本次对所选关系的回答，'
        '不合并成总分，不作百分比、常模排名或临床判断。'
    ),
)


def attachment_pattern(result: QuestionnaireResult) -> tuple[str, str]:
    """Describe this exercise's answer pattern using a stated midpoint heuristic."""
    if (
        result.test_id != ATTACHMENT_EXPLORATION.id
        or set(result.dimensions) != {'anxiety', 'avoidance'}
    ):
        raise ValueError('An attachment exploration result is required.')
    anxiety = result.dimensions['anxiety'].mean
    avoidance = result.dimensions['avoidance'].mean
    if 2.5 <= anxiety <= 3.5 or 2.5 <= avoidance <= 3.5:
        label = '混合或暂不清晰的应答倾向'
    elif anxiety < 2.5 and avoidance < 2.5:
        label = '较接近安全的应答倾向'
    elif anxiety > 3.5 and avoidance < 2.5:
        label = '较多关系焦虑的应答倾向'
    elif anxiety < 2.5 and avoidance > 3.5:
        label = '较多亲近回避的应答倾向'
    else:
        label = '关系焦虑与亲近回避并存的应答倾向'
    explanation = (
        '这只是本原创练习的中点启发式规则：任一题均分落在 2.5—3.5（含边界）时暂不归类，'
        '其余回答仅按两个维度位于中点哪一侧描述。该规则及其边界未经验证，'
        '不是有效的测量阈值、心理诊断或稳定类型。请同时查看两个维度的原始得分，'
        '并结合所选关系与近期处境理解。'
    )
    return label, explanation
