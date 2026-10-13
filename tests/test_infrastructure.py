import unittest,tempfile
from pathlib import Path
from tester.browser import local_url
from tester.agent import Decision,run_task
class Infrastructure(unittest.TestCase):
    def test_allowlist(self):
        self.assertTrue(local_url('http://127.0.0.1:8000/'))
        for url in ['https://example.com','http://127.0.0.1:9000/','http://127.0.0.1.evil:8000/']:
            self.assertFalse(local_url(url))
    def test_offline_agent_plumbing(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            # Do not turn a missing browser into a fake passing browser result.
            if not Path(pw.chromium.executable_path).exists():
                self.skipTest('Chromium not installed; browser smoke remains unverified')
        # This uses fixed decisions, NOT an AI model; never score as AI results.
        decisions=iter([
            Decision(action='fill',role='searchbox',name='Search products',value='head',summary='',task_completed=False,bugs=[]),
            Decision(action='finish',role='',name='',value='',summary='Offline smoke only',task_completed=True,bugs=[])])
        observations=[]
        def fake(task,page,history,remaining):observations.append(page);return next(decisions),{}
        with tempfile.TemporaryDirectory() as directory:
            r=run_task({'id':'smoke'},fake,Path(directory),{'max_steps':3,'timeout_seconds':20})
            self.assertEqual(r['status'],'finished');self.assertIn('Headphones',observations[1]);self.assertNotIn('Add Mouse to cart',observations[1])
            self.assertTrue((Path(directory)/'final.png').exists())

class Reports(unittest.TestCase):
    def test_disallows_unlisted_action(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            Decision(action='execute_code',role='',name='',value='',summary='',task_completed=False,bugs=[])
    def test_claim_is_pending_not_confirmed(self):
        from unittest.mock import patch
        from tester.agent import Bug
        class Page:
            def screenshot(self,**kwargs):Path(kwargs['path']).write_bytes(b'offline placeholder')
        class FakeBrowser:
            page=Page()
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def snapshot(self):return 'offline snapshot'
        def decide(*args):
            return Decision(action='finish',role='',name='',value='',summary='unverified claim',task_completed=False,
                bugs=[Bug(requirement_id='R4',expected='20',actual='10',steps=['Add Headphones'])]),{}
        with tempfile.TemporaryDirectory() as directory,patch('tester.agent.Browser',FakeBrowser):
            r=run_task({'id':'unit'},decide,Path(directory),{'max_steps':2,'timeout_seconds':10})
            self.assertEqual(r['claims'][0]['verification'],'pending')
            self.assertFalse(r['task_completed'])

if __name__=='__main__':unittest.main()
