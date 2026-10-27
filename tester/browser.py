from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

URL='http://127.0.0.1:8000/'
def local_url(url):
    p=urlsplit(url)
    return p.scheme=='http' and p.hostname=='127.0.0.1' and p.port==8000

class Browser:
    def __enter__(self):
        self.pw=sync_playwright().start()
        self.browser=self.pw.chromium.launch()
        self.context=self.browser.new_context(service_workers='block',accept_downloads=False)
        self.context.route('**/*',lambda route: route.continue_() if local_url(route.request.url) else route.abort())
        self.page=self.context.new_page()
        self.page.set_default_timeout(3000)
        self.page.goto(URL)
        return self
    def reset(self):
        self.page.reload()
    def snapshot(self):
        return self.page.locator('body').aria_snapshot()
    def search_state(self):
        return {
            'query': self.page.get_by_role('searchbox', name='Search products', exact=True).input_value(),
            'product_names': self.page.locator('#products article:visible h3').all_text_contents(),
            'no_results_visible': self.page.get_by_text('No products found.', exact=True).is_visible(),
        }
    def cart_state(self):
        rows=[]
        for row in self.page.locator('#cart tr:visible').all():
            cells=row.locator('td')
            field=row.get_by_role('spinbutton')
            rows.append({
                'product': cells.nth(0).inner_text().strip() if cells.count()>0 else None,
                'quantity': field.input_value() if field.count()==1 and field.is_visible() else None,
                'subtotal': cells.nth(2).inner_text().strip() if cells.count()>2 else None,
            })
        return {'rows': rows, 'total': self.page.locator('#total').inner_text().strip()}
    def checkout_state(self):
        state = self.cart_state()
        field = self.page.get_by_role('textbox', name='Email address', exact=True)
        state.update(field.evaluate("""element => ({
            email: element.value,
            email_valid: element.validity.valid,
            email_type_mismatch: element.validity.typeMismatch
        })"""))
        state['message'] = self.page.locator('#message').inner_text().strip()
        return state
    def action(self,a):
        if a['action']=='finish':return
        if a['action'] not in ('click','fill','press'):raise ValueError('Action not permitted')
        target=self.page.get_by_role(a['role'],name=a['name'],exact=True)
        if a['action']=='click':target.click()
        elif a['action']=='fill':target.fill(a['value'])
        else:target.press(a['value'])
        if not local_url(self.page.url):raise ValueError('Navigation outside local shop')
    def __exit__(self,*args):
        self.context.close();self.browser.close();self.pw.stop()
