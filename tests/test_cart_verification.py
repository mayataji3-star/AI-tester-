import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tester.agent import Decision, run_task
from tester.cart_verifier import CartVerifier

EMPTY={'rows':[],'total':'Total: £0.00'}
def state(headphones,mouse):
    rows=[{'product':'Headphones','quantity':str(headphones),'subtotal':f'£{headphones*20:.2f}'}]
    if mouse:rows.append({'product':'Mouse','quantity':str(mouse),'subtotal':f'£{mouse*10:.2f}'})
    return {'rows':rows,'total':f'Total: £{headphones*20+mouse*10:.2f}'}

class CartVerification(unittest.TestCase):
    def test_all_three_states_required_in_order(self):
        v=CartVerifier()
        v.observe(state(3,0),'out-of-order.png')
        self.assertFalse(v.result()['initial_cart_correct'])
        for i,s in enumerate([state(2,1),state(3,1),state(3,0)]):
            v.observe(s,f'{i}.png')
            self.assertEqual(v.result()['passed'],i==2)
        self.assertEqual(len(v.result()['evidence']),3)
    def test_wrong_total_subtotal_missing_input_and_duplicate_rows_rejected(self):
        for bad in ['total','subtotal','quantity','duplicate']:
            with self.subTest(bad=bad):
                s=state(2,1)
                if bad=='total':s['total']='Total: £40.00'
                if bad=='subtotal':s['rows'][0]['subtotal']='£20.00'
                if bad=='quantity':s['rows'][0]['quantity']=None
                if bad=='duplicate':s['rows'].append(s['rows'][0].copy())
                v=CartVerifier();v.observe(s,'bad.png')
                self.assertFalse(v.result()['initial_cart_correct'])
    def run_mock(self,states):
        class Page:
            def screenshot(self,**kwargs):Path(kwargs['path']).write_bytes(b'unit-test placeholder only')
        class Browser:
            page=Page();index=0
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def snapshot(self):return str(states[self.index])
            def cart_state(self):return states[self.index]
            def action(self,a):self.index+=1
        def decide(task,observation,history,remaining):
            done=len(history)==len(states)-1
            return Decision(action='finish' if done else 'click',role='' if done else 'button',
                            name='',value='',summary='Mock claim',task_completed=done,bugs=[]),{}
        with tempfile.TemporaryDirectory() as d,patch('tester.agent.Browser',Browser):
            return run_task({'id':'cart'},decide,Path(d),{'max_steps':8,'timeout_seconds':10})
    def test_initial_finish_does_not_pass(self):
        report=self.run_mock([EMPTY])
        self.assertIn('Finish rejected',report['history'][0]['tool_error'])
        self.assertFalse(report['task_completed'])
        self.assertEqual(report['completion_verification'],'not_verified')
    def test_observed_checkpoints_pass(self):
        report=self.run_mock([EMPTY,state(2,1),state(3,1),state(3,0)])
        self.assertTrue(report['task_completed'])
        self.assertEqual(report['completion_verification'],'verified_cart_outcomes')

if __name__=='__main__':unittest.main()
