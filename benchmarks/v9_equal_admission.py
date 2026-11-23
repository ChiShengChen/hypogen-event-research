"""A bounded operational probe before the V9 benchmark starts."""

from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import re
from time import monotonic

from benchmarks import earnings_execution as journal
from benchmarks.hypothesis_cases import archived, freeze
from benchmarks.hypothesis_pilot import read
from research_app.schema import Event


PROBES = ("P-01", "P-02")
FOLDER = "service-probe"
SOURCE = ("https://newsroom.ibm.com/2025-02-27-ibm-completes-acquisition-of-hashicorp"
          "%2C-creates-comprehensive%2C-end-to-end-hybrid-cloud-platform")
RATE_LIMIT = re.compile(r'\b429\b|usage limit|rate limit|too many requests', re.IGNORECASE)
MODEL_CAPACITY = re.compile(r'model.{0,55}(?:at capacity|overloaded|capacity (?:error|exceeded))|'
                            r'(?:insufficient|no available) (?:model )?capacity|model_capacity',
                            re.IGNORECASE)
RETRY = re.compile(r'(?:retrying sampling request .*?\bin |\bretry(?:[-_ ]after| in)[:= ]*)'
                   r'(\d+(?:\.\d+)?)\s*(milliseconds?|ms|seconds?|secs?|s\b)?', re.IGNORECASE)


def availability_reason(message):
    if RATE_LIMIT.search(message):
        return "rate_limit"
    if MODEL_CAPACITY.search(message):
        return "model_capacity"
    return None


def specification(cases, requests, build_v9_request, timeout):
    event = Event.model_validate({
        "event_text": "IBM 公布完成收購 HashiCorp。分析這筆交易如何影響 IBM 的混合雲與自動化軟體營運。",
        "as_of": "2025-02-27T23:59:59Z", "research_target": "IBM", "research_horizon": "2026-06-30",
        "documents": [archived(
            "ibm-hashicorp-close", "2025-02-27", SOURCE,
            closing="IBM 完成收購 HashiCorp 全部流通普通股，每股現金 35 美元，企業價值約 64 億美元。",
            integration="IBM 宣布 Terraform、Vault 及其他 HashiCorp 產品當時已納入 IBM 自動化軟體組合。"
                        "IBM 以 Terraform 與 Red Hat Ansible 的結合為例：前者供應跨雲基礎設施，後者管理其上的應用設定及中介軟體部署。",
            distribution="IBM 把 Red Hat、watsonx、資料安全、IT 自動化與顧問服務列為可能出現綜效的領域。",
        )],
    })
    point_in_time = freeze(event)
    if any(case["input"]["target"] == point_in_time["target"] for case in cases.values()):
        raise ValueError("探針標的須與正式案例互異")
    request = build_v9_request(event, point_in_time)
    size = len(request["prompt"].encode())
    pilot_sizes = [len(requests[key]["v9"]["prompt"].encode())
                   for key, case in cases.items() if case["split"] == "pilot"]
    if not min(pilot_sizes) <= size <= max(pilot_sizes):
        raise ValueError(f"探針提示 {size} bytes 超出 V9 先導範圍 {min(pilot_sizes)}–{max(pilot_sizes)} bytes")
    return {
        "case": {"name": "IBM 完成收購 HashiCorp", "split": "service-probe", "input": point_in_time,
                 "event": event.model_dump(mode="json"),
                 "anchors": {"ibm-hashicorp-close:closing": "representing an enterprise value of $6.4 billion"}},
        "request": request, "prompt_bytes": size, "pilot_v9_prompt_bytes": [min(pilot_sizes), max(pilot_sizes)],
        "policy": {
            "attempt_ids": list(PROBES), "call_timeout_seconds": timeout, "max_wait_seconds": 360,
            "default_wait_seconds": 30,
            "pass": "同一 Astra medium 的單一無工具回合，V9 回覆通過結構及程式驗證。",
            "stop": "最多兩次。僅限 429、模型容量或單次逾時可再探測；公告等待超限即停止。"
                    "已啟動但中斷的探針計入額度；中斷後可完成尚未開始的已排定等待。",
        },
    }


def wait_hint(job):
    diagnostics = []
    for name in ("stderr.log", "events.jsonl"):
        path = job / name
        if path.exists():
            diagnostics.append(path.read_text(encoding="utf-8", errors="replace"))
    hints = [float(amount) / 1000 if unit.lower().startswith(("ms", "millisecond")) else float(amount)
             for amount, unit in RETRY.findall("\n".join(diagnostics))]
    return max(hints, default=None)


def admitted(root, plan, digest):
    probe_root = root / FOLDER
    for key in PROBES:
        record = read(journal.receipt(probe_root, key, "v9"))
        if record.get("status") == "completed":
            if record.get("request_sha256") != digest(plan["request"]):
                raise ValueError("已完成的探針與封存請求不符")
            return record
    return None


def retry_decision(plan, key, record, job):
    policy = plan["policy"]
    hint = wait_hint(job)
    transient = record.get("reason") in {"rate_limit", "model_capacity", "per_call_deadline"}
    delay = math.ceil(hint) if hint is not None else policy["default_wait_seconds"]
    can_retry = key == PROBES[0] and transient and delay <= policy["max_wait_seconds"]
    return {
        "after": key, "reason": record.get("reason"), "reported_retry_wait_seconds": hint,
        "decision": "retry" if can_retry else "stop",
        "decision_reason": ("wait_within_budget" if can_retry else "retry_budget_used" if key == PROBES[-1]
                            else "non_transient" if not transient else "wait_exceeds_cap"),
        "wait_seconds": delay if can_retry else None,
        "retry_at": (datetime.fromisoformat(record["finished_at"]) + timedelta(seconds=delay)).isoformat()
        if can_retry else None,
    }


def probe(root, plan, stop, attempt, queue_job, digest):
    probe_root = root / FOLDER
    if admitted(root, plan, digest):
        return True
    timeout = plan["policy"]["call_timeout_seconds"]
    for key in PROBES:
        if stop.is_set():
            return False
        job = queue_job(probe_root, key, "v9")
        record = attempt(probe_root, job, plan["case"], plan["request"], stop,
                         monotonic() + journal.budget(1, 1, timeout), timeout)
        print(f"probe {key} {record['status']} {record.get('reason', '')}", flush=True)
        if record["status"] == "completed":
            return True
        if record["status"] == "queued":
            return False
        path = probe_root / f"{key}-decision.json"
        decision = read(path)
        if not decision:
            decision = retry_decision(plan, key, record, job)
            journal.atomic(path, decision)
        if decision["decision"] == "stop":
            return False
        retry_at = datetime.fromisoformat(decision["retry_at"])
        remaining = max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        print(f"probe retry in {remaining:.1f}s (sealed maximum {plan['policy']['max_wait_seconds']}s)", flush=True)
        if stop.wait(remaining):
            return False
    return False
