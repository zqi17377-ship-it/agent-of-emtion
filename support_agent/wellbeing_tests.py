"""Additional questionnaires with source, permission, and translation notices."""

from support_agent.psychometrics import Questionnaire, TestItem


TIPI = Questionnaire(
    id='tipi',
    title='TIPI 十题大五人格简表（研究译文）',
    description=(
        '请判断每对特征整体上在多大程度上符合你对自己的看法。'
        '即使其中一个特征比另一个更符合，也请对整对特征作答。'
        '这是一份很简短的自报工具，每个维度仅两题。'
    ),
    items=(
        TestItem('tipi_1', '我认为自己是：外向、热情的。', 'extraversion'),
        TestItem('tipi_2', '我认为自己是：爱挑剔、容易与人争执的。', 'agreeableness', reverse=True),
        TestItem('tipi_3', '我认为自己是：可靠、自律的。', 'conscientiousness'),
        TestItem('tipi_4', '我认为自己是：焦虑、容易心烦的。', 'emotional_stability', reverse=True),
        TestItem('tipi_5', '我认为自己是：对新体验持开放态度、想法较为复杂的。', 'openness'),
        TestItem('tipi_6', '我认为自己是：内敛、安静的。', 'extraversion', reverse=True),
        TestItem('tipi_7', '我认为自己是：体恤他人、待人温暖的。', 'agreeableness'),
        TestItem('tipi_8', '我认为自己是：缺乏条理、粗心的。', 'conscientiousness', reverse=True),
        TestItem('tipi_9', '我认为自己是：沉着、情绪稳定的。', 'emotional_stability'),
        TestItem('tipi_10', '我认为自己是：循规蹈矩、缺少创造性的。', 'openness', reverse=True),
    ),
    options=(
        '非常不同意', '比较不同意', '有点不同意', '既不同意也不反对',
        '有点同意', '比较同意', '非常同意',
    ),
    min_score=1,
    dimension_labels={
        'extraversion': '外向性',
        'agreeableness': '宜人性',
        'conscientiousness': '尽责性',
        'emotional_stability': '情绪稳定性',
        'openness': '经验开放性',
    },
    source_name=(
        'Gosling, S. D., Rentfrow, P. J., & Swann, W. B., Jr. (2003). '
        'A Very Brief Measure of the Big Five Personality Domains. '
        'Journal of Research in Personality, 37, 504–528.'
    ),
    source_url='https://gosling.psy.utexas.edu/scales-weve-developed/ten-item-personality-measure-tipi/',
    license_notice='作者官网允许任何人将 TIPI 用于任何目的，无需另行申请；项目保留作者与来源署名。',
    translation_note=(
        '本项目依据英文原文自行翻译，供本地研究使用；未经中文样本校准，'
        '不等同于作者收录的既有中文版。'
    ),
    display='mean',
    interpretation=(
        '分别展示五个维度的 1–7 分均值，不计算人格总分。'
        '分数较高表示本次自报更偏向该维度；情绪稳定性高分表示更沉着、情绪更稳定。'
        '每维仅两题，结果较为粗略，可结合具体生活经历反思，不用于诊断或固定人格分类。'
    ),
)


__all__ = ['TIPI']
