import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('report_id')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
base = 'http://127.0.0.1:3400'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width':1440,'height':1000},locale='zh-CN')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(base + '/report/' + args.report_id, wait_until='domcontentloaded')
    page.get_by_text('可信度已重新核验：',exact=False).wait_for(timeout=30000)
    report = page.request.get(base + '/api/reports/' + args.report_id).json()
    high = [c for c in report['claims'] if c['confidence'] == 'high']
    assert high and all(not c['cross_validated'] for c in high)
    badge = page.get_by_text('单一权威来源',exact=True).first
    badge.scroll_into_view_if_needed()
    page.wait_for_timeout(1000)
    assert '高可信' in badge.locator('..').inner_text()
    assert page.get_by_text('已独立交叉验证',exact=True).count() == 0
    assert not errors, errors
    page.screenshot(path=str(root / 'doc/新能源车案例-双维度可信度.png'),full_page=True)
    page.goto(base + '/dashboard', wait_until='domcontentloaded')
    page.get_by_text('独立验证占比', exact=True).wait_for(timeout=30000)
    page.get_by_text('高可信占比', exact=True).wait_for(timeout=30000)
    stats = page.request.get(base + '/api/dashboard').json()
    assert stats['high_confidence_percent'] > 0
    assert stats['independent_verification_percent'] == 0
    page.wait_for_timeout(1200)
    page.screenshot(path=str(root / 'doc/新能源车案例-双维度仪表盘.png'),full_page=True)
    assert not errors, errors
    print(json.dumps({'high_trust':len(high),'independent_corroboration':0,'single_authority_badge':True,'browser_errors':errors},ensure_ascii=False))
    browser.close()
