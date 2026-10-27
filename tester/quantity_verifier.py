"""Verify quantity attempts using executed actions and rendered cart states."""
from copy import deepcopy
from .cart_verifier import matches


class QuantityVerifier:
    def __init__(self):
        self.invalid = {value: False for value in ('0', '-1', '1.5')}
        self.valid_two = False
        self.pending = None
        self.evidence = []

    def record(self, action, before, after, screenshot):
        target = action.get('role') == 'spinbutton' and action.get('name') == 'Quantity for Headphones'
        kind = action.get('action')
        if kind == 'fill':
            self.pending = None
            value = action.get('value')
            if target and value in (*self.invalid, '2') and matches(before, {'Headphones': 1}, 20):
                # Filling alone does not establish that validation/change was committed.
                self.pending = value
            return
        commits = (kind == 'press' and target and action.get('value') in ('Tab', 'Enter')) or (kind == 'click' and not target)
        if self.pending is None or not commits:
            return
        value = self.pending
        self.pending = None
        passed = matches(after, {'Headphones': 1}, 20) if value in self.invalid else (
            all(self.invalid.values()) and matches(after, {'Headphones': 2}, 40))
        if passed:
            if value in self.invalid:
                self.invalid[value] = True
            else:
                self.valid_two = True
            self.evidence.append(deepcopy(dict(attempted_quantity=value, before=before,
                                               after=after, screenshot=screenshot)))

    def result(self):
        return dict(invalid_quantities_rejected=dict(self.invalid),
                    valid_quantity_and_totals_correct=self.valid_two,
                    passed=all(self.invalid.values()) and self.valid_two,
                    evidence=deepcopy(self.evidence))
