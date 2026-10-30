"""Research self-translations of primary-source relationship and risk scales.

ECR numbering follows Fraley's administration page, not the IRT item-bank IDs.
DOSPERT follows the 2006 paper's Appendix A.1 risk-taking (RT) form only.
These definitions do not assign attachment types or combine risk domains.
"""

from .psychometrics import Questionnaire, TestItem


_AGREEMENT7 = (
    '非常不同意', '不同意', '有些不同意', '既不赞同也不反对',
    '有些同意', '同意', '非常同意',
)

_ECR_TRANSLATION_NOTE = (
    '依据作者公开英文题项制作的项目研究自译，未经中文心理测量验证，'
    '不是已验证中文版。采用原1—7分端点；中间选项为项目中文表述，'
    '4表示既不赞同也不反对。'
)

# Official administration order: anxiety 1-18, avoidance 19-36.
_ECR_R36_TEXTS = (
    '我害怕失去伴侣对我的爱。',
    '我经常担心伴侣不愿继续和我在一起。',
    '我经常担心伴侣并不真正爱我。',
    '我担心亲密伴侣对我的在意，不如我对他们的在意那么多。',
    '我经常希望伴侣对我的感情能和我对伴侣的感情一样强烈。',
    '我为自己的亲密关系担心很多。',
    '伴侣不在眼前时，我担心伴侣可能会对别人产生兴趣。',
    '当我向亲密伴侣表达感情时，我害怕他们对我没有同样的感情。',
    '我很少担心伴侣会离开我。',
    '我的亲密伴侣让我怀疑自己。',
    '我并不经常担心被抛弃。',
    '我发现伴侣并不像我希望的那样愿意和我亲近。',
    '有时亲密伴侣对我的感情会改变，却没有明显的原因。',
    '我想要非常亲近的愿望，有时会把别人吓退。',
    '我害怕亲密伴侣真正了解我以后，就不会喜欢真实的我。',
    '无法从伴侣那里得到我需要的关爱和支持，会让我生气。',
    '我担心自己比不上别人。',
    '我的伴侣似乎只有在我生气时才会注意我。',
    '我宁愿不向伴侣表露内心深处的感受。',
    '与伴侣分享我私人的想法和感受，会让我觉得自在。',
    '我发现很难让自己依赖亲密伴侣。',
    '与亲密伴侣亲近时，我感到非常自在。',
    '向亲密伴侣敞开心扉会让我觉得不自在。',
    '我宁愿不与亲密伴侣过于亲近。',
    '当亲密伴侣想要和我非常亲近时，我会感到不自在。',
    '我发现与伴侣亲近是比较容易的。',
    '对我来说，与伴侣亲近并不困难。',
    '我通常会和伴侣讨论自己的问题和担忧。',
    '在有需要时向亲密伴侣求助，对我是有帮助的。',
    '我几乎什么事都会告诉伴侣。',
    '我会和伴侣一起商量事情。',
    '当伴侣和我过于亲近时，我会紧张。',
    '依赖亲密伴侣会让我觉得自在。',
    '我发现依赖亲密伴侣是容易的。',
    '对我来说，向伴侣表达亲昵是容易的。',
    '我的伴侣真正理解我和我的需要。',
)

ECR_R36 = Questionnaire(
    id='ecr_r36',
    title='亲密关系依恋 · ECR-R（36题）',
    description=(
        '请根据你平时亲密伴侣关系的一般感受作答，考虑你通常如何体验亲密关系，'
        '而不限于当前这段关系或最近一个月。逐项选择你赞同或不赞同的程度。'
    ),
    items=tuple(
        TestItem(
            f'ecr_r36_{number}', text,
            'anxiety' if number <= 18 else 'avoidance',
            number in {9, 11, 20, 22, 26, 27, 28, 29, 30, 31, 33, 34, 35, 36},
        )
        for number, text in enumerate(_ECR_R36_TEXTS, 1)
    ),
    options=_AGREEMENT7,
    min_score=1,
    dimension_labels={
        'anxiety': '依恋焦虑（越高越焦虑）',
        'avoidance': '亲近回避（越高越回避）',
    },
    source_name='Fraley, Waller & Brennan (2000), Experiences in Close Relationships-Revised',
    source_url='https://labs.psychology.illinois.edu/~rcfraley/measures/ecrritems.htm',
    license_notice=(
        '作者FAQ允许无需另行联系的非商业研究使用，并允许为研究修改题项：'
        'https://labs.psychology.illinois.edu/~rcfraley/measures/ecrr.htm 。'
        '本项目仅据此用于本地非商业研究；商业使用须获得作者许可。'
    ),
    translation_note=_ECR_TRANSLATION_NOTE,
    display='mean',
    interpretation=(
        '分别显示依恋焦虑与亲近回避的18题均分，范围均为1—7；'
        '较高分分别表示更多对伴侣可依赖性和回应的担忧、更多对亲近和依赖的不自在。'
        '两维独立解读，不合成总分，不用固定分界判定依恋类型，也不是诊断或人群百分位。'
    ),
)

# Relationship-specific items from Fraley's ECR-RS page, not global items.
ECR_RS9 = Questionnaire(
    id='ecr_rs9',
    title='跨关系依恋 · ECR-RS（每个对象9题）',
    description=(
        '先选择一个关系对象，再针对你与这一位对象的关系回答全部9题。'
        '题目中的“这个人”始终指这位对象；母亲或父亲也可指承担相应角色的人。'
        '若选择亲密伴侣而目前没有伴侣，可回想最近一段有意义的关系；'
        '若从未有过，可想象这样的关系。每次仅记录所选关系，不自动合并多个对象。'
    ),
    items=tuple(
        TestItem(
            f'ecr_rs9_{number}', text,
            'avoidance' if number <= 6 else 'anxiety', number <= 4,
        )
        for number, text in enumerate((
            '在有需要时向这个人求助，对我是有帮助的。',
            '我通常会和这个人讨论自己的问题和担忧。',
            '我会和这个人一起商量事情。',
            '我发现依赖这个人是容易的。',
            '向这个人敞开心扉会让我觉得不自在。',
            '我宁愿不向这个人表露内心深处的感受。',
            '我经常担心这个人并不真正关心我。',
            '我害怕这个人可能会抛弃我。',
            '我担心这个人对我的在意，不如我对这个人的在意那么多。',
        ), 1)
    ),
    options=_AGREEMENT7,
    min_score=1,
    dimension_labels={
        'avoidance': '对所选对象的回避（越高越回避）',
        'anxiety': '对所选对象的焦虑（越高越焦虑）',
    },
    source_name=(
        'Fraley, Heffernan, Vicary & Brumbaugh (2011), '
        'Experiences in Close Relationships-Relationship Structures'
    ),
    source_url='https://labs.psychology.illinois.edu/~rcfraley/measures/relstructures.htm',
    license_notice=(
        '作者ECR-RS页面明确允许翻译，并将其介绍为可针对单一关系的ECR-R九题版本。'
        '本项目结合其所链接ECR-R FAQ的非商业研究使用与修改说明，'
        '仅用于本地非商业研究；此为跨页面研究许可依据，RS页未单列完整使用许可。'
        '商业使用须另核许可。FAQ：'
        'https://labs.psychology.illinois.edu/~rcfraley/measures/ecrr.htm'
    ),
    translation_note=(
        _ECR_TRANSLATION_NOTE + '本版本冻结2011年1—7分量尺，'
        '不与作者后续采用的1—5分版本混用。'
    ),
    display='mean',
    interpretation=(
        '仅针对所选关系显示回避6题均分与焦虑3题均分，范围均为1—7；'
        '较高分分别表示面对这个人时更多亲近回避、更多担心被忽视或抛弃。'
        '两维独立解读，不合成总分或固定依恋类型，也不把一个对象的结果推广至所有关系。'
    ),
    context_options=('母亲', '父亲', '亲密伴侣', '最亲近的朋友'),
)


# 2006 Appendix A.1 labels: E, F, H/S, R, S; all RT items are forward keyed.
# Item 21 uses "secure" (not the earlier "prestigious"); retain $200 at item 30.
DOSPERT30 = Questionnaire(
    id='dospert30',
    title='分领域风险选择 · DOSPERT（30题）',
    description=(
        '请设想自己处在题目描述的情境中，并且确实可以选择是否参与该行为。'
        '回答你采取这种行为的可能性；这里询问行为意向，不是你认为行为有多危险。'
    ),
    items=tuple(
        TestItem(f'dospert30_{number}', text, dimension)
        for number, (text, dimension) in enumerate((
            ('承认自己的喜好与一位朋友不同。', 'risk_social'),
            ('到荒野露营。', 'risk_recreational'),
            ('拿出一天的收入投注赛马。', 'risk_financial'),
            ('将年收入的10%投资于中等成长型共同基金。', 'risk_financial'),
            ('在社交聚会中大量饮酒。', 'risk_health_safety'),
            ('申报个人所得税时，使用一些可能有问题的扣除项目。', 'risk_ethical'),
            ('在一个重要问题上与权威人物意见相左。', 'risk_social'),
            ('拿出一天的收入参与高额赌注的扑克游戏。', 'risk_financial'),
            ('与已婚的人发生婚外情。', 'risk_ethical'),
            ('将别人的工作成果冒充为自己的。', 'risk_ethical'),
            ('滑下一条难度超出自己能力的滑雪道。', 'risk_recreational'),
            ('将年收入的5%投资于一只投机性很强的股票。', 'risk_financial'),
            ('在春季水位较高时进行激流漂流。', 'risk_recreational'),
            ('拿出一天的收入押注一场体育赛事的结果。', 'risk_financial'),
            ('在没有采取防护措施的情况下发生性行为。', 'risk_health_safety'),
            ('把一位朋友的秘密透露给别人。', 'risk_ethical'),
            ('开车时不系安全带。', 'risk_health_safety'),
            ('将年收入的10%投资于一项新的创业项目。', 'risk_financial'),
            ('参加跳伞课程。', 'risk_recreational'),
            ('骑摩托车时不戴头盔。', 'risk_health_safety'),
            ('选择自己真正喜欢的职业，而放弃一份更稳定的职业。', 'risk_social'),
            ('在工作会议中，就一个不受欢迎的议题坦率表达自己的看法。', 'risk_social'),
            ('不涂防晒用品就进行日光浴。', 'risk_health_safety'),
            ('从一座高桥上进行蹦极。', 'risk_recreational'),
            ('驾驶一架小型飞机。', 'risk_recreational'),
            ('夜间独自步行穿过城中不安全的区域回家。', 'risk_health_safety'),
            ('搬到远离大家庭的一座城市。', 'risk_social'),
            ('在三十五岁左右开始一种新的职业。', 'risk_social'),
            ('出门办事时，把年幼的孩子独自留在家中。', 'risk_ethical'),
            ('捡到一个装有200美元的钱包后不归还。', 'risk_ethical'),
        ), 1)
    ),
    options=('极不可能', '较不可能', '有些不可能', '不确定', '有些可能', '较可能', '极有可能'),
    min_score=1,
    dimension_labels={
        'risk_ethical': '伦理情境中的风险行为意向',
        'risk_financial': '财务情境中的风险行为意向',
        'risk_health_safety': '健康安全风险行为意向',
        'risk_recreational': '娱乐活动风险行为意向',
        'risk_social': '社交情境中的风险行为意向',
    },
    source_name=(
        'Blais & Weber (2006), A Domain-Specific Risk-Taking (DOSPERT) scale '
        'for adult populations, Judgment and Decision Making, 1, 33–47, Appendix A.1'
    ),
    source_url=(
        'https://www.cambridge.org/core/journals/judgment-and-decision-making/article/'
        'domainspecific-risktaking-dospert-scale-for-adultpopulations/'
        '419BDAAF215313A7EE216F51F38AD205'
    ),
    license_notice=(
        '出版社将原论文明确标为CC BY 3.0，允许署名后的使用与改编：'
        'https://creativecommons.org/licenses/by/3.0/ 。'
        '本项目依据论文附录A.1制作中文研究自译，已更改语言，保留作者及来源署名；'
        '不表示作者认可本项目。哥伦比亚大学作者材料页另明确允许署名使用：'
        'https://business.columbia.edu/cds/research/research-tools/dospert-scale'
    ),
    translation_note=(
        '依据2006年论文附录英文30题及完整七级锚点制作的项目研究自译，'
        '未经中文心理测量验证。未复用官网所列普通话文件，未改换美元、收入比例或题序。'
        '本版本只测风险行为意向RT，不包含风险感知RP或预期收益量表。'
    ),
    display='sum',
    interpretation=(
        '五个领域各6题求和，原始范围均为6—42；较高分仅表示本次自报更可能参与该领域所列行为。'
        '分别比较自己的情境选择，不计算跨领域总分，不据此判定道德品质、实际行为或固定风险类型。'
        '分数不是鼓励冒险、健康建议或投资建议，也不代表风险承受能力测评。'
    ),
)

