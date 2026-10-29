"""Local, descriptive questionnaire interpretations and accessible SVG charts.

Direction meanings follow each stored questionnaire and its original key:
https://ipip.ori.org/MiniIPIPKey.htm
https://ipip.ori.org/newBigFive5broadKey.htm
https://gosling.psy.utexas.edu/scales-weve-developed/ten-item-personality-measure-tipi/
https://socy.umd.edu/about-us/using-rosenberg-self-esteem-scale
https://eddiener.com/satisfaction-with-life-scale-swls/

The chart normalization and the low/middle/high *range descriptions* below are
presentation rules, not validated cutoffs, population norms or trait classes.
No additional model requests, cross-instrument inference or score inversion.
"""
from dataclasses import dataclass
from html import escape
import math

from .psychometrics import Questionnaire, QuestionnaireResult
from .attachment_questions import (
    ATTACHMENT_MIDDLE_MIN, ATTACHMENT_MIDDLE_MAX, attachment_dimension_band,
)


@dataclass(frozen=True)
class SurveyPresentation:
    svg: str
    markdown: str
    chart_label: str


# Each tuple is lower-side wording, upper-side wording, a reflection prompt.
# Opposite emotional axes intentionally remain separate.
_MEANINGS = {
    'extraversion': (
        '本次较少认同主动交谈、活跃社交场面的描述，可能更习惯安静或较少刺激的互动。',
        '本次较多认同主动交谈、参与互动和表达热情的描述。',
        '反思最近一次聚会：你更想主动加入交谈，还是先在旁边观察？熟人和陌生场合是否不同？'),
    'agreeableness': (
        '本次较少认同体谅、关注他人感受的描述；可结合关系情境，核对这些回答是否符合平时。',
        '本次较多认同体谅他人、关注他人感受和温暖互动的描述。',
        '反思一次意见不同时的互动：你怎样同时表达自己的需要、理解对方的感受？'),
    'conscientiousness': (
        '本次较少认同条理、及时完成事务和自律的描述；这不能单独说明能力或责任感。',
        '本次较多认同提前安排、保持条理、及时完成事务的描述。',
        '反思一件最近完成的事情：哪些安排帮助了你？在时间紧迫时，你的做法是否会变化？'),
    'neuroticism': (
        '本次较少认同情绪起伏、心烦和烦扰的描述，只反映这份问卷里的自报。',
        '本次较多认同情绪起伏或烦扰的描述；可回顾近期压力与平时状态的差别。',
        '反思最近一次心烦：什么触发了它，持续多久，又有什么帮助你恢复？'),
    'emotional_stability': (
        '本次较少认同放松、沉着的描述；可进一步核对近期压力是否影响了作答。',
        '本次较多认同放松、沉着和情绪较稳定的描述。',
        '反思一次计划突然变化：你当时怎样反应，之后又怎样回到自己的节奏？'),
    'openness': (
        '本次较少认同新体验、创造性和复杂想法的描述，可能更偏好熟悉的方式。',
        '本次较多认同新体验、创造性和复杂想法的描述。',
        '反思最近一次尝试新事物：什么让你愿意尝试，什么让你更想沿用熟悉的方法？'),
    'intellect_imagination': (
        '本次较少认同想象、抽象概念或点子相关的描述；这不等于智商或实际学习能力。',
        '本次较多认同想象、抽象概念或点子相关的描述；这不等于智商或实际学习能力。',
        '反思一个最近感兴趣的话题：你更享受讨论可能性，还是用具体例子理解它？'),
    'anxiety': (
        '在本次所选关系中，较少认同担心被冷落或关系变淡的描述。',
        '在本次所选关系中，较多认同担心被冷落、在等待回应时反复猜测的描述。',
        '反思一次等待对方回应的经历：当时哪些信息是确定的，哪些是自己的猜测？'),
    'avoidance': (
        '在本次所选关系中，较少认同拉开距离或独自收起需要的描述。',
        '在本次所选关系中，较多认同拉开距离、较少表达脆弱或独自处理需要的描述。',
        '反思一次需要支持的时候：你希望对方怎样靠近，怎样表达需要会更舒服？'),
    'self_esteem': (
        '本次较少认同积极的自我价值描述；可以具体看看哪些题目受到近期经历影响。',
        '本次较多认同积极的自我价值描述，表达了对自身价值较多的肯定。',
        '反思最近一件不顺利的事：你怎样评价这件事，又怎样评价自己？两者能否分开看？'),
    'life_satisfaction': (
        '本次对整体生活的满意描述认同较少，可能有一些重要方面尚未接近你的期待。',
        '本次对整体生活的满意描述认同较多，较多方面接近你目前的期待。',
        '反思生活中最满意的一方面，以及最想改变的一方面：各自最重要的原因是什么？'),
    'coping': (
        '本次对处理当前挑战的信心描述认同较少；自报信心不能代替实际能力判断。',
        '本次对逐步处理当前挑战、调整方法或寻求协助的信心描述认同较多。',
        '反思目前一个具体挑战：最小的下一步是什么，你已经拥有或可以请求哪些帮助？'),
}


def _position(dimension):
    span=dimension.max_value-dimension.min_value
    if span<=0 or not math.isfinite(dimension.mean) or not dimension.min_value<=dimension.mean<=dimension.max_value:
        raise ValueError('A valid raw dimension range is required.')
    return (dimension.mean-dimension.min_value)/span


def _number(value):
    return f'{value:g}'


def _raw(dimension, summed):
    if summed:
        return f'{dimension.total} 分，原始范围 {dimension.min_total}—{dimension.max_total}'
    return f'均分 {dimension.mean:.2f}，原始范围 {dimension.min_value}—{dimension.max_value}'


def _svg_open(label, description, height):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 {height}" '
            f'role="img" aria-label="{escape(label,quote=True)}" '
            'style="width:100%;max-width:720px;height:auto;display:block;margin:0 auto;font-family:Segoe UI,Microsoft YaHei,sans-serif">'
            f'<title>{escape(label)}</title><desc>{escape(description)}</desc>'
            f'<rect width="640" height="{height}" rx="22" fill="#f4f6ef"/>')


def _text(x,y,value,*,size=15,anchor='start',color='#3c5746',weight='400'):
    return (f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
            f'fill="{color}" font-size="{size}" font-weight="{weight}">{escape(value)}</text>')


def _radar(dimensions):
    label='五维得分雷达图'
    description='；'.join(d.label+'：'+_raw(d,False) for d in dimensions)
    description+='。各轴从中心的量程下限向外圈的上限延伸。轴方向依原工具，面积不表示人格总分。'
    parts=[_svg_open(label,description,465)]
    cx,cy,radius=320,220,145
    def point(index,fraction):
        angle=-math.pi/2+index*2*math.pi/5
        return cx+radius*fraction*math.cos(angle),cy+radius*fraction*math.sin(angle)
    def points(fractions):
        return ' '.join(f'{x:.2f},{y:.2f}' for x,y in (point(i,f) for i,f in enumerate(fractions)))
    for fraction in (.25,.5,.75,1):
        parts.append(f'<polygon points="{points([fraction]*5)}" fill="none" stroke="#d7dfd2" stroke-width="1"/>')
    for index,dimension in enumerate(dimensions):
        x,y=point(index,1)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="#d7dfd2"/>')
        lx,ly=point(index,1.32)
        anchor='middle' if index==0 else 'start' if lx>cx else 'end'
        parts.append(_text(lx,ly,dimension.label,anchor=anchor,size=16,weight='600'))
        parts.append(_text(lx,ly+23,f'{dimension.mean:.2f} / {dimension.max_value}',anchor=anchor,size=13,color='#74836d'))
    fractions=[_position(d) for d in dimensions]
    parts.append(f'<polygon data-series="answers" points="{points(fractions)}" fill="#6d947a" fill-opacity=".25" stroke="#496e55" stroke-width="3" stroke-linejoin="round"/>')
    for index,dimension in enumerate(dimensions):
        x,y=point(index,fractions[index])
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#496e55"><title>{escape(dimension.label+"："+_raw(dimension,False))}</title></circle>')
    parts.append(_text(320,420,f'中心 {dimensions[0].min_value} · 外圈 {dimensions[0].max_value}（题均分）',anchor='middle',size=13,color='#74836d'))
    parts.append(_text(320,444,'形状只呈现本次五维回答，不合成人格总分',anchor='middle',size=13,color='#74836d'))
    parts.append('</svg>')
    return ''.join(parts),label


def _bars(dimensions,summed):
    label='原始得分量程图'
    height=70+len(dimensions)*110
    description='；'.join(d.label+'：'+_raw(d,summed) for d in dimensions)+'。圆点表示本次得分在原始量程的位置，不是人群百分位。'
    parts=[_svg_open(label,description,height)]
    for index,dimension in enumerate(dimensions):
        y=44+index*110
        position=_position(dimension)
        lower=dimension.min_total if summed else dimension.min_value
        upper=dimension.max_total if summed else dimension.max_value
        value=str(dimension.total) if summed else f'{dimension.mean:.2f}'
        parts.extend([
            _text(40,y,dimension.label,size=17,weight='600'),
            _text(600,y,value+' 分',anchor='end',size=17,weight='600'),
            f'<line x1="40" y1="{y+29}" x2="600" y2="{y+29}" stroke="#dce4d7" stroke-width="10" stroke-linecap="round"/>',
            f'<line x1="40" y1="{y+29}" x2="{40+560*position:.2f}" y2="{y+29}" stroke="#71947a" stroke-width="10" stroke-linecap="round"/>',
            f'<circle cx="{40+560*position:.2f}" cy="{y+29}" r="7" fill="#3d644b"><title>{escape(_raw(dimension,summed))}</title></circle>',
            _text(40,y+60,_number(lower),size=13,color='#74836d'),
            _text(600,y+60,_number(upper),anchor='end',size=13,color='#74836d'),
        ])
    parts.append(_text(320,height-16,'圆点为本次原始得分的位置',anchor='middle',size=13,color='#74836d'))
    parts.append('</svg>')
    return ''.join(parts),label


def _interpret(dimensions,definition):
    band_rule=(
        f'依恋解读沿用本原创练习的中点启发式：均分 {ATTACHMENT_MIDDLE_MIN:g}—{ATTACHMENT_MIDDLE_MAX:g}（含边界）为中间区间，区间外分别描述较低或较高一侧；规则及边界未经验证。'
        if definition.id=='attachment_exploration'
        else '偏低、居中、偏高仅按本量程的三段辅助描述，未经常模验证。'
    )
    lines=['### 本次作答解读','',
           '以下由本机依据得分方向生成，用于核对你的回答。量程位置不是人群百分位、概率或诊断。'+band_rule,'']
    for dimension in dimensions:
        position=_position(dimension)
        band=(attachment_dimension_band(dimension.mean) if definition.id=='attachment_exploration'
              else 'lower' if position<1/3 else 'higher' if position>2/3 else 'middle')
        lower,higher,prompt=_MEANINGS.get(dimension.key,('本次较少认同这一维度的描述。','本次较多认同这一维度的描述。','反思：哪些具体日常经历与你的回答相符，哪些不同？'))
        if band=='lower':
            wording='在本量程较低一侧'
            meaning=lower
        elif band=='higher':
            wording='在本量程较高一侧'
            meaning=higher
        else:
            wording='在本量程中间一带'
            meaning='本次回答位于量程中间，暂不判断明确方向。可以看看不同情境下的回答是否会变化，也可能是不同题目的正反方向相互抵消。'
        lines.extend([f'#### {escape(dimension.label)}','',
                      _raw(dimension,definition.display=='sum')+'；'+wording+'。'+meaning,'',prompt,''])
    if definition.id in ('mini_ipip','tipi','ipip50'):
        lines.extend(['五个维度分别理解，图形面积和维度合计没有人格总分含义；不同题数与工具的图形不能直接作为变化幅度比较。',''])
        if definition.id=='mini_ipip':
            lines.extend(['这里第四维是负性情绪倾向，高分表示报告的起伏或烦扰更多；它与其他版本的情绪稳定性方向相反。',''])
        if definition.id=='tipi':
            lines.extend(['本版本每维仅两题，描绘较粗略，优先结合具体例子核对。',''])
    if definition.id=='attachment_exploration':
        lines.extend(['这份原创练习只描述本次选定关系，不能给一个人确定稳定的依恋类型；不同关系需分别理解。',''])
    lines.extend(['研究说明：'+definition.translation_note,'',definition.interpretation])
    return '\n'.join(lines)


def build_survey_presentation(definition: Questionnaire,result: QuestionnaireResult) -> SurveyPresentation:
    """Render an already-scored result without inferring any additional scores."""
    if result.test_id!=definition.id or set(result.dimensions)!=set(definition.dimension_labels):
        raise ValueError('Result must match the questionnaire and its dimensions.')
    dimensions=[result.dimensions[key] for key in definition.dimension_labels]
    for dimension in dimensions: _position(dimension)
    if definition.id in ('mini_ipip','tipi','ipip50') and len(dimensions)==5:
        svg,label=_radar(dimensions)
    else:
        svg,label=_bars(dimensions,definition.display=='sum')
    return SurveyPresentation(svg=svg,markdown=_interpret(dimensions,definition),chart_label=label)
