import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tester.agent import Decision,run_task
from tester.search_verifier import SearchVerifier

INITIAL=dict(query='',product_names=['Headphones','Keyboard','Mouse'],no_results_visible=False)
HEAD=dict(query=' HEAD ',product_names=['Headphones'],no_results_visible=False)
EMPTY=dict(query='zzzz',product_names=[],no_results_visible=True)

class SearchVerification(unittest.TestCase):
    def test_initial_state_and_wrong_results_fail(self):
        verifier=SearchVerifier()
        for state in [INITIAL,dict(HEAD,product_names=['Headphones','Mouse']),dict(EMPTY,no_results_visible=False)]:
            verifier.observe(state,'test.png')
        self.assertFalse(verifier.result()['passed'])
    def test_both_exact_search_outcomes_required(self):
        verifier=SearchVerifier();verifier.observe(HEAD,'01.png')
        self.assertFalse(verifier.result()['passed'])
        verifier.observe(EMPTY,'02.png')
        self.assertTrue(verifier.result()['passed'])
        self.assertEqual(len(verifier.result()['evidence']),2)
    def test_normalized_query_alone_does_not_test_outer_spaces(self):
        verifier=SearchVerifier();verifier.observe(dict(HEAD,query='head'),'01.png');verifier.observe(EMPTY,'02.png')
        self.assertFalse(verifier.result()['passed'])
    def run_mock(self,complete):
        class Page:
            def screenshot(self,**kwargs):Path(kwargs['path']).write_bytes(b'unit-test placeholder, not browser evidence')
        class Browser:
            page=Page();state=INITIAL
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def snapshot(self):return str(self.state)
            def search_state(self):return self.state
            def action(self,a):self.state=HEAD if a['value']==' HEAD ' else EMPTY
        decisions=[]
        if complete:
            decisions += [Decision(action='fill',role='searchbox',name='Search products',value=q,summary='',task_completed=False,bugs=[]) for q in [' HEAD ','zzzz']]
        decisions.append(Decision(action='finish',role='',name='',value='',summary='Claimed success',task_completed=True,bugs=[]))
        iterator=iter(decisions)
        with tempfile.TemporaryDirectory() as d,patch('tester.agent.Browser',Browser):
            return run_task({'id':'search'},lambda *args:(next(iterator),{}),Path(d),{'max_steps':5,'timeout_seconds':10})
    def test_false_immediate_completion_rejected(self):
        report=self.run_mock(False)
        self.assertTrue(report['model_claimed_completed'])
        self.assertFalse(report['task_completed'])
        self.assertEqual(report['completion_verification'],'not_verified')
    def test_observed_outcomes_allow_completion(self):
        report=self.run_mock(True)
        self.assertTrue(report['task_completed'])
        self.assertEqual(report['completion_verification'],'verified_search_outcomes')

if __name__=='__main__':unittest.main()
