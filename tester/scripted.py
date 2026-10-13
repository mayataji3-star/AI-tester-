import json,time
from pathlib import Path
from playwright.sync_api import expect
from .browser import Browser
ROOT=Path(__file__).resolve().parents[1]
def search(p):
    p.get_by_role('searchbox',name='Search products').fill(' HEAD ')
    expect(p.get_by_role('heading',name='Headphones',exact=True)).to_be_visible()
    expect(p.locator('#products article')).to_have_count(1)
    p.get_by_role('searchbox',name='Search products').fill('zzzz')
    expect(p.get_by_text('No products found.',exact=True)).to_be_visible()
def cart(p):
    for name in ['Headphones','Headphones','Mouse']:p.get_by_role('button',name=f'Add {name} to cart',exact=True).click()
    expect(p.get_by_role('spinbutton',name='Quantity for Headphones')).to_have_value('2')
    expect(p.locator('#cart tr')).to_have_count(2)
    expect(p.locator('#total')).to_have_text('Total: £50.00')
    field=p.get_by_role('spinbutton',name='Quantity for Headphones');field.fill('3');field.press('Tab')
    expect(p.locator('#total')).to_have_text('Total: £70.00')
    p.get_by_role('button',name='Remove Mouse',exact=True).click()
    expect(p.locator('#total')).to_have_text('Total: £60.00')
def quantity(p):
    p.get_by_role('button',name='Add Headphones to cart',exact=True).click()
    for value in ['0','-1','1.5']:
        field=p.get_by_role('spinbutton',name='Quantity for Headphones');field.fill(value);field.press('Tab');expect(field).to_have_value('1')
    field.fill('2');field.press('Tab');expect(p.locator('#total')).to_have_text('Total: £40.00')
def checkout(p):
    email=p.get_by_role('textbox',name='Email address');email.fill('tester@example.invalid')
    p.get_by_role('button',name='Place demo order').click()
    expect(p.locator('#message')).to_have_text('Your cart is empty.')
    p.get_by_role('button',name='Add Mouse to cart',exact=True).click();email.fill('hello')
    p.get_by_role('button',name='Place demo order').click()
    expect(p.locator('#cart tr')).to_have_count(1)
    email.fill('tester@example.invalid');p.get_by_role('button',name='Place demo order').click()
    expect(p.locator('#message')).to_have_text('Demo order placed. No payment taken.')
    expect(p.locator('#cart tr')).to_have_count(0)

def main():
    out=ROOT/'results/runs'/('scripted-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(parents=True,exist_ok=True)
    results=[]
    for task in [search,cart,quantity,checkout]:
        start=time.monotonic();record={'task':task.__name__,'status':'passed','verification':'not_a_bug_report'}
        try:
            with Browser() as b:
                b.page.set_default_timeout(3000)
                b.context.tracing.start(screenshots=True,snapshots=True,sources=False)
                try:task(b.page)
                except Exception as e:record.update(status='failed_check',error=str(e),verification='pending')
                b.page.screenshot(path=str(out/(task.__name__+'.png')),full_page=True)
                b.context.tracing.stop(path=str(out/(task.__name__+'-trace.zip')))
        except Exception as e:
            record.update(status='infrastructure_error',error=type(e).__name__+': '+str(e),verification='not_a_bug_report')
        record['elapsed_seconds']=round(time.monotonic()-start,3);results.append(record);print(record['task'],record['status'])
    (out/'report.json').write_text(json.dumps(results,indent=2))
    raise SystemExit(any(r['status']!='passed' for r in results))
if __name__=='__main__':main()
