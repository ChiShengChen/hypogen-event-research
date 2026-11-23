import asyncio
import json
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from research_app.adapters import LinkedFixture
from research_app.hypothesis_tree import TreeDraft
from research_app.mcp_server import create_server
from research_app.store import Store


def call(server, tool, **arguments):
    _, result = asyncio.run(server.call_tool(tool, arguments))
    return result


def test_conversation_writes_into_same_report_and_deduplicates_branch(tmp_path):
    example = json.loads(Path("research_app/examples/asml-earnings.json").read_text())
    sample = json.loads(Path("docs/guidance-table/scenario-draft.json").read_text())["stance_cases"][0]["cases"][0]

    class Recorder(LinkedFixture):
        calls = 0

        def branch_hypotheses(self, context):
            self.calls += 1
            attachment = next(row for row in context["evidence"] if row["kind"] == "file")
            assert context["conditional_inputs"][0]["kind"] == "opinion"
            return TreeDraft(hypotheses=[sample | {"stance": "bull",
                                                   "mechanism": f"驗收延後第 {self.calls} 種機制",
                                                   "evidence_ids": [attachment["id"]]}], gaps=[])

    db = Store(tmp_path / "study.sqlite3")
    adapter = Recorder()
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "notes.txt").write_text("分批驗收摘要", encoding="utf-8")
    server = create_server(db, adapter, inbox=inbox)
    created = call(server, "report_create", event=example, request_id=uuid4().hex)
    report_id = created["report_id"]
    assert call(server, "report_find", query="asml")["reports"][0]["report_id"] == report_id
    attachment = call(server, "attachment_add", filename="notes.txt")
    with pytest.raises(ToolError, match="單一檔名"):
        call(server, "attachment_add", filename="../notes.txt")
    payload = {"report_id": report_id, "revision": 1, "parent_id": "root", "mode": "custom", "stance": "驗收節奏",
               "question": "延後驗收", "request_id": uuid4().hex, "inputs": [
                   {"kind": "opinion", "text": "客戶要求分批驗收"},
                   {"kind": "file", "attachment_id": attachment["attachment_id"], "available_on": "2024-10-14"},
               ]}
    reply = call(server, "tree_branch", **payload)
    assert reply["as_of"] == created["report"]["as_of"]
    child, = reply["hypothesis_node_ids"]
    assert reply["citations"][0]["title"] == "notes.txt"
    assert call(server, "tree_branch", **payload) == reply and adapter.calls == 1
    with pytest.raises(ToolError, match="不同輸入"):
        call(server, "tree_branch", **(payload | {"question": "另一問題"}))
    next_reply = call(server, "tree_branch", report_id=report_id, revision=1, parent_id=child,
                      mode="followup", question="怎麼反證？", request_id=uuid4().hex)
    assert next_reply["citations"] == reply["citations"] and adapter.calls == 2
    assert next_reply["hypothesis_node_ids"][0] in {node["id"] for node in db.hypothesis_tree(report_id, 1)["nodes"]}


def test_historical_forecast_uses_identifier_returned_by_mcp(tmp_path):
    example = json.loads(Path("research_app/examples/asml-earnings.json").read_text())
    server = create_server(Store(tmp_path / "earnings.sqlite3"), LinkedFixture())
    created = call(server, "report_create", event=example, request_id=uuid4().hex)
    report = {"report_id": created["report_id"], "revision": 1}
    key = {"metric": "revenue", "period_end": "2024-12-31", "duration": "quarter",
           "scope": "consolidated", "basis": "US_GAAP", "currency": "EUR"}
    registration = call(server, "forecast_register", **report, forecast={
        "key": key, "low": "9000000000", "high": "9500000000", "deadline": "2025-01-31T23:59:59Z",
        "resolution_source": "ASML 2024 Q4", "purpose": "historical_replay", "probability": "0.75",
        "evidence_ids": ["asml-q3:guidance"],
    })
    actual = call(server, "forecast_resolve", **report, forecast_id=registration["id"], outcome={
        "status": "reported", "document": next(d for d in example["documents"] if d["id"] == "asml-q4"),
        "paragraph_id": "actual", "key": key, "value": "9263000000", "note": "原始公布",
    })
    assert actual["outcome"] == "hit"


def test_benchmark_tool_keeps_the_sealed_budget_on_rate_limit(tmp_path, monkeypatch):
    cli = tmp_path / "codex"
    cli.write_text("#!/bin/sh\n"
                   "echo 'retrying sampling request (1/5 in 901s)... 429 Too Many Requests' >&2\n"
                   "exit 1\n")
    cli.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    server = create_server(Store(tmp_path / "benchmark.sqlite3"), jobs=tmp_path / "jobs")
    key = uuid4().hex
    assert call(server, "benchmark_start", request_id=key)["job_id"] == key
    deadline = monotonic() + 15
    while monotonic() < deadline:
        result = call(server, "benchmark_status", job_id=key)
        if result["status"] not in {"starting", "running", "publishing"}:
            break
        sleep(0.05)
    assert result["status"] == "below_gate"
    assert result["started_calls"] == 1 and result["cooldown_blocked"]
    assert result["protocol"]["max_calls"] == 16
    assert result["summary"]["complete_pairs_with_recovery"] == 0
    assert call(server, "benchmark_start", request_id=key, resume=True) == result
