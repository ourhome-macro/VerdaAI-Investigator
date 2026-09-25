import unittest
import sqlite3
import time
import json
import threading
import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from app.core import db, outbound_limit, performance, research_cache, search, search_extra
from app.core.fetcher import is_public_http_url


class SearchProviderTests(unittest.TestCase):
    def test_anysearch_normalizes_only_page_backed_results(self):
        settings = SimpleNamespace(anysearch_base_url="https://api.anysearch.com/v1",
                                   anysearch_api_key="test", search_timeout=5,
                                   anysearch_requests_per_second=1)
        body = {"code": 0, "data": {"results": [
            {"title": "A", "url": "https://example.com/one", "snippet": "real", "content": "body"},
            {"title": "B", "url": "https://example.com.evil.test/two", "snippet": "wrong"},
            {"title": "C", "url": "javascript:alert(1)", "snippet": "bad"}]}}
        with patch.object(search_extra, "get_settings", return_value=settings), \
                patch.object(search_extra, "post_json", return_value=body), \
                patch.object(search_extra.research_cache, "get", return_value=None), \
                patch.object(search_extra.research_cache, "put"):
            rows = search_extra.search_anysearch("A", site="example.com")
        self.assertEqual([r["url"] for r in rows], ["https://example.com/one"])
        self.assertNotIn("content", rows[0])

    def test_grok_gateway_without_tool_usage_is_rejected_and_circuited(self):
        settings = SimpleNamespace(grok_search_api_key="test-grok-key", grok_search_base_url="https://proxy.test/v1",
                                   grok_search_model="grok-test", llm_timeout=5, grok_requests_per_second=1)
        body = {"usage": {"num_server_side_tools_used": 0},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": "invented link"}]}]}
        with patch.object(search_extra, "get_settings", return_value=settings), \
                patch.object(search_extra, "post_json", return_value=body) as post, \
                patch.object(search_extra.research_cache, "get", return_value=None):
            with self.assertRaises(search_extra.SearchProviderError):
                search_extra.search_grok("new thing")
            with self.assertRaises(search_extra.SearchProviderError):
                search_extra.search_grok("another thing")
        self.assertEqual(post.call_count, 1)

    def test_grok_only_uses_structured_citations_after_real_tool_call(self):
        settings = SimpleNamespace(grok_search_api_key="test-grok-valid", grok_search_base_url="https://xai.test/v1",
                                   grok_search_model="grok-test", llm_timeout=5, grok_requests_per_second=1)
        body = {"usage": {"num_server_side_tools_used": 1},
                "citations": ["https://example.com/source", "https://example.com/source",
                              "javascript:alert(1)"], "output": []}
        with patch.object(search_extra, "get_settings", return_value=settings), \
                patch.object(search_extra, "post_json", return_value=body), \
                patch.object(search_extra.research_cache, "get", return_value=None), \
                patch.object(search_extra.research_cache, "put"):
            rows = search_extra.search_grok("new thing", site="example.com")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["search_provider"], "grok")
        self.assertEqual(rows[0]["snippet"], "")

    def test_grok_planner_uses_anysearch_urls_not_model_answer(self):
        settings = SimpleNamespace(grok_search_api_key="planner-key",
                                   grok_search_base_url="https://proxy.test/v1",
                                   grok_search_model="grok-test", llm_timeout=5,
                                   grok_requests_per_second=1)
        body = {"choices": [{"message": {"content": '{"queries":["Notion plan pricing official"]}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        lead = {"url": "https://notion.so/pricing", "title": "Notion Pricing", "snippet": ""}
        with patch.object(search_extra, "get_settings", return_value=settings), \
                patch.object(search_extra, "post_json", return_value=body), \
                patch.object(search_extra, "search_anysearch", return_value=[lead]) as anysearch, \
                patch.object(search_extra.research_cache, "get", return_value=None), \
                patch.object(search_extra.research_cache, "put"):
            rows = search_extra.search_grok_planned("Notion official pricing", num=2)
        self.assertEqual(rows[0]["url"], lead["url"])
        self.assertEqual(rows[0]["search_provider"], "grok+anysearch")
        anysearch.assert_called_once()
        self.assertIn("Notion", anysearch.call_args.args[0])

    def test_native_x_search_accepts_only_x_post_citations(self):
        settings = SimpleNamespace(grok_search_api_key="x-search-key",
                                   grok_search_base_url="https://xai.test/v1",
                                   grok_search_model="grok-test", llm_timeout=5,
                                   grok_requests_per_second=1)
        body = {"usage": {"server_side_tool_usage_details": {"x_search_calls": 1}},
                "citations": ["https://x.com/person/status/123", "https://x.com/person",
                              "https://example.com/other"],
                "output": []}
        with patch.object(search_extra, "get_settings", return_value=settings), \
                patch.object(search_extra, "post_json", return_value=body), \
                patch.object(search_extra.research_cache, "get", return_value=None), \
                patch.object(search_extra.research_cache, "put"):
            rows = search_extra.search_grok_x("Notion review", num=2)
        self.assertEqual([r["url"] for r in rows], ["https://x.com/person/status/123"])
        self.assertEqual(rows[0]["search_provider"], "grok-x")

    def test_native_x_search_rejects_ignored_tool_request(self):
        settings = SimpleNamespace(grok_search_api_key="x-unsupported-key",
                                   grok_search_base_url="https://proxy.test/v1",
                                   grok_search_model="grok-test", llm_timeout=5,
                                   grok_requests_per_second=1)
        body = {"usage": {"num_server_side_tools_used": 0}, "output": []}
        with patch.object(search_extra, "get_settings", return_value=settings), \
                patch.object(search_extra, "post_json", return_value=body) as post, \
                patch.object(search_extra.research_cache, "get", return_value=None):
            with self.assertRaises(search_extra.SearchProviderError):
                search_extra.search_grok_x("Notion review")
            with self.assertRaises(search_extra.SearchProviderError):
                search_extra.search_grok_x("Notion pricing")
        self.assertEqual(post.call_count, 1)

    def test_multi_provider_fallback_deduplicates(self):
        settings = SimpleNamespace(search_providers="bocha,anysearch,grok", bocha_api_key="b",
                                   grok_search_api_key="g", grok_search_mode="native")
        rows = [{"url": "https://example.com/a", "title": "A", "snippet": "", "search_provider": "anysearch"}]
        with patch.object(search, "get_settings", return_value=settings), \
                patch.object(search, "search_bocha", side_effect=RuntimeError("bocha down")), \
                patch.object(search, "search_anysearch", return_value=rows), \
                patch.object(search, "search_grok", return_value=rows):
            result = search.search("test", num=2)
        self.assertEqual(len(result), 1)

    def test_search_routing_avoids_second_paid_call_after_enough_results(self):
        settings = SimpleNamespace(search_providers="bocha,anysearch", bocha_api_key="b", grok_search_api_key="")
        rows = [{"url": "https://example.com/a", "title": "A"}]
        with patch.object(search, "get_settings", return_value=settings), \
                patch.object(search, "search_bocha", return_value=rows) as bocha, \
                patch.object(search, "search_anysearch", return_value=rows) as anysearch:
            search.search("A", num=1, source_kind="official")
            bocha.assert_called_once()
            anysearch.assert_not_called()
            search.search("A", num=1, source_kind="community")
            anysearch.assert_called_once()
            self.assertEqual(bocha.call_count, 1)

    def test_community_routing_invokes_proxy_grok_planner_once(self):
        settings = SimpleNamespace(search_providers="bocha,anysearch,grok", bocha_api_key="b",
                                   grok_search_api_key="g", grok_search_mode="planner")
        rows = [{"url": "https://example.com/a", "title": "A"}]
        with patch.object(search, "get_settings", return_value=settings), \
                patch.object(search, "search_bocha") as bocha, \
                patch.object(search, "search_anysearch", return_value=rows), \
                patch.object(search, "search_grok_planned", return_value=[
                    {"url": "https://example.com/b", "title": "B"}]) as planner:
            result = search.search("A review", num=1, source_kind="community", use_grok=True)
        bocha.assert_not_called()
        planner.assert_called_once()
        self.assertEqual(len(result), 2)

    def test_overseas_x_routing_uses_planner_with_current_gateway(self):
        settings = SimpleNamespace(search_providers="bocha,anysearch,grok", bocha_api_key="b",
                                   grok_search_api_key="g", grok_search_mode="planner")
        lead = {"url": "https://x.com/person/status/123", "title": "post"}
        with patch.object(search, "get_settings", return_value=settings), \
                patch.object(search, "search_anysearch", return_value=[lead]), \
                patch.object(search, "search_bocha") as bocha, \
                patch.object(search, "search_grok_planned", return_value=[]) as planner:
            rows = search.search("Notion review site:x.com", num=1, site="x.com|twitter.com",
                                 source_kind="x", use_grok=True)
        bocha.assert_not_called()
        planner.assert_called_once()
        self.assertEqual(rows[0]["url"], lead["url"])

    def test_performance_records_stage_and_call_percentiles(self):
        with performance.use_task("metric-test"):
            performance.on_node_update("metric-test", {"node": "collect", "status": "working"})
            performance.record("search", "anysearch", 10, cache_hit=True)
            performance.record("search", "bocha", 30)
            performance.record("llm", "deepseek", 200, prompt_tokens=12, completion_tokens=8)
            performance.on_node_update("metric-test", {"node": "collect", "status": "done"})
            sample = performance.snapshot("metric-test")
        performance.cleanup("metric-test")
        self.assertEqual(sample["calls"]["search"]["p95_ms"], 30)
        self.assertEqual(sample["cache_hits"]["search"], 1)
        self.assertEqual(sample["tokens"]["input"], 12)
        self.assertIn("collect", sample["stage_seconds"])

    def test_page_cache_rechecks_requested_max_age(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        with patch.object(db, "_connect", return_value=conn):
            research_cache.put("page", "page-key", {"text": "body"}, 86400)
            self.assertEqual(research_cache.get("page", "page-key"), {"text": "body"})
            conn.execute("UPDATE research_cache SET created_at=? WHERE cache_key=?",
                         (time.time() - 7200, "page-key"))
            conn.commit()
            self.assertIsNone(research_cache.get("page", "page-key", max_age_seconds=3600))
        conn.close()

    def test_outbound_limiter_bounds_in_flight_requests(self):
        key = outbound_limit.scope("test", "https://test.invalid", "unique-unit-key")
        with outbound_limit.permit(key, per_second=100, max_in_flight=1):
            with self.assertRaises(TimeoutError):
                with outbound_limit.permit(key, per_second=100, max_in_flight=1, max_wait=0.01):
                    pass

    def test_oversized_prompt_is_rejected_before_model_request(self):
        from app.core import llm
        settings = SimpleNamespace(llm_max_input_bytes=40,
                                   provider_config=SimpleNamespace(default_model="test", name="custom"))
        with patch.object(llm, "get_settings", return_value=settings), \
                patch.object(llm, "_get_client") as client:
            with self.assertRaises(ValueError):
                llm.chat([{"role": "user", "content": "large prompt" * 20}])
        client.return_value.chat.completions.create.assert_not_called()

    def test_provider_leads_cannot_target_local_network(self):
        self.assertFalse(is_public_http_url("http://127.0.0.1/admin"))
        self.assertFalse(is_public_http_url("http://192.168.1.10/secret"))
        self.assertFalse(is_public_http_url("http://localhost/"))
        self.assertTrue(is_public_http_url("https://example.com/page"))

    def test_x_posts_are_community_evidence_only_for_overseas_scope(self):
        from app.core import orchestrator as orch
        from app.core.source_policy import classify
        self.assertEqual(classify("https://x.com/person/status/123", "Notion"), "community")
        self.assertEqual(orch._source_type("https://x.com/person/status/123"), "x")
        self.assertTrue(orch._overseas_market("美国"))
        self.assertTrue(orch._overseas_market("US"))
        self.assertFalse(orch._overseas_market("中国大陆"))
        self.assertFalse(orch._overseas_market("Russia"))

    def test_overseas_collection_queries_x_once(self):
        from app.core import orchestrator as orch
        from app.core.research_contract import build_contract
        contract = build_contract(["Notion"], ["用户口碑"], {"market": "美国"})
        with patch.object(orch, "multi_search", return_value=[]) as multi:
            orch._collect_brand("Notion", [], "L1", 3, contract["freshness"], set(), contract)
        x_calls = [call for call in multi.call_args_list
                   if call.kwargs.get("source_kind") == "x"]
        self.assertEqual(len(x_calls), 1)
        self.assertTrue(x_calls[0].kwargs["use_grok"])
        self.assertEqual(x_calls[0].kwargs["site"], "x.com|twitter.com")

    def test_x_post_enters_evidence_only_after_body_fetch(self):
        from app.core import orchestrator as orch
        from app.core.research_contract import build_contract
        contract = build_contract(["Notion"], ["用户口碑"], {"market": "美国"})
        lead = {"url": "https://x.com/person/status/123", "title": "Notion user review",
                "snippet": "Notion user experience", "search_provider": "grok+anysearch"}

        def results(*args, **kwargs):
            return [lead] if kwargs.get("source_kind") == "x" else []

        page = {"url": lead["url"], "text": "I use Notion every day and its sync feels slow to me.",
                "ok": True, "fetch_kind": "body", "published_at": "", "captured_at": "2026-09-25T00:00:00Z",
                "origin_url": "", "product_links": []}
        with patch.object(orch, "multi_search", side_effect=results), \
                patch.object(orch, "cached_fetch_page", return_value=page):
            collected = orch._collect_brand("Notion", [], "L1", 3,
                                            contract["freshness"], set(), contract)
        self.assertEqual(len(collected["evidences"]), 1)
        evidence = collected["evidences"][0]
        self.assertEqual(evidence.source_type, "x")
        self.assertEqual(evidence.search_provider, "grok+anysearch")
        self.assertEqual(evidence.fetch_kind, "body")

    def test_cross_report_stage_percentiles_and_rework(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        db._init_schema(conn)
        for i, seconds in enumerate((1.0, 3.0)):
            report = {"performance": {"stage_seconds": {"collect": seconds},
                                      "calls": {"search": {"samples_ms": [seconds * 100]}},
                                      "cache_hits": {"search": i},
                                      "tokens": {"input": 10, "output": 5}},
                      "audit_review": {"rework_rounds": i}}
            conn.execute("INSERT INTO reports(report_id,task_id,data,created_at) VALUES(?,?,?,?)",
                         (str(i), str(i), json.dumps(report), str(i)))
        failed = {"stage_seconds": {"collect": 5.0},
                  "calls": {"search": {"samples_ms": [500]}},
                  "cache_hits": {}, "tokens": {"input": 5, "output": 0}}
        conn.execute("INSERT INTO research_run_metrics VALUES(?,?,?,?,?)",
                     ("failed", 1, "failed", json.dumps(failed), 3.0))
        conn.commit()
        with patch.object(db, "_connect", return_value=conn):
            summary = db.performance_summary()
        conn.close()
        self.assertEqual(summary["stage_seconds"]["collect"]["p50"], 3)
        self.assertEqual(summary["stage_seconds"]["collect"]["p95"], 5)
        self.assertEqual(summary["tokens"]["input"], 25)
        self.assertEqual(summary["failed_attempts"], 1)
        self.assertEqual(summary["rework_rounds"]["p95"], 1)


class ParallelCollectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_collection_caps_brand_parallelism_at_two(self):
        from app.core import orchestrator as orch, trace

        active = maximum = 0
        lock = threading.Lock()

        def collect(*args, **kwargs):
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.04)
            with lock:
                active -= 1
            return {"evidences": [], "images": [], "found": 0}

        plan = {"brands": ["A", "B", "C"], "focus": ["定价"],
                "angles": ["price"], "category": "software"}
        dispatch = {"lead": "L3-001", "members": [{"id": "L3-001", "reason": "lead"},
                                                  {"id": "L1-025", "reason": "collect"}]}
        settings = SimpleNamespace(collect_brand_concurrency=2, search_providers="bocha")
        with patch.object(orch.db, "get_task", return_value={"query": "A B C pricing", "clarifications": {}}), \
                patch.object(orch, "_plan_research", return_value=plan), \
                patch.object(orch, "_dispatch_experts", return_value=dispatch), \
                patch.object(orch, "_collect_brand", side_effect=collect), \
                patch.object(orch, "get_settings", return_value=settings), \
                patch.object(orch.task_runtime, "collection_checkpoint", return_value=[]):
            events = [event async for event in orch.run_pipeline("parallel-fixture")]
        trace.cleanup("parallel-fixture")
        self.assertEqual(maximum, 2)
        self.assertEqual(events[-1]["type"], "error")


if __name__ == "__main__":
    unittest.main()
