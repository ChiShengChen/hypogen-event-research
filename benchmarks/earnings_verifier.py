"""Validate paired replay of one source selection and compare it with direct Astra."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import re
import sys
from time import perf_counter

from research_app import full_revision, revision_bridge
from research_app.adapters import AdapterError, Codex
from research_app.schema import MetricKey

from . import earnings_full_revision as full
from . import earnings_raw_revision as raw
from . import earnings_revision as prior
from .earnings_horizon import freeze_json
from .public_pilot import EFFORT, MODEL, write_json


OUT = Path("output/earnings-verifier")
PREVIOUS = full.ROOT / OUT / "frozen/full_revision_before.py"
PREVIOUS_HASH = "a8f4b675bf800b39c10096f47e49c054de2476b0ec1e027a1afe22a17dde70b6"
EXCLUDED = {"ONDS", "SAIC", "HOLX"}
SPLITS = ("pilot", "holdout")
CALLS = ("extract", "astra")
ARMS = {"current": "現版 Harness", "candidate": "新版 Harness", "astra": "純 Astra"}
TIMEOUT = 240
ERRORS = {"model_location": "模型定位", "verifier_abstention": "驗證器暫緩",
          "calculation": "數值或處置", "citation": "引文不足", "missing": "缺少回覆"}


def manifest_path(split, *, gold=False):
    suffix = "_gold" if gold else ""
    return Path(__file__).with_name(f"earnings_verifier_{split}{suffix}.json")


def previous_verifier():
    if prior.digest(PREVIOUS) != PREVIOUS_HASH:
        raise ValueError("封存現版與上一輪執行雜湊不一致")
    name = "research_app._frozen_full_revision"
    spec = spec_from_file_location(name, PREVIOUS)
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.check_filing_revision


def alternatives(value):
    return [value] if isinstance(value, str) else value


def normalize(value):
    return re.sub(r"(?<=\$)\s+(?=\d)", "", full.normalize(value))


def anchor_matches(group, texts):
    return any(normalize(anchor) in text for anchor in alternatives(group) for text in texts)


def load_inputs():
    cases, gold, inputs = [], {}, {}
    issuers = set()
    preceding = set(prior.load(full.OUT / "inputs.json")) if (full.OUT / "inputs.json").exists() else set()
    for split in SPLITS:
        rows = prior.load(manifest_path(split))
        targets = prior.load(manifest_path(split, gold=True))
        if (split == "pilot" and len(rows) != 4) or (split == "holdout" and len(rows) < 4):
            raise ValueError(f"{split} 案例數不符")
        tickers = {row["ticker"].upper() for row in rows}
        if len(rows) != len(tickers) or tickers & (issuers | EXCLUDED):
            raise ValueError("案例發行人重複或包含已指定回歸案例")
        if set(targets) != {row["id"] for row in rows} or set(targets) & (gold.keys() | preceding):
            raise ValueError(f"{split} 案例 ID 與裁定檔不符，或已用於前一輪")
        for row in rows:
            if row["split"] != split or not re.fullmatch(r"[a-zA-Z0-9_-]+", row["id"]):
                raise ValueError(f"案例 ID 或分組不符 {row['id']}")
            data = full.archive(row)
            expected = targets[row["id"]]
            ids = set(expected["source_ids"])
            texts = [normalize(block["text"]) for item in data["documents"] if item["id"] in ids
                     for block in item["blocks"]]
            groups = expected["required_text"]
            scoring_groups = [group for group in [*groups, expected.get("amount_text"),
                                                   expected.get("selected_cell_text")] if group is not None]
            for group in scoring_groups:
                options = alternatives(group)
                if not options or not all(isinstance(anchor, str) and full.normalize(anchor)
                                          and anchor_matches(anchor, texts) for anchor in options):
                    raise ValueError(f"封存引文選項無法在公告定位 {row['id']} {group}")
            full.validate_gold(row, {**expected, "required_text": [alternatives(group)[0] for group in groups]}, data)
            inputs[row["id"]] = data
        issuers.update(tickers)
        cases.extend(rows)
        gold.update(targets)
    return cases, gold, inputs


def seal(out, cases, inputs, *, continuation=False):
    out.mkdir(parents=True, exist_ok=True)
    protocol = {
        "hypothesis": "Separating new guidance from comparison clauses and following table header lineage "
                      "reduces rejected valid source selections without adding unsupported adjustments.",
        "unit": "One complete point-in-time archived issuer release case and fixed pre-event estimate.",
        "model": MODEL, "effort": EFFORT, "timeout_seconds": TIMEOUT, "tool_search_budget": 0,
        "actual_calls_per_case": 2,
        "calls_per_workflow": "One shared extraction replayed unchanged through both verifiers; one direct call.",
        "token_limit": "Shared model context cap, no separate Codex CLI token cap; actual usage recorded.",
        "primary": "Exact disposition, interval endpoints, signed delta, and issuer-source anchors.",
        "citation_rule": "Every cited ID is visible. All required source documents are cited. Every frozen group "
                         "has at least one exact normalized text alternative in the cited blocks.",
        "unsupported_adjustment": "A nonzero adjustment from a response that fails any primary condition.",
        "pilot_gate": "At least 3/4 exact, at least one exact eligible, zero unsupported candidate adjustments, "
                      "and both model calls returned in every case.",
        "holdout_gate": "At least 75% exact, at least one exact eligible, zero unsupported candidate adjustments, "
                        "and both model calls returned in every case.",
        "lead_gate": "Pass holdout and produce strictly more exact results than both comparisons.",
        "stop": "Run the pilot once. If it fails, stop with the pilot artifacts. Otherwise run the disjoint holdout "
                "once and then stop. A failed model call consumes the budget.",
        "exclusions": sorted(EXCLUDED),
        "failure_hierarchy": "Missing call; wrong/unavailable active model location; false refusal of verified "
                             "location; incorrect bounds/delta/disposition; inadequate citations.",
        "manifest_sha256": {split: prior.digest(manifest_path(split)) for split in SPLITS},
        "gold_sha256": {split: prior.digest(manifest_path(split, gold=True)) for split in SPLITS},
        "code_sha256": {Path(path).name: prior.digest(Path(path)) for path in
                        (__file__, full.__file__, full_revision.__file__, revision_bridge.__file__, PREVIOUS)},
        "archive_sha256": {document["id"]: document["sha256"] for case in cases for document in case["documents"]},
        "cases": {split: [case["id"] for case in cases if case["split"] == split] for split in SPLITS},
        "common_prompt": full.POLICY,
        "prompts": {"extract": full_revision.FILING_SELECTION_PROMPT, "astra": full.DIRECT},
    }
    freeze_json(out / "inputs.json", inputs)
    protocol["model_input_sha256"] = prior.digest(out / "inputs.json")
    if continuation:
        original = prior.load(out / "protocol.json")
        initial_runner = out / "frozen/earnings_verifier_initial.py"
        initial_hash = prior.digest(initial_runner)
        if original["code_sha256"][Path(__file__).name] != initial_hash:
            raise ValueError("原先封存執行器的雜湊無法確認")
        initial_codes = {**protocol["code_sha256"], Path(__file__).name: initial_hash}
        if original != {**protocol, "code_sha256": initial_codes}:
            raise ValueError("續跑只接受執行器修正，其他預註冊輸入須完全相同")
        pilot = original["cases"]["pilot"]
        if any(not (out / "calls" / f"{case_id}-{call}.json").is_file() for case_id in pilot for call in CALLS):
            raise ValueError("續跑須保留全部先導模型回傳")
        freeze_json(out / "protocol.continuation.json", protocol)
        return protocol
    freeze_json(out / "protocol.json", protocol)
    text = [
        "# 完整公告驗證器預註冊", "",
        "假說是分清同句的新舊指引，並沿正式表頭核對欄位後，能減少誤拒已定位的正確指引，且不增加誤調。", "",
        f"每案兩次 {MODEL} {EFFORT} 呼叫。兩版驗證器重播同一次模型擷取。純 Astra 另用一次相同模型直接回答。"
        f"兩次呼叫的公告、現估和時間截點相同，搜尋與工具關閉，單次上限 {TIMEOUT} 秒。", "",
        "主指標是處置、上下限、帶符號差額與引文全對。每組引文可用其中一個預先封存的等價原文。"
        "任何未全對的非零差額都算誤調。定位、驗證器暫緩、數值與引文缺失分開記錄。", "",
        "- 先導 4 案至少 3 案全對才執行保留集。",
        f"- 保留集 {len(protocol['cases']['holdout'])} 案，發行人與先導不重疊，至少 75% 全對。",
        "- 兩階段皆要求新版零誤調、至少一筆應調整案例全對，且所有模型回覆齊全。",
        "- 保留集過門檻且新版全對數同時高於現版及純 Astra，才記為領先。失敗回傳耗用模型額度。",
        "- Ondas、SAIC 和 Hologic 僅用作回歸。每階段執行一次，先導未過即停止。", "",
        "[封存規則及雜湊](protocol.json) · [模型完整輸入](inputs.json)",
    ]
    (out / "protocol.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    return protocol


def invoke(case, data, call, out):
    path = out / "calls" / f"{case['id']}-{call}.json"
    if path.exists():
        return prior.load(path)
    schema, prompt = ((full_revision.FilingExtraction, full_revision.FILING_SELECTION_PROMPT) if call == "extract"
                      else (raw.Decision, full.DIRECT))
    events = []
    started = perf_counter()
    try:
        response = Codex(audit=events.extend, reasoning_effort=EFFORT, call_timeout=TIMEOUT)._generate(
            schema, f"{full.POLICY} {prompt}", data,
        )
        record = {"output": response.model_dump(mode="json")}
    except AdapterError as exc:
        record = {"error": str(exc)}
    prohibited = {"web_search", "command_execution", "mcp_tool_call", "dynamic_tool_call", "collab_tool_call"}
    tools = [event["item"]["type"] for event in events
             if event.get("type") == "item.completed" and event["item"]["type"] in prohibited]
    if tools:
        record = {"error": "模型使用預算外的工具。", "tool_types": tools, "rejected_output": record.get("output")}
    usage = [event["usage"] for event in events if event.get("type") == "turn.completed"]
    record["elapsed_seconds"] = round(perf_counter() - started, 2)
    record["events"] = events
    record["usage"] = {key: sum(turn.get(key, 0) for turn in usage) for key in
                       ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")}
    write_json(path, record)
    return record


def verify(check, data, extracted):
    if extracted is None:
        return None
    if extracted["selection"] is None:
        return full.blocked(extracted["evidence_ids"], "原文中未找到符合條件的數值與財季。")
    result = check(key=MetricKey.model_validate(data["target"]), incumbent=Decimal(data["incumbent"]["amount"]),
                   event_at=prior.instant(data["event_at"]), as_of=prior.instant(data["as_of"]),
                   documents=data["documents"], selection=extracted["selection"], fiscal_label=data["fiscal_label"])
    refs = result.get("evidence_ids") or extracted["evidence_ids"]
    if result["status"] == "blocked":
        return {**full.blocked(refs, result["reason"]), "audit": result}
    return {**result, "evidence_ids": refs}


def assess(decision, expected, refs):
    measures = ("exact", "delta_exact", "range_exact", "disposition_exact", "citations", "unsafe", "eligible_exact", "missing")
    if decision is None:
        return {**dict.fromkeys(measures, False), "missing": True}
    delta = decision["remaining_delta"]
    effective = Decimal(delta) if delta is not None else Decimal(0)
    delta_ok = effective == Decimal(expected["delta"])
    bounds_ok = raw.pair_amounts(decision["new_low"], decision["new_high"]) == raw.pair_amounts(
        expected["new_low"], expected["new_high"],
    )
    disposition_ok = decision["status"] == expected["disposition"] and (
        (delta is None) == (decision["status"] == "blocked")
    )
    citations = set(decision["evidence_ids"])
    supplied = [refs[value] for value in sorted(citations & refs.keys())]
    sources = {block["document_id"] for block in supplied}
    texts = [normalize(block["text"]) for block in supplied if block["document_id"] in expected["source_ids"]]
    citations_ok = (bool(citations) and citations <= refs.keys() and set(expected["source_ids"]) <= sources
                    and all(anchor_matches(group, texts) for group in expected["required_text"]))
    exact = disposition_ok and delta_ok and bounds_ok and citations_ok
    return {"exact": exact, "delta_exact": delta_ok, "range_exact": bounds_ok, "disposition_exact": disposition_ok,
            "citations": citations_ok, "unsafe": bool(effective) and not exact,
            "eligible_exact": exact and decision["status"] == "eligible", "missing": False}


def correct_location(extracted, expected, refs):
    selection = extracted["selection"] if extracted else None
    if expected["disposition"] == "blocked":
        return selection is None
    if not selection:
        return False
    amount = refs.get(selection["amount_ref"])
    context = refs.get(selection["context_ref"])
    if not amount or not context or amount["document_id"] != context["document_id"]:
        return False
    if amount["document_id"] not in expected["source_ids"]:
        return False
    if "amount_text" in expected and not anchor_matches(expected["amount_text"], [normalize(amount["text"])]):
        return False
    if "selected_cell_text" in expected and amount["kind"] == "row":
        column, cells = selection["column"], amount["cells"]
        if column is None or column + 1 >= len(cells):
            return False
        return anchor_matches(expected["selected_cell_text"], [normalize(cells[column + 1])])
    if "amount_text" in expected:
        return True
    selected = [normalize(refs[ref]["text"]) for ref in selection.values() if isinstance(ref, str) and ref in refs]
    return all(anchor_matches(group, selected) for group in expected["required_text"])


def explain(arm, decision, measures, expected, located):
    if measures["exact"]:
        return None
    if measures["missing"]:
        return "missing"
    if arm != "astra" and expected["disposition"] != "blocked":
        if not located:
            return "model_location"
        if decision["status"] == "blocked":
            return "verifier_abstention"
    if arm != "astra" and expected["disposition"] == "blocked" and not located and decision["status"] != "blocked":
        return "model_location"
    if not all(measures[rule] for rule in ("delta_exact", "range_exact", "disposition_exact")):
        return "calculation"
    return "citation"


def score(case, data, expected, calls, old):
    extracted = calls["extract"].get("output")
    decisions = {"current": verify(old, data, extracted),
                 "candidate": verify(full_revision.check_filing_revision, data, extracted),
                 "astra": calls["astra"].get("output")}
    refs = full.source_map(data)
    cited = {ref for decision in decisions.values() if decision for ref in decision["evidence_ids"]}
    scores = {arm: assess(decision, expected, refs) for arm, decision in decisions.items()}
    located = correct_location(extracted, expected, refs)
    return {key: case[key] for key in ("id", "split", "ticker", "issuer")} | {
        "target": data["target"], "event_at": data["event_at"], "as_of": data["as_of"],
        "baseline": case["baseline"], "expected": expected, "decisions": decisions, "scores": scores,
        "shared_location_matches_gold": located,
        "failures": {arm: explain(arm, decisions[arm], scores[arm], expected, located) for arm in ARMS},
        "citations": {ref: refs[ref] for ref in sorted(cited & refs.keys())},
        "calls": {call: {key: value for key, value in record.items() if key != "events"}
                  for call, record in calls.items()},
    }


def run_split(cases, inputs, gold, old, out, workers):
    for directory in ("calls", "cases"):
        (out / directory).mkdir(exist_ok=True)
    rows, calls = {}, {case["id"]: {} for case in cases}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(invoke, case, inputs[case["id"]], call, out): (case, call)
                   for case in cases for call in CALLS}
        for future in as_completed(futures):
            case, call = futures[future]
            case_id = case["id"]
            calls[case_id][call] = future.result()
            if len(calls[case_id]) == len(CALLS):
                row = score(case, inputs[case_id], gold[case_id], calls[case_id], old)
                rows[case_id] = row
                write_json(out / "cases" / f"{case_id}.json", row)
                print(f"{case['split']} {case_id} scored", flush=True)
    return [rows[case["id"]] for case in cases]


def aggregate(rows):
    counts = {arm: {key: sum(row["scores"][arm][key] for row in rows)
                    for key in rows[0]["scores"][arm]} for arm in ARMS}
    usage = {call: {key: sum(row["calls"][call]["usage"][key] for row in rows)
                    for key in rows[0]["calls"][call]["usage"]} for call in CALLS}
    for call in CALLS:
        usage[call]["elapsed_seconds"] = round(sum(row["calls"][call]["elapsed_seconds"] for row in rows), 2)
    failures = {arm: dict(Counter(row["failures"][arm] for row in rows if row["failures"][arm])) for arm in ARMS}
    new, old, astra = (counts[arm] for arm in ("candidate", "current", "astra"))
    gate = (new["exact"] * 4 >= len(rows) * 3 and new["eligible_exact"] > 0 and not new["unsafe"]
            and not any(metrics["missing"] for metrics in counts.values()))
    return {"n": len(rows), "scores": counts, "usage": usage, "failures": failures, "gate": gate,
            "paired_exact_gain": new["exact"] - old["exact"],
            "lead_over_both": gate and new["exact"] > max(old["exact"], astra["exact"])}


def scorecard(out, rows):
    flat = []
    for row in rows:
        for arm in ARMS:
            decision = full.reviewed_answer(row["decisions"][arm])
            call_name = "astra" if arm == "astra" else "extract"
            call = row["calls"][call_name]
            flat.append({"case": row["id"], "split": row["split"], "ticker": row["ticker"], "arm": arm,
                         **{key: value for key, value in decision.items() if key != "evidence_ids"},
                         "evidence_ids": " ".join(decision["evidence_ids"]),
                         **{key: int(value) for key, value in row["scores"][arm].items()},
                         "call": call_name, **call["usage"], "seconds": call["elapsed_seconds"],
                         "failure_stage": row["failures"][arm] or "", "call_error": call.get("error", "")})
    full.csv_file(out / "scores.csv", list(flat[0]), flat)


def render(out, rows, summary):
    lines = ["# 完整公告營收驗證器評測", "",
             "現版及新版共用同一份模型定位輸出，純 Astra 另做同一預算的一次回答。"
             "公告全文、封存現估和時間截點相同。Ondas、SAIC 和 Hologic 留作回歸。", "",
             "[預註冊及停止條件](protocol.md) · [完整公告及封存現估](inputs.json) · "
             "[評分表](scores.csv) · [數字摘要](summary.json) · [匿名覆核包](analyst-review.zip)", ""]
    for split, heading in (("pilot", "先導"), ("holdout", "保留集")):
        lines.extend([f"## {heading}", ""])
        result = summary["splits"].get(split)
        if result is None:
            lines.extend(["依預註冊停止規則，未執行保留集。", ""])
            continue
        lines.extend([f"共 {result['n']} 案。驗收門檻 **{'通過' if result['gate'] else '未通過'}**。"
                      f"共用定位後，新版較現版多全對 {result['paired_exact_gain']:+d} 案。", ""])
        if split == "holdout":
            lines.extend([f"同時領先現版與純 Astra 的門檻 **{'通過' if result['lead_over_both'] else '未通過'}**。", ""])
        lines.extend(["| 組別 | 全對 | 金額 | 區間 | 引文 | 誤調 |", "|---|---:|---:|---:|---:|---:|"])
        for arm, label in ARMS.items():
            measures = result["scores"][arm]
            lines.append(f"| {label} | " + " | ".join(str(measures[key]) for key in
                         ("exact", "delta_exact", "range_exact", "citations", "unsafe")) + " |")
        lines.extend(["", "| 實際呼叫 | 輸入詞元 | 快取輸入 | 輸出詞元 | 累計秒數 |", "|---|---:|---:|---:|---:|"])
        for call, label in (("extract", "兩版共用定位"), ("astra", "純 Astra")):
            use = result["usage"][call]
            lines.append(f"| {label} | {use['input_tokens']:,} | {use['cached_input_tokens']:,} | "
                         f"{use['output_tokens']:,} | {use['elapsed_seconds']:.2f} |")
        lines.extend(["", "| 案例 | 現版 | 新版 | 純 Astra |", "|---|---|---|---|"])
        group = [row for row in rows if row["split"] == split]
        for row in group:
            cells = [raw.show_decision(row["decisions"][arm]) for arm in ARMS]
            lines.append(f"| [{row['ticker']}](cases/{row['id']}.json) | " + " | ".join(cells) + " |")
        lines.append("")
        for row in group:
            case_id = row["id"]
            detail = "、".join(f"{ARMS[arm]} {ERRORS[error]}" for arm, error in row["failures"].items() if error)
            lines.append(f"- **{row['ticker']}** {detail or '三組均全對'}。"
                         f"[公告正文](filing-view/{case_id}.html) · [共用回傳](calls/{case_id}-extract.json) · "
                         f"[純 Astra 回傳](calls/{case_id}-astra.json)")
        lines.append("")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--run-model", action="store_true")
    parser.add_argument("--continuation", action="store_true")
    args = parser.parse_args()
    old = previous_verifier()
    cases, gold, inputs = load_inputs()
    protocol = seal(args.out, cases, inputs, continuation=args.continuation)
    protocol_path = "protocol.continuation.json" if args.continuation else "protocol.json"
    print(f"Frozen protocol: {args.out / protocol_path}", flush=True)
    if not args.run_model:
        return
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    summary = {"model": MODEL, "effort": EFFORT, "splits": {}, "holdout_attempted": False}
    rows = []
    for split in SPLITS:
        group = run_split([case for case in cases if case["split"] == split], inputs, gold, old, args.out, args.workers)
        summary["splits"][split] = result = aggregate(group)
        summary["holdout_attempted"] = split == "holdout"
        rows.extend(group)
        write_json(args.out / "summary.json", summary)
        scorecard(args.out, rows)
        full.delivery_pack(args.out, rows, inputs, protocol)
        render(args.out, rows, summary)
        print(f"{split}: {json.dumps(result, ensure_ascii=False)}", flush=True)
        if not result["gate"]:
            break


if __name__ == "__main__":
    main()
