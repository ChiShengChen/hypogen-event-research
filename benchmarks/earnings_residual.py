"""Frozen T+2 residual challengers against current Harness and pure Astra."""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
from random import Random
from statistics import mean, median
from urllib.parse import parse_qsl, urlencode, urlsplit

from research_app.adapters import EARNINGS_DRIVER_VERSION
from research_app.earnings import METRICS, calculate_earnings
from research_app.revenue import RESIDUAL_CAP, RESIDUAL_GAP_WEIGHT, RESIDUAL_MIN_CHANGE, RESIDUAL_STEP_RETENTION
from research_app.schema import EarningsPlan, EstimateDriver

from .earnings_equal import history_arm, project_rows
from .earnings_horizon import active_case, freeze_json
from .earnings_pilot import read
from .public_pilot import EFFORT, MODEL, write_json

ARMS = ("astra", "harness", "residual_a", "residual_b")
CHALLENGERS = ARMS[2:]
NAMES = {"astra": "純 Astra", "harness": "現版 Harness", "residual_a": "A：衝擊延續", "residual_b": "B：延續與分部驅動"}
THRESHOLDS = {
    "minimum_improvement_vs_harness": Decimal("0.05"),
    "maximum_eps_harm_vs_harness": Decimal("0.02"),
    "maximum_quiet_revenue_harm_vs_harness": Decimal("0.02"),
    "materiality_vs_frozen_harness": Decimal("0.10"),
}
MILLION = Decimal(1_000_000)
BASELINE = Path("output/earnings-calibration/fresh")
TURN_REPLAY = Path("output/earnings-turns")
REVIEW_FIELDS = ("major_errors", "citations_supported", "citations_reviewed",
                 "verifiable_checks", "total_checks", "revision_seconds")


def digest(value):
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def validate_case(case):
    event = case["event"]
    if not case.get("accession") or not event.earnings_plan.revenue_bridge:
        raise ValueError(f"{case['id']} 缺少原始申報或歷史資料")
    if {q.period_end.isoformat() for q in event.earnings_plan.quarters} != set(case["actual"]):
        raise ValueError(f"{case['id']} 的實績期別不符")
    for item in case["context"]["evidence"]:
        if max(datetime.fromisoformat(item[key]) for key in ("published_at", "obtained_at")) > event.as_of:
            raise ValueError(f"{case['id']} 的模型資料包含截止時點之後的證據")
    for period, outcome in case["actual"].items():
        when = datetime.fromisoformat(outcome["document"]["published_at"])
        if when <= event.as_of or when.date().isoformat() < period:
            raise ValueError(f"{case['id']} 的實績公開時點不符")


def dossiers(folder, cases):
    ordered = sorted(cases, key=lambda case: (case["event"].as_of, case["id"]))
    if len({case["accession"] for case in ordered}) != len(ordered):
        raise ValueError("保留集事件重複")
    packets = {}
    for case in ordered:
        validate_case(case)
        packets[case["id"]] = {"event": case["event"].model_dump(mode="json"),
                               "accession": case["accession"],
                               "driver_inputs": case.get("driver_inputs", []),
                               "model_evidence_sha256": digest(case["context"]["evidence"])}
    protocol = {
        "version": 1,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "driver_prompt_version": EARNINGS_DRIVER_VERSION,
        "arms": ARMS,
        "cases": [case["id"] for case in ordered],
        "input_sha256": digest(packets),
        "primary_metric": "issuer-equal mean absolute T+2 revenue error divided by latest visible consolidated quarterly revenue",
        "direction_labels": "sign of signed T+2 revenue residual scaled by the frozen incumbent forecast, outside materiality band",
        "additional_required_checks": ["improve on pure Astra", "at least one up/down/quiet residual case",
                                       "at least one adjustment", "reduces incumbent error after omitting any issuer"],
        "thresholds": {key: str(value) for key, value in THRESHOLDS.items()},
        "new_holdout_use": "fixed-candidate chronological replay; no fitting, no threshold changes",
        "model_evidence_policy": "same public evidence and prompt budget; no web tools; actuals outside model packets",
    }
    freeze_json(folder / "protocol.json", protocol)
    freeze_json(folder / "inputs.json", packets)
    return ordered


def raw_models(folder, cases, workers):
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [pool.submit(history_arm, folder, active_case(case), arm)
                for case in cases for arm in ARMS[:2]]
        for job in as_completed(jobs):
            print(*job.result(), flush=True)


def prepare_driver_plan(event, points, bridge):
    """Restore the complete incumbent scenario surface after its guidance calibration."""
    plan = event.earnings_plan
    quarters = {quarter.period_end.isoformat(): quarter for quarter in plan.quarters}
    drivers = []
    for row in points:
        quarter = quarters[row["period_end"]]
        if set(quarter.segment_revenue) != {"consolidated"}:
            raise ValueError("評測只接受合併營收基準")
        revenue, margin, income = (Decimal(row[key]) for key in ("revenue", "gross_margin", "operating_income"))
        drivers.append(EstimateDriver(
            period_end=quarter.period_end, scenario=row["scenario"],
            segment_revenue_delta={"consolidated": revenue - quarter.segment_revenue["consolidated"]},
            shipment_changes={}, gross_margin_delta=margin - quarter.gross_margin,
            opex_delta=(revenue * margin - income - quarter.opex).quantize(Decimal("0.00000001")),
            rationale=row["rationale"], evidence_ids=row["evidence_ids"],
        ))
    return EarningsPlan.model_validate({
        **plan.model_dump(), "generate_drivers": False, "calibrate_guidance": False,
        "revenue_bridge": bridge, "drivers": drivers,
    })


def evaluate_candidate(event, context, incumbent_points, method, residual_inputs=(), *, drop=frozenset()):
    bridge = event.earnings_plan.revenue_bridge.model_dump()
    bridge["method"] = method
    if method == "residual_a":
        bridge.pop("residual_inputs", None)
    elif residual_inputs:
        bridge["residual_inputs"] = [item for item in residual_inputs if item.get("id") not in drop]
    elif drop and "residual_inputs" in bridge:
        bridge["residual_inputs"] = [item for item in bridge["residual_inputs"] if item["id"] not in drop]
    plan = prepare_driver_plan(event, incumbent_points, bridge)
    result = calculate_earnings(plan, event.as_of, context["evidence"])
    audit = result.get("revenue_bridge", {})
    return project_rows(result), audit


def point(rows, period):
    return next(row for row in rows if row["period_end"] == period and row["scenario"] == "base")


def audited_case(case, old, candidates, audits):
    event = case["event"]
    period = max(case["actual"])
    earlier_period = min(case["actual"])
    before = point(old["harness"], period)
    actual = case["actual"][period]["values"]
    earlier_actual = case["actual"][earlier_period]["values"]
    final = {arm: point(rows, period) for arm, rows in {**old, **candidates}.items()}
    revenue = Decimal(actual["revenue"])
    incumbent = Decimal(before["revenue"])
    if incumbent <= 0:
        raise ValueError(f"{case['id']} 的現版營收預測無法用於誤差尺度")
    history = sorted(event.earnings_plan.revenue_bridge.history, key=lambda row: row.period_end)
    scale = history[-1].value
    residual = revenue - incumbent
    relative = residual / incumbent
    material = THRESHOLDS["materiality_vs_frozen_harness"]
    direction = "up" if relative >= material else "down" if relative <= -material else "quiet"
    evidence = {item["id"]: item for item in case["context"]["evidence"]}
    arms = {}
    for arm, forecast in final.items():
        deviation = Decimal(forecast["revenue"]) - revenue
        earnings_loss = abs(Decimal(forecast["eps"]) - Decimal(actual["eps"]))
        delta = Decimal(forecast["revenue"]) - incumbent
        arms[arm] = {
            "forecasts": {metric: forecast[metric] for metric in METRICS},
            "absolute_revenue_error": str(abs(deviation)),
            "scaled_revenue_error": str(abs(deviation) / scale),
            "absolute_eps_error": str(earnings_loss),
            "delta_vs_incumbent": str(delta),
            "loss_delta_vs_incumbent": str(abs(deviation) - abs(residual)),
        }
        if arm in CHALLENGERS:
            audit = audits[arm]
            refs = set(audit.get("anchor_evidence_ids", ())) | set(forecast["evidence_ids"])
            counterfactuals = {"without_full_revision": {"revenue": before["revenue"], "eps": before["eps"],
                                                        "revenue_error_increase": str(abs(residual) - abs(deviation)),
                                                        "eps_error_increase": str(abs(Decimal(before["eps"]) -
                                                                                    Decimal(actual["eps"])) - earnings_loss)}}
            for component in audit.get("residual", {}).get("ablation", ()):
                if "without" not in component:
                    counterfactuals[component["id"]] = component
                    continue
                undisputed = component["without"]
                counterfactuals[component["id"]] = {
                    "revenue": undisputed["revenue"], "eps": undisputed["eps"],
                    "revenue_error_increase": str(abs(Decimal(undisputed["revenue"]) - revenue) - abs(deviation)),
                    "eps_error_increase": str(abs(Decimal(undisputed["eps"]) - Decimal(actual["eps"])) - earnings_loss),
                }
            if arm == "residual_b":
                without_inputs = final["residual_a"]
                counterfactuals["without_all_segment_inputs"] = {
                    "revenue": without_inputs["revenue"], "eps": without_inputs["eps"],
                    "revenue_error_increase": str(abs(Decimal(without_inputs["revenue"]) - revenue) - abs(deviation)),
                    "eps_error_increase": str(abs(Decimal(without_inputs["eps"]) - Decimal(actual["eps"])) - earnings_loss),
                }
            arms[arm].update(audit=audit, counterfactuals=counterfactuals,
                             sources={ref: evidence[ref]["source"] for ref in sorted(refs) if ref in evidence})
    # Candidate evaluation may not change the short horizon's operative numbers.
    short = {arm: point(rows, earlier_period) for arm, rows in {**old, **candidates}.items()}
    for arm in CHALLENGERS:
        if any(abs(Decimal(short[arm][key]) - Decimal(short["harness"][key])) > Decimal("0.000001") for key in METRICS):
            raise ValueError(f"{case['id']} {arm} 改動了第一個預測季")
    return {
        "case": case["id"], "issuer": event.research_target, "cutoff": event.as_of.isoformat(), "period": period,
        "latest_visible_revenue_scale": str(scale), "latest_visible_revenue_date": history[-1].period_end.isoformat(),
        "signed_residual": str(residual), "signed_residual_relative_to_incumbent": str(relative),
        "outcome_group": direction, "prior_actual": earlier_actual,
        "actual": actual, "actual_source": case["actual"][period]["document"]["source"],
        "actual_available_at": case["actual"][period]["document"]["published_at"], "arms": arms,
    }


def average(data, arm, key, *, issuer_equal=False):
    if not data:
        return None
    if not issuer_equal:
        return mean(Decimal(row["arms"][arm][key]) for row in data)
    grouped = defaultdict(list)
    for row in data:
        grouped[row["issuer"]].append(Decimal(row["arms"][arm][key]))
    return mean(mean(values) for values in grouped.values())


def is_adjusted(row, arm):
    return Decimal(row["arms"][arm]["delta_vs_incumbent"]) != 0


def issuer_intervals(rows, issuers):
    if len(issuers) < 2:
        return {}
    samples = {arm: [] for arm in CHALLENGERS}
    for issuer in issuers:
        case_rows = [row for row in rows if row["issuer"] == issuer]
        incumbent = average(case_rows, "harness", "scaled_revenue_error")
        for arm in CHALLENGERS:
            samples[arm].append(average(case_rows, arm, "scaled_revenue_error") - incumbent)
    rng = Random(221110)
    draws = [rng.choices(range(len(issuers)), k=len(issuers)) for _ in range(4000)]
    intervals = {}
    for arm, values in samples.items():
        distribution = sorted(mean(values[i] for i in draw) for draw in draws)
        intervals[arm] = [float(distribution[99]), float(distribution[3899])]
    return intervals


def aggregate(rows, expected):
    quiet = [row for row in rows if row["outcome_group"] == "quiet"]
    counts = Counter(row["outcome_group"] for row in rows)
    scaled = {arm: average(rows, arm, "scaled_revenue_error", issuer_equal=True) for arm in ARMS}
    eps = {arm: average(rows, arm, "absolute_eps_error") for arm in ARMS}
    quiet_old = average(quiet, "harness", "scaled_revenue_error", issuer_equal=True)
    issuers = sorted({row["issuer"] for row in rows})
    omit = {issuer: {arm: average([row for row in rows if row["issuer"] != issuer], arm, "scaled_revenue_error",
                                  issuer_equal=True) for arm in ARMS} for issuer in issuers} if len(issuers) > 1 else {}
    comparison = {}
    for arm in CHALLENGERS:
        adjusted = [row for row in rows if is_adjusted(row, arm)]
        quiet_new = average(quiet, arm, "scaled_revenue_error", issuer_equal=True)
        tests = {
            "full_coverage": len(rows) == expected,
            "all_outcome_groups": all(counts[group] for group in ("up", "down", "quiet")),
            "actual_adjustment": bool(adjusted),
            "incumbent_revenue_edge": scaled[arm] is not None and scaled["harness"] > 0
            and scaled[arm] <= scaled["harness"] * (1 - THRESHOLDS["minimum_improvement_vs_harness"]),
            "strictly_better_than_astra": scaled[arm] is not None and scaled[arm] < scaled["astra"],
            "eps_noninferior": eps[arm] is not None and eps[arm] <= eps["harness"] * (1 + THRESHOLDS["maximum_eps_harm_vs_harness"]),
            "quiet_noninferior": quiet_new is not None and quiet_new <= quiet_old * (1 + THRESHOLDS["maximum_quiet_revenue_harm_vs_harness"]),
            "issuer_omission_robust": bool(omit) and all(results[arm] < results["harness"] for results in omit.values()),
        }
        adjustment_delta = average(adjusted, arm, "loss_delta_vs_incumbent")
        comparison[arm] = {
            "passes_historical_gate": all(tests.values()), "checks": tests, "adjusted_cases": len(adjusted),
            "adjustment_coverage": len(adjusted) / len(rows) if rows else None,
            "correct_direction_cases": sum(
                (Decimal(row["arms"][arm]["delta_vs_incumbent"]) > 0) == (row["outcome_group"] == "up")
                for row in adjusted if row["outcome_group"] in {"up", "down"}
            ),
            "quiet_adjustments": sum(is_adjusted(row, arm) for row in quiet),
            "with_applied_segment_input": sum(any(
                component["kind"] == "segment" and component["status"] == "applied"
                for component in row["arms"][arm]["audit"].get("residual", {}).get("components", ())
            ) for row in rows),
            "adjusted_mean_loss_delta_usd_m": as_float(adjustment_delta / MILLION) if adjustment_delta is not None else None,
            "wins_vs_harness": sum(Decimal(row["arms"][arm]["loss_delta_vs_incumbent"]) < 0 for row in rows),
        }
    return {
        "planned": expected, "paired": len(rows), "issuers": issuers, "outcome_groups": dict(counts),
        "issuer_equal_scaled_revenue_mae": map_float(scaled), "t2_eps_mae": map_float(eps),
        "t2_revenue_mae_usd_m": {arm: as_float(average(rows, arm, "absolute_revenue_error") / MILLION)
                                 if rows else None for arm in ARMS},
        "quiet_issuer_equal_scaled_revenue_mae": {arm: as_float(average(quiet, arm, "scaled_revenue_error", issuer_equal=True))
                                                 for arm in ARMS},
        "omit_issuer_scaled_revenue_mae": {issuer: map_float(values) for issuer, values in omit.items()},
        "issuer_resampled_paired_loss_delta": issuer_intervals(rows, issuers),
        "candidates": comparison,
    }


def as_float(value):
    return float(value) if value is not None else None


def map_float(items):
    return {name: as_float(value) for name, value in items.items()}


def shareable_url(value):
    parts = urlsplit(value)
    query = urlencode([(key, data) for key, data in parse_qsl(parts.query, keep_blank_values=True)
                      if not key.lower().startswith(("utm_", "fbclid"))])
    return parts._replace(netloc=parts.netloc.lower(), query=query, fragment="").geturl()


def review_metrics(form, key):
    entries = defaultdict(dict)
    if form.exists():
        with form.open(newline="", encoding="utf-8-sig") as stream:
            for row in csv.DictReader(stream):
                if not any(row.get(field) for field in (*REVIEW_FIELDS, "decision")):
                    continue
                case, candidate, reviewer = row["case"], row["candidate"], row["reviewer"]
                if candidate not in key.get(case, {}) or reviewer not in {"1", "2"} or not row.get("decision"):
                    raise ValueError("盲評表的案例、候選或研究員無效")
                counts = tuple(int(row[field]) for field in REVIEW_FIELDS)
                row_key = (candidate, reviewer)
                if min(counts) < 0 or counts[1] > counts[2] or counts[3] > counts[4] or not counts[5] or row_key in entries[case]:
                    raise ValueError("盲評表含無效計數、時間或重複項")
                entries[case][row_key] = counts
    complete = {case: rows for case, rows in entries.items() if len(rows) == len(ARMS) * 2}
    by_arm = defaultdict(list)
    for case, rows in complete.items():
        for (candidate, _), value in rows.items():
            by_arm[key[case][candidate]].append(value)

    def ratio(rows, p, q):
        total = sum(row[q] for row in rows)
        return sum(row[p] for row in rows) / total if total else None

    return {"complete_cases": len(complete), "arms": {
        arm: {"major_error_rate": mean(row[0] > 0 for row in values),
              "citation_support": ratio(values, 1, 2), "check_verifiability": ratio(values, 3, 4),
              "median_revision_seconds": median(row[5] for row in values)}
        for arm, values in by_arm.items()
    }}


def blind_pack(output, cases, points):
    payload, key = [], {}
    for case in cases:
        case_id = case["id"]
        if case_id not in points:
            continue
        order = list(ARMS)
        Random(f"hypogen-residual-control-v1/{case_id}").shuffle(order)
        labels = dict(zip("ABCD", order))
        key[case_id] = labels
        refs = {ref for rows in points[case_id].values() for row in rows for ref in row["evidence_ids"]}
        evidence = [{**item, "source": shareable_url(item["source"])}
                    for item in case["context"]["evidence"] if item["id"] in refs]
        payload.append({"case": case_id, "as_of": case["context"]["as_of"], "event": case["context"]["event_text"],
                        "evidence": evidence, "candidates": {label: points[case_id][arm] for label, arm in labels.items()}})
    write_json(output / "blind-review.json", payload)
    write_json(output / "review-key.json", key)
    path = output / "review-form.csv"
    columns = ("case", "candidate", "reviewer", *REVIEW_FIELDS, "decision", "notes")
    existing = {}  # Preserve any analyst entries if cases are resumed.
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as stream:
            existing = {(row["case"], row["candidate"], row["reviewer"]): row for row in csv.DictReader(stream)}
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for case, labels in key.items():
            for label in labels:
                for reviewer in ("1", "2"):
                    index = (case, label, reviewer)
                    writer.writerow(existing.get(index, dict(zip(columns[:3], index))))
    return review_metrics(path, key)


def retrospective_diagnostics(output):
    result = []
    for row in read(TURN_REPLAY / "diagnosis.json") or []:
        old = read(BASELINE / row["case"] / "harness.json").get("points")
        if not old:
            continue
        far = max(item["period_end"] for item in old)
        incumbent = point(old, far)["revenue"]
        result.append({"case": row["case"], "source": "earlier_diagnosis", "prior_rule_label": row["outcome_label"],
                       "incumbent": incumbent, "actual": row["actual"],
                       "signed_incumbent_residual": str(Decimal(row["actual"]) - Decimal(incumbent))})
    for row in read(TURN_REPLAY / "heldout-results.json") or []:
        incumbent = row["predictions"]["harness"]
        result.append({"case": row["case"], "source": "earlier_turn_holdout", "prior_rule_label": row["outcome_label"],
                       "incumbent": incumbent, "actual": row["actual"],
                       "signed_incumbent_residual": str(Decimal(row["actual"]) - Decimal(incumbent))})
    write_json(output / "previous-diagnostics.json", result)


def format_cell(value, places=3):
    return f"{value:,.{places}f}" if value is not None else "—"


def adjustment_table(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(("case", "issuer", "cutoff", "period", "outcome_group", "candidate", "incumbent_revenue_usd",
                         "actual_revenue_usd", "candidate_revenue_usd", "delta_usd", "candidate_eps", "actual_eps",
                         "component_removed", "without_component_revenue_usd", "without_component_eps",
                         "revenue_error_increase_usd", "eps_error_increase", "status", "signal_sources", "actual_source"))
        for row in rows:
            before = row["arms"]["harness"]["forecasts"]
            for arm in CHALLENGERS:
                result = row["arms"][arm]
                audit = result["audit"].get("residual", {})
                for component, without in result["counterfactuals"].items():
                    writer.writerow((
                        row["case"], row["issuer"], row["cutoff"], row["period"], row["outcome_group"], arm,
                        before["revenue"], row["actual"]["revenue"], result["forecasts"]["revenue"],
                        result["delta_vs_incumbent"], result["forecasts"]["eps"], row["actual"]["eps"],
                        component, without.get("revenue"), without.get("eps"), without.get("revenue_error_increase"),
                        without.get("eps_error_increase"), without.get("status", audit.get("status", "")),
                        " | ".join(dict.fromkeys(result["sources"].values())), row["actual_source"],
                    ))


def report(output, summary, rows, available_inputs):
    result = summary["candidates"]
    lines = [
        "# T+2 盈利預測修正｜配對驗收", "",
        f"前次未使用的事件共 {summary['planned']} 案，完成 {summary['paired']} 案。純 Astra 與現版 Harness "
        "使用相同的截止時點證據，停用搜尋。兩個候選共用每案凍結的現版預測。後續實績不進模型資料包。",
        "候選規則在保留集評測前固定。回放按照各事件原始截止時點排序；公告日期的 UTC 日末作為取得時間代理。"
        "歷史結果可能已存在於模型訓練資料。", "",
        "## 主要結果", "",
        "| 指標 | " + " | ".join(NAMES.values()) + " |",
        "|---|" + "---:|" * len(ARMS),
    ]
    for label, key, conversion in (
        ("公司等權標準化 T+2 營收 MAE（%）", "issuer_equal_scaled_revenue_mae", 100),
        ("T+2 營收 MAE（百萬美元）", "t2_revenue_mae_usd_m", 1),
        ("T+2 GAAP EPS MAE（美元／股）", "t2_eps_mae", 1),
    ):
        values = summary[key]
        table_row = [format_cell(values[arm] * conversion if values[arm] is not None else None) for arm in ARMS]
        lines.append(f"| {label} | " + " | ".join(table_row) + " |")
    counts = summary["outcome_groups"]
    lines += ["", "營收標準化使用截至事件的最後一季已公開合併營收。先在公司內平均，再讓公司等權。"
              "相對現版實績殘差達正負 10% 列為上行或下行，其餘列為正常。",
              f"上行 {counts.get('up', 0)} 案、下行 {counts.get('down', 0)} 案、正常 {counts.get('quiet', 0)} 案。", "",
              "## 使用範圍與驗收", "",
              f"保留集具備 B 的研究輸入 {available_inputs} 案，實際採用分部輸入 "
              f"{result['residual_b']['with_applied_segment_input']} 案。"
              "缺少可證明為現版尚未反映的量化增量時，B 沿用 A。"
              f"另外列有 {summary['watchpoints']} 個當時可見的研究訊號，供分析師核對。"]
    for arm in CHALLENGERS:
        row = result[arm]
        lines.append(f"- {NAMES[arm]} 調整 {row['adjusted_cases']} 案，正常季度調整 {row['quiet_adjustments']} 案，"
                     f"實際上行或下行方向命中 {row['correct_direction_cases']} 案。"
                     f"相較現版較準 {row['wins_vs_harness']} 案。歷史門檻"
                     f"{'通過' if row['passes_historical_gate'] else '未通過'}。")
    if intervals := summary["issuer_resampled_paired_loss_delta"]:
        rows_with_intervals = []
        for arm, result_interval in intervals.items():
            lo, high = (value * 100 for value in result_interval)
            rows_with_intervals.append(f"{NAMES[arm]} {lo:+.2f} 至 {high:+.2f} 個百分點")
        lines.append("按公司分組重抽樣的 95% 誤差差額區間（候選減現版）為" + "、".join(rows_with_intervals) +
                     "。公司數有限，區間用於觀察集中度。")
    lines += ["", "預設門檻要求營收誤差比現版低至少 5%，並低於 Astra。GAAP EPS 與正常季度營收"
              "最多容許 2% 退步。樣本須涵蓋三種結果，有實際調整，而且移除任一公司後仍具增量。"
              "歷史門檻與正式上線判斷各自記錄。"]
    if rows:
        lines += ["", "## 個案修正", "", "| 案例 | 現版 | A | B | 實績（百萬美元） |",
                  "|---|---:|---:|---:|---:|"]
        for row in rows:
            numbers = [format_cell(float(Decimal(row["arms"][arm]["forecasts"]["revenue"]) / MILLION), 1)
                       for arm in ("harness", *CHALLENGERS)]
            actual = format_cell(float(Decimal(row["actual"]["revenue"]) / MILLION), 1)
            lines.append(f"| {row['case']} | " + " | ".join([*numbers, actual]) + " |")
    lines += ["", f"已完成雙人覆核 {summary['human_review']['complete_cases']} 案。逐案來源、取消整體修正、"
              "移除單項及移除全部分部輸入的反事實保存於 JSON。前瞻實績另由獨立隊列追蹤。"]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sec-dir", type=Path, default=Path("output/earnings-benchmark/sec"))
    parser.add_argument("--output", type=Path, default=Path("output/earnings-residual"))
    parser.add_argument("--run-model", action="store_true")
    parser.add_argument("--forecast-only", action="store_true")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    from .earnings_residual_inputs import load_driver_ledger, load_holdout

    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    cases = dossiers(out, list(load_holdout(args.sec_dir)))
    if not cases:
        parser.error("保留集沒有可執行事件")
    raw = out / "forecasts"
    raw.mkdir(exist_ok=True)
    freeze_json(out / "candidate-protocol.json", {
        "formula": "signed residual projected from consecutive fiscal-season transitions; A is decayed "
                   "historical shock and B adds demonstrably incremental source-backed settlement in the target period",
        "retention_per_step": str(RESIDUAL_STEP_RETENTION), "residual_gap_weight": str(RESIDUAL_GAP_WEIGHT),
        "maximum_revenue_multiplier_delta": str(RESIDUAL_CAP), "minimum_revenue_multiplier_delta": str(RESIDUAL_MIN_CHANGE),
    })
    if args.run_model or args.forecast_only:
        raw_models(raw, cases, args.workers)
    if args.forecast_only:
        return
    rows, all_points, failures = [], {}, {}
    for case in cases:
        case_id = case["id"]
        old_results = {arm: read(raw / case_id / f"{arm}.json") for arm in ARMS[:2]}
        old = {arm: payload.get("points") for arm, payload in old_results.items()}
        if not all(old.values()):
            failures[case_id] = {arm: payload.get("error", "尚未完成") for arm, payload in old_results.items()
                                 if not payload.get("points")}
            continue
        event, context = case["event"], case["context"]
        try:
            projected = {arm: evaluate_candidate(event, context, old["harness"], arm, case.get("driver_inputs", ()))
                         for arm in CHALLENGERS}
            candidates = {arm: result[0] for arm, result in projected.items()}
            audits = {arm: result[1] for arm, result in projected.items()}
            row = audited_case(case, old, candidates, audits)
        except (ArithmeticError, ValueError) as exc:
            failures[case_id] = {"candidates": str(exc)}
            continue
        rows.append(row)
        all_points[case_id] = {**old, **candidates}
    if all_points:
        freeze_json(out / "outcomes.json", {case["id"]: case["actual"] for case in cases})
    metrics = aggregate(rows, len(cases))
    metrics["b_with_driver_inputs"] = sum(bool(case.get("driver_inputs")) for case in cases)
    ledger = load_driver_ledger(cases)
    metrics["watchpoints"] = len(ledger)
    write_json(out / "driver-ledger.json", ledger)
    metrics["failures"] = failures
    metrics["human_review"] = blind_pack(out, cases, all_points)
    write_json(out / "summary.json", metrics)
    write_json(out / "case-audit.json", rows)
    adjustment_table(out / "adjustments.csv", rows)
    write_json(out / "forecast-points.json", all_points)
    write_json(out / "rolling-origin.json", [{
        "case": row["case"], "origin": row["cutoff"], "target_period": row["period"],
        "first_actual_available_at": row["actual_available_at"],
        "normalizer_observation_date": row["latest_visible_revenue_date"],
        "candidate_adjusted": {arm: is_adjusted(row, arm) for arm in CHALLENGERS},
        "earlier_resolved_cases": [prior["case"] for prior in rows if
                                   datetime.fromisoformat(prior["actual_available_at"]) < datetime.fromisoformat(row["cutoff"])],
        "estimation": "fixed candidate; no fit on earlier outcomes",
    } for row in rows])
    retrospective_diagnostics(out)
    report(out, metrics, rows, metrics["b_with_driver_inputs"])
    print(json.dumps({key: metrics[key] for key in ("planned", "paired", "failures", "candidates")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
