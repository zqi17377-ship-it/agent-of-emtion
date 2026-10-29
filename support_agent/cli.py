import argparse
from .model_client import make_gateway
from .schemas import ModelCallError, EligibilityContext
from .session import new_session, clear_session
from .workflow import run_turn


def main():
    p=argparse.ArgumentParser(description='中文心理支持研究原型：仅输入虚构案例')
    p.add_argument('--live',action='store_true',help=argparse.SUPPRESS)
    p.parse_args()
    try:
        gateway=make_gateway()
    except ModelCallError as e:
        print('配置错误：'+str(e)+'。请参考 README 在本机配置 .env。'); return 2
    session=new_session()
    session.eligibility=EligibilityContext(adult_status='confirmed')
    print(f'心理支持研究原型 | {gateway.mode} | 仅限成年人虚构案例 | /clear 清除，/quit 退出')
    try:
        while True:
            try: text=input('你 > ')
            except (EOFError,KeyboardInterrupt): break
            if text.strip()=='/quit': break
            if text.strip()=='/clear':
                clear_session(session)
                session.eligibility=EligibilityContext(adult_status='confirmed')
                print('当前会话已清除。'); continue
            result=run_turn(session,text,gateway)
            print('助手 > '+result.text)
            print(f'[{result.status}; action={result.action}]')
    finally:
        if hasattr(gateway,'close'): gateway.close()
    return 0


if __name__=='__main__': raise SystemExit(main())
