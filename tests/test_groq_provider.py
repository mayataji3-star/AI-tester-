import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from groq import Groq
from tester.agent import Decision, run_task
from tester.groq_provider import create_decider, ModelResponseError

DECISION=dict(action='finish',role='',name='',value='',summary='Healthy task',task_completed=True,bugs=[])
CONFIG=dict(provider='groq',model='openai/gpt-oss-20b',temperature=0.2,request_interval_seconds=0,max_steps=2,timeout_seconds=10)

def sdk(handler):
    return Groq(api_key='offline-placeholder',max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(handler),trust_env=False))

def completion(content=None,finish='stop'):
    return dict(id='offline',object='chat.completion',created=1,model=CONFIG['model'],
                choices=[dict(index=0,finish_reason=finish,message=dict(role='assistant',content=content))],
                usage=dict(prompt_tokens=10,completion_tokens=5,total_tokens=15))

class GroqAdapter(unittest.TestCase):
    def test_request_uses_groq_and_strict_schema(self):
        def handler(request):
            self.assertEqual(request.url.host,'api.groq.com')
            self.assertEqual(request.url.path,'/openai/v1/chat/completions')
            body=json.loads(request.content)
            self.assertEqual(body['model'],CONFIG['model'])
            schema=body['response_format']['json_schema']
            self.assertTrue(schema['strict'])
            self.assertFalse(schema['schema']['additionalProperties'])
            self.assertFalse(schema['schema']['$defs']['Bug']['additionalProperties'])
            self.assertNotIn('store',body)
            payload=json.loads(body['messages'][1]['content'])
            self.assertNotIn('observation',payload['actions'][0])
            return httpx.Response(200,json=completion(json.dumps(DECISION)))
        decide=create_decider(CONFIG,'instructions',Decision,client=sdk(handler))
        decision,usage=decide({'id':'search'},'current page',[{'step':0,'decision':DECISION,'observation':'old large snapshot'}],10)
        self.assertEqual(decision.action,'finish');self.assertEqual(usage['total_tokens'],15)
    def test_invalid_action_and_extra_fields_rejected(self):
        for bad in [dict(DECISION,action='execute'),dict(DECISION,secret='extra'),dict(DECISION,task_completed='true')]:
            with self.subTest(bad=bad):
                client=sdk(lambda request:httpx.Response(200,json=completion(json.dumps(bad))))
                decide=create_decider(CONFIG,'instructions',Decision,client=client)
                with self.assertRaises(ModelResponseError):decide({},'page',[],10)
    def test_truncated_output_rejected(self):
        client=sdk(lambda request:httpx.Response(200,json=completion(json.dumps(DECISION),'length')))
        with self.assertRaises(ModelResponseError):create_decider(CONFIG,'x',Decision,client=client)({},'page',[],10)
    def test_openai_key_does_not_substitute_for_groq_key(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'offline-placeholder'},clear=True):
            with self.assertRaisesRegex(ValueError,'GROQ_API_KEY'):
                create_decider(CONFIG,'x',Decision)
    def test_rate_limit_recorded_without_leaking_response(self):
        calls=[]
        def handler(request):
            calls.append(request)
            return httpx.Response(429,json={'error':{'message':'SENSITIVE-RESPONSE','type':'rate_limit_error'}})
        decide=create_decider(CONFIG,'x',Decision,client=sdk(handler))
        class Page:
            def screenshot(self,**kwargs):Path(kwargs['path']).write_bytes(b'offline')
        class Browser:
            page=Page()
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def snapshot(self):return 'snapshot'
            def search_state(self):return dict(query='',product_names=[],no_results_visible=False)
        with tempfile.TemporaryDirectory() as d,patch('tester.agent.Browser',Browser):
            report=run_task({'id':'search'},decide,Path(d),CONFIG)
            self.assertEqual(report['status'],'rate_limited')
            self.assertNotIn('SENSITIVE-RESPONSE',json.dumps(report))
            self.assertEqual(len(calls),1)
            self.assertFalse(report['task_completed'])

if __name__=='__main__':unittest.main()
