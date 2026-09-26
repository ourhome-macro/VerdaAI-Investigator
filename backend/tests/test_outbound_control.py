"""Admission, retry and matrix scheduling regression tests; no network calls."""
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from openai import APITimeoutError
from app.core import llm, orchestrator, outbound_limit, search
from app.core.config import Settings
from app.core.research_contract import build_contract
from app.core.search_extra import SearchProviderError


class OutboundControlTests(unittest.TestCase):
    def test_token_bucket_paces_requests(self):
        key = outbound_limit.scope("rate-fixture", "https://test.invalid", "unique")
        started = time.monotonic()
        with outbound_limit.permit(key, per_second=5, max_in_flight=2):
            pass
        with outbound_limit.permit(key, per_second=5, max_in_flight=2):
            pass
        self.assertGreaterEqual(time.monotonic() - started, 0.17)

    def test_provider_and_global_caps_across_credentials(self):
        settings = Settings(_env_file=None, outbound_global_max_in_flight=2,
                            outbound_global_requests_per_second=1000)
        active = maximum = 0
        lock = threading.Lock()

        def call(i):
            nonlocal active, maximum
            with outbound_limit.settings_permit(
                    "deepseek", "https://test.invalid", f"key-{i}", settings,
                    per_second=1000, max_in_flight=1, max_wait=2):
                with lock:
                    active += 1
                    maximum = max(maximum, active)
                time.sleep(0.03)
                with lock:
                    active -= 1

        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(call, range(6)))
        self.assertEqual(maximum, 1)  # provider budget is one across all six keys

        with outbound_limit.permit(outbound_limit.scope("llm", "", "a"),
                                   per_second=1000, max_in_flight=1,
                                   provider="llm", provider_max_in_flight=2,
                                   global_max_in_flight=1):
            with self.assertRaises(TimeoutError):
                with outbound_limit.permit(outbound_limit.scope("search", "", "b"),
                                           per_second=1000, max_in_flight=1, max_wait=0.01,
                                           provider="search", provider_max_in_flight=2,
                                           global_max_in_flight=1):
                    pass

        key = outbound_limit.scope("bocha", "https://test.invalid", "unique")
        with outbound_limit.permit(key, per_second=1000, max_in_flight=1,
                                   provider="test-provider", provider_max_in_flight=1):
            with self.assertRaises(TimeoutError):
                with outbound_limit.permit(outbound_limit.scope("bocha", "https://test.invalid", "other"),
                                           per_second=1000, max_in_flight=1, max_wait=0.01,
                                           provider="test-provider", provider_max_in_flight=1):
                    pass

    def test_llm_retries_transient_but_not_permanent(self):
        settings = Settings(_env_file=None, deepseek_api_key="unit-key", llm_attempts=3,
                            llm_retry_base_seconds=0, llm_retry_max_seconds=0)
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))], usage=None)
        transient = RuntimeError("overloaded")
        transient.status_code = 503
        permanent = RuntimeError("invalid credential")
        permanent.status_code = 401
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **kwargs: None)))
        with patch.object(llm, "get_settings", return_value=settings), \
                patch.object(llm, "_get_client", return_value=client), \
                patch.object(llm, "_permit", return_value=nullcontext()), \
                patch.object(llm.time, "sleep") as sleep:
            with patch.object(client.chat.completions, "create", side_effect=[transient, response]) as create:
                self.assertEqual(llm.chat([{"role": "user", "content": "hello"}]), "ok")
                self.assertEqual(create.call_count, 2)
            timeout = APITimeoutError(request=httpx.Request("POST", "https://test.invalid"))
            with patch.object(client.chat.completions, "create", side_effect=[timeout, response]) as create:
                self.assertEqual(llm.chat([{"role": "user", "content": "hello"}]), "ok")
                self.assertEqual(create.call_count, 2)
            with patch.object(client.chat.completions, "create", side_effect=permanent) as create:
                with self.assertRaises(RuntimeError):
                    llm.chat([{"role": "user", "content": "hello"}])
                self.assertEqual(create.call_count, 1)
        self.assertEqual(sleep.call_count, 2)

    def test_retry_after_header_is_used_for_rate_limit(self):
        settings = Settings(_env_file=None, llm_retry_base_seconds=1,
                            llm_retry_max_seconds=20)
        error = RuntimeError("rate limit")
        error.response = httpx.Response(429, headers={"Retry-After": "5"},
                                        request=httpx.Request("POST", "https://test.invalid"))
        self.assertGreaterEqual(llm._retry_delay(error, 0, settings), 5)

    def test_bocha_retries_timeout_and_429(self):
        settings = Settings(_env_file=None, bocha_api_key="unit-key", search_attempts=3,
                            search_retry_base_seconds=0, search_retry_max_seconds=0)
        error = SearchProviderError("bocha", 429, "rate limited")
        with patch.object(search, "get_settings", return_value=settings), \
                patch.object(search, "cached", side_effect=lambda *args: args[-1]()), \
                patch.object(search, "_search_bocha_uncached", side_effect=[error, [{"url": "https://a.example"}]]) as request, \
                patch.object(search.time, "sleep"), \
                patch.object(search.outbound_limit, "cool_down") as cooldown:
            self.assertEqual(len(search.search_bocha("query")), 1)
            self.assertEqual(request.call_count, 2)
            cooldown.assert_called_once()
        with patch.object(search, "get_settings", return_value=settings), \
                patch.object(search, "cached", side_effect=lambda *args: args[-1]()), \
                patch.object(search, "_search_bocha_uncached", side_effect=[httpx.ReadTimeout("read"), []]) as request, \
                patch.object(search.time, "sleep"):
            self.assertEqual(search.search_bocha("query"), [])
            self.assertEqual(request.call_count, 2)

    def test_stream_does_not_replay_after_first_chunk(self):
        settings = Settings(_env_file=None, deepseek_api_key="unit-key", llm_attempts=3,
                            llm_retry_base_seconds=0, llm_retry_max_seconds=0)
        timeout = APITimeoutError(request=httpx.Request("POST", "https://test.invalid"))

        def stream():
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="first"))])
            raise timeout

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=stream)))
        with patch.object(llm, "get_settings", return_value=settings), \
                patch.object(llm, "_get_client", return_value=client), \
                patch.object(llm, "_permit", return_value=nullcontext()), \
                patch.object(client.chat.completions, "create", side_effect=lambda **kwargs: stream()) as create:
            received = []
            with self.assertRaises(APITimeoutError):
                for chunk in llm.chat_stream([{"role": "user", "content": "hello"}]):
                    received.append(chunk)
            self.assertEqual(received, ["first"])
            self.assertEqual(create.call_count, 1)

    def test_five_by_six_analysis_is_batched(self):
        brands = [f"brand-{i}" for i in range(5)]
        focus = [f"dimension-{i}" for i in range(6)]
        contract = build_contract(brands, focus)
        active = maximum = calls = 0
        lock = threading.Lock()

        def analyze(*args, **kwargs):
            nonlocal active, maximum, calls
            with lock:
                active += 1
                calls += 1
                maximum = max(maximum, active)
            time.sleep(0.015)
            with lock:
                active -= 1
            return {"claims": [], "evidence_selection": []}

        with patch.object(orchestrator, "get_settings", return_value=SimpleNamespace(analyze_batch_size=3)), \
                patch.object(orchestrator, "_analyze_brand", side_effect=analyze):
            orchestrator._analyze("query", brands, focus, [], [], contract=contract)
        self.assertEqual(calls, 30)
        self.assertEqual(maximum, 3)


if __name__ == "__main__":
    unittest.main()
