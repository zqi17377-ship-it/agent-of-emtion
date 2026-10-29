"""Public-domain self-esteem and personality scales with research-only Chinese renderings.

Item order for RSES follows the UMD scoring key. Mini-IPIP items are grouped
by the official IPIP key, rather than retaining an interleaved administration
order. Chinese item text is this project's translation of the English items.
"""

from .psychometrics import Questionnaire, TestItem


_TRANSLATION_NOTE = (
    "中文题项为本项目依据公共领域英文题项所作的研究自译，未经中文信效度验证，"
    "不代表已发表的验证中文版。"
)


RSES = Questionnaire(
    id="rses",
    title="自尊感受 · Rosenberg 10 题",
    description="了解你对自身价值的一般感受。请根据你通常对自己的感受作答。",
    items=(
        TestItem("rses_1", "我觉得自己是一个有价值的人，至少与别人一样有价值。", "self_esteem"),
        TestItem("rses_2", "我觉得自己有不少优点。", "self_esteem"),
        TestItem("rses_3", "总的来说，我倾向于觉得自己是一个失败者。", "self_esteem", reverse=True),
        TestItem("rses_4", "我做事的能力和大多数人一样好。", "self_esteem"),
        TestItem("rses_5", "我觉得自己没有多少值得自豪的地方。", "self_esteem", reverse=True),
        TestItem("rses_6", "我对自己持积极的态度。", "self_esteem"),
        TestItem("rses_7", "总体而言，我对自己感到满意。", "self_esteem"),
        TestItem("rses_8", "我希望自己能更加尊重自己。", "self_esteem", reverse=True),
        TestItem("rses_9", "有时候，我确实觉得自己没什么用。", "self_esteem", reverse=True),
        TestItem("rses_10", "有时候，我觉得自己一无是处。", "self_esteem", reverse=True),
    ),
    options=("非常不同意", "不同意", "同意", "非常同意"),
    min_score=0,
    dimension_labels={"self_esteem": "整体自尊"},
    source_name=(
        "Rosenberg, M. (1965). Society and the Adolescent Self-Image. "
        "University of Maryland: Using the Rosenberg Self-Esteem Scale."
    ),
    source_url="https://socy.umd.edu/about-us/using-rosenberg-self-esteem-scale",
    license_notice=(
        "UMD 官方声明 Rosenberg Self-Esteem Scale 已属公共领域（public domain），"
        "可免费使用、翻译及改编，无需另行许可或通知；使用时保留 Rosenberg 的学术出处。"
    ),
    translation_note=_TRANSLATION_NOTE,
    display="sum",
    interpretation=(
        "10 题按官方正反向计分后相加，总分为 0–30 分；分数越高，表示报告的整体自尊越高。"
        "本工具用于自我了解，不提供诊断阈值、临床结论或常模百分位。"
    ),
)


MINI_IPIP = Questionnaire(
    id="mini_ipip",
    title="大五人格 · Mini-IPIP 20 题",
    description="从五个连续维度了解自己的通常倾向。请判断每个描述在多大程度上符合平时的你。",
    items=(
        TestItem("mini_ipip_1", "在聚会中，我常常是活跃气氛的人。", "extraversion"),
        TestItem("mini_ipip_2", "聚会时，我会与许多不同的人交谈。", "extraversion"),
        TestItem("mini_ipip_3", "我不太爱说话。", "extraversion", reverse=True),
        TestItem("mini_ipip_4", "我倾向于待在不引人注意的位置。", "extraversion", reverse=True),
        TestItem("mini_ipip_5", "我能体谅他人的感受。", "agreeableness"),
        TestItem("mini_ipip_6", "我能感受到他人的情绪。", "agreeableness"),
        TestItem("mini_ipip_7", "我对他人并不怎么感兴趣。", "agreeableness", reverse=True),
        TestItem("mini_ipip_8", "我对他人的困扰不感兴趣。", "agreeableness", reverse=True),
        TestItem("mini_ipip_9", "我会及时把日常杂事做完。", "conscientiousness"),
        TestItem("mini_ipip_10", "我喜欢井然有序。", "conscientiousness"),
        TestItem("mini_ipip_11", "我经常忘记把东西放回原处。", "conscientiousness", reverse=True),
        TestItem("mini_ipip_12", "我常把事情弄得一团糟。", "conscientiousness", reverse=True),
        TestItem("mini_ipip_13", "我的情绪经常起伏变化。", "neuroticism"),
        TestItem("mini_ipip_14", "我很容易心烦或难过。", "neuroticism"),
        TestItem("mini_ipip_15", "大多数时候，我感到放松。", "neuroticism", reverse=True),
        TestItem("mini_ipip_16", "我很少感到忧郁低落。", "neuroticism", reverse=True),
        TestItem("mini_ipip_17", "我的想象力生动丰富。", "intellect_imagination"),
        TestItem("mini_ipip_18", "我觉得理解抽象概念有困难。", "intellect_imagination", reverse=True),
        TestItem("mini_ipip_19", "我对抽象概念不感兴趣。", "intellect_imagination", reverse=True),
        TestItem("mini_ipip_20", "我的想象力不太丰富。", "intellect_imagination", reverse=True),
    ),
    options=("非常不符合", "比较不符合", "介于符合与不符合之间", "比较符合", "非常符合"),
    min_score=1,
    dimension_labels={
        "extraversion": "外向性",
        "agreeableness": "宜人性",
        "conscientiousness": "尽责性",
        "neuroticism": "负性情绪倾向",
        "intellect_imagination": "智性/想象力",
    },
    source_name=(
        "Donnellan, M. B., Oswald, F. L., Baird, B. M., & Lucas, R. E. (2006). "
        "The Mini-IPIP scales: Tiny-yet-effective measures of the Big Five factors "
        "of personality. Psychological Assessment, 18, 192–203. "
        "International Personality Item Pool: Mini-IPIP Scoring Key."
    ),
    source_url="https://ipip.ori.org/MiniIPIPKey.htm",
    license_notice=(
        "IPIP 官方声明其题项和量表属公共领域（public domain），可复制、编辑、翻译，"
        "并用于商业及非商业目的，无需许可或费用。许可声明："
        "https://ipip.ori.org/newPermission.htm；计分说明："
        "https://ipip.ori.org/newScoringInstructions.htm。保留原量表的学术出处。"
    ),
    translation_note=_TRANSLATION_NOTE,
    display="mean",
    interpretation=(
        "每个维度包含 4 题，按官方正反向计分后取均值，范围均为 1–5 分。"
        "负性情绪倾向得分越高，表示报告的情绪起伏和烦扰越多；"
        "智性/想象力仅反映本短量表所覆盖的相关特征。"
        "五个维度分别呈现，不合成人格总分或人格类型。"
        "结果用于自我了解，不提供临床诊断或常模百分位。"
    ),
)
