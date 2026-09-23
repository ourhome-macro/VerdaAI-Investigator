import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    try:
        page = browser.new_page(locale='zh-CN')
        page.goto('https://www.byd.com/cn/ocean-home/models/haishi/haishi-08-ev', wait_until='domcontentloaded')
        page.wait_for_timeout(2000)
        print('parameters buttons', page.get_by_text('参数对比', exact=True).count(), flush=True)
        print('alts', json.dumps(page.locator('img[alt]').evaluate_all('els=>els.map(i=>i.alt).filter(Boolean)'),ensure_ascii=False)[:2500], flush=True)
        page.get_by_text('参数对比', exact=True).first.click()
        page.wait_for_timeout(4000)
        print(json.dumps({'url': page.url, 'pages': [x.url for x in page.context.pages], 'text': page.locator('body').inner_text()[:6000]},ensure_ascii=False),flush=True)
        for x in page.context.pages:
            if x != page:
                print('NEW_PAGE',x.url,x.locator('body').inner_text()[:6000],flush=True)
    finally:
        browser.close()
