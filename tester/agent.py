import argparse,json,os,time
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from .browser import Browser
ROOT=Path(__file__).resolve().parents[1]
class Bug(BaseModel):
    requirement_id:str
    expected:str
    actual:str
    steps:list[str]
class Decision(BaseModel):
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
    report={'task':task,'engine':'ai','config':config,'claims':[]}
    try:
        with Browser() as b:
            for i in range(config['max_steps']):
                remaining=config['timeout_seconds']-(time.monotonic()-started)
                if remaining<=0:status='timeout';break
                observation=b.snapshot()
                b.page.screenshot(path=str(out/f'{i:02d}.png'),full_page=True)
                decision,tokens=decide(task,observation,history,remaining)
                d=decision.model_dump();usage.append(tokens)
                entry={'step':i,'observation':observation,'decision':d,'screenshot':f'{i:02d}.png'}
                history.append(entry)
                if d['action']=='finish':
                    final=d;status='finished';break
                try:b.action(d)
                except Exception as e:entry['tool_error']=type(e).__name__+': '+str(e)
            b.page.screenshot(path=str(out/'final.png'),full_page=True)
    except Exception as e:
        status='infrastructure_error';report['error']=type(e).__name__+': '+str(e)
    report.update(status=status,elapsed_seconds=round(time.monotonic()-started,3),history=history,usage=usage,
        task_completed=bool(final and final['task_completed']),summary=final['summary'] if final else '',
        claims=[dict(x,verification='pending',evidence='final.png') for x in final['bugs']] if final else [])
    (out/'report.json').write_text(json.dumps(report,indent=2))
    return report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repeats',type=int,default=1);args=parser.parse_args()
    config=json.loads((ROOT/'config.json').read_text())
    if not config['trainer_reviewed']:raise SystemExit('Send docs/trainer_message.txt to your trainer first. Set trainer_reviewed=true only after their review.')
    if not os.getenv('OPENAI_API_KEY'):raise SystemExit('Set OPENAI_API_KEY locally; never put it in code or send it in chat.')
    from openai import OpenAI
    client=OpenAI(max_retries=0)
    instructions=(ROOT/'docs/ai_instructions.txt').read_text()+'\n'+(ROOT/'docs/requirements.md').read_text()
    def decide(task,observation,history,remaining):
        response=client.responses.parse(model=config['model'],temperature=config['temperature'],store=False,
            max_output_tokens=1500,timeout=max(0.1,min(45,remaining)),text_format=Decision,
            input=[{'role':'system','content':instructions},{'role':'user','content':json.dumps({'task':task,'page':observation,'history':history})}])
        if response.output_parsed is None:raise RuntimeError('No parsed decision (refusal or incomplete output)')
        return response.output_parsed,response.usage.model_dump() if response.usage else {}
    stamp=time.strftime('%Y%m%d-%H%M%S')
    for repeat in range(args.repeats):
        for task in json.loads((ROOT/'docs/tasks.json').read_text()):
            out=ROOT/'results/runs'/f'ai-{stamp}'/f'run-{repeat+1}'/task['id']
            report=run_task(task,decide,out,config)
            print(task['id'],report['status'],report['task_completed'])
if __name__=='__main__':main()
