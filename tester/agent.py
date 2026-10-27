import argparse,json,os,time
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict
from .browser import Browser
from .gemini_provider import GeminiAPIError
from .search_verifier import SearchVerifier
from .cart_verifier import CartVerifier
from .quantity_verifier import QuantityVerifier
from .checkout_verifier import CheckoutVerifier
ROOT=Path(__file__).resolve().parents[1]
class Bug(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requirement_id:str
    expected:str
    actual:str
    steps:list[str]
class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action:Literal['click','fill','press','finish']
    role:str
    name:str
    value:str
    summary:str
    task_completed:bool
    bugs:list[Bug]

def run_task(task,decide,out,config):
    out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();history=[];usage=[];status='step_limit';final=None
    timing_start = dict(getattr(decide, 'timing', {}))
    report={'task':task,'engine':'ai','config':config,'claims':[]}
    search_verifier=SearchVerifier() if task.get('id')=='search' else None
    cart_verifier=CartVerifier() if task.get('id')=='cart' else None
    action_verifier = {'quantity': QuantityVerifier, 'checkout': CheckoutVerifier}.get(task.get('id'))
    action_verifier = action_verifier() if action_verifier else None
    try:
        with Browser() as b:
            for i in range(config['max_steps']):
                remaining=config['timeout_seconds']-(time.monotonic()-started)
                if remaining<=0:status='timeout';break
                observation=b.snapshot()
                b.page.screenshot(path=str(out/f'{i:02d}.png'),full_page=True)
                if search_verifier is not None:
                    search_verifier.observe(b.search_state(), f'{i:02d}.png')
                if cart_verifier is not None:
                    cart_verifier.observe(b.cart_state(), f'{i:02d}.png')
                decision,tokens=decide(task,observation,history,remaining)
                d=decision.model_dump();usage.append(tokens)
                entry={'step':i,'observation':observation,'decision':d,'screenshot':f'{i:02d}.png'}
                history.append(entry)
                if d['action'] == 'finish':
                    acted = any(
                        item['decision']['action'] in ('click', 'fill', 'press')
                        and 'tool_error' not in item
                        for item in history
                    )
                    if task.get('id') == 'cart' and not acted:
                        entry['tool_error'] = (
                            'Finish rejected: no browser actions were executed. '
                            'Choose one actual click action on an observed Add button.'
                        )
                        continue
                    final = d
                    status = 'finished'
                    break
                before = None
                if action_verifier is not None:
                    before = b.checkout_state() if task['id'] == 'checkout' else b.cart_state()
                try:
                    b.action(d)
                except Exception as e:
                    entry['tool_error'] = type(e).__name__+': '+str(e)
                    if isinstance(action_verifier, QuantityVerifier):
                        action_verifier.pending = None
                else:
                    if action_verifier is not None:
                        after = b.checkout_state() if task['id'] == 'checkout' else b.cart_state()
                        evidence_file = f'after-{i:02d}.png'
                        b.page.screenshot(path=str(out/evidence_file), full_page=True)
                        action_verifier.record(d, before, after, evidence_file)
                        entry['observed_before'] = before
                        entry['observed_after'] = after
                        entry['after_screenshot'] = evidence_file
            b.page.screenshot(path=str(out/'final.png'),full_page=True)
    except TimeoutError:
        status='timeout';report['error']='Task time budget exhausted.'
    except Exception as e:
        # Never put API response bodies, request headers, or credentials in reports.
        error_type=type(e).__name__
        if isinstance(e, GeminiAPIError):
            status = 'rate_limited' if error_type == 'RateLimitError' else 'provider_error'
            report['error'] = str(e)
            for field in ('http_status', 'retry_after_seconds', 'reason_code'):
                value = getattr(e, field, None)
                if value is not None:
                    report[field] = value
        elif error_type=='RateLimitError':
            status='rate_limited';report['error']=config.get('provider','AI').capitalize()+' quota reached. Wait or reduce runs; no paid fallback was attempted.'
            if getattr(e,'retry_after_seconds',None) is not None:
                report['retry_after_seconds']=e.retry_after_seconds
            if getattr(e,'http_status',None) is not None:
                report['http_status']=e.http_status
        elif error_type in ('AuthenticationError','PermissionDeniedError'):
            status='provider_error';report['error']=config.get('provider','AI').capitalize()+' key or model permission rejected. Check your local setup.'
        elif error_type=='GeminiAPIError':
            status='provider_error';report['error']=str(e)
            if getattr(e,'http_status',None) is not None:
                report['http_status']=e.http_status
        elif error_type in ('ModelResponseError','APIConnectionError','APIStatusError','APITimeoutError','BadRequestError','NotFoundError','InternalServerError','UnprocessableEntityError'):
            status='provider_error';report['error']=error_type+'; no usable model result. Check the configured provider and service status.'
        else:
            status='infrastructure_error';report['error']=error_type+'; check the local shop and Chromium setup.'
    report.update(status=status,elapsed_seconds=round(time.monotonic()-started,3),history=history,usage=usage,
        task_completed=bool(final and final['task_completed']),summary=final['summary'] if final else '',
        claims=[dict(x,verification='pending',evidence='final.png') for x in final['bugs']] if final else [])
    totals = getattr(decide, 'timing', {})
    timing_delta = {name: totals.get(name, 0) - timing_start.get(name, 0)
                    for name in ('request_wait_seconds', 'api_request_seconds', 'api_requests')}
    elapsed = time.monotonic() - started
    report['elapsed_seconds'] = round(elapsed, 3)
    report['timing'] = {
        **{name: round(value, 3) for name, value in timing_delta.items()},
        'execution_seconds_excluding_request_wait': round(max(0, elapsed - timing_delta['request_wait_seconds']), 3),
    }
    report['model_claimed_completed'] = bool(final and final['task_completed'])
    if search_verifier is not None:
        verification = search_verifier.result()
        report['independent_checks'] = verification
        report['task_completed'] = bool(final and final['task_completed'] and verification['passed'])
        report['completion_verification'] = 'verified_search_outcomes' if report['task_completed'] else 'not_verified'
    elif cart_verifier is not None:
        verification = cart_verifier.result()
        report['independent_checks'] = verification
        report['task_completed'] = bool(final and final['task_completed'] and verification['passed'])
        report['completion_verification'] = 'verified_cart_outcomes' if report['task_completed'] else 'not_verified'
    elif action_verifier is not None:
        verification = action_verifier.result()
        report['independent_checks'] = verification
        report['task_completed'] = bool(final and final['task_completed'] and verification['passed'])
        report['completion_verification'] = ('verified_'+task['id']+'_outcomes') if report['task_completed'] else 'not_verified'
    else:
        report['completion_verification'] = 'model_claim_only'
    (out/'report.json').write_text(json.dumps(report,indent=2), encoding='utf-8')
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repeats',type=int,default=1)
    parser.add_argument('--task',help='Run one task ID, e.g. search, before attempting the full suite.')
    args=parser.parse_args()
    if args.repeats < 1:parser.error('--repeats must be at least 1')
    config=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    if config.get('provider')!='gemini':raise SystemExit('Set provider to gemini in config.json.')
    if not os.getenv('GEMINI_API_KEY'):raise SystemExit('Set GEMINI_API_KEY locally; never put it in code or send it in chat.')
    tasks=json.loads((ROOT/'docs/tasks.json').read_text(encoding='utf-8'))
    if args.task:
        tasks=[task for task in tasks if task['id']==args.task]
        if not tasks:parser.error('Unknown task ID. See docs/tasks.json.')
    from .gemini_provider import create_decider
    instructions=(ROOT/'docs/ai_instructions.txt').read_text(encoding='utf-8')+'\n'+(ROOT/'docs/requirements.md').read_text(encoding='utf-8')
    decide=create_decider(config,instructions,Decision)
    stamp=time.strftime('%Y%m%d-%H%M%S')
    failed=False
    for repeat in range(args.repeats):
        for task in tasks:
            out=ROOT/'results/runs'/f'ai-gemini-{stamp}'/f'run-{repeat+1}'/task['id']
            report=run_task(task,decide,out,config)
            print(task['id'],report['status'],report['task_completed'])
            if report['status']!='finished' or not report['task_completed']:failed=True
            if report['status'] in ('rate_limited','provider_error'):
                print(report['error'])
                raise SystemExit(1)
    raise SystemExit(1 if failed else 0)
if __name__=='__main__':main()
