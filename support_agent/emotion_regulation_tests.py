"""Untranslated ERQ-30, administered under the authors' original-form permission.

Item order, instructions, anchors and ten sum keys follow Preece & Gross's
author-uploaded questionnaire and scoring manual. No translated items or US
norm-based categories are provided. Changes of layout do not change wording.
"""
from .psychometrics import Questionnaire,TestItem


_KEYS={
    'erq30_behavioral_activation':('Behavioral activation',(4,14,23)),
    'erq30_problem_solving':('Problem solving',(6,16,25)),
    'erq30_situational_avoidance':('Situational avoidance',(5,15,24)),
    'erq30_social_withdrawal':('Social withdrawal',(11,21,30)),
    'erq30_distraction':('Distraction',(9,19,28)),
    'erq30_rumination':('Rumination',(8,18,27)),
    'erq30_acceptance':('Acceptance',(10,20,29)),
    'erq30_cognitive_reappraisal':('Cognitive reappraisal',(1,3,12)),
    'erq30_expressive_suppression':('Expressive suppression',(2,13,22)),
    'erq30_social_sharing':('Social sharing',(7,17,26)),
}
_ITEMS=(
    'When I want to feel more positive emotion (such as joy or amusement), I change the way I’m thinking about the situation.',
    'I keep my emotions to myself.',
    'When I want to feel less negative emotion (such as sadness or anger), I change the way I’m thinking about the situation.',
    'I control my emotions by regularly doing pleasant and meaningful activities throughout my week.',
    'When I am faced with a stressful situation, I try to get away from that situation as quickly as possible.',
    'When I want to feel more positive emotion, I look for practical solutions that will fix the issues or unpleasant situations in my life.',
    'I control my emotions by talking with other people about what I’m feeling.',
    'When I am faced with a stressful situation, I manage my emotions by repeatedly thinking about the negative parts of the situation.',
    'When I want to feel less negative emotion, I distract myself.',
    'I control my emotions by accepting the things in my life that I cannot change.',
    'When I want to feel more positive emotion, I retreat into my own space, away from others.',
    'I control my emotions by changing the way I think about the situation I’m in.',
    'I control my emotions by not expressing them.',
    'When I want to feel more positive emotion, I make a point of doing enjoyable activities throughout the week that are consistent with what I want in life.',
    'When I want to feel less negative emotion, I avoid any situations that seem like they potentially may get stressful.',
    'When I am faced with a stressful situation, I make realistic plans to help solve the situation.',
    'When I want to feel more positive emotion, I let others know what I’m feeling.',
    'I manage my emotions by ‘ruminating’ about stressful situations (thinking about the bad parts of situations again and again).',
    'During stressful situations, I distract myself to feel better.',
    'When I want to feel more positive emotion, I try to accept the parts of upsetting situations in my life that I cannot change.',
    'I control my emotions by distancing myself from other people.',
    'When I am feeling negative emotions, I make sure not to express them.',
    'When I want to feel less negative emotion, I make sure to do things that will get me energized by moving physically.',
    'When I want to feel more positive emotion, I try to avoid all situations that might end up being uncomfortable.',
    'I control my emotions by solving the problems or stressful situations in my life.',
    'When I am faced with a stressful situation, I share what I’m feeling in order to feel better.',
    'When I want to feel better about an upsetting situation, I go over and over what happened and why.',
    'I distract myself during upsetting situations to feel better.',
    'When I am faced with a stressful situation, I try to keep calm by accepting the parts of it that I cannot change.',
    'When I want to feel less negative emotion, I isolate myself, away from friends or family.',
)

ERQ30_EN=Questionnaire(
    id='erq30_en',title='情绪调节 · ERQ-30（30题，英文原版）',
    description='We would like to ask you some questions about your emotional life, in particular, how you control (that is, regulate and manage) your emotions. For each item, please answer using the following scale:',
    items=tuple(TestItem(f'erq30_{n}',text,next(key for key,(_,numbers) in _KEYS.items() if n in numbers)) for n,text in enumerate(_ITEMS,1)),
    options=('1 · Strongly disagree','2','3','4 · Neither agree nor disagree','5','6','7 · Strongly agree'),
    min_score=1,dimension_labels={key:label for key,(label,_) in _KEYS.items()},
    source_name='© Preece & Gross (2026). The Emotion Regulation Questionnaire-30 (ERQ-30). Journal of Affective Disorders, 395, 120727. Author questionnaire and scoring manual.',
    source_url='https://www.researchgate.net/publication/398122614_The_Emotion_Regulation_Questionnaire-30_ERQ-30_Copy_of_Questionnaire_and_Scoring_Instructions',
    license_notice='© Preece & Gross (2026)。作者手册允许原表不限次数免费用于研究及临床的纸笔或在线施测；翻译、改编或修改内容需另行联系作者取得许可。本项目仅在既有本地非商业研究范围使用英文原表，不声称获得翻译许可。原始机构入口：https://spl.stanford.edu/resources 。',
    translation_note='本版本保留英文指导语、题项和作答锚点，不提供项目自译。原表只给1、4、7标注文字，其他位置只保留数字。原作者的英文研究结果不等于本应用已完成独立验证。',
    display='sum',
    interpretation='Each strategy is scored by summing its three items (range 3–21), with no reversed items and no overall total. Higher scores indicate greater self-reported use of that strategy. These raw scores are not diagnoses or recommendations. This app does not apply the manual’s US normative categories to this research session.',
)
