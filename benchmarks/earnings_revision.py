"""Replay a single-quarter guidance revision using identical archived evidence."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import AwareDatetime, ValidationError

from research_app.adapters import AdapterError, Codex
from research_app.schema import DecimalText, MetricKey, Schema

from .earnings_horizon import freeze_json
from .public_pilot import EFFORT, MODEL, write_json

DATA_PATH = Path(__file__).with_name("earnings_revision_cases.json")
GOLD_PATH = Path(__file__).with_name("earnings_revision_gold.json")
OUTPUT = Path("output/earnings-revision")
SPLITS = ("pilot", "holdout")
ARMS = {"current": "現版沿用凍結預估", "astra": "純 Astra", "candidate": "新版 Harness"}
POLICY = (
    "Use the frozen incumbent and archived evidence to assess a new issuer guidance disclosure. "
    "Use only an explicit issuer guidance range or preliminary point estimate for consolidated "
    "quarterly revenue with the exact period end, currency and accounting basis. A point estimate "
    "has the same low and high at its stated precision. The active disclosure must be published "
    "at or after event_at and both published and obtained by as_of. Do not infer missing estimates "
    "from reported earnings, analyst estimates, prior guidance or differently scoped disclosures. "
    "Apply a zero adjustment if the "
    "incumbent falls inside the interval (including the edges). Outside it, use the nearest edge, "
    "then subtract the incumbent to give a signed amount. If no qualifying disclosure can be "
    "verified, the decision is blocked. Cite source IDs for the current disclosure or the specific "
    "mismatch. Use decimal strings in full currency units, without separators."
)
DIRECT = (
    "Return the decision and signed remaining adjustment. Use eligible for a nonzero adjustment, "
    "noop for a qualifying interval that already covers the incumbent and blocked if the required "
    "disclosure could not be verified. For blocked, return null as remaining_delta."
)
EXTRACT = (
    "Extract the explicit candidate issuer disclosure range for the requested target with its own "
    "source obtained_at timestamp as available_at and original source IDs. Return a null quote "
    "if the qualifying range cannot be verified. In either case return the source IDs most "
    "directly supporting the decision. The downstream evaluator calculates the adjustment."
)


class Decision(Schema):
    status: Literal["eligible", "noop", "blocked"]
    remaining_delta: DecimalText | None
    evidence_ids: list[str]
    reason: str


class GuidanceQuote(Schema):
    key: MetricKey
    available_at: AwareDatetime
    low: DecimalText
    high: DecimalText
    evidence_ids: list[str]


class Extraction(Schema):
    quote: GuidanceQuote | None
    evidence_ids: list[str]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def instant(value):
    return datetime.fromisoformat(value)


def target(case):
    return {"duration": "quarter", **case["target"]}


def validate(cases, gold):
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)) or set(ids) != set(gold):
        raise ValueError("案例與評分資料的 ID 必須唯一且一致")
    if set(case["split"] for case in cases) != set(SPLITS):
        raise ValueError("案例需標明 pilot 或 holdout")
    if sum(case["split"] == "pilot" for case in cases) != 4:
        raise ValueError("先導測試需恰好四案")
    if sum(case["split"] == "holdout" for case in cases) < 4:
        raise ValueError("保留集至少四案")
    for case in cases:
        MetricKey.model_validate(target(case))
        cutoff = instant(case["as_of"])
        event_at = instant(case["event_at"])
        baseline_at = instant(case["baseline"]["available_at"])
        if not baseline_at <= event_at <= cutoff:
            raise ValueError(f"基準、事件或截止時間順序不符 {case['id']}")
        known = set()
        for row in case["evidence"]:
            if row["id"] in known or not (
                instant(row["published_at"]) <= instant(row["obtained_at"]) <= cutoff
            ):
                raise ValueError(f"來源 ID 或時間不符 {case['id']}/{row['id']}")
            known.add(row["id"])
        expected = gold[case["id"]]
        if expected["disposition"] not in {"eligible", "noop", "blocked"}:
            raise ValueError(f"未知裁定 {case['id']}")
        if not set(expected["evidence_ids"]) or not set(expected["evidence_ids"]) <= known:
            raise ValueError(f"裁定缺少同時點的來源 {case['id']}")
        if not set(case["baseline"]["evidence_ids"]) or not set(case["baseline"]["evidence_ids"]) <= known:
            raise ValueError(f"基準引用缺少同時點的來源 {case['id']}")


def model_input(case):
    return {
        "issuer": case["issuer"],
        "ticker": case["ticker"],
        "as_of": case["as_of"],
        "event_at": case["event_at"],
        "target": target(case),
        "incumbent": {
            key: case["baseline"][key]
            for key in ("kind", "amount", "available_at", "evidence_ids")
        },
        "evidence": case["evidence"],
    }


def seal(out, cases):
    import research_app.revision_bridge as revision

    protocol = {
        "hypothesis": "Cited extraction followed by deterministic validation improves reconstruction "
                      "over the frozen no-adjustment path. A strict holdout lead over Astra is separate.",
        "scope": "Point-in-time guidance revision decisions, never subsequent reported revenue.",
        "model": MODEL,
        "effort": EFFORT,
        "per_case_per_live_arm_max_calls": 1,
        "per_call_timeout_seconds": 240,
        "token_ceiling": "No separate token ceiling configured in Codex CLI; observed usage recorded.",
        "external_search_budget": 0,
        "shared_case_inputs": "inputs.json; excludes adjudications, split, case ID, and baseline rationale.",
        "current_arm": "Legacy path with no new model entry: frozen incumbent, no adjustment.",
        "primary": "Exact disposition, effective signed delta and disposition-supporting citations.",
        "citation_rule": "At least one reference, every reference visible by the cutoff, and "
                         "every required gold support ID cited.",
        "pilot_gate": "At least 3/4 exact, zero false adjustments and zero missing live outputs. "
                      "At least one eligible exact and more exact signed deltas than current.",
        "holdout_go_gate": "At least 75% exact, zero false adjustments and zero missing live outputs. "
                           "At least one eligible exact and more exact signed deltas than current.",
        "astra_superiority_gate": "Holdout go gate passes and candidate has strictly more exact outcomes "
                                  "than pure Astra with no additional false adjustments.",
        "stop": "Run pilot first. Do not run holdout if pilot gate fails. "
                "Do not retry model requests after an evaluated call. Stop after the fixed holdout.",
        "dataset_sha256": digest(DATA_PATH),
        "gold_sha256": digest(GOLD_PATH),
        "runner_sha256": digest(Path(__file__)),
        "evaluator_sha256": digest(Path(revision.__file__)),
        "ids": {split: [case["id"] for case in cases if case["split"] == split] for split in SPLITS},
        "policy": POLICY,
        "astra_prompt": DIRECT,
        "candidate_prompt": EXTRACT,
    }
    out.mkdir(parents=True, exist_ok=True)
    freeze_json(out / "protocol.json", protocol)
    freeze_json(out / "inputs.json", {case["id"]: model_input(case) for case in cases})
    preregistration = [
        "# 事件後營收指引調整預註冊",
        "",
        "假說是先擷取、核對揭露再計算，能比沿用既有數值更準確地還原剩餘調整。"
        "新版若在保留集嚴格勝過純 Astra，才記為本次比較領先。",
        "",
        "三組共用既有估值與當時可見的歷史公告。純 Astra 直接判定，新版只請模型擷取區間，"
        "再用程式驗證來源與計算。兩組各用 GPT-6.2 Astra medium 每案一次請求，關閉搜尋，"
        "上限 240 秒。CLI 未另設詞元上限，執行後記錄實際用量。現版依已凍結的無新輸入路徑，"
        "沿用原估值。",
        "",
        "主指標同時要求處置、帶正負號的調整額和支持理由的全部必要引文正確。"
        "把拒絕輸入的有效調整額計為零。對零調整裁定輸出任何非零額，記為錯誤調整。",
        "",
        f"- 先導固定為 {'、'.join(protocol['ids']['pilot'])}。至少四案全對三案，"
        "兩組模型回覆齊全，且無錯誤調整。至少一個可調整案全對，調整金額正確數嚴格高於現版。",
        f"- 保留集固定為 {'、'.join(protocol['ids']['holdout'])}。"
        "先導通過才執行，要求至少 75% 全對，兩組模型回覆齊全且無錯誤調整。"
        "至少一個可調整案全對，調整金額正確數嚴格高於現版。",
        "- 新版需通過保留集門檻，主指標正確數嚴格多於純 Astra，且錯誤調整數不高於純 Astra，"
        "才記為領先。先導未通過或保留集完成即停止。模型回合失敗仍保留紀錄。",
        "",
        f"案例 SHA-256 `{protocol['dataset_sha256']}`",
        "",
        f"裁定 SHA-256 `{protocol['gold_sha256']}`",
        "",
        "[完整機器可讀規則與程式雜湊](protocol.json) · [模型可見資料](inputs.json)",
    ]
    (out / "protocol.md").write_text("\n".join(preregistration) + "\n", encoding="utf-8")
    return protocol


def evaluate(case, extraction):
    from research_app.revision_bridge import RevisionQuote, RevisionRequest, evaluate_revision

    key = MetricKey.model_validate(target(case))
    base = case["baseline"]
    incumbent = RevisionQuote(
        key=key, available_at=base["available_at"], low=base["amount"],
        high=base["amount"], evidence_ids=base["evidence_ids"],
    )
    try:
        disclosure = RevisionQuote.model_validate(extraction["quote"]) if extraction["quote"] else None
    except ValidationError as exc:
        return {
            "status": "blocked", "remaining_delta": None, "evidence_ids": extraction["evidence_ids"],
            "reason": "擷取結果未通過揭露資料格式驗證。",
            "validation_errors": exc.errors(include_url=False, include_context=False, include_input=False),
        }
    original = RevisionQuote.model_validate({"key": key, **base["original"]}) if base.get("original") else None
    evidence = [
        {
            "id": row["id"], "quote": row["text"], "source": row["source_url"],
            "kind": "disclosure", "synthetic": False,
            "published_at": row["published_at"], "obtained_at": row["obtained_at"],
        }
        for row in case["evidence"]
    ]
    decision = evaluate_revision(RevisionRequest(
        key=key, event_at=case["event_at"], original=original,
        incumbent=incumbent, disclosure=disclosure,
    ), evidence, as_of=instant(case["as_of"]))
    if decision["status"] == "blocked":
        decision["evidence_ids"] = extraction["evidence_ids"]
    return decision


def invoke(case, arm, out):
    path = out / "calls" / f"{case['id']}-{arm}.json"
    if path.exists():
        return load(path)
    schema, instruction = (Decision, DIRECT) if arm == "astra" else (Extraction, EXTRACT)
    events = []
    started = perf_counter()
    try:
        result = Codex(audit=events.extend, reasoning_effort=EFFORT, call_timeout=240)._generate(
            schema, POLICY + " " + instruction, model_input(case),
        )
        record = {"output": result.model_dump(mode="json")}
    except AdapterError as exc:
        record = {"error": str(exc)}
    usage = [event["usage"] for event in events if event.get("type") == "turn.completed"]
    record["elapsed_seconds"] = round(perf_counter() - started, 2)
    record["usage"] = {key: sum(turn.get(key, 0) for turn in usage) for key in (
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
    )}
    write_json(path, record)
    return record


def assess(decision, expected, evidence):
    if decision is None:
        return {"exact": False, "delta_exact": False, "citations": False,
                "false_adjustment": False, "eligible_exact": False, "missing": True}
    delta = decision["remaining_delta"]
    effective_delta = Decimal(delta) if delta is not None else Decimal(0)
    expected_delta = Decimal(expected["delta"] or "0")
    delta_exact = effective_delta == expected_delta
    disposition = decision["status"] == expected["disposition"]
    signed = (delta is None) == (decision["status"] == "blocked")
    cited = set(decision["evidence_ids"])
    citation_ok = bool(cited) and set(expected["evidence_ids"]) <= cited <= evidence
    exact = disposition and signed and delta_exact and citation_ok
    return {"exact": exact, "delta_exact": delta_exact, "citations": citation_ok,
            "false_adjustment": expected_delta == 0 and effective_delta != 0,
            "eligible_exact": exact and decision["status"] == "eligible", "missing": False}


def score(case, expected, calls):
    astra = calls["astra"].get("output")
    extraction = calls["candidate"].get("output")
    candidate = evaluate(case, extraction) if extraction is not None else None
    current = {"status": "noop", "remaining_delta": "0", "evidence_ids": case["baseline"]["evidence_ids"]}
    evidence = {row["id"] for row in case["evidence"]}
    decisions = {"current": current, "astra": astra, "candidate": candidate}
    return {
        "id": case["id"], "split": case["split"], "issuer": case["issuer"],
        "baseline": case["baseline"], "expected": expected,
        "decisions": decisions, "scores": {
            arm: assess(decision, expected, evidence) for arm, decision in decisions.items()
        },
        "sources": {row["id"]: row["source_url"] for row in case["evidence"]},
        "calls": calls,
    }


def run_split(cases, gold, out, workers):
    rows = {}
    (out / "calls").mkdir(exist_ok=True)
    (out / "cases").mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(invoke, case, arm, out): (case["id"], arm)
                   for case in cases for arm in ("astra", "candidate")}
        received = {case["id"]: {} for case in cases}
        for future in as_completed(futures):
            case_id, arm = futures[future]
            received[case_id][arm] = future.result()
            if len(received[case_id]) == 2:
                case = next(item for item in cases if item["id"] == case_id)
                rows[case_id] = score(case, gold[case_id], received[case_id])
                write_json(out / "cases" / f"{case_id}.json", rows[case_id])
                print(f"{case['split']} {case_id} scored", flush=True)
    return [rows[case["id"]] for case in cases]


def aggregate(rows):
    scores = {
        arm: {key: sum(row["scores"][arm][key] for row in rows)
              for key in ("exact", "delta_exact", "citations", "false_adjustment", "eligible_exact", "missing")}
        for arm in ARMS
    }
    model_usage = {
        arm: {key: sum(row["calls"][arm]["usage"][key] for row in rows)
              for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")}
        for arm in ("astra", "candidate")
    }
    candidate, current, astra = (scores[arm] for arm in ("candidate", "current", "astra"))
    go = (candidate["exact"] * 4 >= len(rows) * 3
          and candidate["eligible_exact"] > 0
          and not candidate["false_adjustment"]
          and not candidate["missing"] and not astra["missing"]
          and candidate["delta_exact"] > current["delta_exact"])
    lead = (go and candidate["exact"] > astra["exact"]
            and candidate["false_adjustment"] <= astra["false_adjustment"])
    return {"n": len(rows), "scores": scores, "usage": model_usage, "gate": go,
            "lead_over_astra": lead}


def render(summary, rows, out):
    def show(decision):
        if decision is None:
            return "缺少回覆"
        status = {"eligible": "可調整", "noop": "零調整", "blocked": "拒絕輸入"}[decision["status"]]
        amount = decision["remaining_delta"]
        return status if amount is None else f"{status} {Decimal(amount):+,f}"

    lines = [
        "# 事件後營收指引調整重建",
        "",
        "三組沿用同一凍結基準。兩個模型組各以 GPT-6.2 Astra medium 讀取相同公告摘錄，"
        "每案一次請求，關閉工具與搜尋，每次上限 240 秒。CLI 未另設詞元上限，"
        "實際用量見下表。現版組使用無新輸入時的零調整路徑，未重跑完整 Harness。",
        "",
        "主指標要求調整處置、有方向的金額和證據引用都正確。金額單項把拒絕輸入視為零調整。"
        "這項回放衡量能否正確套用已公開的指引，尚未收集前瞻實績或分析師盲評。",
        "",
        "來源為歷史發行人公告的正規化摘錄，時間欄位重建每案可見範圍。"
        "部分控制案採用假設的既有分析師估值，逐案紀錄標註其來源和性質。",
        "",
        "[預註冊規則](protocol.md) · [模型可見輸入](inputs.json) · [數字摘要](summary.json)",
    ]
    for split in SPLITS:
        block = summary["splits"].get(split)
        lines += ["", f"## {'先導測試' if split == 'pilot' else '保留集'}", ""]
        if block is None:
            lines.append("未執行。先導測試未通過。")
            continue
        lines += [
            f"執行門檻 **{'通過' if block['gate'] else '未通過'}**，共 {block['n']} 案。"
            + (f"嚴格領先 Astra 門檻 **{'通過' if block['lead_over_astra'] else '未通過'}**。"
               if split == "holdout" else ""),
            "",
            "|組別|主指標全對|金額正確|引用正確|錯誤調整|缺少回覆|",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for arm, name in ARMS.items():
            stats = block["scores"][arm]
            counts = " | ".join(str(stats[key]) for key in (
                "exact", "delta_exact", "citations", "false_adjustment", "missing",
            ))
            lines.append(f"| {name} | {counts} |")
        lines += ["", "|模型組|輸入詞元|輸出詞元|推理詞元（含於輸出）|",
                  "|---|---:|---:|---:|"]
        for arm, usage in block["usage"].items():
            lines.append(
                f"| {ARMS[arm]} | {usage['input_tokens']:,} | {usage['output_tokens']:,} | "
                f"{usage['reasoning_output_tokens']:,} |"
            )
        lines += ["", "|案例|裁定|現版|純 Astra|新版 Harness|來源|", "|---|---|---|---|---|---|"]
        for row in rows:
            if row["split"] != split:
                continue
            case_id = row["id"]
            expected = {"status": row["expected"]["disposition"],
                        "remaining_delta": None if row["expected"]["disposition"] == "blocked"
                        else row["expected"]["delta"]}
            figures = " | ".join(show(row["decisions"][arm]) for arm in ARMS)
            sources = "、".join(f"[{ref}]({url})" for ref, url in row["sources"].items())
            lines.append(f"| [{case_id}](cases/{case_id}.json) | {show(expected)} | {figures} | {sources} |")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--run-model", action="store_true")
    args = parser.parse_args()
    cases, gold = load(DATA_PATH), load(GOLD_PATH)
    validate(cases, gold)
    protocol = seal(args.out, cases)
    print(f"Frozen protocol: {args.out / 'protocol.json'}", flush=True)
    if not args.run_model:
        return
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    summary = {"model": MODEL, "effort": EFFORT, "gold_sha256": protocol["gold_sha256"], "splits": {},
               "assessment": {"prospective": "not_collected", "analyst_blind": "not_collected"}}
    rows = []
    for split in SPLITS:
        group = run_split([case for case in cases if case["split"] == split], gold, args.out, args.workers)
        rows.extend(group)
        block = aggregate(group)
        summary["splits"][split] = block
        summary["holdout_attempted"] = "holdout" in summary["splits"]
        write_json(args.out / "summary.json", summary)
        render(summary, rows, args.out)
        print(f"{split}: {json.dumps(block, ensure_ascii=False)}", flush=True)
        if not block["gate"]:
            break


if __name__ == "__main__":
    main()
