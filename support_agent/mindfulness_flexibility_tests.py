"""Final seven-item AAQ-II in its unchanged English wording.

FFMQ-39 is deliberately absent: its author-hosted download and ACBS listing
provide the form and scoring key, but did not establish explicit reuse terms
for this project during the 2026-10-30 permission review.
"""

from .psychometrics import Questionnaire, TestItem


AAQII7 = Questionnaire(
    id='aaqii7',
    title='心理不灵活与经验性回避 · AAQ-II（7题，英文原版）',
    description=(
        'Below you will find a list of statements. Please rate how true each '
        'statement is for you by circling a number next to it. '
        'Use the scale below to make your choice.'
    ),
    items=tuple(
        TestItem(f'aaqii7_{number}', text, 'psychological_inflexibility')
        for number, text in enumerate((
            'My painful experiences and memories make it difficult for me to live a life that I would value.',
            'I’m afraid of my feelings.',
            'I worry about not being able to control my worries and feelings.',
            'My painful memories prevent me from having a fulfilling life.',
            'Emotions cause problems in my life.',
            'It seems like most people are handling their lives better than I am.',
            'Worries get in the way of my success.',
        ), 1)
    ),
    options=(
        'never true', 'very seldom true', 'seldom true', 'sometimes true',
        'frequently true', 'almost always true', 'always true',
    ),
    min_score=1,
    dimension_labels={'psychological_inflexibility': '心理不灵活 / 经验性回避'},
    source_name=(
        'Bond, Hayes, Baer, Carpenter, Guenole, Orcutt, Waltz & Zettle (2011), '
        'Acceptance and Action Questionnaire–II, Behavior Therapy, 42, 676–688; '
        'Ruth Baer 作者页面所提供的最终7题表格和计分说明'
    ),
    source_url='https://ruthbaer.com/academics/AAQ-II.pdf',
    license_notice=(
        'ACBS 引述作者 Frank Bond 明确允许研究及与来访者使用，无需另行取得作者许可；'
        '任何营利用途需向作者申请许可。本项目按本地非商业个人研究范围使用。'
        '授权说明：https://contextualscience.org/acceptance_action_questionnaire_aaq_aaqii'
    ),
    translation_note=(
        '题项、指导语和作答锚点保留作者公开表格的英文原文；仅标题和结果说明为中文。'
        '未加入项目译文，不冒称已验证的中文版。'
    ),
    display='sum',
    interpretation=(
        '最终7题全部正向计分，求和范围7—49（单题均分1—7）。'
        '较高分表示本次自报的心理不灵活或经验性回避较多，不表示心理灵活性更高。'
        '本地研究仅报告原始分，不提供诊断阈值、人群百分位或临床诊断。'
    ),
)
