"""Check executed submissions against cart, visible message and native validity."""
from copy import deepcopy
from .cart_verifier import matches


class CheckoutVerifier:
    def __init__(self):
        self.empty_rejected = False
        self.invalid_rejected = False
        self.success = False
        self.evidence = []

    def record(self, action, before, after, screenshot):
        if (action.get('action'), action.get('role'), action.get('name')) != (
                'click', 'button', 'Place demo order'):
            return
        empty_before = matches(before, {}, 0)
        mouse_before = matches(before, {'Mouse': 1}, 10)
        empty_after = matches(after, {}, 0)
        confirmed = after.get('message') == 'Demo order placed. No payment taken.'
        checkpoint = None
        if (empty_before and before.get('email_valid') is True and empty_after
                and after.get('message') == 'Your cart is empty.'):
            self.empty_rejected = True
            checkpoint = 'empty_cart_rejected'
        elif (self.empty_rejected and mouse_before and before.get('email_type_mismatch') is True
              and before.get('email_valid') is False and matches(after, {'Mouse': 1}, 10)
              and after.get('email_valid') is False and not confirmed):
            self.invalid_rejected = True
            checkpoint = 'invalid_email_rejected'
        elif (self.empty_rejected and self.invalid_rejected and mouse_before
              and before.get('email_valid') is True and empty_after and confirmed
              and before.get('message') != after.get('message')):
            self.success = True
            checkpoint = 'valid_checkout_confirmed_and_cart_cleared'
        if checkpoint:
            self.evidence.append(deepcopy(dict(checkpoint=checkpoint, before=before,
                                               after=after, screenshot=screenshot)))

    def result(self):
        return dict(empty_cart_rejected=self.empty_rejected,
                    invalid_email_rejected=self.invalid_rejected,
                    valid_checkout_confirmed_and_cart_cleared=self.success,
                    passed=self.empty_rejected and self.invalid_rejected and self.success,
                    evidence=deepcopy(self.evidence))
