"""Read-only diagnostic for rendered official navigation; no credentials required."""
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    try:
        for url in ("https://www.byd.com/cn", "https://www.lixiang.com/"):
            page = browser.new_page(locale="zh-CN")
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(2500)
            if 'lixiang' in url:
                page.get_by_text('新一代理想L6', exact=True).last.click()
                page.wait_for_timeout(2000)
                print(json.dumps({'product_url': page.url, 'title': page.title(), 'text': page.locator('body').inner_text()[:2000]}, ensure_ascii=False), flush=True)
            links = page.locator("a[href]").evaluate_all("els => els.map(a => ({url:a.href,text:(a.innerText+' '+Array.from(a.querySelectorAll('img')).map(i=>i.alt).join(' ')).trim()}))")
            print(json.dumps({"url": url, "links": links[:75]}, ensure_ascii=False), flush=True)
            page.close()
    finally:
        browser.close()
