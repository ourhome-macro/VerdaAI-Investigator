import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.core import orchestrator as orch
from app.core.audit import evaluate_quality, decide_rework
from app.core.evidence_context import field_for, select_evidence
from app.core.final_audit import finalize_report
from app.core.claim_verifier import _without_source_dates
from app.core.models import Evidence
from app.core.research_contract import build_contract, build_matrix, cell_id, source_time, stamp_claim, section_plan, merge_rework
from app.core.source_policy import official_for, classify, admission

NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)
FOCUS = ['功能对比', '用户口碑', '生态壁垒', '技术架构']
BRANDS = ['Notion', 'Obsidian', '飞书', '语雀', 'OneNote']


def evidence(brand='Notion', date='', key='feature_tree'):
    return Evidence('e_' + brand, 'https://www.notion.com/help', 'official', brand + ' 功能',
                    brand + ' 支持文档。', '2026-09-23', 90, 'L1-001', brand=brand,
                    full_text=brand + ' 支持文档。', fetch_kind='body', source_tier='official',
                    published_at=date, research_dimensions=[key])


def fact(brand='Notion', key='feature_tree'):
    return {'claim_id': 'c_' + brand + key, 'brand': brand, 'field': key, 'text': brand + ' 支持文档。',
            'cell_id': cell_id(brand, key), 'evidence_ids': ['e_' + brand], 'confidence': 'high',
            'verification': {'verdict': 'supported', 'supports': [
                {'evidence_id': 'e_' + brand, 'relation': 'supports', 'quote': brand + ' 支持文档。'}]}}


class ContractTests(unittest.TestCase):
    def test_empty_rework_cannot_erase_verified_background_or_other_cells(self):
        a, b = fact(), fact('语雀')
        a['temporal'] = {'label': 'unknown', 'published_at': ['']}
        result, kept = merge_rework([a, b], [], {a['cell_id']})
        self.assertEqual({c['claim_id'] for c in result}, {a['claim_id'], b['claim_id']})
        self.assertEqual(kept, [a['claim_id']])
        self.assertIs(result[0], b)
        ct = build_contract(['Notion'], ['功能对比'], {'freshness': '优先最新（近一月）'}, now=NOW)
        self.assertEqual(build_matrix(ct, result, [evidence()])['covered'], 0)

    def test_rework_contradiction_does_not_rescue_old_cell(self):
        old, new = fact(), fact()
        new['claim_id'] = 'conflict'
        new['verification']['verdict'] = 'contradicted'
        result, kept = merge_rework([old], [new], {old['cell_id']})
        self.assertEqual(result, [new])
        self.assertFalse(kept)

    def test_supported_replacement_updates_cell(self):
        old, new = fact(), fact()
        new['claim_id'], new['text'] = 'updated', '新的核验事实'
        result, kept = merge_rework([old], [new], {old['cell_id']})
        self.assertEqual(result, [new])
        self.assertFalse(kept)

    def test_exact_focus_mapping_no_user_persona_collision(self):
        self.assertEqual([field_for(x) for x in FOCUS], ['feature_tree', 'sentiment', 'ecosystem', 'architecture'])
        self.assertEqual(field_for('用户画像'), 'user_persona')

    def test_twenty_cells_even_without_any_claim(self):
        contract = build_contract(BRANDS, FOCUS, now=NOW)
        matrix = build_matrix(contract, [], [evidence(b) for b in BRANDS])
        self.assertEqual(matrix['total'], 20)
        self.assertEqual(matrix['fact_covered'], 0)
        self.assertEqual(len({c['cell_id'] for c in matrix['cells']}), 20)

    def test_brand_requires_own_verified_claim_not_many_urls(self):
        qr = evaluate_quality(['Notion', '语雀'], ['功能对比'], [fact()], [evidence(), evidence('语雀')], {})
        self.assertFalse(qr.coverage_by_dimension['功能对比'])
        self.assertEqual(qr.coverage_by_brand['语雀']['verified_claims'], 0)
        self.assertEqual(qr.brand_coverage_rate, 0.5)
        targets = decide_rework(qr)[0].payload['cells']
        self.assertEqual(targets, [{'cell_id': cell_id('语雀', 'feature_tree'), 'brand': '语雀', 'dimension': 'feature_tree'}])

    def test_time_unknown_not_collection_time_and_future_denied(self):
        ct = build_contract(['Notion'], ['功能对比'], {'freshness': '优先最新（近一月）'}, now=NOW)
        self.assertEqual(ct['freshness'], 'oneMonth')
        self.assertEqual(source_time('', ct), 'unknown')
        self.assertEqual(source_time('2026-09-01', ct), 'recent_month')
        self.assertEqual(source_time('2026-07-01', ct), 'recent_quarter')
        self.assertEqual(source_time('2025-01-01', ct), 'background')
        self.assertEqual(source_time('2026-10-01', ct), 'future')
        c = stamp_claim(fact(), [evidence()], ct)
        self.assertEqual(c['temporal']['label'], 'unknown')
        m = build_matrix(ct, [c], [evidence()])
        self.assertEqual((m['fact_covered'], m['covered']), (1, 0))
        future = stamp_claim(fact(), [evidence(date='2026-10-01')], ct)
        self.assertEqual(future['confidence'], 'unverified')

    def test_old_and_recent_sources_cannot_mislabel_combined_fact(self):
        ct = build_contract(['Notion'], ['功能对比'], now=NOW)
        a, b = evidence(date='2026-09-01'), evidence(date='2025-01-01')
        b.evidence_id = 'old'
        c = fact()
        c['verification']['supports'].append({'evidence_id': 'old', 'relation': 'partial'})
        self.assertEqual(stamp_claim(c, [a, b], ct)['temporal']['label'], 'background')

    def test_custom_dimensions_are_not_silently_dropped(self):
        ct = build_contract(['A'], ['离线迁移成本'], now=NOW)
        self.assertEqual(ct['dimensions'][0]['label'], '离线迁移成本')
        self.assertTrue(ct['dimensions'][0]['key'].startswith('custom_'))

    def test_year_window_also_rejects_old_or_undated_sources(self):
        ct = build_contract(['Notion'], ['功能对比'], {'freshness': '近一年即可'}, now=NOW)
        for date in ('', '2025-01-01'):
            ev = evidence(date=date)
            c = stamp_claim(fact(), [ev], ct)
            self.assertEqual(build_matrix(ct, [c], [ev])['covered'], 0)

    def test_fact_coverage_does_not_disappear_due_to_recency_gap(self):
        ct = build_contract(['Notion'], ['功能对比'], {'freshness': '优先最新（近一月）'}, now=NOW)
        c, ev = fact(), evidence()
        stamp_claim(c, [ev], ct)
        qr = evaluate_quality(['Notion'], ['功能对比'], [c], [ev], {'research_matrix': {'contract': ct}})
        self.assertTrue(qr.coverage_by_dimension['功能对比'])
        self.assertEqual(qr.schema_completeness, 1)
        self.assertEqual(qr.freshness_coverage_rate, 0)
        self.assertTrue(qr.issues)

    def test_negative_car_reference_cannot_select_car_profile(self):
        self.assertEqual(build_contract(BRANDS, FOCUS, query='不要出现整车和车型')['industry'], 'general')
        self.assertEqual(build_contract(['特斯拉', '比亚迪', '理想'], ['定价'])['industry'], 'automotive')

    def test_report_sections_follow_user_not_fixed_price_schema(self):
        ids = [sid for sid, _ in section_plan(FOCUS)]
        self.assertEqual(ids, ['summary', 'feature', 'sentiment', 'ecosystem', 'architecture', 'conclusion'])
        self.assertNotIn('pricing', ids)

    def test_empty_requested_section_survives_final_audit(self):
        ct = build_contract(['A'], ['用户口碑'], now=NOW)
        matrix = build_matrix(ct, [], [])
        report = {'claims': [], 'evidence': [], 'research_matrix': matrix,
                  'sections': [{'id': 'sentiment', 'claims': [], 'paragraphs': ['无来源的好评']}],
                  'toc': [{'id': 'sentiment'}]}
        result = finalize_report(report, model='test', reviewer=lambda *a, **kw: {})
        self.assertEqual(result['sections'][0]['id'], 'sentiment')
        self.assertEqual(result['final_audit']['coverage_status'], 'needs_review')
        self.assertEqual(result['quality_status'], 'needs_review')


class SourceAndExecutionTests(unittest.TestCase):
    def test_tenant_content_is_not_official(self):
        self.assertTrue(official_for('https://www.yuque.com/yuque/developer/api', '语雀'))
        self.assertFalse(official_for('https://www.yuque.com/someone/notes', '语雀'))
        self.assertFalse(official_for('https://a.feishu.cn/wiki/a', '飞书'))
        self.assertFalse(official_for('https://www.notion.so/someones-workspace', 'Notion'))
        self.assertEqual(classify('https://forum.obsidian.md/t/review/123', 'Obsidian'), 'community')
        self.assertTrue(official_for('https://support.microsoft.com/zh-cn/onenote', 'OneNote'))
        self.assertFalse(official_for('https://notion.com.attacker.example/help', 'Notion'))
        self.assertTrue(official_for('https://github.com/yuque/sdk', '语雀'))
        self.assertFalse(official_for('https://github.com/yuque/sdk/issues/1', '语雀'))
        self.assertFalse(official_for('https://github.com/attacker/sdk', '语雀'))

    def test_marketing_cannot_satisfy_sentiment_gate(self):
        c = {'field': 'sentiment', 'text': '官网称用户喜爱此功能'}
        refs = [{'evidence_id': 'a'}]
        by = {'a': [{'source_tier': 'official', 'fetch_kind': 'body'}]}
        self.assertFalse(admission(c, refs, by)[0])
        by['a'][0]['source_tier'] = 'community'
        self.assertTrue(admission(c, refs, by)[0])
        by['a'][0]['fetch_kind'] = 'snippet'
        self.assertFalse(admission(c, refs, by)[0])

    def test_recent_search_and_background_search_are_distinct(self):
        ct = build_contract(['Notion'], ['功能对比'], {'freshness': '优先最新（近一月）'}, now=NOW)
        with patch.object(orch, 'multi_search', return_value=[]) as search:
            orch._collect_brand('Notion', ['unused'], 'L1', 3, ct['freshness'], set(), ct)
        self.assertEqual([call.kwargs['freshness'] for call in search.call_args_list], ['oneMonth', 'noLimit'])
        self.assertNotIn('车型', str(search.call_args_list))

    def test_sentiment_routes_to_community_with_separate_background_window(self):
        ct = build_contract(['Notion'], ['用户口碑'], {'freshness': '优先最新（近一月）'}, now=NOW)
        with patch.object(orch, 'multi_search', return_value=[]) as search:
            orch._collect_brand('Notion', [], 'L1', 3, ct['freshness'], set(), ct)
        routed = [c for c in search.call_args_list if c.kwargs.get('site')]
        self.assertEqual([c.args[0] for c in routed], [['Notion']] * 4)
        self.assertEqual([c.kwargs['freshness'] for c in routed], ['oneMonth', 'noLimit'] * 2)
        self.assertEqual({c.kwargs['site'] for c in routed}, {'sspai.com', 'v2ex.com'})

    def test_source_publication_date_is_not_an_unquoted_product_number(self):
        support = [{'evidence_id': 'e'}]
        by_id = {'e': [{'published_at': '2023-07-03'}]}
        self.assertNotIn('2023', _without_source_dates('作者在2023年7月3日发布的文章中表示喜欢此工具', support, by_id))
        self.assertNotIn('2023', _without_source_dates('文章发布日期为2023-07-03', support, by_id))
        self.assertIn('2023', _without_source_dates('文章发布日期为2023-07-04', support, by_id))
        self.assertIn('2023', _without_source_dates('产品在2023年7月3日上市', support, by_id))
        self.assertIn('2023', _without_source_dates('产品在2023年7月3日发布', support, by_id))
        self.assertIn('2023', _without_source_dates('价格2023元', support, by_id))
        self.assertIn('2023', _without_source_dates('作者在2023年7月3日发布的文章中表示喜欢此工具', support, {'e': []}))

    def test_targeted_analysis_does_not_call_completed_cells(self):
        ct = build_contract(BRANDS, FOCUS, now=NOW)
        target = cell_id('语雀', 'architecture')
        with patch.object(orch, '_analyze_brand', return_value={'claims': [], 'evidence_selection': []}) as analyze:
            orch._analyze('知识管理', BRANDS, FOCUS, [], ['L2'], contract=ct, target_cells={target})
        self.assertEqual(analyze.call_count, 1)
        self.assertEqual(analyze.call_args.args[1:3], (['语雀'], ['技术架构']))

    def test_plan_failure_keeps_selected_dimensions(self):
        with patch.object(orch, 'chat_json', side_effect=TimeoutError):
            plan = orch._plan_research('知识管理', {'competitors': BRANDS, 'focus': FOCUS})
        self.assertEqual(plan['focus'], FOCUS)

    def test_recent_relevant_source_enters_context_before_background(self):
        a, b = evidence(), evidence(date='2026-09-20')
        a.full_text = 'Notion 功能 特性 配置 support features ' * 30
        b.evidence_id, b.full_text = 'recent', 'Notion 功能支持文档。'
        context = select_evidence([a, b], brands=['Notion'], focus=['功能对比'], limit=1, prefer_ids={'recent'})
        self.assertEqual(context.evidence_ids, {'recent'})

    def test_review_cannot_schedule_unrequested_brand_or_dimension(self):
        qr = evaluate_quality(['Notion'], ['功能对比'], [fact()], [evidence()], {})
        review = {'rework_cells': [{'brand': 'Notion', 'dimension': 'pricing_model'},
                                   {'brand': '语雀', 'dimension': 'feature_tree'},
                                   {'brand': 'Notion', 'dimension': 'feature_tree', 'reason': '需要更明确的功能事实'}]}
        cells = decide_rework(qr, review)[0].payload['cells']
        self.assertEqual(len(cells), 1)
        self.assertEqual(cells[0]['cell_id'], cell_id('Notion', 'feature_tree'))


if __name__ == '__main__':
    unittest.main()
