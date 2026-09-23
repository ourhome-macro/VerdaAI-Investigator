"""Read-only final visual QA of an already persisted report."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('report_id')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
url = 'http://127.0.0.1:3400/report/' + args.report_id
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width':1440,'height':1000},locale='zh-CN')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(url, wait_until='domcontentloaded')
    page.get_by_text('最终审校：',exact=False).wait_for(timeout=30000)
    page.wait_for_timeout(1400)
    page.screenshot(path=str(root/'doc/新能源车案例-报告页面.png'),full_page=True)
    page.locator('aside').first.get_by_text('三、商业模式与定价博弈',exact=True).click()
    page.wait_for_timeout(1200)
    pricing = page.locator('#sec-pricing')
    assert '235,500' in pricing.inner_text()
    assert '24.98' in pricing.inner_text()
    page.screenshot(path=str(root/'doc/新能源车案例-定价分析.png'),full_page=True)
    page.reload(wait_until='domcontentloaded')
    page.get_by_text('最终审校：',exact=False).wait_for(timeout=30000)
    assert not errors, errors
    print(json.dumps({'url':url,'browser_errors':errors,'pricing_visible':True,'reload_persisted_report':True},ensure_ascii=False))
    browser.close()
