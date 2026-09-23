"""Regression tests for visitor API key isolation across concurrent research work."""
import asyncio
import hashlib
import sqlite3
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.client_credentials import browser_settings
from app.core.config import Settings, get_settings, use_request_settings


class ClientCredentialsTests(unittest.TestCase):
    def setUp(self):
        self.base = Settings(
            _env_file=None,
            require_client_api_keys=True,
            llm_provider="zhipu",
            llm_api_key="server-key",
            bocha_api_key="server-search-key",
            llm_base_url="https://server.example.com/v1",
            deepseek_base_url="https://server.example.com/deepseek",
            bocha_base_url="https://server.example.com/search",
        )

    def settings(self, llm_key: str, search_key: str):
        return browser_settings({
            "x-verda-deepseek-key": llm_key,
            "x-verda-bocha-key": search_key,
        }, self.base)

    def test_keys_are_required_in_visitor_mode(self):
        with self.assertRaisesRegex(ValueError, "页面填写"):
            browser_settings({}, self.base)
        with self.assertRaisesRegex(ValueError, "有效"):
            self.settings("only-one-key", "")

    def test_visitor_does_not_inherit_server_credentials_or_urls(self):
        visitor = self.settings("visitor-llm", "visitor-search")
        self.assertEqual(visitor.provider_config.name, "deepseek")
        self.assertEqual(visitor.provider_config.api_key, "visitor-llm")
        self.assertEqual(visitor.provider_config.base_url, "https://api.deepseek.com")
        self.assertEqual(visitor.bocha_api_key, "visitor-search")
        self.assertEqual(visitor.bocha_base_url, "https://api.bocha.cn/v1")

    def test_llm_client_is_not_shared_between_visitors(self):
        from app.core import llm

        with use_request_settings(self.settings("visitor-a", "search-a")):
            with llm.use_request_client():
                first = llm._get_client()
                self.assertEqual(first.api_key, "visitor-a")
        with use_request_settings(self.settings("visitor-b", "search-b")):
            with llm.use_request_client():
                second = llm._get_client()
                self.assertEqual(second.api_key, "visitor-b")
            self.assertIsNot(first, second)

    def test_concurrent_async_and_thread_work_remain_isolated(self):
        async def job(llm_key: str, search_key: str):
            with use_request_settings(self.settings(llm_key, search_key)):
                await asyncio.sleep(0)
                direct = get_settings().provider_config.api_key
                threaded = await asyncio.to_thread(lambda: (
                    get_settings().provider_config.api_key,
                    get_settings().bocha_api_key,
                ))
                return direct, threaded

        async def run_jobs():
            return await asyncio.gather(
                job("visitor-a", "search-a"),
                job("visitor-b", "search-b"),
            )

        result = asyncio.run(run_jobs())
        self.assertEqual(result, [
            ("visitor-a", ("visitor-a", "search-a")),
            ("visitor-b", ("visitor-b", "search-b")),
        ])

    def test_http_health_and_stream_with_no_server_keys(self):
        from app.main import app
        from app.core import db

        empty_server = Settings(
            _env_file=None,
            require_client_api_keys=True,
            llm_api_key="",
            deepseek_api_key="",
            zhipu_api_key="",
            bocha_api_key="",
        )

        async def fake_pipeline(_task_id, sub_id=""):
            self.assertEqual(get_settings().provider_config.api_key, "visitor-a")
            self.assertIsNotNone(db.get_task(_task_id))
            self.assertEqual(
                await asyncio.to_thread(lambda: get_settings().bocha_api_key),
                "search-a",
            )
            yield {"type": "done", "data": {"reportId": "report-test"}}

        visitor_a = "a" * 64
        visitor_b = "b" * 64
        headers = {
            "X-Verda-Visitor": visitor_a,
            "X-Verda-Deepseek-Key": "visitor-a",
            "X-Verda-Bocha-Key": "search-a",
        }
        other_headers = {"X-Verda-Visitor": visitor_b}
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        db._init_schema(conn)
        with patch("app.core.config._base_settings", return_value=empty_server), \
                patch("app.core.db._connect", return_value=conn), \
                patch("app.main.run_pipeline", fake_pipeline), \
                TestClient(app) as client:
            self.assertEqual(client.get("/health").json()["status"], "ok")
            self.assertEqual(client.get("/api/llm/config").status_code, 400)
            config = client.get("/api/llm/config", headers=headers).json()
            self.assertTrue(config["client_keys_required"])
            self.assertFalse(config["configured"])
            self.assertEqual(client.post("/api/tasks", json={"query": "test"}, headers=other_headers).status_code, 400)
            created = client.post("/api/tasks", json={"query": "test"}, headers=headers)
            self.assertEqual(created.status_code, 200)
            task_id = created.json()["taskId"]
            self.assertEqual(client.get(f"/api/tasks/{task_id}/stream", headers=other_headers).status_code, 404)
            stream = client.get(f"/api/tasks/{task_id}/stream", headers=headers)
            self.assertEqual(stream.status_code, 200)
            self.assertIn("event: done", stream.text)
            self.assertNotIn("event: error", stream.text)
            with db.use_visitor(None):
                db.save_report({"id": "legacy-report", "title": "Legacy"})
            with db.use_visitor(hashlib.sha256(visitor_a.encode()).hexdigest()):
                db.save_report({"id": "visitor-report", "title": "Private"}, task_id=task_id)
            self.assertEqual([r["id"] for r in client.get("/api/reports", headers=headers).json()], ["visitor-report"])
            self.assertEqual(client.get("/api/reports", headers=other_headers).json(), [])
            self.assertEqual(client.get("/api/dashboard", headers=headers).json()["reports"], 1)
            self.assertEqual(client.get("/api/dashboard", headers=other_headers).json()["reports"], 0)
            self.assertEqual(client.get("/api/reports/visitor-report", headers=other_headers).json()["ok"], False)
            self.assertEqual(client.post("/api/reports/visitor-report/feedback", json={}, headers=other_headers).status_code, 404)
            subscription = client.post("/api/subscriptions", json={"query": "test"}, headers=headers).json()
            self.assertEqual(client.get("/api/subscriptions", headers=other_headers).json(), [])
            self.assertEqual(client.delete(f"/api/subscriptions/{subscription['sub_id']}", headers=other_headers).status_code, 404)
        conn.close()


if __name__ == "__main__":
    unittest.main()
