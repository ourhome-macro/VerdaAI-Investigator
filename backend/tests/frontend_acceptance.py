"""End-to-end UI acceptance against local Vite and FastAPI, with real .env APIs.

Leaves the actual report in the app DB and exports its audited content to docs.
No mocked API responses, no direct database seeding, no secret browser injection.
"""
import json
import argparse
from pathlib import Path
import re
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = 'http://127.0.0.1:3400'
OUT = ROOT / 'doc'


def export_report(report):
    lines = ['# 新能源车竞争格局：特斯拉、比亚迪、理想的产品与定价竞争分析', '',
             f"报告 ID：`{report['id']}`", '', f"生成时间：{report['created_at']}", '',
             f"本地页面：{BASE}/report/{report['id']}", '',
             f"研究质检：{report.get('quality_status')}；最终发布审校：{report.get('final_audit', {}).get('status')}", '',
             '价格为资料采集时的页面口径，不是成交承诺；不同年款、配置、地区、金融方案及限时权益不可直接混用。', '']
    evs = {e['evidence_id']: e for e in report['evidence']}
    if report.get('confidence_review'):
        review = report['confidence_review']
        lines += [f"可信度规则：{review['policy_version']}；高可信 {review['after']['levels'].get('high', 0)} 条，独立交叉验证 {review['after']['cross_validated']} 条。", '', review['note'], '']
    def citations(text):
        for eid, ev in evs.items():
            text = text.replace(f'[{eid}]', f"[来源：{ev.get('brand', '')}]({ev['source_url']})")
        return text
    for section in report['sections']:
        lines += ['## ' + section['title'], '']
        if section.get('key_takeaway'):
            lines += [citations(section['key_takeaway']), '']
        for paragraph in section.get('paragraphs', []):
            lines += [citations(paragraph), '']
    lines += ['## 可追溯论点台账', '']
    for claim in report['claims']:
        if claim.get('verification', {}).get('verdict') != 'supported':
            continue
        lines += [f"### {claim['claim_id']}", '', claim['text'], '']
        if claim.get('confidence_policy_version'):
            levels = {'high':'高可信','medium':'中可信','low':'低可信','unverified':'待验证'}
            statuses = {'single_authority':'单一权威来源','corroborated':'已独立交叉验证','composite_support':'多源联合支持',
                        'same_origin':'多条同源证据','single_source':'单一来源','not_verified':'未核验'}
            independence = claim.get('independent_verification', {})
            lines += [f"可信度：{levels.get(claim['confidence'])}；独立验证：{statuses.get(independence.get('status'), '未分类')}。", '', claim.get('confidence_reason', ''), '']
        for ref in claim['evidence_ids']:
            e = evs[ref]
            lines += [f"- [{e['title']}]({e['source_url']})（{e.get('source_tier')}，{e.get('fetch_kind')}）"]
        lines += ['']
    lines += ['## 来源与审校说明', '',
              json.dumps(report.get('source_governance', {}), ensure_ascii=False, indent=2), '',
              f"最终审校检查 {report['final_audit']['checked_units']} 个单元，记录 {len(report['final_audit']['repairs'])} 项删除或提取式修订。",
              '同源转载合并计算；正文支持性核验不构成第三方事实真实性保证。', '']
    OUT.mkdir(exist_ok=True)
    (OUT / '新能源车竞争格局分析.md').write_text('\n'.join(lines), encoding='utf-8')
    (OUT / '新能源车竞争格局分析.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume-task')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='zh-CN')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        if args.resume_task:
            page.goto(BASE, wait_until='domcontentloaded')
            task_id = args.resume_task
            for _ in range(60):
                state = context.request.get(BASE + '/api/tasks/' + task_id).json()
                if state.get('execution', {}).get('status') != 'running':
                    break
                page.wait_for_timeout(1000)
            response = context.request.post(BASE + '/api/tasks/' + task_id + '/retry')
            assert response.ok, response.status
            page.goto(BASE + '/workspace/' + task_id, wait_until='domcontentloaded')
            print(json.dumps({'resumed_task': task_id, 'workspace': page.url}), flush=True)
        else:
            page.goto(BASE, wait_until='domcontentloaded')
            page.get_by_text('新能源车竞争格局', exact=True).click()
            page.wait_for_url('**/clarify/**', timeout=120000)
            task_id = page.url.rsplit('/', 1)[-1]
            field = page.get_by_placeholder('补充其他想调研的竞品，回车添加（可用逗号分隔多个）')
            field.fill('特斯拉,比亚迪,理想')
            field.press('Enter')
            for name in ('功能对比', '定价策略', '中国大陆', '个人用户', '通用/综合', '近一年即可'):
                page.get_by_role('button', name=name, exact=True).click()
            page.locator('textarea').fill('只研究特斯拉、比亚迪、理想三家。以当前官网在售车型为主，区分整车指导价、预售价、金融月供和限时补贴；产品定位与价格带均需引用证据。')
            page.get_by_role('button', name='启动调研', exact=True).click()
            page.wait_for_url('**/workspace/**', timeout=30000)
            print(json.dumps({'task_id': task_id, 'workspace': page.url}, ensure_ascii=False), flush=True)
            # Prove frontend disconnect is not task cancellation: close the observer, reopen it.
            page.wait_for_timeout(3000)
            page.goto(BASE + '/library', wait_until='domcontentloaded')
            status = context.request.get(BASE + '/api/tasks/' + task_id).json()
            assert status['execution']['status'] == 'running', status
            page.goto(BASE + '/workspace/' + task_id, wait_until='domcontentloaded')
        deadline, last = time.monotonic() + 1800, ''
        while time.monotonic() < deadline:
            status = context.request.get(BASE + '/api/tasks/' + task_id).json()
            current = status.get('execution', {}).get('status')
            if current != last:
                print(json.dumps({'execution': current}, ensure_ascii=False), flush=True)
                last = current
            if current == 'done':
                break
            if current in ('failed', 'interrupted'):
                raise AssertionError('Research execution failed; inspect persisted event stream')
            page.wait_for_timeout(5000)
        else:
            raise AssertionError('Acceptance timeout; background job remains available')
        rid = status['report_id']
        report = context.request.get(BASE + '/api/reports/' + rid).json()
        assert set(report['brands']) == {'特斯拉', '比亚迪', '理想'}, report['brands']
        verified = [c for c in report['claims'] if c.get('verification', {}).get('verdict') == 'supported']
        assert verified, 'No supported claims'
        by_id = {e['evidence_id']: e for e in report['evidence']}
        for brand in report['brands']:
            for dimension in ('feature_tree', 'pricing_model'):
                assert any(c['field'] == dimension and any(by_id[e]['brand'] == brand for e in c['evidence_ids'])
                           for c in verified), f'Missing verified {brand}/{dimension}'
        assert report['final_audit']['status'] == 'passed'
        page.goto(BASE + '/report/' + rid, wait_until='domcontentloaded')
        page.get_by_text('最终审校：', exact=False).wait_for(timeout=30000)
        page.screenshot(path=str(OUT / '新能源车案例-报告页面.png'), full_page=True)
        assert not errors, errors
        export_report(report)
        result = {'task_id': task_id, 'report_id': rid, 'url': BASE + '/report/' + rid,
                  'verified_claims': len(verified), 'evidence_count': len(report['evidence']),
                  'source_governance': report.get('source_governance'), 'quality_status': report.get('quality_status'),
                  'final_audit': report['final_audit']['status'], 'browser_errors': errors,
                  'disconnect_resume': True, 'checks': 'all three brands have admitted product and pricing claims'}
        (OUT / '新能源车案例-验收结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False), flush=True)
        browser.close()


if __name__ == '__main__':
    main()
