"""Benchmark scoped units on the same archived announcement and extraction."""

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import re
import sys
from time import perf_counter
from zipfile import ZIP_DEFLATED, ZipFile

from research_app import adapters, full_revision, revision_bridge, schema
from research_app.adapters import AdapterError, Codex

from . import earnings_full_revision as full
from . import earnings_raw_revision as raw
from . import earnings_revision as prior
from . import earnings_verifier as match
from .earnings_horizon import freeze_json
from .public_pilot import EFFORT, MODEL, write_json


OUT = Path("output/earnings-units")
PREVIOUS = full.ROOT / OUT / "frozen/full_revision_before.py"
PREVIOUS_HASH = "543343b3658ba2b5f7f7bc09731dc452c4fd06280f44dd8586d35134ea2a0367"
EXCLUDED = {"ONDS", "SAIC", "HOLX", "PRGS"}
SPLITS, CALLS, ARMS, TIMEOUT = match.SPLITS, match.CALLS, match.ARMS, match.TIMEOUT
ERRORS = {**match.ERRORS, "units": "金額單位"}
POLICY = (full.POLICY + " Apply only the currency and magnitude that govern the selected revenue cell. "
          "For table values, account for any applicable common label, spanning heading or table caption. "
          "Cite the unit text with the amount, and abstain if the unit is absent, incompatible, or ambiguous.")


def manifest_path(split, *, gold=False):
    suffix = "_gold" if gold else ""
    return Path(__file__).with_name(f"earnings_units_{split}{suffix}.json")


def previous_verifier():
    if prior.digest(PREVIOUS) != PREVIOUS_HASH:
        raise ValueError("對照版本與上一輪封存雜湊不一致")
    module_name = "research_app._units_previous_full_revision"
    spec = spec_from_file_location(module_name, PREVIOUS)
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.check_filing_revision


def load_inputs():
    cases, gold, inputs = [], {}, {}
    issuers = set()
    archived_ids, archived_documents = set(), set()
    for previous_out in (full.OUT, match.OUT):
        frozen = previous_out / "inputs.json"
        if frozen.exists():
            archived = prior.load(frozen)
            archived_ids.update(archived)
            archived_documents.update(doc["source_url"] for case in archived.values() for doc in case["documents"])
    archive_hashes = set()
    for split in SPLITS:
        rows = prior.load(manifest_path(split))
        targets = prior.load(manifest_path(split, gold=True))
        if len(rows) != 4:
            raise ValueError(f"{split} 須封存四案")
        tickers = {row["ticker"].upper() for row in rows}
        if len(rows) != len(tickers) or tickers & (issuers | EXCLUDED):
            raise ValueError("發行人重複或屬回歸案例")
        if set(targets) != {row["id"] for row in rows} or set(targets) & (gold.keys() | archived_ids):
            raise ValueError(f"{split} 案例 ID 與裁定不符，或已執行過")
        for row in rows:
            if row["split"] != split or not re.fullmatch(r"[a-zA-Z0-9_-]+", row["id"]):
                raise ValueError(f"案例 ID 或分組不符 {row['id']}")
            for document in row["documents"]:
                if document["source_url"] in archived_documents or document["sha256"] in archive_hashes:
                    raise ValueError(f"公告曾參與評測 {document['id']}")
                archived_documents.add(document["source_url"])
                archive_hashes.add(document["sha256"])
            data = full.archive(row)
            expected = targets[row["id"]]
            texts = [match.normalize(block["text"]) for item in data["documents"]
                     if item["id"] in expected["source_ids"] for block in item["blocks"]]
            groups = expected["required_text"]
            for group in [*groups, *(expected[key] for key in ("amount_text", "unit_text", "selected_cell_text")
                                     if expected.get(key) is not None)]:
                options = match.alternatives(group)
                if not options or not all(isinstance(anchor, str) and full.normalize(anchor)
                                          and match.anchor_matches(anchor, texts) for anchor in options):
                    raise ValueError(f"封存引文選項無法在公告定位 {row['id']} {group}")
            full.validate_gold(row, {**expected, "required_text": [match.alternatives(group)[0] for group in groups]}, data)
            inputs[row["id"]] = data
        issuers.update(tickers)
        cases.extend(rows)
        gold.update(targets)
    return cases, gold, inputs


def prompts():
    return {"extract": full_revision.FILING_SELECTION_PROMPT, "astra": full.DIRECT}


def seal(out, cases, inputs):
    out.mkdir(parents=True, exist_ok=True)
    sources = [Path(path) for path in (__file__, full.__file__, raw.__file__, prior.__file__, match.__file__,
                                      full_revision.__file__, revision_bridge.__file__, adapters.__file__,
                                      schema.__file__, PREVIOUS)]
    sources.append(Path(full_revision.__file__).with_name("financial_units.py"))
    protocol = {
        "hypothesis": "Resolving currency and scale within the selected table cell's scope will prevent scaling "
                      "errors and recover valid decisions without permitting unproven units.",
        "unit": "One complete point-in-time archived issuer release and fixed pre-event estimate.",
        "model": MODEL, "effort": EFFORT, "timeout_seconds": TIMEOUT, "tool_search_budget": 0,
        "actual_calls_per_case": 2,
        "calls_per_workflow": "One shared extraction replayed unchanged through both verifiers and one direct call.",
        "token_limit": "Shared model context cap, no separate Codex CLI token cap. Actual usage recorded.",
        "primary": "Exact disposition, interval endpoints, signed delta, and issuer-source anchors.",
        "citation_rule": "Every cited ID must be visible. Every required source document must be cited. Cited blocks "
                         "must contain an exact normalized alternative in each group, including units where specified.",
        "unsafe": "A nonzero adjustment from a response that fails any primary condition.",
        "pilot_gate": "At least 3/4 exact, at least one exact eligible, zero unsafe candidate adjustments, no missing.",
        "holdout_gate": "At least 75% exact, at least one exact eligible, zero unsafe candidate adjustments, no missing.",
        "lead_gate": "Pass holdout and produce strictly more exact results than both comparisons.",
        "stop": "Run pilot once. If it fails, stop. Otherwise run the disjoint holdout once and stop. "
                "Any failed model response consumes the budget. Preserve all responses.",
        "exclusions": sorted(EXCLUDED),
        "failure_hierarchy": "Missing call. Incorrect shared model location. Explicit unit validation failure or "
                             "both bounds off by the same supported thousand/million/billion factor. Other verifier "
                             "abstention. Incorrect bounds/delta/disposition. Inadequate citations.",
        "manifest_sha256": {split: prior.digest(manifest_path(split)) for split in SPLITS},
        "gold_sha256": {split: prior.digest(manifest_path(split, gold=True)) for split in SPLITS},
        "code_sha256": {path.name: prior.digest(path) for path in sources},
        "archive_sha256": {document["id"]: document["sha256"] for case in cases for document in case["documents"]},
        "cases": {split: [case["id"] for case in cases if case["split"] == split] for split in SPLITS},
        "common_prompt": POLICY,
        "prompts": prompts(),
    }
    freeze_json(out / "inputs.json", inputs)
    protocol["model_input_sha256"] = prior.digest(out / "inputs.json")
    freeze_json(out / "protocol.json", protocol)
    lines = [
        "# 完整公告金額單位預註冊", "",
        "假說是按選定數值欄核對幣別和倍率，能減少金額尺度誤讀，並恢復有充分原文支持的判定。", "",
        f"每案實際兩次 {MODEL} {EFFORT} 呼叫。現版及新版重播同一份定位，純 Astra 直接回答。"
        f"兩次呼叫使用同一份公告全文、封存現估及時間截點，關閉搜尋與工具，單次 {TIMEOUT} 秒。", "",
        "主指標要求處置、區間上下限、帶符號差額與必要原文均正確。"
        "引文可用裁定預先封存的等價選項。任何未全對的非零差額皆計作誤調。", "",
        "- 先導四案至少三案全對，才執行四案保留集。兩組發行人互斥。",
        "- 保留集至少 75% 全對。兩階段都要求新版零誤調、至少一筆應調整案例全對，且模型回覆齊全。",
        "- 新版須通過保留集，且全對數同時高於現版和純 Astra，才記為本輪領先。",
        "- 先導未過即停止。保留集執行一次後停止。失敗回傳占用模型預算。",
        "- Progress、Ondas、SAIC、Hologic 留作回歸測試。", "",
        "[封存規則及雜湊](protocol.json) · [模型完整輸入](inputs.json)", "",
    ]
    (out / "protocol.md").write_text("\n".join(lines), encoding="utf-8")
    return protocol


def invoke(case, data, call, out):
    path = out / "calls" / f"{case['id']}-{call}.json"
    if path.exists():
        return prior.load(path)
    schema = full_revision.FilingExtraction if call == "extract" else raw.Decision
    events = []
    started = perf_counter()
    try:
        response = Codex(audit=events.extend, reasoning_effort=EFFORT, call_timeout=TIMEOUT)._generate(
            schema, f"{POLICY} {prompts()[call]}", data,
        )
        record = {"output": response.model_dump(mode="json")}
    except AdapterError as exc:
        record = {"error": str(exc)}
    prohibited = {"web_search", "command_execution", "mcp_tool_call", "dynamic_tool_call", "collab_tool_call"}
    tools = [event["item"]["type"] for event in events
             if event.get("type") == "item.completed" and event.get("item", {}).get("type") in prohibited]
    if tools:
        record = {"error": "模型使用預算外的工具。", "tool_types": tools, "rejected_output": record.get("output")}
    usage = [event["usage"] for event in events if event.get("type") == "turn.completed"]
    record["elapsed_seconds"] = round(perf_counter() - started, 2)
    record["events"] = events
    record["usage"] = {key: sum(turn.get(key, 0) for turn in usage) for key in
                       ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")}
    write_json(path, record)
    return record


def unit_failure(decision, expected):
    if decision.get("audit", {}).get("block_stage") == "units" or decision.get("block_stage") == "units":
        return True
    limits = ("new_low", "new_high")
    if any(decision[key] is None or expected[key] is None or not Decimal(expected[key]) for key in limits):
        return False
    observed = tuple(Decimal(decision[key]) for key in limits)
    target = tuple(Decimal(expected[key]) for key in limits)
    factors = [Decimal(10) ** exponent for exponent in (-9, -6, -3, 3, 6, 9)]
    return any(all(value == correct * scale for value, correct in zip(observed, target)) for scale in factors)


def explain(arm, decision, measures, expected, located):
    if measures["exact"] or measures["missing"]:
        return match.explain(arm, decision, measures, expected, located)
    if (arm == "astra" or located) and unit_failure(decision, expected):
        return "units"
    return match.explain(arm, decision, measures, expected, located)


def score(case, data, expected, calls, old):
    extracted = calls["extract"].get("output")
    decisions = {"current": match.verify(old, data, extracted),
                 "candidate": match.verify(full_revision.check_filing_revision, data, extracted),
                 "astra": calls["astra"].get("output")}
    refs = full.source_map(data)
    cited = {ref for decision in decisions.values() if decision for ref in decision["evidence_ids"]}
    scores = {arm: match.assess(decision, expected, refs) for arm, decision in decisions.items()}
    located = match.correct_location(extracted, expected, refs)
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


def delivery_pack(out, rows, inputs, protocol):
    full.delivery_pack(out, rows, inputs, protocol)
    pack = out / "analyst-review"
    form = pack / "review-form.csv"
    with form.open(encoding="utf-8-sig", newline="") as file:
        answers = list(csv.DictReader(file))
    for answer in answers:
        answer["unit_ok"] = ""
    full.csv_file(form, list(answers[0]), answers)
    page = pack / "review.html"
    html = page.read_text(encoding="utf-8").replace('<nav aria-label="案例">',
        '<p>請在 unit_ok 欄另外核對原始數值、幣別、倍率與適用範圍。</p><nav aria-label="案例">', 1)
    page.write_text(html, encoding="utf-8")
    with ZipFile(out / "analyst-review.zip", "w", compression=ZIP_DEFLATED) as bundle:
        for path in (page, form):
            bundle.write(path, arcname=path.name)


def render(out, rows, summary):
    lines = ["# 完整公告金額單位評測", "",
             "現版及新版共用同一份定位。純 Astra 使用相同預算直接回答。", "",
             "[預註冊及停止條件](protocol.md) · [封存輸入](inputs.json) · [評分表](scores.csv) · "
             "[數字摘要](summary.json) · [模型回傳雜湊](calls.sha256.json) · [匿名覆核包](analyst-review.zip)", ""]
    for split, heading in (("pilot", "先導"), ("holdout", "保留集")):
        lines.extend([f"## {heading}", ""])
        result = summary["splits"].get(split)
        if result is None:
            lines.extend(["依預註冊停止規則，未執行保留集。", ""])
            continue
        lines.extend([f"共 {result['n']} 案。驗收門檻 **{'通過' if result['gate'] else '未通過'}**。"
                      f"共用定位後，新版比現版多全對 {result['paired_exact_gain']:+d} 案。", ""])
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
                         f" [公告正文](filing-view/{case_id}.html) · [共用回傳](calls/{case_id}-extract.json) · "
                         f"[純 Astra 回傳](calls/{case_id}-astra.json)")
        lines.append("")
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--run-model", action="store_true")
    args = parser.parse_args()
    old = previous_verifier()
    cases, gold, inputs = load_inputs()
    protocol = seal(args.out, cases, inputs)
    print(f"Frozen protocol: {args.out / 'protocol.json'}", flush=True)
    if not args.run_model:
        return
    manifest = args.out / "calls.sha256.json"
    if manifest.is_file() and any(prior.digest(args.out / "calls" / name) != digest
                                  for name, digest in prior.load(manifest).items()):
        raise ValueError("先前封存的模型回傳已變動")
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    summary = {"model": MODEL, "effort": EFFORT, "splits": {}, "holdout_attempted": False}
    rows = []
    for split in SPLITS:
        group = run_split([case for case in cases if case["split"] == split], inputs, gold, old, args.out, args.workers)
        summary["splits"][split] = result = match.aggregate(group)
        summary["holdout_attempted"] = split == "holdout"
        rows.extend(group)
        write_json(args.out / "summary.json", summary)
        write_json(manifest, {path.name: prior.digest(path) for path in sorted((args.out / "calls").glob("*.json"))})
        match.scorecard(args.out, rows)
        delivery_pack(args.out, rows, inputs, protocol)
        render(args.out, rows, summary)
        print(f"{split}: {json.dumps(result, ensure_ascii=False)}", flush=True)
        if not result["gate"]:
            break


if __name__ == "__main__":
    main()
