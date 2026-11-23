"""Equal-workload earnings comparisons on frozen point-in-time evidence."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from decimal import Decimal
import hashlib
import os
from pathlib import Path
from statistics import mean
from time import perf_counter

from pydantic import Field

from benchmarks.earnings_cases import load_cases
from benchmarks.earnings_pilot import read
from benchmarks.public_pilot import EFFORT, MODEL, write_json
from research_app.adapters import AdapterError, Codex, EARNINGS_DRIVER_VERSION
from research_app.earnings import METRICS, SCENARIOS, EarningsError, available_evidence, calculate_earnings, complete_plan
from research_app.schema import DecimalText, EarningsPlan, EstimateDriver, Nonempty, Scenario, Schema

ARMS = ("astra", "calculator", "harness")
VERSION = 1
INSTRUCTION = (
    "Using only the supplied frozen public evidence, forecast exactly two quarters, each with bear, base and bull "
    "scenarios. In every scenario report consolidated revenue, gross margin, operating income and diluted EPS, "
    "and a short Traditional Chinese rationale with one public observation and the opposite result. Use exact "
    "evidence IDs. Express money in unscaled USD and margin as a decimal fraction. Numbers must be plain "
    "decimal strings with up to eight decimal places. Use the current filing as the operating scale and the "
    "old baselines as history. Treat later information as unavailable."
)


class Point(Schema):
    period_end: date
    scenario: Scenario
    revenue: DecimalText
    gross_margin: DecimalText
    operating_income: DecimalText
    eps: DecimalText
    rationale: Nonempty
    evidence_ids: list[Nonempty] = Field(min_length=1)


class PointPacket(Schema):
    points: list[Point]


def project_rows(result):
    drafts = {(row["period_end"], row["scenario"]): row for row in result["inputs"]["drivers"]}
    profiles = {row["period_end"]: row for row in result["inputs"].get("eps_assumptions", [])}
    points = []
    for row in result["quarters"]:
        period = row["period_end"]
        guides = [entry for entry in result.get("guidance_calibration", []) if entry["period_end"] == period]
        profile = profiles.get(period)
        sources, notes = [], []
        for entry in guides:
            sources.extend(entry["reference"]["evidence_ids"])
        if guides:
            labels = "、".join(METRICS[entry["metric"]] for entry in guides)
            notes.append(f"{labels}情境已按同季公司指引中點校準。")
        if profile:
            for item in [profile["tax_rate"], profile["diluted_shares"], profile["recurring_nonoperating"], *profile["one_offs"]]:
                sources.extend(item["evidence_ids"])
            notes.append("EPS 使用另列的稅率、稀釋股數與營業外假設重算。")
        for scenario, values in row["scenarios"].items():
            draft = drafts[(period, scenario)]
            points.append({"period_end": period, "scenario": scenario,
                           **{metric: values["revised"][metric] for metric in METRICS},
                           "rationale": " ".join([draft["rationale"], *notes]),
                           "evidence_ids": list(dict.fromkeys([*draft["evidence_ids"], *sources]))})
    return points


def direct_points(event, context, adapter):
    plan = event.earnings_plan
    excluded = {"eps_assumptions", "calibrate_guidance"} if getattr(adapter, "earnings_driver_version", None) == 3 else set()
    packet = adapter._generate(PointPacket, INSTRUCTION, {
        "target": context["target"], "event": context["event_text"], "as_of": context["as_of"],
        "evidence": context["evidence"], "baseline": plan.model_dump(mode="json", exclude=excluded),
    })
    expected = {(quarter.period_end, scenario) for quarter in plan.quarters for scenario in SCENARIOS}
    if len(packet.points) != len(expected) or {(row.period_end, row.scenario) for row in packet.points} != expected:
        raise EarningsError("須完整回覆兩季三情境，且期別一致")
    visible = {row["id"]: row for row in context["evidence"]}
    for point in packet.points:
        if Decimal(point.revenue) < 0 or Decimal(point.gross_margin) > 1:
            raise EarningsError("營收或毛利率超出可用範圍")
        available_evidence(point.evidence_ids, visible, event.as_of)
    return [point.model_dump(mode="json") for point in packet.points]


def recalculate_direct(event, context, points):
    plan = event.earnings_plan
    quarters = {quarter.period_end.isoformat(): quarter for quarter in plan.quarters}
    drivers = []
    for row in points:
        baseline = quarters[row["period_end"]]
        if set(baseline.segment_revenue) != {"consolidated"}:
            raise EarningsError("對照組只處理合併營收基準")
        revenue, margin, income = map(Decimal, (row["revenue"], row["gross_margin"], row["operating_income"]))
        opex = revenue * margin - income
        drivers.append(EstimateDriver(
            period_end=row["period_end"], scenario=row["scenario"],
            segment_revenue_delta={"consolidated": revenue - baseline.segment_revenue["consolidated"]},
            shipment_changes={}, gross_margin_delta=margin - baseline.gross_margin,
            opex_delta=(opex - baseline.opex).quantize(Decimal("0.00000001")),
            rationale=row["rationale"], evidence_ids=row["evidence_ids"],
        ))
    filled = EarningsPlan.model_validate({**plan.model_dump(), "drivers": drivers, "generate_drivers": False})
    return project_rows(calculate_earnings(filled, event.as_of, context["evidence"]))


def history_arm(folder, case, arm, driver_version=EARNINGS_DRIVER_VERSION):
    dest = folder / case["id"] / f"{arm}.json"
    if read(dest).get("points"):
        return case["id"], arm, "reused"
    dest.parent.mkdir(exist_ok=True)
    started = perf_counter()
    event, context = case["event"], case["context"]
    adapter = Codex(reasoning_effort=EFFORT, earnings_driver_version=driver_version)
    try:
        if arm == "astra":
            points = direct_points(event, context, adapter)
        else:
            points = project_rows(complete_plan(event.earnings_plan, event.as_of, context, adapter))
        write_json(dest, {"points": points, "elapsed_seconds": round(perf_counter() - started, 2)})
        return case["id"], arm, "ok"
    except (ValueError, AdapterError) as exc:
        write_json(dest, {"error": str(exc), "elapsed_seconds": round(perf_counter() - started, 2)})
        return case["id"], arm, "failed"


def calculator_arm(folder, case):
    root = folder / case["id"]
    direct = read(root / "astra.json")
    if not direct.get("points"):
        return
    started = perf_counter()
    try:
        rows = recalculate_direct(case["event"], case["context"], direct["points"])
        result = {"points": rows, "shares_call_with": "astra",
                  "elapsed_seconds": direct["elapsed_seconds"] + round(perf_counter() - started, 4)}
    except ValueError as exc:
        result = {"error": str(exc), "shares_call_with": "astra"}
    write_json(root / "calculator.json", result)


def blind_records(cases, results):
    review, key = [], {}
    for case in cases:
        case_id = case["id"]
        if case_id not in results:
            continue
        offset = hashlib.sha256(case_id.encode()).digest()[0] % len(ARMS)
        order = ARMS[offset:] + ARMS[:offset]
        key[case_id] = dict(zip(("A", "B", "C"), order))
        review.append({
            "case": case_id, "as_of": case["context"]["as_of"], "event": case["context"]["event_text"],
            "evidence": case["context"]["evidence"],
            "candidates": {label: results[case_id][arm]["points"] for label, arm in key[case_id].items()},
            "review": {label: {"major_error": None, "public_check": None, "seconds": None, "notes": ""}
                       for label in key[case_id]},
        })
    return review, key


def score_rows(observations, *, arms=ARMS):
    scales = {"revenue": Decimal(1_000_000), "gross_margin": Decimal("0.01"),
              "operating_income": Decimal(1_000_000), "eps": Decimal(1)}
    metrics = {}
    for metric, scale in scales.items():
        metrics[metric] = {
            arm: float(mean(abs(Decimal(forecast[metric]) - Decimal(actual[metric]))
                            for candidate, forecast, actual in observations if candidate == arm) / scale)
            for arm in arms if any(candidate == arm for candidate, _, _ in observations)
        }
    return metrics


def historical_export(folder, cases):
    observations, complete, failures = [], {}, []
    for case in cases:
        case_id = case["id"]
        result = {arm: read(folder / case_id / f"{arm}.json") for arm in ARMS}
        missing = [arm for arm in ARMS if not result[arm].get("points")]
        if missing:
            failures.extend({"case": case_id, "arm": arm, "reason": result[arm].get("error", "未執行")} for arm in missing)
            continue
        complete[case_id] = result
        for arm, value in result.items():
            for forecast in value["points"]:
                if forecast["scenario"] == "base":
                    observations.append((arm, forecast, case["actual"][forecast["period_end"]]["values"]))
    metrics = score_rows(observations)
    lines = [
        "# 三組等工作量盈利測試｜歷史回放", "",
        f"已完成 {len(complete)}/{len(cases)} 案、{len(observations) // 3} 季。這批沿用 2019–2024 的已知歷史資料。",
        "三組都交兩季、每季三情境及四項同口徑指標。純 Astra 與計算器沿用同一份 Astra 輸出，"
        "計算器以原基準的稅率、稀釋股數和固定稅後餘額重算 EPS。Harness 以另一次相同模型額度生成"
        "三情境驅動，再走正式財務計算。各組使用相同證據且停用搜尋。",
        "平均絕對誤差只評基準情境，愈低愈好。模型可能知道歷史結果。", "",
        "| 指標 | 純 Astra | Astra＋計算器 | Harness |", "|---|---:|---:|---:|",
    ]
    labels = ("營收（百萬 USD）", "毛利率（百分點）", "營業利益（百萬 USD）", "稀釋 EPS（USD）")
    for label, values in zip(labels, metrics.values()):
        lines.append(f"| {label} | " + " | ".join(f"{values[arm]:.3f}" if arm in values else "—" for arm in ARMS) + " |")
    lines += ["", "人工覆核包另存，尚未納入實際研究員評分。"]
    if failures:
        lines += ["", "## 未完成", ""] + [f"- {item['case']} {item['arm']} {item['reason']}" for item in failures]
    (folder / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(folder / "summary.json", {"planned": len(cases), "paired": len(complete),
                                        "quarters": len(observations) // 3, "metrics": metrics, "failures": failures})
    review, key = blind_records(cases, complete)
    write_json(folder / "blind-review.json", review)
    write_json(folder / "review-key.json", key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sec-dir", type=Path, default=Path("output/earnings-benchmark/sec"))
    parser.add_argument("--output", type=Path, default=Path("output/earnings-equal-replay"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--driver-version", type=int, choices=(3, EARNINGS_DRIVER_VERSION), default=EARNINGS_DRIVER_VERSION)
    args = parser.parse_args()
    cases = load_cases(args.sec_dir)
    version = {"version": VERSION, "model": MODEL, "effort": EFFORT, "driver_prompt_version": args.driver_version,
               "sec_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(args.sec_dir.glob("*.json"))}}
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = args.output / "manifest.json"
    if manifest.exists() and read(manifest) != version:
        parser.error("輸入或版本已變更，請使用新輸出目錄")
    write_json(manifest, version)
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(history_arm, args.output, case, arm, args.driver_version)
                for case in cases for arm in ("astra", "harness")]
        for job in as_completed(jobs):
            print(*job.result(), flush=True)
    for case in cases:
        calculator_arm(args.output, case)
    historical_export(args.output, cases)


if __name__ == "__main__":
    main()
