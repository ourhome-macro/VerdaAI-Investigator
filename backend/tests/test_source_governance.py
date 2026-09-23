import unittest
from unittest.mock import patch

from app.core.models import Evidence
from app.core.source_policy import canonical_url, classify, annotate_sources, admission
from app.core.final_audit import finalize_report


def evidence(eid, url, text="A product " * 60, origin=""):
    return Evidence(eid, url, "web", "产品", text[:280], "", 50, "test", brand="特斯拉",
                    full_text=text, origin_url=origin, fetch_kind="body")


class SourceTests(unittest.TestCase):
    def test_quote_whitespace_normalization_keeps_original_offsets(self):
        from app.core.claim_verifier import locate_quote
        text = '价格：¥3,060\u00a0/月\n按首付 ¥79,900 计算'
        found = locate_quote(text, '¥3,060/月 按首付¥79,900计算')
        self.assertIsNotNone(found)
        self.assertEqual(text[found[0]:found[1]], text[3:])
        self.assertIsNone(locate_quote(text, '¥3,061/月'))

    def test_secondary_keyword_stuffing_cannot_displace_available_primary_price(self):
        from app.core.evidence_context import select_evidence
        primary = evidence('primary', 'https://www.tesla.cn/model3', '特斯拉 Model 3 售价为239800元。')
        spam = evidence('spam', 'https://spam.test/cars', '特斯拉 比亚迪 理想 价格 定价 售价 指导价 万元 产品 功能 对比 ' * 100)
        annotate_sources([primary, spam])
        ctx = select_evidence([spam, primary], brands=['特斯拉'], focus=['定价'], query='特斯拉定价', limit=1)
        self.assertEqual(ctx.evidence_ids, {'primary'})

    def test_explicit_yuan_unit_conversion_without_scaling_model_year(self):
        from app.core.claim_verifier import _numbers
        self.assertTrue(_numbers('23.98万元') <= _numbers('¥239,800', conversions=True))
        self.assertTrue(_numbers('239800元') <= _numbers('23.98万元', conversions=True))
        self.assertTrue(_numbers('74,800元至104,800元') <= _numbers('￥74,800 - 104,800', conversions=True))
        self.assertTrue(_numbers('7.48至10.48万元') <= _numbers('￥74,800 - 104,800', conversions=True))
        self.assertNotIn('0.2026', _numbers('2026款', conversions=True))
        self.assertEqual(_numbers('理想L6采用M100芯片，纯电续航300公里'), {'3E+2'})
        self.assertTrue(_numbers('整车质保6年或15万公里') <= _numbers('6年或150000公里', conversions=True))
    def test_strict_domains_and_mobile_alias(self):
        self.assertEqual(classify("https://www.tesla.cn/modely", "特斯拉"), "official")
        self.assertNotEqual(classify("https://tesla.cn.attacker.test/", "特斯拉"), "official")
        self.assertNotEqual(classify("https://www.byd.com/", "特斯拉"), "official")
        self.assertEqual(canonical_url("http://m.example.com/a?utm_source=x&id=2#top"), "https://example.com/a?id=2")
        self.assertNotEqual(canonical_url("https://x.test/a?id=2"), canonical_url("https://x.test/a?id=3"))

    def test_same_original_and_rewrite_attribution(self):
        first = evidence("a", "https://media-a.test/one", "different first " * 40, "https://origin.test/report")
        second = evidence("b", "https://media-b.test/two", "rewritten second " * 40, "https://origin.test/report")
        annotate_sources([first, second])
        self.assertEqual(first.source_group, second.source_group)
        self.assertNotEqual(first.source_tier, "official")

    def test_near_duplicates_and_publisher_under_count(self):
        text = "新能源车价格及产品参数如下，具体配置与交付日期需要核实。" * 40
        # Use nonrepeating content so the shingle set passes the conservative minimum.
        text += " ".join(f"feature{i}: specification{i * 3}" for i in range(70))
        a, b = evidence("a", "https://one.test/a", text), evidence("b", "https://two.test/b", text + "转载说明")
        annotate_sources([a, b])
        self.assertEqual(a.source_group, b.source_group)
        self.assertIn("near_duplicate", b.provenance_reason)

    def test_price_needs_primary_body_for_every_brand(self):
        refs = [{"evidence_id": "a"}]
        by_id = {"a": [{"source_tier": "secondary", "fetch_kind": "body", "brand": "A"}]}
        self.assertFalse(admission({"field": "pricing_model"}, refs, by_id)[0])
        by_id["a"][0]["source_tier"] = "official"
        self.assertTrue(admission({"field": "pricing_model"}, refs, by_id)[0])
        by_id["a"][0]["fetch_kind"] = "snippet"
        self.assertFalse(admission({"field": "pricing_model"}, refs, by_id)[0])

    def test_search_filters_provider_out_of_scope_results(self):
        from app.core.search import search_bocha
        from app.core.config import Settings
        payload = {"data": {"webPages": {"value": [
            {"url": "https://tesla.cn.attacker.test", "name": "Tesla pricing", "summary": "Tesla price"},
            {"url": "https://www.tesla.cn/modely", "name": "Tesla pricing", "summary": "Tesla price"}]}}}
        with patch("app.core.search.get_settings", return_value=Settings(_env_file=None, bocha_api_key="test")), \
                patch("app.core.search.httpx.Client") as client:
            response = client.return_value.__enter__.return_value.post.return_value
            response.status_code = 200
            response.json.return_value = payload
            result = search_bocha("Tesla pricing", site="tesla.cn")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["captured_at"], "")


class FinalAuditTests(unittest.TestCase):
    def test_fabricated_number_is_removed_and_verified_table_preserved(self):
        claim = {"claim_id": "c1", "text": "A costs 20 USD.", "field": "pricing_model",
                 "evidence_ids": ["e_one"], "verification": {"verdict": "supported"}}
        report = {"claims": [claim], "evidence": [{"evidence_id": "e_one", "source_url": "https://a.test"}],
                  "sections": [{"id": "pricing", "paragraphs": ["A costs 999 USD. [e_one]"], "claims": [claim]}]}
        reviewer = lambda *a, **kw: {"results": [{"id": "pricing:paragraphs:0", "supported": True, "claim_ids": ["c1"]}]}
        result = finalize_report(report, model="test", reviewer=reviewer)
        self.assertNotIn("999", "".join(result["sections"][0]["paragraphs"]))
        self.assertIn("20", result["sections"][0]["data_grid"]["rows"][0]["value"])
        self.assertTrue(result["final_audit"]["repairs"])

    def test_final_audit_failure_never_publishes_unchecked_prose(self):
        claim = {"claim_id": "c1", "text": "A has CSV export.", "field": "feature_tree",
                 "evidence_ids": ["e_one"], "verification": {"verdict": "supported"}}
        report = {"claims": [claim], "evidence": [], "sections": [
            {"id": "feature", "paragraphs": ["A also has SAML."], "claims": [claim]}]}
        result = finalize_report(report, model="test", reviewer=lambda *a, **kw: None)
        self.assertNotIn("SAML", "".join(result["sections"][0]["paragraphs"]))
        self.assertIn("CSV", "".join(result["sections"][0]["paragraphs"]))


if __name__ == "__main__":
    unittest.main()
