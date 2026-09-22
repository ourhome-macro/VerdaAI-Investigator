"""Explicit opt-in integration smoke. Uses backend/.env; never prints secrets.

Run from backend: .venv/Scripts/python.exe -X utf8 tests/live_evidence_chain.py --live
Fixed plan/roster and small runtime-only budgets; real search, fetch, analysis,
verification, quality review and writing. Database is isolated in memory.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sqlite3
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import db, llm, orchestrator as orch, trace
from app.core.claim_verifier import verify_claims
from app.core.config import get_settings
from app.core.evidence_context import select_evidence
from app.core.llm import TOKEN_USAGE
from app.core.models import Evidence


def emit(event, **fields):
    print(json.dumps({"event": event, **fields}, ensure_ascii=False), flush=True)


def verifier_probe(model):
    # Synthetic facts deliberately distinguish currencies/periods/comparisons.
    body = ("Alpha Standard costs USD 20 per user per month, billed monthly. "
            "Beta Standard costs USD 15 per user per month, billed monthly. "
            "Alpha supports CSV export. Beta is billed in USD, not EUR.")
    evidence = Evidence("probe", "https://example.org/fixture", "official", "Fixture pricing",
                        body[:280], "2026-09-23", 80, "test", brand="Alpha", full_text=body)
    ctx = select_evidence([evidence], query="Alpha Beta pricing export", focus=["pricing_model"])
    texts = ["Alpha Standard costs USD 20 per user per month, billed monthly.",
             "Alpha Standard is cheaper than Beta Standard on monthly billing.",
             "Alpha Standard costs EUR 20 per user per month.",
             "Alpha supports SAML single sign-on."]
    claims = [{"claim_id": f"probe{i}", "text": text, "evidence_ids": ["probe"],
               "field": "pricing_model", "author": "test"} for i, text in enumerate(texts)]
    verified = verify_claims(claims, ctx, model=model)
    verdicts = [c["verification"]["verdict"] for c in verified]
    passed = verdicts[0] == "supported" and all(v != "supported" for v in verdicts[1:])
    emit("live_verification_probe", passed=passed, verdicts=verdicts)
    if not passed:
        raise AssertionError("Verifier probe did not distinguish grounded and unsupported claims")
    section = orch._write_single_section(
        "pricing", "Alpha Standard 定价", "仅复述 Alpha Standard 已核验的价格，不新增事实", ["Alpha"],
        ["定价"], [evidence], verified, {"pricing": [{"entry_price": 999}]}, model,
        min_paragraphs=1, para_words="40-80", section_max_tokens=1000)
    text = "\n".join(section["paragraphs"])
    written = "20" in text and "[probe]" in text and "999" not in text
    emit("live_writing_probe", passed=written)
    if not written:
        raise AssertionError("Writing did not preserve the verified pricing and citation")


async def pipeline_probe():
    task_id = "live-evidence-chain"
    cfg = {**orch.MODE_CONFIG["quick"], "max_angles": 2, "fetch_per_brand": 3,
           "sentiment_brands": 0, "sections": ["summary", "pricing"], "rework_rounds": 1,
           "min_paragraphs": 1, "para_words": "80-140", "section_max_tokens": 1800,
           "analyze_max_tokens": 6000, "structured_max_tokens": 4000}
    plan = {"brands": ["GitHub Copilot"], "focus": ["定价"],
            "angles": ["定价 site:github.com", "pricing site:docs.github.com"], "category": "AI编程工具"}
    dispatch = {"lead": "L3-001", "members": [{"id": eid, "reason": "bounded live integration"}
                for eid in ("L3-001", "L2-001", "L1-025", "L3-003")]}
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db._init_schema(conn)
    completed = False
    actual_analyze = orch._analyze
    def inspected_analyze(*args, **kwargs):
        result = actual_analyze(*args, **kwargs)
        emit("analysis_result", claims=len(result["claims"]),
             error=result.get("analysis_error"),
             selected=len(result.get("evidence_selection", [])),
             verdicts=[c.get("verification", {}).get("verdict") for c in result["claims"]])
        return result
    try:
        with patch.object(db, "_connect", return_value=conn), \
                patch.dict(orch.MODE_CONFIG, {"quick": cfg}), \
                patch.object(orch, "_analyze", side_effect=inspected_analyze), \
                patch.object(orch, "_plan_research", return_value=plan), \
                patch.object(orch, "_dispatch_experts", return_value=dispatch):
            db.save_task(task_id, "仅根据当前官方来源研究 GitHub Copilot 定价，注明计费口径。", {"_mode": "quick"})
            async for event in orch.run_pipeline(task_id):
                kind, data = event["type"], event["data"]
                if kind == "node_update" and data.get("node"):
                    emit("stage", node=data["node"], status=data["status"])
                elif kind == "error":
                    raise RuntimeError("Research pipeline reported an error")
                elif kind == "done":
                    completed = True
                    report = db.get_report(data["reportId"])
                    verified = [c for c in report["claims"] if c.get("verification", {}).get("verdict") == "supported"]
                    unverified = [c for c in report["claims"] if c not in verified]
                    emit("report_checks", evidence=len(report["evidence"]), supported=len(verified),
                         claims=len(report["claims"]), selected=len(report["evidence_selection"]),
                         quality_status=report["quality_status"])
                    assert all(c["confidence"] == "unverified" and not c["cross_validated"] for c in unverified)
                    assert report["evidence"] and report["evidence_selection"]
                    assert verified, "No live claim received anchored semantic support"
                    assert any("本章节尚无" not in p for s in report["sections"] if s["id"] in ("summary", "pricing")
                               for p in s["paragraphs"]), "No verified chapter written"
                    emit("live_report", evidence_count=len(report["evidence"]),
                         selected_passages=len(report["evidence_selection"]), claims=len(report["claims"]),
                         supported=len(verified), unresolved=len(unverified),
                         rework_rounds=report["audit_review"]["rework_rounds"], quality_status=report["quality_status"],
                         trace_count=len(db.get_traces_by_report(report["id"])),
                         sources=list(dict.fromkeys(e["source_url"] for e in report["evidence"]))[:6])
            assert completed, "Pipeline did not persist a report"
    finally:
        trace.cleanup(task_id)
        trace.clear_context()
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Explicitly allow real paid API calls")
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args()
    if not args.live:
        parser.error("Pass --live to use .env credentials")
    settings = get_settings()
    if not settings.llm_configured or not settings.bocha_api_key:
        emit("configuration_missing", llm_configured=settings.llm_configured, search_configured=bool(settings.bocha_api_key))
        return 2
    # Bound per-call timeout/retries without modifying the user's .env or models.
    settings = settings.model_copy(update={"llm_timeout": 90.0, "llm_max_retries": 0})
    started, tokens_before = time.monotonic(), TOKEN_USAGE["total"]
    try:
        provider = settings.provider_config
        # This standalone process does not depend on the optional visitor/BYOK layer.
        with llm.OpenAI(api_key=provider.api_key, base_url=provider.base_url,
                        timeout=settings.llm_timeout, max_retries=settings.llm_max_retries) as client, \
                patch.object(llm, "_client", client), patch.object(llm, "get_settings", return_value=settings):
            emit("start", provider=settings.provider_config.name,
                 core_model=settings.provider_config.core_model, verifier_model=settings.provider_config.aux_model)
            verifier_probe(settings.provider_config.aux_model)
            if not args.probe_only:
                asyncio.run(pipeline_probe())
        emit("passed", elapsed_seconds=round(time.monotonic() - started, 1),
             tokens=TOKEN_USAGE["total"] - tokens_before)
        return 0
    except Exception as exc:
        # Provider error strings may contain credentials; never echo them.
        emit("failed", error_type=type(exc).__name__, elapsed_seconds=round(time.monotonic() - started, 1))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
