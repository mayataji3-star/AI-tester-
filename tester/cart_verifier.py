"""Check cart outcomes from rendered UI state, independently of AI claims."""
from decimal import Decimal, InvalidOperation


def pounds(text, expected):
    if not isinstance(text, str):
        return False
    value=text.strip()
    if value.startswith('Total:'):
        value=value[len('Total:'):].strip()
    if not value.startswith('£'):
        return False
    try:
        return Decimal(value[1:]) == Decimal(expected)
    except InvalidOperation:
        return False


def matches(state, quantities, total):
    rows=state.get('rows', [])
    if len(rows)!=len(quantities):
        return False
    by_name={row.get('product'):row for row in rows}
    if len(by_name)!=len(rows) or set(by_name)!=set(quantities):
        return False
    prices={'Headphones':20, 'Mouse':10}
    for name, count in quantities.items():
        row=by_name[name]
        if row.get('quantity') != str(count) or not pounds(row.get('subtotal'), str(prices[name]*count)):
            return False
    return pounds(state.get('total'), str(total))


class CartVerifier:
    def __init__(self):
        self.stage=0
        self.evidence=[]

    def observe(self, state, screenshot):
        expected=[({'Headphones':2,'Mouse':1},50),
                  ({'Headphones':3,'Mouse':1},70),
                  ({'Headphones':3},60)]
        if self.stage < len(expected):
            quantities,total=expected[self.stage]
            if matches(state,quantities,total):
                self.evidence.append(dict(state,checkpoint=self.stage+1,screenshot=screenshot))
                self.stage+=1

    def result(self):
        return dict(initial_cart_correct=self.stage>=1, updated_quantity_correct=self.stage>=2,
                    mouse_removed_correct=self.stage>=3, passed=self.stage==3, evidence=self.evidence)
