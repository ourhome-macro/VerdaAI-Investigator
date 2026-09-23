"""Real .env-backed frontend/backend regression; no source or LLM mocks.

Usage: python tests/live_matrix_acceptance.py knowledge|auto [--task existing_id]
Reports retain honest missing cells; passing this test is not passing research completeness.
"""
import argparse
import copy
import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'doc'
BASE = 'http://127.0.0.1:3400'
CASES = {
    'knowledge': {'query': '知识管理软件竞争分析：Notion、Obsidian、飞书、语雀、OneNote，重点功能对比、用户口碑、生态壁垒、技术架构。',
                  'brands': ['Notion', 'Obsidian', '飞书', '语雀', 'OneNote'],
                  'focus': ['功能对比', '用户口碑', '生态壁垒', '技术架构'], 'freshness': '优先最新（近一月）'},
    'auto': {'query': '新能源车竞争格局分析：特斯拉、比亚迪、理想的产品与定价竞争。',
             'brands': ['特斯拉', '比亚迪', '理想'], 'focus': ['功能对比', '定价策略'], 'freshness': '近一年即可'},
}


def export(report, name):
    evs = {e['evidence_id']: e for e in report['evidence']}
    matrix = report['research_matrix']
    lines = ['# ' + report['title'], '', f"本地报告：{BASE}/report/{report['id']}", '',
             f"研究状态：{report['quality_status']}；正文审校：{report['final_audit']['status']}。", '',
             f"事实覆盖 {matrix['fact_covered']}/{matrix['total']}；满足时效 {matrix['covered']}/{matrix['total']}。", '',
             '## 品牌 × 维度覆盖', '', '| 品牌 | 维度 | 核验事实数 | 高可信数 | 状态 | 缺口 |', '|---|---|---:|---:|---|---|']
    for cell in matrix['cells']:
        lines.append(f"| {cell['brand']} | {cell['label']} | {len(cell['claim_ids'])} | {cell['high_count']} | {cell['status']} | {cell['gap']} |")
    for section in report['sections']:
        lines += ['', '## ' + section['title'], '']
        for text in section.get('paragraphs', []):
            text = re.sub(r'\[(e_\w+)\]', lambda m: f"[来源]({evs[m[1]]['source_url']})" if m[1] in evs else m[0], text)
            lines += [text, '']
    lines += ['## 原子事实与时效台账', '']
    for c in report['claims']:
        lines += [f"### {c['brand']} · {c['dimension']} · {c['claim_id']}", '', c['text'], '',
                  f"可信度：{c['confidence']}；核验：{c['verification']['verdict']}；来源时间：{c.get('temporal', {}).get('label', 'unknown')}。", '']
        for eid in c['evidence_ids']:
            ev = evs[eid]
            lines += [f"- [{ev['title']}]({ev['source_url']}) · 发布日期：{ev['published_at'] or '未知'} · 采集：{ev['captured_at']} · {ev['source_tier']}/{ev['fetch_kind']}"]
        lines += ['']
    lines += ['来源时间不等于产品变更时间；单条用户意见不代表群体满意度；高可信不是统计校准概率。', '']
    (OUT / f'通用矩阵-{name}-竞争分析.md').write_text('\n'.join(lines), encoding='utf-8')
    public = copy.deepcopy({k: v for k, v in report.items() if k != 'trace'})
    # Public Git examples are not mirrors of third-party articles. Full source
    # snapshots remain in the local report DB for original-offset verification.
    def omit_source_text(value):
        if isinstance(value, dict):
            for key in ('full_text', 'excerpt', 'quote'):
                value.pop(key, None)
            for item in value.values():
                omit_source_text(item)
        elif isinstance(value, list):
            for item in value:
                omit_source_text(item)
    omit_source_text(public)
    for passage in public.get('evidence_selection', []):
        passage.pop('text', None)
    public['export_note'] = '公开样例省略网页全文、摘要、原文引句及模型上下文；保留来源URL、偏移与核验结果。完整取证快照在本地报告中。'
    (OUT / f'通用矩阵-{name}-报告.json').write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=CASES)
    parser.add_argument('--task')
    parser.add_argument('--retry', action='store_true')
    args = parser.parse_args()
    case = CASES[args.case]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='zh-CN')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        if args.task:
            task_id = args.task
            if args.retry:
                response = context.request.post(BASE + '/api/tasks/' + task_id + '/retry')
                assert response.ok
        else:
            response = context.request.post(BASE + '/api/tasks', data={'query': case['query'], 'mode': 'deep'}, timeout=180000)
            assert response.ok, response.status
            task_id = response.json()['taskId']
            response = context.request.post(BASE + f'/api/tasks/{task_id}/clarify', data={'answers': {
                'competitors': case['brands'], 'focus': case['focus'], 'market': '中国大陆', 'user': '个人用户',
                'perspective': '通用/综合', 'freshness': case['freshness']}}, timeout=30000)
            assert response.ok
        print(json.dumps({'case': args.case, 'task_id': task_id}, ensure_ascii=False), flush=True)
        page.goto(BASE + '/workspace/' + task_id, wait_until='domcontentloaded')
        deadline = time.monotonic() + 2400
        previous = ''
        while time.monotonic() < deadline:
            state = context.request.get(BASE + '/api/tasks/' + task_id).json()
            status = (state.get('execution') or {}).get('status')
            if status != previous:
                print(json.dumps({'status': status}), flush=True)
                previous = status
            if status == 'done':
                break
            assert status not in ('failed', 'interrupted'), 'Research failed; inspect task events'
            page.wait_for_timeout(5000)
        else:
            raise AssertionError('Timeout; background task is not cancelled')
        rid = state['report_id']
        report = context.request.get(BASE + '/api/reports/' + rid).json()
        export(report, args.case)
        matrix = report['research_matrix']
        assert set(report['brands']) == set(case['brands'])
        assert matrix['total'] == len(case['brands']) * len(case['focus'])
        assert {d['label'] for d in matrix['contract']['dimensions']} == set(case['focus'])
        allowed = {d['key'] for d in matrix['contract']['dimensions']}
        evs = {e['evidence_id']: e for e in report['evidence']}
        by_id = {c['claim_id']: c for c in report['claims']}
        for cell in matrix['cells']:
            for cid in cell['claim_ids']:
                c = by_id[cid]
                assert c['verification']['verdict'] == 'supported'
                assert c['brand'] == cell['brand'] and c['field'] == cell['dimension']
                assert all(evs[eid]['brand'] == cell['brand'] for eid in c['evidence_ids'])
            if cell['status'] != 'covered':
                assert cell['gap'] and report['quality_status'] == 'needs_review'
        assert report['claims'] and all(c['field'] in allowed for c in report['claims'])
        assert all(any(c['brand'] == b for c in report['claims']) for b in case['brands']), 'Brand completely empty'
        if args.case == 'knowledge':
            assert matrix['contract']['freshness'] == 'oneMonth'
            prose = ' '.join(c['text'] for c in report['claims']) + ' '.join(p for s in report['sections'] for p in s.get('paragraphs', []))
            assert not re.search('整车|车型|续航|指导价', prose), 'Automotive template drift'
            assert not any(s['id'] == 'pricing' for s in report['sections'])
        else:
            assert matrix['fact_covered'] == matrix['total'], 'EV product/price fact gap'
        page.goto(BASE + '/report/' + rid, wait_until='domcontentloaded')
        panel = page.get_by_test_id('research-matrix')
        try:
            panel.wait_for(timeout=30000)
        except Exception:
            print(json.dumps({'page_errors': errors}, ensure_ascii=False), flush=True)
            raise
        assert panel.locator('tbody tr').count() == len(case['brands'])
        panel.locator('tbody details').first.locator('summary').click()
        page.reload(wait_until='domcontentloaded')
        page.get_by_test_id('research-matrix').wait_for(timeout=30000)
        page.get_by_test_id('research-matrix').screenshot(path=str(OUT / f'通用矩阵-{args.case}-页面.png'))
        assert not errors, errors
        result = {'case': args.case, 'task_id': task_id, 'report_id': rid, 'url': BASE + '/report/' + rid,
                  'cells': matrix['total'], 'fact_covered': matrix['fact_covered'], 'freshness_covered': matrix['covered'],
                  'claims': len(report['claims']), 'high': sum(c['confidence'] == 'high' for c in report['claims']),
                  'quality_status': report['quality_status'], 'final_audit': report['final_audit']['status'],
                  'rework_rounds': report['audit_review']['rework_rounds'], 'browser_errors': errors,
                  'checks': 'real API + frontend stream + matrix attribution + draft honesty + page reload'}
        (OUT / f'通用矩阵-{args.case}-验收.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False), flush=True)
        browser.close()


if __name__ == '__main__':
    main()
