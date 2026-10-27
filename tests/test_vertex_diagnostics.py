import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from tester.agent import Decision, run_task
from tester.gemini_provider import create_decider, AuthenticationError, safe_error
from test_gemini_provider import CONFIG, result


class VertexDiagnostics(unittest.TestCase):
    def test_service_disabled_reaches_report_without_raw_body(self):
        body = {'error': {'message': 'PRIVATE-KEY-AND-BODY', 'details': [
            {'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'SERVICE_DISABLED'}]}}
        failure = safe_error(HTTPError('https://example.invalid', 403, 'private', {},
                                      io.BytesIO(json.dumps(body).encode())))
        class Page:
            def screenshot(self, **kwargs): pass
        class Browser:
            page = Page()
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def snapshot(self): return 'synthetic page'
        def decide(*args): raise failure
        with tempfile.TemporaryDirectory() as d, patch('tester.agent.Browser', Browser):
            report = run_task({'id': 'diagnostics'}, decide, Path(d),
                              {'max_steps': 1, 'timeout_seconds': 10})
        self.assertEqual(report['status'], 'provider_error')
        self.assertEqual(report['reason_code'], 'SERVICE_DISABLED')
        self.assertEqual(report['http_status'], 403)
        self.assertIn('SERVICE_DISABLED', report['error'])
        self.assertNotIn('PRIVATE-KEY-AND-BODY', json.dumps(report))

    def test_wait_and_api_duration_include_failed_call(self):
        clock = [0.0]
        def advance(seconds): clock[0] += seconds
        calls = []
        def sender(req, timeout):
            advance(0.25)
            calls.append(req)
            if len(calls) == 2:
                raise HTTPError(req.full_url, 403, 'private', {}, io.BytesIO(b'{}'))
            return result()
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'offline-placeholder'}, clear=True), \
             patch('tester.gemini_provider.time.monotonic', side_effect=lambda: clock[0]), \
             patch('tester.gemini_provider.time.sleep', side_effect=advance):
            decide = create_decider(dict(CONFIG, request_interval_seconds=1), 'instructions', Decision, sender)
            decide({}, 'page', [], 10)
            with self.assertRaises(AuthenticationError): decide({}, 'page', [], 10)
        self.assertEqual(decide.timing['api_requests'], 2)
        self.assertAlmostEqual(decide.timing['api_request_seconds'], 0.5)
        self.assertAlmostEqual(decide.timing['request_wait_seconds'], 0.75)

    def test_untrusted_reason_is_not_echoed(self):
        body = {'error': {'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo',
                                     'reason': 'private credential with spaces'}]}}
        failure = safe_error(HTTPError('https://example.invalid', 403, 'private', {},
                                      io.BytesIO(json.dumps(body).encode())))
        self.assertIsNone(failure.reason_code)
        self.assertNotIn('credential', str(failure))

if __name__ == '__main__': unittest.main()
