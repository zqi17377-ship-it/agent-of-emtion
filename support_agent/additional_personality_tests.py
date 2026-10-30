"""Public-domain IPIP factor markers; unvalidated project Chinese translation."""

from .psychometrics import Questionnaire, TestItem


# Official Big-Five Factor Markers, five 20-item scales. Preserve the source
# page's factor order and, within each factor, its + keyed then - keyed order.
# Each row records the number of positive items; the remaining items reverse.
# English comments identify the public-domain source item for translation audit.
_IPIP100_FACTOR_ITEMS = (
    ('extraversion', '外向性', 10, (
        '在聚会中，我是活跃气氛的人。',  # Am the life of the party.
        '与人相处时，我感到自在。',  # Feel comfortable around people.
        '我会主动开始交谈。',  # Start conversations.
        '聚会时，我会和许多不同的人交谈。',  # Talk to a lot of different people at parties.
        '我不介意成为注意力的中心。',  # Don't mind being the center of attention.
        '我很容易交到朋友。',  # Make friends easily.
        '我会带头做事。',  # Take charge.
        '我知道如何吸引他人的注意。',  # Know how to captivate people.
        '与人相处时，我感到轻松。',  # Feel at ease with people.
        '我善于应对社交场合。',  # Am skilled in handling social situations.
        '我不太爱说话。',  # Don't talk a lot.
        '我倾向于待在不引人注意的位置。',  # Keep in the background.
        '我没有多少话可说。',  # Have little to say.
        '我不喜欢让别人注意到自己。',  # Don't like to draw attention to myself.
        '在陌生人身边，我很安静。',  # Am quiet around strangers.
        '我觉得主动接近他人很困难。',  # Find it difficult to approach others.
        '与他人相处时，我经常感到不自在。',  # Often feel uncomfortable around others.
        '我会把感受藏在心里。',  # Bottle up my feelings.
        '我是一个很少向他人透露自己的人。',  # Am a very private person.
        '我会等待他人带头。',  # Wait for others to lead the way.
    )),
    ('agreeableness', '宜人性', 14, (
        '我对他人感兴趣。',  # Am interested in people.
        '我能体谅他人的感受。',  # Sympathize with others' feelings.
        '我心肠柔软。',  # Have a soft heart.
        '我会抽出时间给他人。',  # Take time out for others.
        '我能感受到他人的情绪。',  # Feel others' emotions.
        '我让他人感到自在。',  # Make people feel at ease.
        '我会询问他人是否安好。',  # Inquire about others' well-being.
        '我知道怎样安慰他人。',  # Know how to comfort others.
        '我喜爱孩子。',  # Love children.
        '我与几乎所有人都相处融洽。',  # Am on good terms with nearly everyone.
        '对于每个人，我都能说出一些好话。',  # Have a good word for everyone.
        '我会表达感激。',  # Show my gratitude.
        '我会先为他人着想。',  # Think of others first.
        '我喜爱帮助他人。',  # Love to help others.
        '我会侮辱他人。',  # Insult people.
        '我对他人的困扰不感兴趣。',  # Am not interested in other people's problems.
        '我很少关心他人。',  # Feel little concern for others.
        '我对他人并不怎么感兴趣。',  # Am not really interested in others.
        '别人很难了解我。',  # Am hard to get to know.
        '我对他人的感受漠不关心。',  # Am indifferent to the feelings of others.
    )),
    ('conscientiousness', '尽责性', 11, (
        '我总是做好准备。',  # Am always prepared.
        '我注意细节。',  # Pay attention to details.
        '我会及时做完日常杂事。',  # Get chores done right away.
        '我喜欢井然有序。',  # Like order.
        '我按日程安排做事。',  # Follow a schedule.
        '我对自己的工作要求严格。',  # Am exacting in my work.
        '我会按照计划做事。',  # Do things according to a plan.
        '我会一直做下去，直到一切尽善尽美。',  # Continue until everything is perfect.
        '我会制定计划并坚持执行。',  # Make plans and stick to them.
        '我喜爱有条理、有规律的生活。',  # Love order and regularity.
        '我喜欢整理收拾。',  # Like to tidy up.
        '我把自己的东西随处乱放。',  # Leave my belongings around.
        '我常把事情弄得一团糟。',  # Make a mess of things.
        '我经常忘记把东西放回原处。',  # Often forget to put things back in their proper place.
        '我会逃避自己的职责。',  # Shirk my duties.
        '我会疏于履行自己的职责。',  # Neglect my duties.
        '我会浪费自己的时间。',  # Waste my time.
        '我做事常常只做到一半。',  # Do things in a half-way manner.
        '我觉得很难开始投入工作。',  # Find it difficult to get down to work.
        '我会把自己的房间弄得凌乱不堪。',  # Leave a mess in my room.
    )),
    ('emotional_stability', '情绪稳定性', 5, (
        '大多数时候，我感到放松。',  # Am relaxed most of the time.
        '我很少感到忧郁低落。',  # Seldom feel blue.
        '我不容易被事情困扰。',  # Am not easily bothered by things.
        '我很少感到烦躁。',  # Rarely get irritated.
        '我很少生气。',  # Seldom get mad.
        '我很容易感到压力过大。',  # Get stressed out easily.
        '我会担心各种事情。',  # Worry about things.
        '我很容易受到困扰。',  # Am easily disturbed.
        '我很容易心烦或难过。',  # Get upset easily.
        '我的心情经常变化。',  # Change my mood a lot.
        '我的情绪经常大起大落。',  # Have frequent mood swings.
        '我很容易烦躁。',  # Get irritated easily.
        '我经常感到忧郁低落。',  # Often feel blue.
        '我很容易生气。',  # Get angry easily.
        '我很容易惊慌。',  # Panic easily.
        '我很容易感到受威胁。',  # Feel threatened easily.
        '我会被情绪淹没。',  # Get overwhelmed by emotions.
        '我很容易感到被冒犯。',  # Take offense easily.
        '我会陷在自己的问题中。',  # Get caught up in my problems.
        '我会抱怨各种事情。',  # Grumble about things.
    )),
    ('intellect_imagination', '智性/想象力', 13, (
        '我的词汇丰富。',  # Have a rich vocabulary.
        '我的想象力生动丰富。',  # Have a vivid imagination.
        '我有很出色的想法。',  # Have excellent ideas.
        '我能很快理解事情。',  # Am quick to understand things.
        '我会使用难懂的词。',  # Use difficult words.
        '我会花时间反思事情。',  # Spend time reflecting on things.
        '我有很多点子。',  # Am full of ideas.
        '我能把谈话引向更深入的层次。',  # Carry the conversation to a higher level.
        '我能很快领会事情。',  # Catch on to things quickly.
        '我能处理大量信息。',  # Can handle a lot of information.
        '我喜爱想出做事的新方法。',  # Love to think up new ways of doing things.
        '我喜爱阅读有挑战性的材料。',  # Love to read challenging material.
        '我擅长许多事情。',  # Am good at many things.
        '我觉得理解抽象概念有困难。',  # Have difficulty understanding abstract ideas.
        '我对抽象概念不感兴趣。',  # Am not interested in abstract ideas.
        '我的想象力不太丰富。',  # Do not have a good imagination.
        '我尽量避开复杂的人。',  # Try to avoid complex people.
        '我觉得在脑海中想象事物很困难。',  # Have difficulty imagining things.
        '我会避开难读的材料。',  # Avoid difficult reading material.
        '我不会深入探究某个主题。',  # Will not probe deeply into a subject.
    )),
)


IPIP100 = Questionnaire(
    id='ipip100', title='大五人格 · IPIP Factor Markers 100题（研究自译）',
    description=(
        '判断每个描述在多大程度上符合平时的你；五个宽维分别呈现。'
        '采用官方五组20题计分键的顺序，每维先列正向题，再列反向题。'
    ),
    items=tuple(
        TestItem(
            f'ipip100_{factor_index * 20 + item_index}', text, dimension,
            reverse=item_index > positive,
        )
        for factor_index, (dimension, _, positive, texts)
        in enumerate(_IPIP100_FACTOR_ITEMS)
        for item_index, text in enumerate(texts, 1)
    ),
    options=('非常不符合', '比较不符合', '介于符合与不符合之间', '比较符合', '非常符合'),
    min_score=1,
    dimension_labels={
        dimension: label for dimension, label, _, _ in _IPIP100_FACTOR_ITEMS
    },
    source_name=(
        'International Personality Item Pool: Big-Five Factor Markers, '
        'five 20-item scales (100 items); Surgency or Extraversion, '
        'Agreeableness, Conscientiousness, Emotional Stability, '
        'Intellect or Imagination'
    ),
    source_url='https://ipip.ori.org/newBigFive5broadKey.htm',
    license_notice=(
        'IPIP题项与量表属公共领域，官方允许任何人用于商业或非商业用途，'
        '无需费用或另行许可；本项目中文为依据英文题项制作的研究自译。'
        'https://ipip.ori.org/newPermission.htm；本项目仍限本地非商业研究。'
    ),
    translation_note=(
        '本项目依据公共领域英文题项制作的研究自译，未经中文信效度验证，'
        '不是已验证中文版，不沿用英文原版的信效度结论。'
        '100题顺序与正反向键于2026-10-30依据IPIP官方五组20题计分键核对。'
    ),
    display='mean',
    interpretation=(
        '按官方1—5计分，正向题使用原值，反向题使用6减原值；每维20题，'
        '各维原始总分20—100，并列呈现均分1—5。'
        '第四维是情绪稳定性：高分代表更稳定，与Mini-IPIP负性情绪倾向方向相反，'
        '不能直接混比。智性/想象力不等于智商。'
        '不计算人格总分、类型、诊断或百分位；100题版不与50题版直接换算。'
        '计分：https://ipip.ori.org/newScoringInstructions.htm。'
    ),
)
