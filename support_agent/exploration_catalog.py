from .attachment_questions import ATTACHMENT_EXPLORATION
from .published_personality_tests import MINI_IPIP,RSES
from .wellbeing_tests import TIPI
from .research_wellbeing_tests import SWLS,COPING_CONFIDENCE

SURVEYS=(ATTACHMENT_EXPLORATION,MINI_IPIP,TIPI,RSES,COPING_CONFIDENCE,SWLS)
SURVEY_BY_ID={q.id:q for q in SURVEYS}
TOOL_LABELS={'mbti':'对话性格 · MBTI 风格',**{q.id:q.title for q in SURVEYS}}
TOOL_LABELS.pop('tipi',None)
TOOL_LABELS['mini_ipip']='大五人格 · 10 / 20 / 50题'
TOOL_LABELS['swls']='生活满意度 · 3 / 5题'
TOOL_LABELS['conversation_observation']='对话观察 · 性格与关系'


def export_survey_report(definition,result,context=''):
    lines=['# '+definition.title,'','本次自我探索记录，不构成诊断或稳定类型判断。']
    if context: lines.extend(['','本次想到的关系：'+context])
    for dimension in result.dimensions.values():
        value=f'{dimension.total}（范围{dimension.min_total}—{dimension.max_total}）' if definition.display=='sum' else f'{dimension.mean:.2f}（范围{dimension.min_value}—{dimension.max_value}）'
        lines.extend(['',dimension.label+'：'+value])
    lines.extend(['',definition.interpretation,'','来源：'+definition.source_name,definition.source_url,'',definition.license_notice,'',definition.translation_note])
    return '\n'.join(lines)
