"""Compare two-quarter earnings forecasts on identical SEC filing snapshots."""

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
from statistics import mean, median
from time import perf_counter

from pydantic import Field, model_validator

from benchmarks.earnings_cases import TICKERS, load_cases
from benchmarks.public_pilot import EFFORT, MODEL, write_json
from research_app.adapters import AdapterError, Codex, EARNINGS_DRIVER_VERSION
from research_app.earnings import METRICS, available_evidence, complete_plan, operating_numbers
from research_app.schema import DecimalText, Nonempty, Schema

ARMS = ("harness", "astra")
DIRECT = (
    "Forecast the consolidated US GAAP revenue, gross margin, operating income and diluted EPS "
    "for the two listed fiscal quarter endings. Use the supplied filing snapshot and same seasonal baseline. "
    "Give your best single estimates as of the cutoff. Use plain decimal strings without separators. "
    "Amounts are unscaled USD and gross margin is a fraction. "
    "Use exact evidence IDs for your drivers and explain the largest assumption in the rationale. "
    "Return the two requested quarter dates. Treat future data as unknown."
)


class QuarterForecast(Schema):
    period_end: date
    revenue: DecimalText
    gross_margin: DecimalText
    operating_income: DecimalText
    eps: DecimalText
    evidence_ids: list[Nonempty] = Field(min_length=1)
    rationale: Nonempty

    @model_validator(mode="after")
    def check_ranges(self):
        if Decimal(self.revenue) < 0 or Decimal(self.gross_margin) > 1:
            raise ValueError("預測營收或毛利率超出可用範圍")
        return self


class DirectForecast(Schema):
    quarters: list[QuarterForecast]


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def run_arm(case, arm, folder):
    destination = folder / case["id"] / f"{arm}.json"
    destination.parent.mkdir(exist_ok=True)
    previous = read(destination)
    if "forecasts" in previous:
        return case["id"], arm, "reused"
    event, context = case["event"], case["context"]
    plan = event.earnings_plan
    adapter = Codex(reasoning_effort=EFFORT)
    started = perf_counter()
    evidence = context["evidence"]
    try:
        if arm == "harness":
            report = complete_plan(plan, event.as_of, context, adapter)
            forecasts = {row["period_end"]: row["scenarios"]["base"]["revised"] for row in report["quarters"]}
            result = {"forecasts": forecasts, "revision": report}
        else:
            prediction = adapter._generate(DirectForecast, DIRECT, {
                "target": context["target"], "event": context["event_text"], "as_of": context["as_of"],
                "evidence": evidence, "baseline": plan.model_dump(mode="json"),
            })
            periods = {row.period_end for row in prediction.quarters}
            if len(prediction.quarters) != 2 or periods != {quarter.period_end for quarter in plan.quarters}:
                raise ValueError("模型預測期別與指定季度不符")
            for row in prediction.quarters:
                available_evidence(row.evidence_ids, {item["id"]: item for item in evidence}, event.as_of)
            result = {"forecasts": {row.period_end.isoformat(): row.model_dump(mode="json")
                                    for row in prediction.quarters}}
        label = "ok"
    except (ValueError, AdapterError) as exc:
        result = {"error": str(exc)}
        label = "failed"
    if previous:
        result["previous_failures"] = [*previous.get("previous_failures", []), previous.get("error")]
    write_json(destination, {**result, "elapsed_seconds": round(perf_counter() - started, 2)})
    return case["id"], arm, label


def errors(forecast, actual):
    return {key: abs(Decimal(forecast[key]) - Decimal(actual[key])) for key in METRICS}


def write_review_packet(folder, review):
    lines = [
        "# 盈利預測匿名覆核包", "",
        "逐案使用同一份事件當日可得來源。先核對申報證據與期別，再看候選 A、B。"
        "逐份在 CSV 填寫有無重大錯誤、是否有可驗證路徑、所花秒數與評語。",
        "重大錯誤包含數字、會計口徑、事件時點與核心引文錯誤。可驗證路徑須明定原公司、期別和公開來源。"
        "所有未來實績與方法標籤存於分開的資料。", "",
    ]
    sheet = []
    for record in review:
        lines += [f"## {record['case']}", "", record["event"], "", f"截止時點 {record['as_of']}。", ""]
        for source in record["evidence"]:
            lines += [f"- {source['quote']} [{source['id']}]({source['source']})"]
        for label, item in record["candidates"].items():
            lines += ["", f"### {label}", "", "| 季度 | 營收 USD 百萬 | 毛利率 | 營業利益 USD 百萬 | EPS USD |",
                      "|---|---:|---:|---:|---:|"]
            for period, row in item["forecasts"].items():
                lines.append(f"| {period} | {Decimal(row['revenue']) / 1_000_000:.1f} | "
                             f"{Decimal(row['gross_margin']):.2%} | "
                             f"{Decimal(row['operating_income']) / 1_000_000:.1f} | {Decimal(row['eps']):.2f} |")
            lines.append("")
            for period, rationale in item["rationales"].items():
                refs = "、".join(item["evidence_ids"][period])
                lines.append(f"- {period}　{rationale}（{refs}）")
            sheet.append([record["case"], label, "", "", "", ""])
        lines.append("")
    (folder / "blind-review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (folder / "review-form.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case", "candidate", "major_error_0_or_1", "public_check_0_or_1", "review_seconds", "notes"])
        writer.writerows(sheet)


def export(cases, folder):
    rows = []
    failures = []
    invalid_opex = dict.fromkeys(ARMS, 0)
    for case in cases:
        result = {arm: read(folder / case["id"] / f"{arm}.json") for arm in ARMS}
        for arm in ARMS:
            if "forecasts" not in result[arm]:
                failures.append({"id": case["id"], "arm": arm, "reason": result[arm].get("error", "未執行")})
        if not all("forecasts" in result[arm] for arm in ARMS):
            continue
        event = case["event"]
        baselines = {quarter.period_end.isoformat(): operating_numbers(quarter) for quarter in event.earnings_plan.quarters}
        for period, actual in case["actual"].items():
            forecasts = {arm: result[arm]["forecasts"][period] for arm in ARMS}
            for arm, forecast in forecasts.items():
                gross = Decimal(forecast["revenue"]) * Decimal(forecast["gross_margin"])
                invalid_opex[arm] += Decimal(forecast["operating_income"]) > gross
            rows.append({
                "case": case["id"], "period": period, "actual": actual["values"],
                "actual_source": actual["document"]["source"],
                "errors": {arm: errors(forecast, actual["values"]) for arm, forecast in forecasts.items()}
                          | {"seasonal": errors(baselines[period], actual["values"])},
            })
    totals = {}
    scales = {"revenue": Decimal("1000000"), "gross_margin": Decimal("0.01"),
              "operating_income": Decimal("1000000"), "eps": Decimal(1)}
    labels = {"revenue": "營收（百萬美元）", "gross_margin": "毛利率（百分點）",
              "operating_income": "營業利益（百萬美元）", "eps": "稀釋 EPS（美元）"}
    report = [
        "# 半導體盈利預測修正｜30 案 SEC 回放", "",
        f"完成 {len(rows) // 2}/{len(cases)} 組配對及 {len(rows)} 個未來季度。"
        "五家同產業公司，2019 至 2024 年每年一件 Q1 申報，前一年同季為季節基準。",
        "兩組共用相同的申報資料、模型、推理強度與一次 CLI 呼叫額度，停用搜尋。"
        "Harness 用該呼叫產生三種情境並由程式計算，採基準情境評分。"
        "純 Astra 用同一呼叫額度直接產生基準預測。",
        "實績只用於核對。SEC Company Facts 期間資料連回首次符合條件的 10-Q accession，"
        "申報日期按 UTC 日末作歷史可得代理。這組衡量整體財務指標與計算，未提供歷史市場共識。",
        "美分和百分點近似程度保留於來源。所有數值為平均絕對誤差，愈低愈好。", "",
        "| 指標 | 季節基準 | 純 Astra | Harness | Harness 較小／和／較大 |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, scale in scales.items():
        if not rows:
            break
        averages = {arm: float(mean(row["errors"][arm][key] for row in rows) / scale)
                    for arm in ("seasonal", "astra", "harness")}
        differences = [row["errors"]["harness"][key] - row["errors"]["astra"][key] for row in rows]
        outcomes = [sum(delta < 0 for delta in differences), differences.count(0),
                    sum(delta > 0 for delta in differences)]
        totals[key] = {"mae": averages, "head_to_head": outcomes}
        report.append(f"| {labels[key]} | {averages['seasonal']:.3f} | {averages['astra']:.3f} | "
                      f"{averages['harness']:.3f} | {'／'.join(map(str, outcomes))} |")
    seconds = {}
    paired_ids = {row["case"] for row in rows}
    for arm in ARMS:
        measured = [read(folder / key / f"{arm}.json")["elapsed_seconds"] for key in paired_ids]
        seconds[arm] = median(measured) if measured else None
    if paired_ids:
        report += ["", f"生成耗時中位數為純 Astra {seconds['astra']:.1f} 秒，Harness {seconds['harness']:.1f} 秒。"]
        report += [
            f"已取得 {len(rows)} 個同口徑的季度實績。"
            f"推算營業費用為負的機械檢查，純 Astra 為 {invalid_opex['astra']} 季，"
            f"Harness 為 {invalid_opex['harness']} 季。",
        ]
    report += ["", "研究員覆核包隱去方法名稱與後續實績。人工評分及覆核時間等候實際研究員填寫。", ""]
    if failures:
        report += ["## 未完成", ""] + [f"- {item['id']} {item['arm']} {item['reason']}" for item in failures]
    (folder / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    write_json(folder / "summary.json", {"planned": len(cases), "paired": len(paired_ids), "quarters": len(rows),
                                        "metrics": totals, "median_seconds": seconds, "failures": failures,
                                        "negative_implied_opex": invalid_opex, "human_reviews": 0})
    write_json(folder / "quarter-results.json", [
        {**row, "errors": {arm: {key: str(error) for key, error in errors.items()}
                           for arm, errors in row["errors"].items()}} for row in rows
    ])
    review = []
    ordering = {}
    for case in cases:
        if case["id"] not in paired_ids:
            continue
        arms = ARMS if hashlib.sha256(case["id"].encode()).digest()[0] % 2 else ARMS[::-1]
        ordering[case["id"]] = dict(zip(("A", "B"), arms))
        candidates = {}
        for label, arm in ordering[case["id"]].items():
            result = read(folder / case["id"] / f"{arm}.json")
            drafts = ({row["period_end"]: row for row in result["revision"]["inputs"]["drivers"]
                       if row["scenario"] == "base"} if arm == "harness" else result["forecasts"])
            candidates[label] = {
                "forecasts": {period: {key: values[key] for key in METRICS}
                              for period, values in result["forecasts"].items()},
                "rationales": {period: row["rationale"] for period, row in drafts.items()},
                "evidence_ids": {period: row["evidence_ids"] for period, row in drafts.items()},
            }
        review.append({
            "case": case["id"], "event": case["event"].event_text,
            "as_of": case["event"].as_of.isoformat(), "evidence": case["context"]["evidence"],
            "candidates": candidates,
            "review": {"preferred": None, "critical_errors": None, "public_checks": None, "seconds": None},
        })
    write_json(folder / "blind-review.json", review)
    write_json(folder / "review-key.json", ordering)
    write_review_packet(folder, review)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=Path("output/earnings-benchmark"), type=Path)
    parser.add_argument("--sec-dir", type=Path, help="Optional alternate folder with frozen SEC inputs.")
    parser.add_argument("--case", action="append")
    parser.add_argument("--workers", default=8, type=int)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    folder = args.output
    source = args.sec_dir or folder / "sec"
    cases = load_cases(source)
    selected = set(args.case or [case["id"] for case in cases])
    if args.workers < 1 or selected - {case["id"] for case in cases}:
        parser.error("使用已知案例 ID 及正整數 workers")
    spec = {
        "model": MODEL, "reasoning_effort": EFFORT,
        "driver_prompt_version": EARNINGS_DRIVER_VERSION,
        "sources": {ticker: hashlib.sha256((source / f"{ticker}.json").read_bytes()).hexdigest()
                    for ticker in TICKERS},
        "case_ids": [case["id"] for case in cases],
    }
    manifest = folder / "manifest.json"
    if manifest.exists() and read(manifest) != spec:
        parser.error("案例輸入已改變，請使用新的輸出資料夾")
    folder.mkdir(parents=True, exist_ok=True)
    write_json(manifest, spec)
    if args.prepare_only:
        print(f"Prepared {len(cases)} point-in-time cases")
        return
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(run_arm, case, arm, folder) for case in cases if case["id"] in selected for arm in ARMS]
        for job in as_completed(jobs):
            print(*job.result(), flush=True)
    export(cases, folder)
    if any("forecasts" not in read(folder / key / f"{arm}.json") for key in selected for arm in ARMS):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
