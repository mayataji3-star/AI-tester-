"""Independent checks of the specified search outcomes, using observed UI state.
This checks results, not an action path. It never reads application source.
"""
class SearchVerifier:
    def __init__(self):
        self.head_only = False
        self.no_results = False
        self.evidence = []

    def observe(self, state, screenshot):
        head = (state['query'] == ' HEAD ' and
                state['product_names'] == ['Headphones'] and
                not state['no_results_visible'])
        empty = (state['query'] == 'zzzz' and
                 state['product_names'] == [] and
                 state['no_results_visible'])
        if head or empty:
            self.evidence.append(dict(state, screenshot=screenshot))
        self.head_only = self.head_only or head
        self.no_results = self.no_results or empty

    def result(self):
        return dict(head_only=self.head_only, no_results=self.no_results,
                    passed=self.head_only and self.no_results, evidence=self.evidence)
