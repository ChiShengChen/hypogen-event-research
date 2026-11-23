"""Compare frozen earnings guidance episodes using issuer excerpts."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import ValidationError

from research_app import revision_bridge
from research_app.adapters import AdapterError, Codex
from research_app.schema import DecimalText, MetricKey, Schema

from . import earnings_revision as previous
from .earnings_horizon import freeze_json
from .public_pilot import EFFORT, MODEL, write_json


OUTPUT = Path("output/earnings-raw-revision")
SPLITS = ("pilot", "holdout")
ARMS = {"current": "現版同句核對", "astra": "純 Astra", "candidate": "新版 Harness"}
LIVE_ARMS = ("astra", "extraction")
TIMEOUT = 240
POLICY = (
    "Use the frozen incumbent, target and raw archived issuer excerpts only. Assess the exact target "
    "fiscal quarter's consolidated revenue guidance range or preliminary point estimate, matching "
    "currency and accounting basis. Unqualified companywide revenue or net sales in these archived US "
    "issuer documents is US GAAP consolidated revenue in USD absent conflicting source labels. Sections "
    "of the same issuer document can jointly support a claim. Use the frozen fiscal_label mapping. "
    "An evidence ID identifies a source section, not a publication date. The disclosure "
    "must be first published at or after event_at and obtained by as_of. Use the updated figure, "
    "not any side-by-side older column, reported actual, year, segment, EPS or one-sided signal. "
    "A single explicit monetary point has equal low and high. For a disclosed midpoint with a symmetric "
    "tolerance, compute both endpoints. Do not infer an unavailable forecast. "
    "For a usable disclosure, cite both its amount section and the same document's lead/period context "
    "section when separate, even if a table header repeats the fiscal label. For a declined disclosure, "
    "cite the section with the specific reason to decline. "
    "Use decimal strings in full currency units without separators."
)
DIRECT = (
    "Return status, available guidance bounds new_low and new_high, remaining_delta, evidence_ids and reason. "
    "If the incumbent is outside the supported interval, return eligible and the nearest bound less the incumbent "
    "as the signed adjustment. If within the interval (including boundary), return noop and 0. "
    "If no valid guidance is available, return blocked and null for both endpoints and remaining_delta."
)
EXTRACT = (
    "For a usable disclosure, return quote with target key, source obtained_at as available_at, low, high, "
    "and native_proof. In native_proof, amount_ref is the ID carrying the stated bounds or point, "
    "and context_ref is the ID from the same document carrying the matching period lead or exact period. "
    "For a pipe-delimited table, header_ref must equal amount_ref because the header and amount are "
    "frozen in the same section. Set column to the zero-based value column (excluding the left metric name) "
    "that carries the updated value. For prose, set header_ref and column to null. Include every proof ref "
    "in the quote's evidence_ids. If a compatible disclosure cannot be verified, return a null quote and cite "
    "the source section(s) supporting that decision in the outer evidence_ids. Downstream code calculates the adjustment."
)


class Decision(Schema):
    status: Literal["eligible", "noop", "blocked"]
    new_low: DecimalText | None
    new_high: DecimalText | None
    remaining_delta: DecimalText | None
    evidence_ids: list[str]
    reason: str


class NativeProof(Schema):
    amount_ref: str
    context_ref: str
    header_ref: str | None
    column: int | None


class GuidanceQuote(previous.GuidanceQuote):
    native_proof: NativeProof


class Extraction(Schema):
    quote: GuidanceQuote | None
    evidence_ids: list[str]


def input_path(split, *, gold=False):
    suffix = "_gold" if gold else ""
    return Path(__file__).with_name(f"earnings_raw_revision_{split}{suffix}.json")


def load_sets():
    cases, gold = [], {}
    issuers = set()
    for split in SPLITS:
        rows = previous.load(input_path(split))
        if len(rows) != 4 or any(row["split"] != split for row in rows):
            raise ValueError(f"{split} 應有四個標明區組的案例")
        tickers = {row["ticker"] for row in rows}
        if len(tickers) != len(rows) or issuers.intersection(tickers):
            raise ValueError("先導與保留集各案需為不同發行人")
        issuers.update(tickers)
        cases.extend(rows)
        gold.update(previous.load(input_path(split, gold=True)))
    previous.validate(cases, gold)
    for row in cases:
        expected = gold[row["id"]]
        amount = Decimal(row["baseline"]["amount"])
        low, high = expected["new_low"], expected["new_high"]
        if expected["disposition"] == "blocked":
            if low is not None or high is not None or Decimal(expected["delta"]) != 0:
                raise ValueError(f"{row['id']} 拒絕裁定不應有替代營收區間或非零調整")
            continue
        if not 0 <= Decimal(low) <= Decimal(high):
            raise ValueError(f"{row['id']} 保留集的區間下限與上限不合法")
        delta = min(max(amount, Decimal(low)), Decimal(high)) - amount
        if delta != Decimal(expected["delta"]) or bool(delta) != (expected["disposition"] == "eligible"):
            raise ValueError(f"{row['id']} 裁定狀態、金額及區間互不一致")
    return cases, gold


def model_input(case):
    return {**previous.model_input(case), "fiscal_label": case["fiscal_label"]}


def seal(out, cases):
    protocol = {
        "hypothesis": "Same-source multi-section proof increases exact decisions on raw issuer excerpts "
                      "relative to requiring all qualifiers in one sentence, while preserving zero unsafe adjustments.",
        "model": MODEL,
        "effort": EFFORT,
        "max_calls_per_live_arm_per_case": 1,
        "timeout_seconds": TIMEOUT,
        "external_tool_budget": 0,
        "token_ceiling": "No separately configured token ceiling, observed tokens recorded.",
        "comparison": {
            "astra": "Direct signed adjustment and supporting bounds with citations.",
            "current": "Current strict same-sentence verifier using the shared extraction.",
            "candidate": "Candidate same-source evidence verifier using the same extraction as current.",
        },
        "primary": "Exact disposition, effective signed adjustment, bounds (including no-op), "
                   "and all preregistered evidence IDs. All cited evidence must be visible.",
        "unsafe_adjustment": "Any nonzero adjustment outside an entirely correct decision.",
        "go_gate": "At least 3/4 exact, at least one exact eligible, greater exact count than current, "
                   "zero unsafe adjustments and no missing live output on either arm.",
        "superiority_gate": "Pass holdout acceptance, strictly more exact than direct Astra, "
                            "and at most as many unsafe adjustments as direct Astra.",
        "stop": "Freeze evidence, gold and implementation before first model call. Stop if pilot fails; "
                "otherwise run the sealed holdout once and stop. Preserve all completed and failed calls.",
        "inputs_sha256": {split: previous.digest(input_path(split)) for split in SPLITS},
        "gold_sha256": {split: previous.digest(input_path(split, gold=True)) for split in SPLITS},
        "runner_sha256": previous.digest(Path(__file__)),
        "prior_runner_sha256": previous.digest(Path(previous.__file__)),
        "evaluator_sha256": previous.digest(Path(revision_bridge.__file__)),
        "ids": {split: [row["id"] for row in cases if row["split"] == split] for split in SPLITS},
        "shared_prompt": POLICY,
        "astra_prompt": DIRECT,
        "shared_extraction_prompt": EXTRACT,
    }
    out.mkdir(parents=True, exist_ok=True)
    freeze_json(out / "protocol.json", protocol)
    freeze_json(out / "inputs.json", {case["id"]: model_input(case) for case in cases})
    preregistration = [
        "# 原始公告營收指引覆核預註冊",
        "",
        "假說是允許同一份公告的多段可核對引文共同支持營收指引，能提升原文輸入的正確率，並維持零誤調。",
        "",
        "現版與新版 Harness 共用同一份擷取結果，分別以現版同句規則及新版來源核對規則計算。"
        "純 Astra 在等額請求下直接輸出處置、指引區間與差額。兩個模型呼叫共用同時點原始公告摘錄、"
        "凍結現估與來源時點。每案各用一次 GPT-6.2 Astra medium，240 秒上限，停用工具與搜尋。"
        "CLI 未另設詞元上限，另記錄實際詞元與耗時。",
        "",
        "主指標要求處置、帶方向的剩餘金額、區間兩端及必要引文同時正確。"
        "維持原估也要查對兩端。暫緩調整的有效差額為零，沒有可用區間。"
        "非全對的決策如建議任何非零金額，一律記為誤調。",
        "",
        f"- 先導固定四案，{'、'.join(protocol['ids']['pilot'])}。",
        f"- 保留集固定四案，{'、'.join(protocol['ids']['holdout'])}。",
        "- 兩階段各至少 3/4 全對，含至少一筆可採用且全對的調整。全對案數須高於現版，"
        "且無新版誤調或任一模型回覆缺失。先導未通過就停止。",
        "- 保留集通過執行門檻後，新版須嚴格多於純 Astra 的全對案數且誤調不增加，才記為領先。"
        "固定保留集跑完即停止，保留失敗回合。",
        "",
        "[詳細規則、案例及程式雜湊](protocol.json) · [模型可見原文摘錄](inputs.json)",
    ]
    (out / "protocol.md").write_text("\n".join(preregistration) + "\n", encoding="utf-8")


def invoke(case, arm, out):
    path = out / "calls" / f"{case['id']}-{arm}.json"
    if path.exists():
        return previous.load(path)
    schema, task = (Decision, DIRECT) if arm == "astra" else (Extraction, EXTRACT)
    events = []
    started = perf_counter()
    try:
        result = Codex(audit=events.extend, reasoning_effort=EFFORT, call_timeout=TIMEOUT)._generate(
            schema, f"{POLICY} {task}", model_input(case),
        )
        record = {"output": result.model_dump(mode="json")}
    except AdapterError as exc:
        record = {"error": str(exc)}
    items = [event["item"] for event in events if event.get("type") == "item.completed"]
    raw_responses = [item["text"] for item in items if item.get("type") == "agent_message"]
    tools = [item["type"] for item in items if item.get("type") in {
        "web_search", "command_execution", "mcp_tool_call", "dynamic_tool_call", "collab_tool_call",
    }]
    if tools:
        record = {"error": "模型嘗試使用評測預算外的工具。", "tool_types": tools,
                  "rejected_output": record.get("output")}
    usage = [event["usage"] for event in events if event.get("type") == "turn.completed"]
    record["elapsed_seconds"] = round(perf_counter() - started, 2)
    record["raw_responses"] = raw_responses
    record["usage"] = {key: sum(turn.get(key, 0) for turn in usage) for key in (
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
    )}
    write_json(path, record)
    return record


def harness_decisions(case, extraction):
    key = MetricKey.model_validate(previous.target(case))
    baseline = case["baseline"]
    incumbent = revision_bridge.RevisionQuote(
        key=key, available_at=baseline["available_at"], low=baseline["amount"],
        high=baseline["amount"], evidence_ids=baseline["evidence_ids"],
    )
    try:
        quote = revision_bridge.RevisionQuote.model_validate(extraction["quote"]) if extraction["quote"] else None
    except ValidationError as exc:
        decision = {"status": "blocked", "remaining_delta": None, "new_low": None, "new_high": None,
                    "evidence_ids": extraction["evidence_ids"], "reason": "擷取結果未通過格式驗證。",
                    "validation_errors": exc.errors(include_url=False, include_context=False, include_input=False)}
        return decision, decision
    request = revision_bridge.RevisionRequest(
        key=key, event_at=case["event_at"], incumbent=incumbent, disclosure=quote,
    )
    evidence = [{
        **row, "quote": row["text"], "source": row["source_url"], "kind": "disclosure",
        "text_format": "excerpt", "synthetic": False,
    } for row in case["evidence"]]
    cutoff = previous.instant(case["as_of"])
    strict_quote = quote.model_copy(update={"native_proof": None}) if quote else None
    strict_request = request.model_copy(update={"disclosure": strict_quote})
    current = revision_bridge.evaluate_revision(strict_request, evidence, as_of=cutoff)
    candidate = revision_bridge.evaluate_revision(request, evidence, as_of=cutoff, fiscal_label=case["fiscal_label"])
    return tuple(as_decision(audit, extraction) for audit in (current, candidate))


def as_decision(audit, extraction):
    blocked = audit["status"] == "blocked"
    quote = audit.get("disclosure") if not blocked else None
    return {
        "status": audit["status"], "remaining_delta": audit["remaining_delta"],
        "new_low": quote["low"] if quote else None, "new_high": quote["high"] if quote else None,
        "evidence_ids": extraction["evidence_ids"] if blocked else audit["evidence_ids"],
        "reason": audit["reason"], "audit": audit,
    }


def pair_amounts(low, high):
    return tuple(Decimal(value) if value is not None else None for value in (low, high))


def assess(decision, expected, evidence):
    if decision is None:
        return {"exact": False, "delta_exact": False, "range_exact": False, "citations": False,
                "unsafe": False, "eligible_exact": False, "missing": True}
    delta = decision["remaining_delta"]
    effective_delta = Decimal(delta) if delta is not None else Decimal(0)
    delta_exact = effective_delta == Decimal(expected["delta"])
    range_exact = pair_amounts(decision["new_low"], decision["new_high"]) == pair_amounts(
        expected["new_low"], expected["new_high"],
    )
    disposition = decision["status"] == expected["disposition"]
    signed = (delta is None) == (decision["status"] == "blocked")
    cited = set(decision["evidence_ids"])
    citation_ok = bool(cited) and set(expected["evidence_ids"]) <= cited <= evidence
    exact = disposition and signed and range_exact and delta_exact and citation_ok
    return {"exact": exact, "delta_exact": delta_exact, "range_exact": range_exact,
            "citations": citation_ok, "unsafe": bool(effective_delta) and not exact,
            "eligible_exact": exact and decision["status"] == "eligible", "missing": False}


def score(case, expected, calls):
    extraction = calls["extraction"].get("output")
    current, candidate = harness_decisions(case, extraction) if extraction is not None else (None, None)
    decisions = {"current": current, "astra": calls["astra"].get("output"), "candidate": candidate}
    sources = {row["id"]: row["source_url"] for row in case["evidence"]}
    return {
        "id": case["id"], "split": case["split"], "issuer": case["issuer"], "ticker": case["ticker"],
        "baseline": case["baseline"], "expected": expected, "decisions": decisions, "sources": sources,
        "scores": {arm: assess(decision, expected, set(sources)) for arm, decision in decisions.items()},
        "calls": calls,
    }


def run_split(cases, gold, out, workers):
    rows = {}
    (out / "calls").mkdir(exist_ok=True)
    (out / "cases").mkdir(exist_ok=True)
    received = {case["id"]: {} for case in cases}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(invoke, case, arm, out): (case, arm) for case in cases for arm in LIVE_ARMS}
        for future in as_completed(futures):
            case, arm = futures[future]
            case_id = case["id"]
            received[case_id][arm] = future.result()
            if len(received[case_id]) == len(LIVE_ARMS):
                rows[case_id] = score(case, gold[case_id], received[case_id])
                write_json(out / "cases" / f"{case_id}.json", rows[case_id])
                print(f"{case['split']} {case_id} scored", flush=True)
    return [rows[case["id"]] for case in cases]


def aggregate(rows):
    measures = ("exact", "delta_exact", "range_exact", "citations", "unsafe", "eligible_exact", "missing")
    counts = {arm: {key: sum(row["scores"][arm][key] for row in rows) for key in measures} for arm in ARMS}
    usage = {arm: {key: sum(row["calls"][arm]["usage"][key] for row in rows)
                   for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")}
             for arm in LIVE_ARMS}
    for arm in LIVE_ARMS:
        usage[arm]["elapsed_seconds"] = round(sum(row["calls"][arm]["elapsed_seconds"] for row in rows), 2)
    candidate, current, astra = (counts[arm] for arm in ("candidate", "current", "astra"))
    go = (candidate["exact"] >= 3 and candidate["eligible_exact"] > 0 and not candidate["unsafe"]
          and not candidate["missing"] and not astra["missing"] and candidate["exact"] > current["exact"])
    return {"n": len(rows), "scores": counts, "usage": usage, "gate": go,
            "lead_over_astra": go and candidate["exact"] > astra["exact"] and candidate["unsafe"] <= astra["unsafe"]}


def show_decision(decision):
    if decision is None:
        return "缺少回覆"
    status = {"eligible": "可調整", "noop": "維持", "blocked": "暫緩"}[decision["status"]]
    amount = decision["remaining_delta"]
    bounds = pair_amounts(decision["new_low"], decision["new_high"])
    shown = f" [{bounds[0]:,f}–{bounds[1]:,f}]" if None not in bounds else ""
    return f"{status} {Decimal(amount):+,f}{shown}" if amount is not None else f"{status}{shown}"


def render(summary, rows, out):
    lines = [
        "# 原始公告的營收指引覆核",
        "",
        "各組使用同一份點時原文摘錄與凍結現估。現版與新版使用同一份模型擷取結果，純 Astra 直接輸出"
        "核對結論。兩個模型組各用一次 GPT-6.2 Astra medium，停用工具與搜尋，每次 240 秒上限。",
        "",
        "主指標把處置、差額、區間兩端及必要引文合併評分。零誤調要求所有非零建議都同時符合上述條件。"
        "這輪只驗證公司公告所支持的差額情境。後續財報實績及分析師盲評各由獨立研究流程追蹤。",
        "",
        "[預註冊](protocol.md) · [原文與凍結輸入](inputs.json) · [數字摘要](summary.json)",
    ]
    for split, label in (("pilot", "先導評測"), ("holdout", "保留集")):
        lines.extend(["", f"## {label}", ""])
        result = summary["splits"].get(split)
        if result is None:
            lines.append("依先導停止條件，保留集未執行。")
            continue
        lines.append(f"流程門檻 **{'通過' if result['gate'] else '未通過'}**，共 {result['n']} 案。")
        if split == "holdout":
            lines.append(f"純 Astra 領先門檻 **{'通過' if result['lead_over_astra'] else '未通過'}**。")
        lines.extend(["", "| 組別 | 全對 | 金額 | 區間 | 引文 | 誤調 | 缺少回覆 |", "|---|---:|---:|---:|---:|---:|---:|"])
        for arm, name in ARMS.items():
            values = [result["scores"][arm][key] for key in (
                "exact", "delta_exact", "range_exact", "citations", "unsafe", "missing",
            )]
            lines.append(f"| {name} | " + " | ".join(map(str, values)) + " |")
        lines.extend(["", "| 呼叫 | 輸入詞元 | 快取輸入詞元 | 輸出詞元 | 累計秒數 |", "|---|---:|---:|---:|---:|"])
        for arm, name in (("astra", "純 Astra"), ("extraction", "兩個 Harness 共用擷取")):
            usage = result["usage"][arm]
            lines.append(f"| {name} | {usage['input_tokens']:,} | {usage['cached_input_tokens']:,} | "
                         f"{usage['output_tokens']:,} | {usage['elapsed_seconds']:.2f} |")
        lines.extend(["", "| 案例 | 裁定 | 現版 | 純 Astra | 新版 | 來源 |", "|---|---|---|---|---|---|"])
        for row in rows:
            if row["split"] != split:
                continue
            expected = row["expected"]
            gold = show_decision({**expected, "status": expected["disposition"], "remaining_delta": (
                None if expected["disposition"] == "blocked" else expected["delta"]
            )})
            decisions = " | ".join(show_decision(row["decisions"][arm]) for arm in ARMS)
            sources = "、".join(f"[來源 {i}]({url})" for i, url in enumerate(dict.fromkeys(row["sources"].values()), 1))
            lines.append(f"| [{row['ticker']}](cases/{row['id']}.json) | {gold} | {decisions} | {sources} |")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--run-model", action="store_true")
    args = parser.parse_args()
    cases, gold = load_sets()
    seal(args.out, cases)
    print(f"Frozen protocol: {args.out / 'protocol.json'}", flush=True)
    if not args.run_model:
        return
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    summary = {"model": MODEL, "effort": EFFORT, "splits": {}, "holdout_attempted": False}
    rows = []
    for split in SPLITS:
        group = run_split([case for case in cases if case["split"] == split], gold, args.out, args.workers)
        rows.extend(group)
        summary["splits"][split] = result = aggregate(group)
        summary["holdout_attempted"] = split == "holdout"
        write_json(args.out / "summary.json", summary)
        render(summary, rows, args.out)
        print(f"{split}: {json.dumps(result, ensure_ascii=False)}", flush=True)
        if not result["gate"]:
            break


if __name__ == "__main__":
    main()
