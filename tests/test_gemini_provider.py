import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from tester.agent import Decision
from tester.gemini_provider import create_decider,ModelResponseError,GeminiAPIError,RateLimitError,AuthenticationError

CONFIG=dict(provider='gemini',model='gemini-3.5-flash-lite',temperature=0.2,request_interval_seconds=0)
DECISION=dict(action='click',role='button',name='Add Headphones to cart',value='',summary='Next action',task_completed=False,bugs=[])
def result(decision=DECISION,finish='STOP'):
    return dict(candidates=[dict(finishReason=finish,content=dict(parts=[{'text':json.dumps(decision)}]))],
                usageMetadata=dict(promptTokenCount=100,candidatesTokenCount=30,totalTokenCount=130),modelVersion='gemini-test-version')

class GeminiAdapter(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'GEMINI_API_KEY':'offline-placeholder'},clear=True);self.env.start();self.addCleanup(self.env.stop)
    def test_gemini_endpoint_key_header_schema_and_metadata(self):
        calls=[]
        def sender(req,timeout):
            calls.append(req)
            self.assertEqual(req.full_url,'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent')
            self.assertNotIn('offline-placeholder',req.full_url)
            self.assertEqual(req.get_header('X-goog-api-key'),'offline-placeholder')
            body=json.loads(req.data)
            self.assertEqual(body['generationConfig']['responseMimeType'],'application/json')
            self.assertFalse(body['generationConfig']['responseJsonSchema']['additionalProperties'])
            self.assertLessEqual(timeout,45)
            payload=json.loads(body['contents'][0]['parts'][0]['text'])
            self.assertNotIn('observation',payload['actions'][0])
            return result()
        decide=create_decider(CONFIG,'instructions',Decision,sender)
        d,u=decide({'id':'cart'},'current page',[{'step':0,'decision':DECISION,'observation':'old snapshot'}],20)
        self.assertEqual(d.action,'click');self.assertEqual(u['total_tokens'],130)
        self.assertEqual(u['response_model'],'gemini-test-version');self.assertEqual(len(calls),1)
    def test_other_provider_keys_are_not_used(self):
        with patch.dict(os.environ,{'GROQ_API_KEY':'offline-placeholder'},clear=True):
            with self.assertRaisesRegex(ValueError,'GEMINI_API_KEY'):create_decider(CONFIG,'x',Decision)
    def test_invalid_schema_and_incomplete_result_rejected(self):
        for payload in [result(dict(DECISION,action='execute_code')),result(dict(DECISION,task_completed='true')),result(finish='MAX_TOKENS'),{'candidates':[]}]:
            with self.subTest(payload=payload):
                with self.assertRaises(ModelResponseError):
                    create_decider(CONFIG,'x',Decision,lambda *a,**k:payload)({},'page',[],20)
    def test_quota_error_sanitized_with_retry_delay(self):
        def sender(req,timeout):
            body={'error':{'message':'DO-NOT-LOG-THIS','details':[{'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':'42s'}]}}
            raise HTTPError(req.full_url,429,'rate limit',{},io.BytesIO(json.dumps(body).encode()))
        with self.assertRaises(RateLimitError) as caught:
            create_decider(CONFIG,'x',Decision,sender)({},'page',[],20)
        self.assertEqual(caught.exception.retry_after_seconds,42)
        self.assertEqual(caught.exception.http_status,429)
        self.assertNotIn('DO-NOT-LOG-THIS',str(caught.exception))
    def test_key_error_is_distinguished_from_model_unavailable(self):
        for status,expected in [(401,AuthenticationError),(404,GeminiAPIError)]:
            with self.subTest(status=status):
                def sender(req,timeout):raise HTTPError(req.full_url,status,'private body',{},io.BytesIO(b'{}'))
                with self.assertRaises(expected):create_decider(CONFIG,'x',Decision,sender)({},'page',[],20)
    def test_model_cannot_override_google_endpoint(self):
        with self.assertRaises(ValueError):create_decider(dict(CONFIG,model='../../another-host'),'x',Decision)

if __name__=='__main__':unittest.main()
