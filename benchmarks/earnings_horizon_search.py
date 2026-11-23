"""Matched-budget, independently searched benchmark for the earnings bridge."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
from time import perf_counter

from research_app.adapters import AdapterError, Codex
from research_app.discovery import collect
from research_app.earnings import complete_plan
from research_app.research import build_context

from .earnings_calibration import score_group
from .earnings_equal import direct_points, project_rows
from .earnings_horizon import HOLDOUT, freeze_json, holdout_cases
from .earnings_horizon_inputs import revenue_history
from .earnings_pilot import read
from .public_pilot import EFFORT, MODEL, web_audit, write_json

SEARCH_CASES = {"AMD-2025": ("amd.com", "sec.gov"), "MU-2025": ("micron.com", "sec.gov"),
                "NVDA-2025": ("nvidia.com", "sec.gov")}
BUDGET = {"search": 2, "open": 2}


def run(case, arm, output):
    case_id = case["id"]
    dest = output / f"{case_id}-{arm}.json"
    if read(dest).get("points"):
        return case_id, arm, "reused"
    began = perf_counter()
    domains = SEARCH_CASES[case_id]
    event = case["event"].model_copy(update={"search_mode": "historical_replay", "search_domains": list(domains)})
    raw = []
    adapter = Codex(reasoning_effort=EFFORT, audit=raw.extend, call_timeout=150)
    try:
        documents, log = collect(
            event, adapter,
            question="以截止時點找出可支持第二個預測季營收的具體公開驅動、分部訊號或管理層展望。"
                     "只取較原始資料多出的正式揭露。最多兩次搜尋與兩次開頁。",
            parent_evidence=case["context"]["evidence"],
        )
        audit = web_audit(raw, domains)
        audit["budget_exceeded"] = any(audit["actions"][key] > BUDGET[key] for key in BUDGET)
        enriched = event.model_copy(update={"documents": [*event.documents, *documents]})
        context = build_context(enriched)
        if arm == "astra":
            points = direct_points(enriched, context, adapter)
        else:
            points = project_rows(complete_plan(enriched.earnings_plan, enriched.as_of, context, adapter))
        write_json(dest, {"points": points, "audit": audit, "new_sources": log["rounds"][0]["accepted"],
                          "searched_documents": [row.model_dump(mode="json") for row in documents],
                          "seconds": round(perf_counter() - began, 2)})
        message = "over_budget" if audit["budget_exceeded"] else "ok"
    except (ValueError, AdapterError) as exc:
        write_json(dest, {"error": str(exc), "seconds": round(perf_counter() - began, 2)})
        message = str(exc)
    return case_id, arm, message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sec-dir", type=Path, default=Path("output/earnings-benchmark/sec"))
    parser.add_argument("--benchmark", type=Path, default=Path("output/earnings-horizon"))
    args = parser.parse_args()
    protocol = read(args.benchmark / "protocol.json")
    method = protocol["method"]
    output = args.benchmark / "search"
    output.mkdir(exist_ok=True)
    freeze_json(output / "protocol.json", {"cases": SEARCH_CASES, "budget": BUDGET, "method": method,
                                          "as_of_policy": "filing_date_utc_day_end", "model": MODEL, "effort": EFFORT})
    history = revenue_history(args.sec_dir, HOLDOUT)
    cases = [case for case in holdout_cases(args.sec_dir, history, method) if case["id"] in SEARCH_CASES]
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    arms = ("astra", "harness")
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(run, case, arm, output) for case in cases for arm in arms]
        for job in as_completed(jobs):
            print(*job.result(), flush=True)
    complete, in_budget, detail = {}, {}, {}
    for case in cases:
        case_id = case["id"]
        rows = {arm: read(output / f"{case_id}-{arm}.json") for arm in arms}
        detail[case_id] = {arm: {k: row.get(k) for k in ("audit", "new_sources", "seconds", "error")}
                           for arm, row in rows.items()}
        if all(row.get("points") for row in rows.values()):
            complete[case_id] = {arm: row["points"] for arm, row in rows.items()}
            if not any(row["audit"]["budget_exceeded"] for row in rows.values()):
                in_budget[case_id] = complete[case_id]
    far = lambda case: [max(case["actual"])]
    write_json(output / "summary.json", {"planned": len(cases), "paired": len(complete), "in_budget": len(in_budget),
                                         "t2_mae_in_budget": score_group(cases, in_budget, arms, far),
                                         "t2_mae_all": score_group(cases, complete, arms, far), "detail": detail})


if __name__ == "__main__":
    main()
