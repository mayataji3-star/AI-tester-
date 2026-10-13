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
