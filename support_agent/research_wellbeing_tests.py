"""A noncommercial research scale and a separately labeled original exercise."""
from .psychometrics import Questionnaire,TestItem

SWLS=Questionnaire(
    id='swls',title='生活满意度 · SWLS（5题）',
    description='根据你目前对整体生活的看法作答，不需要与他人比较。',
    items=tuple(TestItem(f'swls_{i}',text,'life_satisfaction') for i,text in enumerate((
        '在大多数方面，我的生活接近我理想中的样子。','我的生活条件很好。','我对自己的生活感到满意。',
        '到目前为止，我已经得到生活中对我重要的东西。','如果可以重新过一遍人生，我几乎不会改变什么。'),1)),
    options=('非常不同意','不同意','有点不同意','既不同意也不反对','有点同意','同意','非常同意'),min_score=1,
    dimension_labels={'life_satisfaction':'生活满意度'},
    source_name='Diener, Emmons, Larsen & Griffin (1985), Satisfaction With Life Scale',
    source_url='https://eddiener.com/satisfaction-with-life-scale-swls/',
    license_notice='作者当前页面允许署名后的非商业研究使用；本项目仅用于本地非商业研究。不得据此推定已获商业产品授权。',
    translation_note='依据作者公开英文题项制作的项目研究译文，未经本项目中文样本校准，不冒称已验证中文版。',
    display='sum',interpretation='5题求和，原始范围5—35。较高分表示本次报告的整体生活满意度较高，不是心理健康诊断或人群百分位。',
)

COPING_CONFIDENCE=Questionnaire(
    id='coping_confidence',title='应对信心探索（原创6题）',
    description='想一想你目前面对的日常挑战；选择你通常觉得多么符合的描述。',
    items=(
        TestItem('coping_1','面对复杂的事情，我通常能先找到一个可以开始的小步骤。','coping'),
        TestItem('coping_2','一种方法不顺利时，我愿意尝试其他可行办法。','coping'),
        TestItem('coping_3','遇到超出自己能力的事情时，我能寻找合适的协助。','coping'),
        TestItem('coping_4','遇到困难时，我常觉得无论尝试什么都不会有用。','coping',True),
        TestItem('coping_5','事情突然变化时，我相信自己能逐步调整安排。','coping'),
        TestItem('coping_6','一次不顺利就常让我觉得，之后也没办法解决类似的事。','coping',True),
    ),options=('很不符合','不太符合','介于两者之间','比较符合','很符合'),min_score=1,
    dimension_labels={'coping':'当前应对信心'},source_name='本项目原创探索问答；自我效能概念背景参考 Schwarzer 的研究说明',
    source_url='https://userpage.fu-berlin.de/health/faq_gse.pdf',
    license_notice='6题为本项目原创，可随项目使用；未复制或翻译GSE题项，不是GSE或其验证版本，也不代表相关作者认可。',
    translation_note='原创中文探索问答，尚未进行信效度验证。',display='mean',
    interpretation='显示6题均分1—5，仅描述你对当前日常挑战的自报信心；没有高低诊断阈值，也不等于实际能力。',
)
