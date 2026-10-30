from .attachment_questions import ATTACHMENT_EXPLORATION
from .published_personality_tests import MINI_IPIP,RSES
from .wellbeing_tests import TIPI
from .research_wellbeing_tests import SWLS,COPING_CONFIDENCE
from .self_care_tests import SCS26,MAAS15
from .relationship_risk_tests import DOSPERT30

SURVEYS=(ATTACHMENT_EXPLORATION,MINI_IPIP,TIPI,RSES,COPING_CONFIDENCE,SWLS,SCS26,MAAS15,DOSPERT30)
SURVEY_BY_ID={q.id:q for q in SURVEYS}
TOOL_LABELS={'mbti':'对话性格 · MBTI 风格',**{q.id:q.title for q in SURVEYS}}
TOOL_LABELS.pop('tipi',None)
TOOL_LABELS['mini_ipip']='大五人格 · 10 / 20 / 50 / 100题'
TOOL_LABELS['attachment_exploration']='关系中的依恋 · 9 / 12 / 36题'
TOOL_LABELS['scs26']='自我关怀 · 12 / 26题'
TOOL_LABELS['maas15']='日常正念觉察 · 15题'
TOOL_LABELS['dospert30']='不同领域的风险偏好 · 30题'
TOOL_LABELS['swls']='生活满意度 · 3 / 5题'
TOOL_LABELS['conversation_observation']='对话观察 · 性格与关系'


def export_survey_report(definition,result,context=''):
    lines=['# '+definition.title,'','本次自我探索记录，不构成诊断或稳定类型判断。']
    if context: lines.extend(['','本次想到的关系：'+context])
    for composite in result.composites.values():
        lines.extend(['',composite.label+f'：{composite.mean:.2f}（范围{composite.min_value}—{composite.max_value}）'])
    for dimension in (result.dimensions.values() if definition.show_dimensions else ()):
        value=f'{dimension.total}（范围{dimension.min_total}—{dimension.max_total}）' if definition.display=='sum' else f'{dimension.mean:.2f}（范围{dimension.min_value}—{dimension.max_value}）'
        lines.extend(['',dimension.label+'：'+value])
    lines.extend(['',definition.interpretation,'','来源：'+definition.source_name,definition.source_url,'',definition.license_notice,'',definition.translation_note])
    return '\n'.join(lines)
