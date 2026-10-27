import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tester.agent import Decision, run_task
from tester.quantity_verifier import QuantityVerifier
from tester.checkout_verifier import CheckoutVerifier


def cart(quantity=1, product='Headphones'):
    price = 20 if product == 'Headphones' else 10
    return {'rows': [{'product': product, 'quantity': str(quantity), 'subtotal': f'£{quantity*price:.2f}'}],
            'total': f'Total: £{quantity*price:.2f}'}


def checkout(empty=False, valid=True, mismatch=False, message=''):
    return dict({'rows': [], 'total': 'Total: £0.00'} if empty else cart(1, 'Mouse'),
                email='test@example.com' if valid else 'invalid-email', email_valid=valid,
                email_type_mismatch=mismatch, message=message)


def action(kind, value='', role='spinbutton', name='Quantity for Headphones'):
    return dict(action=kind, value=value, role=role, name=name)


SUBMIT = action('click', role='button', name='Place demo order')


class QuantityChecks(unittest.TestCase):
    def attempt(self, v, value, after=None):
        before = cart()
        editing = cart(); editing['rows'][0]['quantity'] = value
        v.record(action('fill', value), before, editing, 'fill.png')
        v.record(action('press', 'Tab'), editing, after or cart(), 'committed.png')

    def test_all_invalid_attempts_and_valid_total_required(self):
        v = QuantityVerifier()
        for value in ('0', '-1', '1.5'):
            self.attempt(v, value)
            self.assertFalse(v.result()['passed'])
        self.attempt(v, '2', cart(2))
        self.assertTrue(v.result()['passed'])
        self.assertEqual(len(v.result()['evidence']), 4)

    def test_no_commit_or_skipped_case_does_not_pass(self):
        v = QuantityVerifier()
        for value in ('0', '-1'):
            self.attempt(v, value)
        self.attempt(v, '2', cart(2))
        self.assertFalse(v.result()['passed'])
        v = QuantityVerifier()
        v.record(action('fill', '0'), cart(), cart(), 'fill.png')
        v.record(action('click'), cart(), cart(), 'same-field.png')
        self.assertFalse(v.result()['invalid_quantities_rejected']['0'])

    def test_accepted_invalid_value_or_wrong_totals_are_rejected(self):
        for value in ('0', '-1', '1.5'):
            with self.subTest(value=value):
                v = QuantityVerifier()
                bad = cart(); bad['rows'][0]['quantity'] = value
                self.attempt(v, value, bad)
                self.assertFalse(v.result()['invalid_quantities_rejected'][value])
        v = QuantityVerifier()
        for value in ('0', '-1', '1.5'): self.attempt(v, value)
        bad = cart(2); bad['total'] = 'Total: £20.00'
        self.attempt(v, '2', bad)
        self.assertFalse(v.result()['passed'])


class CheckoutChecks(unittest.TestCase):
    def prepare(self):
        v = CheckoutVerifier()
        v.record(SUBMIT, checkout(empty=True), checkout(empty=True, message='Your cart is empty.'), 'empty.png')
        return v

    def test_full_submission_sequence(self):
        v = self.prepare()
        before = checkout(valid=False, mismatch=True, message='Your cart is empty.')
        v.record(SUBMIT, before, before, 'invalid.png')
        v.record(SUBMIT, checkout(), checkout(empty=True, message='Demo order placed. No payment taken.'), 'success.png')
        self.assertTrue(v.result()['passed'])
        self.assertEqual(len(v.result()['evidence']), 3)

    def test_blank_email_does_not_prove_empty_cart_rejection(self):
        v = CheckoutVerifier()
        v.record(SUBMIT, checkout(empty=True, valid=False), checkout(empty=True, valid=False), 'blank.png')
        self.assertFalse(v.result()['empty_cart_rejected'])

    def test_skipped_invalid_submission_or_accepted_invalid_email_fails(self):
        v = self.prepare()
        v.record(SUBMIT, checkout(), checkout(empty=True, message='Demo order placed. No payment taken.'), 'success.png')
        self.assertFalse(v.result()['passed'])
        v = self.prepare()
        v.record(SUBMIT, checkout(valid=False, mismatch=True),
                 checkout(empty=True, valid=False, mismatch=True, message='Demo order placed. No payment taken.'), 'bad.png')
        self.assertFalse(v.result()['invalid_email_rejected'])

    def test_confirmation_without_clearing_cart_is_not_success(self):
        v = self.prepare()
        bad_email = checkout(valid=False, mismatch=True)
        v.record(SUBMIT, bad_email, bad_email, 'invalid.png')
        v.record(SUBMIT, checkout(), checkout(message='Demo order placed. No payment taken.'), 'bad.png')
        self.assertFalse(v.result()['passed'])


class AgentVerificationIntegration(unittest.TestCase):
    def run_mock(self, task, states, actions, tool_failure=False):
        class Page:
            def screenshot(self, **kwargs): Path(kwargs['path']).write_bytes(b'offline placeholder')
        class Browser:
            page = Page()
            index = 0
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def snapshot(self): return str(states[self.index])
            def cart_state(self): return states[self.index]
            def checkout_state(self): return states[self.index]
            def action(self, decision):
                if tool_failure: raise ValueError('offline action failed')
                self.index += 1
        def decide(task, observation, history, remaining):
            d = actions[len(history)] if len(history) < len(actions) else action('finish', role='', name='')
            return Decision(**d, summary='offline claim', task_completed=d['action']=='finish', bugs=[]), {}
        with tempfile.TemporaryDirectory() as d, patch('tester.agent.Browser', Browser):
            return run_task({'id': task}, decide, Path(d), {'max_steps': 20, 'timeout_seconds': 10})

    def test_immediate_false_finish_fails_both_tasks(self):
        for task, state in [('quantity', cart()), ('checkout', checkout(empty=True))]:
            with self.subTest(task=task):
                report = self.run_mock(task, [state], [])
                self.assertTrue(report['model_claimed_completed'])
                self.assertFalse(report['task_completed'])
                self.assertEqual(report['completion_verification'], 'not_verified')

    def test_quantity_success_reaches_report_with_evidence(self):
        states = [cart()]; actions = []
        for value in ('0', '-1', '1.5', '2'):
            edited = cart(); edited['rows'][0]['quantity'] = value
            states.extend([edited, cart(2) if value=='2' else cart()])
            actions.extend([action('fill', value), action('press', 'Tab')])
        report = self.run_mock('quantity', states, actions)
        self.assertTrue(report['task_completed'])
        self.assertEqual(report['completion_verification'], 'verified_quantity_outcomes')
        self.assertEqual(len(report['independent_checks']['evidence']), 4)
        self.assertIn('observed_after', report['history'][0])

    def test_checkout_success_reaches_report(self):
        invalid = checkout(valid=False, mismatch=True)
        states = [checkout(empty=True), checkout(empty=True, message='Your cart is empty.'),
                  checkout(message='Your cart is empty.'), invalid, invalid, checkout(), checkout(empty=True, message='Demo order placed. No payment taken.')]
        actions = [SUBMIT, action('click', role='button', name='Add Mouse to cart'), action('fill', 'invalid-email', 'textbox', 'Email address'), SUBMIT,
                   action('fill', 'test@example.com', 'textbox', 'Email address'), SUBMIT]
        report = self.run_mock('checkout', states, actions)
        self.assertTrue(report['task_completed'])
        self.assertEqual(report['completion_verification'], 'verified_checkout_outcomes')

    def test_failed_browser_actions_cannot_supply_evidence(self):
        report = self.run_mock('quantity', [cart()], [action('fill', '0'), action('press', 'Tab')], tool_failure=True)
        self.assertFalse(report['task_completed'])
        self.assertEqual(report['independent_checks']['evidence'], [])

if __name__ == '__main__': unittest.main()
