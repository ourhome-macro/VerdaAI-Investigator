"""Offline regression for selection, grounded verification and collect-only rework."""
import asyncio
import json
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from app.core import orchestrator as orch
from app.core.audit import evaluate_quality, QualityReport, decide_rework
from app.core.claim_verifier import verify_claims
from app.core.evidence_context import select_evidence
from app.core.models import Evidence


def ev(eid, brand="A", text="A pricing monthly USD 20.", url=None):
    return Evidence(eid, url or f"https://{eid}.example/pricing", "official", brand + " plans",
                    text[:280], "2026-09-23", 80, "L1-025", brand=brand, full_text=text,
                    source_tier="official", fetch_kind="body")


def claim(eids=None, text="A costs USD 20 monthly.", cid="c1"):
    return {"claim_id": cid, "text": text, "field": "pricing_model",
            "evidence_ids": eids or ["e1"], "confidence": "high", "cross_validated": True, "author": "L2-001"}


class EvidenceSelectionTests(unittest.TestCase):
    def test_brand_analysis_has_isolated_evidence_and_copied_request_context(self):
        from contextvars import ContextVar
        marker = ContextVar('analysis-test-context', default='missing')
        token = marker.set('request-owner')
        records = []
        def analyze_brand(query, brands, focus, evidence, members, *args, **kwargs):
            records.append((brands[0], [e.brand for e in evidence], marker.get()))
            return {'claims': [{'text': brands[0]}], 'evidence_selection': []}
        try:
            with patch.object(orch, '_analyze_brand', side_effect=analyze_brand):
                result = orch._analyze('compare', ['A', 'B', 'C'], ['定价'],
                                       [ev('a', 'A'), ev('b', 'B'), ev('c', 'C')], ['L2-001'])
            self.assertEqual({c['text'] for c in result['claims']}, {'A', 'B', 'C'})
            self.assertEqual(sorted(records), [(b, [b], 'request-owner') for b in ['A', 'B', 'C']])
        finally:
            marker.reset(token)

    def test_tail_brand_and_late_passage_survive_roundtrip(self):
        evidence = [ev(f"a{i}", text="A product feature integration.") for i in range(40)]
        tail = ev("tail", "B", "Company introduction. " * 300 + "B pricing monthly USD 37 per seat.")
        evidence.append(tail)
        ctx = select_evidence([e.to_dict() for e in evidence], query="A B 价格对比",
                              brands=["A", "B"], focus=["定价"], limit=4)
        self.assertIn("tail", ctx.evidence_ids)
        self.assertIn("USD 37", ctx.digest)
        passage = next(p for p in ctx.passages if p["evidence_id"] == "tail")
        self.assertGreater(passage["start"], 1500)
        self.assertEqual(tail.full_text[passage["start"]:passage["end"]], passage["text"])

    def test_rework_evidence_replaces_irrelevant_context(self):
        old = [ev(f"e{i}", text="A feature integration and collaboration.") for i in range(40)]
        before = select_evidence(old, query="A pricing", brands=["A"], focus=["定价"], limit=1)
        after = select_evidence(old + [ev("fresh", text="A pricing USD 29 monthly.")],
                                query="A pricing", brands=["A"], focus=["定价"], limit=1)
        self.assertNotIn("fresh", before.evidence_ids)
        self.assertEqual(after.evidence_ids, {"fresh"})

    def test_budget_is_bounded_and_old_reports_work(self):
        evidence = [ev(str(i), text="A 定价每月20美元。" * 500) for i in range(6)]
        ctx = select_evidence(evidence, query="定价", max_chars=3000, max_tokens=3200)
        self.assertLessEqual(len(ctx.digest), 3000)
        self.assertLessEqual(len(ctx.digest.encode("utf-8")), 3200)
        legacy = ev("old").to_dict()
        del legacy["full_text"]
        self.assertIn("USD 20", select_evidence([legacy], query="pricing").digest)
        self.assertFalse(select_evidence(evidence, max_tokens=1).passages)

    def test_six_brands_get_representation_under_default_budget(self):
        brands = [f"Brand{i}" for i in range(6)]
        evidence = [ev(f"{brand}-{i}", brand, (brand + " 定价按月20美元。") * 100)
                    for brand in brands for i in range(8)]
        ctx = select_evidence(evidence, query="比较定价", brands=brands, focus=["定价"])
        self.assertEqual({p["brand"] for p in ctx.passages}, set(brands))

    def test_different_dimensions_retrieve_different_passages(self):
        document = ev("long", text="A pricing USD 20 monthly. " + "Background information. " * 150
                      + "A features include CSV export and integration.")
        price = select_evidence([document], query="A", focus=["定价"], limit=1)
        feature = select_evidence([document], query="A", focus=["功能"], limit=1)
        self.assertIn("USD 20", price.digest)
        self.assertIn("CSV export", feature.digest)
        self.assertNotEqual(price.passages[0]["start"], feature.passages[0]["start"])


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.evidence = [ev("e1"), ev("e2")]
        self.ctx = select_evidence(self.evidence, query="A pricing", brands=["A"])

    def review(self, verdict="supported", quote="A pricing monthly USD 20.", relation="supports"):
        return lambda *a, **kw: {"results": [{"claim_id": "c1", "verdict": verdict,
            "assessment": {"claim_type": "declared_fact", "scope_complete": True, "temporal_alignment": "consistent"},
            "reason": "checked", "supports": [{"evidence_id": eid, "quote": quote, "relation": relation}
                                               for eid in ("e1", "e2")]}]}

    def test_valid_support_has_original_offsets(self):
        c = verify_claims([claim(["e1", "e2"])], self.ctx, model="test", reviewer=self.review())[0]
        self.assertEqual(c["confidence"], "high")
        self.assertTrue(c["cross_validated"])
        for s in c["verification"]["supports"]:
            original = next(e.full_text for e in self.evidence if e.evidence_id == s["evidence_id"])
            self.assertEqual(original[s["start"]:s["end"]], s["quote"])

    def test_invented_quote_fails_closed(self):
        c = verify_claims([claim(["e1", "e2"])], self.ctx, model="test",
                          reviewer=self.review(quote="Invented price USD 20."))[0]
        self.assertEqual(c["confidence"], "unverified")

    def test_wrong_number_not_promoted_even_if_reviewer_says_supported(self):
        c = verify_claims([claim(["e1", "e2"], "A costs USD 999 monthly.")], self.ctx,
                          model="test", reviewer=self.review())[0]
        self.assertEqual(c["verification"]["verdict"], "partial")
        self.assertFalse(c["cross_validated"])

    def test_partial_or_contradicted_never_promoted(self):
        for verdict in ("partial", "contradicted", "insufficient"):
            c = verify_claims([claim(["e1", "e2"])], self.ctx, model="test", reviewer=self.review(verdict))[0]
            self.assertEqual(c["confidence"], "unverified")
        c = verify_claims([claim(["e1", "e2"])], self.ctx, model="test",
                          reviewer=self.review(relation="contradicts"))[0]
        self.assertEqual(c["verification"]["verdict"], "contradicted")

    def test_composite_support_not_independent_cross_validation(self):
        c = verify_claims([claim(["e1", "e2"])], self.ctx, model="test",
                          reviewer=self.review(relation="partial"))[0]
        self.assertEqual(c["confidence"], "medium")
        self.assertFalse(c["cross_validated"])

    def test_unavailable_or_malformed_reviewer_does_not_pass(self):
        def fail(*a, **kw):
            raise TimeoutError()
        for reviewer in (fail, lambda *a, **kw: None, lambda *a, **kw: {"results": "invalid"}):
            c = verify_claims([claim()], self.ctx, model="test", reviewer=reviewer)[0]
            self.assertEqual(c["confidence"], "unverified")

    def test_unknown_id_and_duplicates_cannot_create_support(self):
        result = verify_claims([claim(["fake"])], self.ctx, model="test", reviewer=self.review())[0]
        self.assertEqual(result["evidence_ids"], [])
        self.assertEqual(result["confidence"], "unverified")

    def test_analyze_filters_ids_not_visible_in_context(self):
        evidence = self.evidence + [ev("hidden", text="unrelated gardening", brand="Garden")]
        evidence[-1].title = "Gardening"
        raw = {"claims": [{"text": "A costs USD 999 monthly.", "field": "pricing_model",
                           "evidence_ids": ["hidden", "not_real"], "author": "L2-001"}]}
        with patch.object(orch, "chat_json", return_value=raw):
            result = orch._analyze("A pricing", ["A"], ["定价"], evidence, ["L2-001"])
        self.assertEqual(result["claims"], [])  # Invalid references are rejected before NLI.

    def test_dimension_coverage_requires_verified_matching_claim(self):
        c = claim()
        c["verification"] = {"verdict": "supported"}
        c["confidence"] = "low"
        quality = evaluate_quality(["A"], ["定价", "功能", "生态壁垒"], [c], self.evidence, {})
        self.assertEqual(quality.coverage_by_dimension, {"定价": True, "功能": False, "生态壁垒": False})

    def test_failed_claim_is_actionable_rework_not_covered(self):
        c = claim()
        c["verification"] = {"verdict": "partial", "reason": "缺计费周期"}
        quality = evaluate_quality(["A"], ["定价"], [c], self.evidence, {})
        self.assertFalse(quality.coverage_by_dimension["定价"])
        collect = next(e for e in decide_rework(quality) if e.receiver == "collect")
        self.assertEqual(collect.payload["cells"][0]["brand"], "A")
        self.assertEqual(collect.payload["cells"][0]["dimension"], "pricing_model")

    def test_analysis_failure_never_creates_high_confidence_fallback(self):
        with patch.object(orch, "chat_json", side_effect=TimeoutError("do-not-expose-provider-error")):
            result = orch._analyze("A pricing", ["A"], ["定价"], self.evidence, ["L2-001"])
        self.assertEqual(result["claims"], [])
        self.assertEqual(result["analysis_errors"], ["TimeoutError"])

    def test_writing_only_receives_supported_claims_not_auxiliary_numbers(self):
        accepted = claim(text="A costs USD 20 monthly.")
        accepted["verification"] = {"verdict": "supported", "supports": []}
        rejected = claim(text="A costs USD 999 monthly.", cid="c2")
        rejected["verification"] = {"verdict": "contradicted", "supports": []}
        with patch.object(orch, "chat_json", return_value={"paragraphs": ["A costs USD 20."]}) as llm:
            orch._write_single_section("pricing", "定价", "A", ["A"], ["定价"], self.evidence,
                                       [accepted, rejected], {"pricing": [{"brand": "A", "entry_price": 999}]}, "test")
            prompt = llm.call_args.args[0][-1]["content"]
            self.assertIn("USD 20", prompt)
            self.assertNotIn("999", prompt)
        with patch.object(orch, "chat_json") as llm:
            result = orch._write_single_section("pricing", "定价", "A", ["A"], ["定价"],
                                               self.evidence, [rejected], {}, "test")
            llm.assert_not_called()
            self.assertIn("待验证", result["key_takeaway"])


class ReworkTests(unittest.TestCase):
    def test_collect_only_rework_refreshes_claims_and_persisted_report(self):
        self.run_case(resolve=True)

    def test_budget_exhaustion_keeps_report_needs_review(self):
        self.run_case(resolve=False)

    def run_case(self, resolve):
        before = ev("before", text="A pricing was USD 99 monthly.")
        after = ev("after", text="A pricing is now USD 20 monthly.")
        snapshots = []
        def analyze(query, brands, focus, evidences, members, *args, **kwargs):
            snapshots.append([e.evidence_id for e in evidences])
            ctx = select_evidence(evidences, query="A pricing now", brands=["A"], focus=["定价"])
            c = claim([evidences[-1].evidence_id], evidences[-1].full_text)
            c.update(brand="A", cell_id=orch.cell_id("A", "pricing_model"))
            c["verification"] = {"verdict": "supported", "reason": "fixture", "supports": []}
            return {"claims": [c], "evidence_selection": ctx.passages}
        gap = QualityReport(issues=[{"target": "cell:pricing", "reason": "缺来源", "severity": "medium",
                                    "cell_id": orch.cell_id("A", "pricing_model"), "brand": "A", "dimension": "pricing_model"}])
        done = QualityReport() if resolve else gap
        plan = {"brands": ["A"], "focus": ["定价"], "angles": ["a", "b", "c", "d"], "category": "software"}
        dispatch = {"lead": "L3-001", "members": [{"id": "L3-001", "reason": "lead"},
                    {"id": "L1-025", "reason": "collect"}, {"id": "L2-001", "reason": "analysis"}]}
        cfg = {**orch.MODE_CONFIG["quick"], "sections": ["summary"], "sentiment_brands": 0, "rework_rounds": 1}
        with ExitStack() as stack:
            stack.enter_context(patch.object(orch, "finalize_report", side_effect=lambda report, **kw: report))
            stack.enter_context(patch.dict(orch.MODE_CONFIG, {"quick": cfg}))
            stack.enter_context(patch.object(orch.db, "get_task", return_value={"query": "A pricing", "clarifications": {"_mode": "quick"}}))
            for name, result in (("_plan_research", plan), ("_dispatch_experts", dispatch),
                                 ("_analyze_structured", {}), ("analyze_sentiment", {}), ("_build_charts", []),
                                 ("_write_single_section", {"paragraphs": ["verified draft"]})):
                stack.enter_context(patch.object(orch, name, return_value=result))
            collector = stack.enter_context(patch.object(orch, "_collect_brand", side_effect=[
                {"evidences": [before], "images": [], "found": 1},
                {"evidences": [after], "images": [], "found": 1}]))
            stack.enter_context(patch.object(orch, "_analyze", side_effect=analyze))
            quality = stack.enter_context(patch.object(orch, "evaluate_quality", side_effect=[gap, done]))
            stack.enter_context(patch.object(orch, "llm_quality_review", side_effect=[
                {"verdict": "rework", "issues": ["缺来源"]}, {"verdict": "pass" if resolve else "rework"}]))
            saved = stack.enter_context(patch.object(orch.db, "save_report"))
            for name in ("save_traces", "mark_task_done", "bump_expert_stats"):
                stack.enter_context(patch.object(orch.db, name))
            async def consume():
                return [e async for e in orch.run_pipeline("test-evidence-rework")]
            events = asyncio.run(consume())
            self.assertEqual(snapshots, [["before"], ["before", "after"]])
            self.assertEqual(quality.call_count, 2)
            self.assertEqual(collector.call_args_list[1].args[-1][0]["key"], "pricing_model")
            report = saved.call_args.args[0]
            self.assertIn("USD 20", report["claims"][0]["text"])
            self.assertEqual(report["quality_status"], "passed" if resolve else "needs_review")
            self.assertTrue(any(p["evidence_id"] == "after" for p in report["evidence_selection"]))
            replacements = [e for e in events if e["type"] == "message" and e["data"]["kind"] == "claims_replaced"]
            self.assertEqual(replacements[-1]["data"]["claims"], report["claims"])
            self.assertEqual(events[-1]["type"], "done")


if __name__ == "__main__":
    unittest.main()
