"""Bounded live checks of fixed fictional adults, never real chat material.

Run with --live; at most 14 requests across the real chat and observation paths.
Only final content and safe counters are saved. This is not an accuracy study.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from support_agent.conversation_observation import analyze_observations,build_snapshot
from support_agent.dialogue_exploration import build_exploration_context
from support_agent.model_client import make_gateway
from support_agent.observation_scheduler import ObservationState
from support_agent.schemas import CallBudget,Message,ModelCallError,SessionState
from support_agent.workflow import run_turn


TURNS=(
    '这是同一个成年人虚构案例，以第一人称描述这个角色：周六和同事团建后，我回家独自看书一小时，之后才又有精力做别的事。我希望通过聊天梳理这个角色平时的偏好。',
    '我主要是想把注意力收回来。那次团建一直在接话和照顾气氛，自己看书时终于不用关注别人，感觉轻松了；不是讨厌同事。',
    '另一个不同场景是家庭旅行。上个月和家人旅行几天，每晚我都会先独自散步，再回去分享当天的见闻。安静一会之后，我反而更愿意继续交流。',
)
SUPPORTED=(
    '固定的成年人虚构案例，以下三条都指同一叙述者。我通常在社交后独处恢复。上周末同学聚会结束，我独自走路回家，安静半小时后恢复了精力。聚会前我列好要办的三件事，按顺序完成后才出发。',
    '上周三的工作会议让我有点累，我像平时一样先自己坐一会，之后再和同事交流。准备新任务时我先找过去的具体例子，再列出每一步和截止时间；上周的报告也是提前两天完成的。',
    '上个月家庭旅行，我每天晚上自己散步或看书恢复精力，再回去聊天。出门前我按经验列好了路线、车次和每天要做的事，提前订好住宿，通常不喜欢最后一刻再改安排。',
)
MIXED=(
    '同一成年人虚构案例、同一段伴侣关系。我通常在对方很晚还没回复时担心被疏远。上周二我反复查看手机，又发了几条消息确认对方是不是生气了。',
    '同一段关系里，月初的一次周末也是这样，对方临时忙工作没回消息，我很想马上得到回应，连续问了几遍自己是不是哪里做错了。这种等回复的担忧发生过多次。',
    '同一段关系也有不同的时候。上周对方出差前告诉我晚上才方便回复，那天我安心去运动，没有反复查看手机。我发现事先讲清楚安排时，我通常能够放心等待。',
)


class Meter:
    def __init__(self,maximum): self.maximum=maximum;self.calls=0
    def wrap(self,gateway):
        meter=self
        class BoundedGateway:
            mode='live'
            model_id=gateway.model_id
            def generate(self,*args,**kwargs):
                if meter.calls>=meter.maximum: raise ModelCallError('budget')
                meter.calls+=1
                return gateway.generate(*args,**kwargs)
        return BoundedGateway()


def analyze_case(name,texts,gateway,domains,relations=None):
    messages=[Message(id=f'{name}-{n}',role='user',content=t) for n,t in enumerate(texts)]
    bindings={m.id:'partner_1' for m in messages} if relations else {}
    snapshot=build_snapshot(name,'fixed-generation',1,0,messages,domains,
        relations=relations,message_relations=bindings,subject_mode='synthetic_case')
    result=analyze_observations(snapshot,gateway,CallBudget(limit=2,deadline_seconds=90,max_request_seconds=45))
    return {'name':name,'status':result.status,'error_code':result.error_code,
        'attempts':result.metrics['attempts'],
        'observations':[{'dimension':o.dimension,'direction':o.direction,
            'tentative_direction':o.tentative_direction,'coverage':o.coverage,
            'reason':o.coverage_reason,'evidence':[e.quote for e in o.evidence],
            'counter_evidence':[e.quote for e in o.counter_evidence]} for o in result.observations]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--max-requests',type=int,default=14)
    parser.add_argument('--out',type=Path,default=ROOT/'reports/guided-dialogue-live.json')
    args=parser.parse_args()
    if not args.live: parser.error('--live is required; only fixed fictional adult fixtures are sent')
    if not 1<=args.max_requests<=14: parser.error('--max-requests must be 1–14')
    meter=Meter(args.max_requests)
    raw_chat=raw_observation=None
    record={'synthetic_only':True,'request_cap':meter.maximum,'turns':[],'reports':[]}
    try:
        raw_chat=make_gateway();raw_observation=make_gateway(purpose='observation')
        chat=meter.wrap(raw_chat);observation=meter.wrap(raw_observation)
        session=SessionState()
        scope=ObservationState(mode='manual',domains=('mbti','big_five'),subject_mode='synthetic_case')
        for text in TURNS:
            context=build_exploration_context(scope,session.messages,subject_mode='synthetic_case')
            result=run_turn(session,text,chat,exploration_context=context)
            record['turns'].append({'status':result.status,'error_code':result.error_code,
                'reply':result.text,'topic':session.inquiry_state.topic,
                'stage':session.inquiry_state.stage,'question':session.inquiry_state.last_question,
                'attempts':result.metrics.get('attempts',0)})
            print(json.dumps({'completed_turn':len(record['turns']),'status':result.status,'requests':meter.calls}),flush=True)
        for name,texts,domains,relations in (
            ('supported',SUPPORTED,('mbti','big_five'),None),
            ('limited',(SUPPORTED[0],),('mbti',),None),
            ('mixed',MIXED,('attachment',),{'partner_1':'partner'}),
        ):
            record['reports'].append(analyze_case(name,texts,observation,domains,relations))
            print(json.dumps({'completed_report':name,'status':record['reports'][-1]['status'],'requests':meter.calls}),flush=True)
        record['checks']={
            'three_checked_turns':len(record['turns'])==3 and all(t['status']=='ok' for t in record['turns']),
            'distinct_questions':len({t['question'] for t in record['turns'] if t['question']})==3,
            'does_not_reask_supplied_action_or_motive':[t['stage'] for t in record['turns']]==['motivation','cross_context','counterexample'],
            'supported_pattern':any(o['coverage']=='supported' for o in record['reports'][0]['observations']),
            'sparse_not_strong':bool(record['reports'][1]['observations']) and all(o['coverage']!='supported' for o in record['reports'][1]['observations']),
            'independent_counterexample':any(o['coverage']=='conflicting' and o['counter_evidence'] for o in record['reports'][2]['observations']),
        }
    except ModelCallError as error:
        record['error_code']=str(error)
    finally:
        for gateway in (raw_chat,raw_observation):
            if gateway is not None: gateway.close()
    record['requests']=meter.calls
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'requests':meter.calls,'checks':record.get('checks',{}),'error_code':record.get('error_code'),'report':str(args.out)},ensure_ascii=False))
    return 0 if record.get('checks') and all(record['checks'].values()) else 1


if __name__=='__main__': raise SystemExit(main())
