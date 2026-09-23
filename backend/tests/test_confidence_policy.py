import unittest

from app.core.claim_verifier import verify_claims
from app.core.evidence_context import EvidenceContext
from app.core.models import make_claim
from app.core.metrics import compute_report_metrics


def run_case(*, tier='official', groups=('one',), text='Alpha Standard costs USD 20 monthly.',
             kind='declared_fact', complete=True, temporal='consistent', relation='supports',
             verdict='supported', quote=None, field='pricing_model', assessment=True, fetch_kind='body'):
    refs = [f'e_{i}' for i in range(len(groups))]
    passages = [{'evidence_id': eid, 'source_url': f'https://source{i}.example', 'source_group': group,
                 'title': 'Official pricing', 'brand': 'Alpha', 'source_tier': tier, 'fetch_kind': fetch_kind,
                 'text': text, 'start': 0, 'end': len(text)} for i, (eid, group) in enumerate(zip(refs, groups))]
    claim = {'claim_id': 'c', 'text': text, 'field': field, 'evidence_ids': refs, 'author': 'test'}
    row = {'claim_id': 'c', 'verdict': verdict, 'reason': 'fixture judgment',
           'supports': [{'evidence_id': eid, 'quote': quote if quote is not None else text, 'relation': relation} for eid in refs]}
    if assessment:
        row['assessment'] = {'claim_type': kind, 'scope_complete': complete, 'temporal_alignment': temporal}
    return verify_claims([claim], EvidenceContext(passages, ''), model='fixture',
                         reviewer=lambda *a, **kw: {'results': [row]})[0]


class ConfidencePolicyTests(unittest.TestCase):
    def test_single_official_price_can_be_high_without_corroboration(self):
        c = run_case()
        self.assertEqual(c['confidence'], 'high')
        self.assertFalse(c['cross_validated'])
        self.assertEqual(c['independent_verification']['status'], 'single_authority')

    def test_multiple_official_pages_are_still_one_source(self):
        c = run_case(groups=('issuer', 'issuer', 'issuer'))
        self.assertEqual(c['confidence'], 'high')
        self.assertFalse(c['cross_validated'])
        self.assertEqual(c['independent_verification']['source_count'], 1)

    def test_joint_quotes_from_one_official_origin_are_not_independent(self):
        c = run_case(groups=('issuer', 'issuer'), relation='partial')
        self.assertEqual(c['confidence'], 'high')
        self.assertFalse(c['cross_validated'])

    def test_incomplete_or_unknown_scope_not_high(self):
        for kwargs in ({'complete': False}, {'temporal': 'unknown'}, {'assessment': False}):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(run_case(**kwargs)['confidence'], 'medium')

    def test_temporal_conflict_remains_unverified(self):
        c = run_case(temporal='conflicting')
        self.assertEqual(c['confidence'], 'unverified')
        self.assertEqual(c['verification']['verdict'], 'partial')

    def test_manufacturer_marketing_cannot_be_high_even_if_model_misclassifies(self):
        c = run_case(text='Alpha is the safest car.', field='feature_tree', kind='declared_fact')
        self.assertEqual(c['claim_kind'], 'comparison')
        self.assertEqual(c['confidence'], 'medium')

    def test_manufacturer_price_cannot_prove_actual_transaction(self):
        c = run_case(text='Alpha actual transaction price is USD 20.', kind='declared_fact')
        self.assertEqual(c['confidence'], 'unverified')

    def test_third_party_safety_rating_is_not_manufacturer_authority(self):
        c = run_case(text='Alpha在中保研安全指数获得最高评级G+。', field='feature_tree', kind='declared_fact')
        self.assertEqual(c['confidence'], 'unverified')

    def test_comparison_requires_two_credible_independent_sources_for_high(self):
        c = run_case(tier='media', groups=('lab_a', 'lab_b'), field='overview',
                     text='Alpha is safer than Beta in the defined crash test.', kind='comparison')
        self.assertEqual(c['confidence'], 'high')
        self.assertTrue(c['cross_validated'])
        single = run_case(tier='media', field='overview', text='Alpha is safer than Beta.', kind='comparison')
        self.assertEqual(single['confidence'], 'medium')

    def test_two_weak_sources_are_not_automatically_high(self):
        c = run_case(tier='secondary', groups=('blog_a', 'blog_b'), field='overview')
        self.assertTrue(c['cross_validated'])
        self.assertEqual(c['confidence'], 'medium')

    def test_reposting_cannot_raise_low_trust(self):
        c = run_case(tier='secondary', groups=('original', 'original'), field='overview')
        self.assertEqual(c['confidence'], 'low')
        self.assertFalse(c['cross_validated'])
        self.assertEqual(c['independent_verification']['status'], 'same_origin')

    def test_partial_conflicting_or_fake_quotes_never_promoted(self):
        for kwargs in ({'verdict':'partial'}, {'verdict':'contradicted'}, {'quote':'Fabricated quotation'}, {'fetch_kind':'snippet'}):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(run_case(**kwargs)['confidence'], 'unverified')

    def test_inference_is_not_a_high_trust_fact(self):
        c = run_case(tier='media', groups=('one','two'), field='overview', kind='inference')
        self.assertEqual(c['confidence'], 'medium')

    def test_factory_does_not_promote_unverified_proposals(self):
        self.assertEqual(make_claim('c', 'fact', 'overview', ['a','b'], 'test', 2).confidence, 'unverified')

    def test_metrics_keep_high_trust_and_independence_separate(self):
        c = run_case()
        metrics = compute_report_metrics(brands=['Alpha'],focus=['pricing'],claims=[c],evidences=[],structured={},
                                         elapsed_seconds=1,tokens_used=0)
        self.assertEqual(metrics['business']['high_confidence_ratio'], 1)
        self.assertEqual(metrics['business']['cross_validated_ratio'], 0)

    def test_dashboard_never_uses_high_trust_ratio_as_independence(self):
        import sqlite3
        from unittest.mock import patch
        from app.core import db
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        db._init_schema(conn)
        try:
            with patch.object(db, '_connect', return_value=conn), db.use_visitor(None):
                db.save_report({'id':'legacy','claims':[{'confidence':'high','cross_validated':True}]})
                self.assertIsNone(db.dashboard_stats()['independent_verification_percent'])
                db.save_report({'id':'new','claims':[run_case()]})
                stats = db.dashboard_stats()
                self.assertEqual(stats['rated_claim_count'], 1)
                self.assertEqual(stats['high_confidence_percent'], 100)
                self.assertEqual(stats['independent_verification_percent'], 0)
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main()
