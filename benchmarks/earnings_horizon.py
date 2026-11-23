"""Evaluate the second-quarter revenue bridge on frozen inputs and reserved issuers."""

import argparse
import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from hashlib import sha256
import json
import os
from decimal import Decimal
from pathlib import Path
from random import Random
from statistics import mean, median

from research_app.adapters import Codex, EARNINGS_DRIVER_VERSION
from research_app.earnings import METRICS, issuer_guidance
from research_app.research import build_context
from research_app.revenue import anchors, bridge_forecast

from .earnings_calibration import prepare, score_group
from .earnings_cases import TICKERS, load_cases
from .earnings_equal import direct_points, history_arm, recalculate_direct
from .earnings_horizon_inputs import CIKS, add_revenue_history, revenue_history
from .earnings_inputs import add_eps_assumptions, add_guidance, financial_history, load_guidance
from .earnings_pilot import read
from .public_pilot import EFFORT, MODEL, write_json

HOLDOUT = {"AMD": (2025, 2026), "INTC": (2025, 2026), "MU": (2025,), "QCOM": (2025,),
           "TXN": (2025, 2026), "NVDA": (2022, 2023, 2025)}
METHODS = ("latest_run_rate", "seasonal_prior", "guided_seasonal", "guided_absolute", "year_on_year")
ARM_NAMES = {"astra": "純 Astra", "harness": "現版 Harness", "new": "新版 Harness"}
PRIMARY_TARGET = Decimal("0.05")
DEVELOPMENT_CASES = Path(__file__).with_name("earnings_guidance.csv")
HOLDOUT_GUIDE = Path(__file__).with_name("earnings_guidance_horizon.csv")


def freeze_json(path, value):
    normalized = json.loads(json.dumps(value, ensure_ascii=False))
    if path.exists():
        if read(path) != normalized:
            raise ValueError(f"已封存的輸入不符：{path}")
    else:
        write_json(path, normalized)


def enrich(case, history, method):
    ticker = case["id"].split("-", 1)[0]
    event = add_revenue_history(case["event"], ticker, history[ticker], (2, 3), method)
    return {**case, "event": event, "context": build_context(event)}


def far_options(case):
    plan = case["event"].earnings_plan
    quarter = min(row.period_end for row in plan.quarters)
    guide = issuer_guidance(plan).get((quarter, "revenue"))
    return anchors(plan.revenue_bridge, guide), guide


def development_scores(cases):
    errors = defaultdict(list)
    for case in cases:
        actual = Decimal(case["actual"][max(case["actual"])]["values"]["revenue"])
        options, _ = far_options(case)
        for method in METHODS:
            value, _ = options.get(method, options.get("seasonal_prior", options["latest_run_rate"]))
            errors[method].append(abs(value - actual) / 1_000_000)
    return {method: float(mean(values)) for method, values in errors.items()}


def rolling_development(cases):
    order = sorted(cases, key=lambda item: (item["event"].as_of, item["id"]))
    rows = []
    for case in order:
        eligible = [prior for prior in order if prior["event"].as_of < case["event"].as_of
                    and all(datetime.fromisoformat(actual["document"]["published_at"]) < case["event"].as_of
                            for actual in prior["actual"].values())]
        if len(eligible) < 5:
            continue
        scores = development_scores(eligible)
        method = min(scores, key=scores.get)
        options, _ = far_options(case)
        prediction, _ = options.get(method, options.get("seasonal_prior", options["latest_run_rate"]))
        actual = Decimal(case["actual"][max(case["actual"])]["values"]["revenue"])
        rows.append({"case": case["id"], "method": method, "training_cases": [prior["id"] for prior in eligible],
                     "absolute_error_millions": float(abs(prediction - actual) / 1_000_000)})
    return rows


def holdout_cases(sec_dir, history, method):
    eps_history = financial_history(sec_dir, HOLDOUT)
    guidance = load_guidance(HOLDOUT_GUIDE)
    for case in load_cases(sec_dir, HOLDOUT):
        ticker = case["id"].split("-", 1)[0]
        rows = guidance[case["id"]]
        event = add_eps_assumptions(add_guidance(case["event"], rows), ticker, eps_history, rows, cik=CIKS[ticker])
        yield enrich({**case, "event": event}, history, method)


def forecasts(folder, case):
    old = {arm: read(folder / case["id"] / f"{arm}.json").get("points") for arm in ("astra", "harness")}
    if not all(old.values()):
        return None
    value = case["event"]
    # The v4 output already includes first-quarter guidance calibration.
    plan = value.earnings_plan.model_copy(update={"calibrate_guidance": False})
    event = value.model_copy(update={"earnings_plan": plan})
    return {**old, "new": recalculate_direct(event, case["context"], old["harness"])}


def active_case(case):
    event = case["event"]
    old = event.model_copy(update={"earnings_plan": event.earnings_plan.model_copy(update={"revenue_bridge": None})})
    return {**case, "event": old}


def revenue_row(result, arm, period):
    return next(Decimal(row["revenue"]) for row in result[arm]
                if row["period_end"] == period and row["scenario"] == "base")


def inspect_case(case, result):
    period = max(case["actual"])
    actual = Decimal(case["actual"][period]["values"]["revenue"])
    options, guide = far_options(case)
    bridge = case["event"].earnings_plan.revenue_bridge
    _, audit = bridge_forecast(bridge, guide)
    predictions = {arm: revenue_row(result, arm, period) for arm in result}
    return {
        "case": case["id"], "period": period, "actual": str(actual),
        "forecasts": {arm: str(number) for arm, number in predictions.items()},
        "anchor_errors_millions": {name: float(abs(amount - actual) / 1_000_000) for name, (amount, _) in options.items()},
        "paired_delta_millions": float((abs(predictions["new"] - actual) - abs(predictions["astra"] - actual)) / 1_000_000),
        "bridge": audit,
        "adjustment_ablation": [{"id": item.id, "without": str(predictions["new"] - item.value),
                                 "change_in_error": str(abs(predictions["new"] - item.value - actual)
                                                        - abs(predictions["new"] - actual))}
                                for item in bridge.adjustments],
    }


def development_diagnostics(output, cases, archived):
    rows = []
    for case in cases:
        period = max(case["actual"])
        actual = Decimal(case["actual"][period]["values"]["revenue"])
        options, guide = far_options(case)
        if guide is None:
            continue
        midpoint = (guide.low + guide.high) / 2
        old = {arm: read(archived / case["id"] / f"{arm}.json").get("points") for arm in ("astra", "harness")}
        forecasts = {arm: revenue_row(old, arm, period) for arm, points in old.items() if points}
        change = (actual - midpoint) / midpoint
        regime = "高於指引尺度至少一成" if change >= Decimal("0.10") else (
            "低於指引尺度至少一成" if change <= Decimal("-0.10") else "接近指引尺度"
        )
        rows.append({"case": case["id"], "period": period, "actual": str(actual), "t1_guidance_midpoint": str(midpoint),
                     "pattern": regime, "forecast_direction": {
                         arm: "低估" if value < actual else "高估" if value > actual else "相同"
                         for arm, value in forecasts.items()},
                     "predictions": {arm: str(value) for arm, value in forecasts.items()},
                     "signed_errors": {arm: str(value - actual) for arm, value in forecasts.items()},
                     "candidate_errors": {method: str(value - actual) for method, (value, _) in options.items()},
                     "outcome_source": case["actual"][period]["document"]["source"]})
    write_json(output / "development-diagnostics.json", rows)


def review_metrics(form, key):
    if not form.exists():
        return {"dual_review_cases": 0, "arms": {}}
    assessments = defaultdict(dict)
    fields = ("major_errors", "citations_supported", "citations_reviewed", "verifiable_checks", "total_checks", "revision_seconds")
    with form.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            if not any(row.get(field) for field in (*fields, "decision")):
                continue
            case, candidate, reviewer = row["case"], row["candidate"], row["reviewer"]
            if candidate not in key.get(case, {}) or reviewer not in {"1", "2"} or not row.get("decision"):
                raise ValueError("盲評表的案例、匿名候選、研究員或決定無效")
            content = tuple(int(row[field]) for field in fields)
            errors, cites, claims, valid, checks, seconds = content
            if min(content) < 0 or cites > claims or valid > checks or not seconds:
                raise ValueError("盲評數量或覆核時間無效")
            if (candidate, reviewer) in assessments[case]:
                raise ValueError("同一研究員和候選的盲評重複")
            assessments[case][candidate, reviewer] = content
    complete = {case: rows for case, rows in assessments.items() if len(rows) == len(ARM_NAMES) * 2}
    result = defaultdict(list)
    for case, rows in complete.items():
        for (candidate, _), content in rows.items():
            result[key[case][candidate]].append(content)
    def ratio(rows, hits, total):
        den = sum(row[total] for row in rows)
        return sum(row[hits] for row in rows) / den if den else None
    return {"dual_review_cases": len(complete),
            "arms": {arm: {"major_error_rate": mean(row[0] > 0 for row in rows),
                            "citation_support": ratio(rows, 1, 2), "check_verifiability": ratio(rows, 3, 4),
                            "median_revision_seconds": median(row[5] for row in rows)}
                     for arm, rows in result.items()}}


def blind_review(output, cases, results):
    rng = Random(20261123)
    payload, key = [], {}
    for case in cases:
        if case["id"] not in results:
            continue
        arms = list(ARM_NAMES)
        rng.shuffle(arms)
        pairs = dict(zip(("A", "B", "C"), arms))
        key[case["id"]] = pairs
        ids = {ref for rows in results[case["id"]].values() for row in rows for ref in row["evidence_ids"]}
        payload.append({"case": case["id"], "event": case["context"]["event_text"],
                        "as_of": case["context"]["as_of"],
                        "source_packet": [item for item in case["context"]["evidence"] if item["id"] in ids],
                        "candidates": {label: results[case["id"]][variant] for label, variant in pairs.items()}})
    write_json(output / "blind-review.json", payload)
    write_json(output / "review-key.json", key)
    form = output / "review-form.csv"
    if not form.exists():
        with form.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream)
            writer.writerow(("case", "candidate", "reviewer", "major_errors", "citations_supported", "citations_reviewed",
                             "verifiable_checks", "total_checks", "revision_seconds", "decision", "notes"))
            writer.writerows((case_id, label, reviewer, "", "", "", "", "", "", "", "")
                             for case_id, pairs in key.items() for label in pairs for reviewer in (1, 2))


def export(output, development, holdout, method, scores, results, errors):
    observed = [inspect_case(case, results[case["id"]]) for case in holdout if case["id"] in results]
    named = list(ARM_NAMES)
    by_horizon = {str(step): score_group(holdout, results, named, lambda case: [sorted(case["actual"])[step - 1]])
                  for step in (1, 2)}
    groups = {"later_known_issuers": [case for case in holdout if not case["id"].startswith("NVDA-")],
              "unseen_issuer_nvda": [case for case in holdout if case["id"].startswith("NVDA-")]}
    by_group = {name: score_group(group, results, named, lambda case: [max(case["actual"])])
                for name, group in groups.items()}
    issuers = sorted({row["case"].split("-", 1)[0] for row in observed})
    omission = {issuer: mean(row["paired_delta_millions"] for row in observed
                             if not row["case"].startswith(issuer + "-")) for issuer in issuers} if len(issuers) > 1 else {}
    far = by_horizon["2"]["revenue"]
    effect = (far["astra"] - far["new"]) / far["astra"] if far.get("astra") else None
    passed = len(results) == len(holdout) and effect is not None and effect >= float(PRIMARY_TARGET)
    if "blind-review.json" not in os.listdir(output) or len(results) == len(holdout):
        blind_review(output, holdout, results)
    review = review_metrics(output / "review-form.csv", read(output / "review-key.json"))
    write_json(output / "summary.json", {"development_cases": len(development), "holdout_cases": len(holdout),
                                         "paired": len(results), "selected_method": method, "development_mae": scores,
                                         "horizon_mae": by_horizon, "holdout_group_mae": by_group,
                                         "primary_target_met": passed, "relative_improvement": effect, "failures": errors,
                                         "human_review": review, "omit_each_issuer_mae_delta_millions": omission})
    write_json(output / "holdout-bridges.json", observed)
    lines = ["# 第二個預測季營收橋接｜驗收紀錄", "",
             f"使用 {len(development)} 個已知案例選擇季節性規則。驗收保留 {len(holdout)} 個案例，完成 {len(results)} 組配對。",
             "保留集包含較晚期間和未供選模的 NVIDIA。Astra 與現版均取得相同的截止時點原始證據。"
             "新版沿用現版草擬的財務假設，只修改第二個預測季的營收並重算報表。", "",
             "## 開發集選模", "",
             "| 基準 | T+2 營收平均絕對誤差（百萬美元） |", "|---|---:|"]
    lines.extend(f"| `{label}` | {value:.2f} |" for label, value in sorted(scores.items(), key=lambda item: item[1]))
    lines += ["", f"選定 `{method}`。取得第一個預測季指引中點後，加計截至研究時點可取得的最近三組同季節轉換金額中位數。", ""]
    for step, values in by_horizon.items():
        lines += [f"## 保留集 T+{step}", "", "| 指標 | 純 Astra | 現版 Harness | 新版 Harness |", "|---|---:|---:|---:|"]
        for metric, display in METRICS.items():
            units = {"revenue": "百萬美元", "operating_income": "百萬美元", "gross_margin": "百分點", "eps": "美元／股"}
            cells = [f"{values[metric][arm]:.3f}" if arm in values[metric] else "—" for arm in named]
            lines.append(f"| {display}（{units[metric]}） | " + " | ".join(cells) + " |")
        lines.append("")
    if effect is not None:
        lines.append(f"T+2 營收相對純 Astra 的改善為 {effect:+.1%}。預先訂定的 5% 門檻{'已達成' if passed else '未達成'}。")
    if observed:
        benchmark = mean(row["anchor_errors_millions"][method] for row in observed if method in row["anchor_errors_millions"])
        lines.extend(["", f"單獨使用選定數值基準，T+2 營收 MAE 為 {benchmark:.2f} 百萬美元。"])
    if omission:
        lines.extend(["", "每次排除一家公司時，新版減 Astra 的 T+2 營收誤差差額介於 "
                      f"{min(omission.values()):+.1f} 至 {max(omission.values()):+.1f} 百萬美元。"])
    if observed:
        worst = max(observed, key=lambda row: row["paired_delta_millions"])
        case = next(item for item in holdout if item["id"] == worst["case"])
        actual_source = case["actual"][worst["period"]]["document"]["source"]
        actual = Decimal(worst["actual"]) / 1_000_000
        estimate = Decimal(worst["forecasts"]["new"]) / 1_000_000
        lines.extend(["", f"最大配對落差是 {case['id']}。新版估 {estimate:,.0f} 百萬美元，實績為 {actual:,.0f} 百萬美元。"
                      f"這個案例中，近期指引加固定季節差額低估了後續增幅。[實績披露]({actual_source})"])
    search = read(output / "search" / "summary.json")
    if search.get("paired"):
        lines += ["", "## 相同搜尋額度", "",
                  f"{search['paired']} 案配對完成，其中 {search['in_budget']} 案兩組均遵守搜尋額度。"]
        revenue = search["t2_mae_in_budget"]["revenue"]
        if revenue:
            lines.append(f"同額度樣本的 T+2 營收誤差為 Astra {revenue['astra']:,.0f}，"
                         f"新版 Harness {revenue['harness']:,.0f} 百萬美元。")
    lines += ["", "附檔保留各案基準、來源、逐項調整的移除比較及盲評入口。歷史資料可能在模型訓練中已出現。",
              f"已有 {review['dual_review_cases']} 案完成兩位分析師對三組候選的覆核。前瞻實績另依封存隊列追蹤。"]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sec-dir", type=Path, default=Path("output/earnings-benchmark/sec"))
    parser.add_argument("--output", type=Path, default=Path("output/earnings-horizon"))
    parser.add_argument("--historical-predictions", type=Path, default=Path("output/earnings-calibration/fresh"))
    parser.add_argument("--run-model", action="store_true")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    history = revenue_history(args.sec_dir, CIKS)
    development = [enrich(case, history, "guided_absolute") for case in prepare(args.sec_dir, DEVELOPMENT_CASES)]
    scores = development_scores(development)
    method = min(scores, key=scores.get)
    development_diagnostics(output, development, args.historical_predictions)
    write_json(output / "development-rolling.json", rolling_development(development))
    protocol = {"selection_stage": "2019–2024 development", "holdout": HOLDOUT, "score": "T+2 revenue MAE",
                "selection_rule": "lowest development MAE in five anchors", "primary_relative_target": str(PRIMARY_TARGET),
                "method": method, "model": MODEL, "effort": EFFORT, "driver_version": EARNINGS_DRIVER_VERSION,
                "guidance_sha256": sha256(HOLDOUT_GUIDE.read_bytes()).hexdigest()}
    freeze_json(output / "protocol.json", protocol)
    holdout = list(holdout_cases(args.sec_dir, history, method))
    freeze_json(output / "inputs.json", {case["id"]: case["event"].model_dump(mode="json") for case in holdout})
    persisted = output / "holdout"
    persisted.mkdir(exist_ok=True)
    if args.run_model:
        os.environ["RESEARCH_CODEX_MODEL"] = MODEL
        with ThreadPoolExecutor(max_workers=6) as pool:
            jobs = [pool.submit(history_arm, persisted, active_case(case), arm)
                    for case in holdout for arm in ("astra", "harness")]
            for job in jobs:
                print(*job.result(), flush=True)
    results, errors = {}, []
    for case in holdout:
        if result := forecasts(persisted, case):
            results[case["id"]] = result
        else:
            errors.append(case["id"])
    if results:
        freeze_json(output / "outcomes.json", {case["id"]: case["actual"] for case in holdout})
        write_json(output / "points.json", results)
    export(output, development, holdout, method, scores, results, errors)


if __name__ == "__main__":
    main()
