"""Run a frozen T+2 turning-point test with disjoint event accessions."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path

from research_app.earnings import issuer_guidance
from research_app.research import build_context
from research_app.revenue import GUIDANCE_THRESHOLD, MOMENTUM_THRESHOLD, TURN_CAP, TURN_PASS_THROUGH, anchors, turn_forecast
from research_app.schema import Document, Event, RevenueTurnSignal

from .earnings_calibration import prepare, score_group
from .earnings_cases import baseline, disclosure
from .earnings_equal import history_arm, recalculate_direct
from .earnings_horizon import active_case, freeze_json, revenue_row
from .earnings_horizon_inputs import CIKS, add_revenue_history, revenue_history
from .earnings_inputs import add_eps_assumptions, add_guidance, end_of_day, financial_history
from .earnings_pilot import read
from .public_pilot import EFFORT, MODEL, write_json

DEVELOPMENT_GUIDE = Path(__file__).with_name("earnings_guidance.csv")
HELD_OUT = Path(__file__).with_name("earnings_turns_cases.csv")
DIAGNOSIS = {
    "up": ("AMD-2020", "INTC-2023", "MU-2020", "TXN-2020"),
    "down": ("AMD-2022", "INTC-2022", "MU-2022", "QCOM-2019"),
    "quiet": ("AMD-2019", "INTC-2024", "QCOM-2024", "TXN-2023"),
}
OUTCOME_CUTOFF = Decimal("0.10")
ARMS = ("astra", "harness", "turn")
PRIMARY_EDGE = 0.05
MAX_QUIET_FALSE_POSITIVE = 0.20


def oneday(raw):
    return end_of_day(date.fromisoformat(raw))


def far_actual(period, values, when, source, identifier):
    return {
        "values": {key: str(number) for key, number in values.items()},
        "document": {"id": identifier, "source": source, "published_at": when.isoformat(), "obtained_at": when.isoformat(),
                     "kind": "disclosure", "text_format": "summary",
                     "paragraphs": {"results": f"{period} 單季公開的 US GAAP 實績。"}},
    }


def reserved_cases(sec_dir, history, *, cases_path=HELD_OUT, method="confirmed_turn"):
    eps = financial_history(sec_dir, CIKS)
    with cases_path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            case_id = row["case"]
            ticker, year, _ = case_id.split("-")
            cik = CIKS[ticker]
            filings = list(eps[ticker][0])
            current, = [item for item in filings if item["fp"] == "Q2" and item["end"].year == int(year)]
            upcoming, = [item for item in filings if item["fp"] == "Q3" and 75 <= (item["end"] - current["end"]).days <= 110]
            far_period = date.fromisoformat(row["far_end"])
            far_filed = oneday(row["actual_date"])
            cutoff = end_of_day(current["filed"])
            if not (75 <= (far_period - upcoming["end"]).days <= 110 and far_filed.date() > far_period
                    and upcoming["filed"] > current["filed"] and oneday(row["outlook_date"]) <= cutoff):
                raise ValueError(f"{case_id} 的季度或資料時點不符")
            prior_q3, = [item for item in filings if item["fp"] == "Q3"
                        and 345 <= (upcoming["end"] - item["end"]).days <= 385 and item["filed"] < current["filed"]]
            prior_q1 = max((item for item in filings if item["fp"] == "Q1" and item["filed"] < current["filed"]),
                           key=lambda item: item["end"])
            docs = [disclosure(cik, "past-q3", prior_q3), disclosure(cik, "past-q1", prior_q1),
                    disclosure(cik, "issuer-q2", current)]
            near_baseline = baseline(prior_q3, upcoming["end"], docs[0])
            far_baseline = baseline(prior_q1, far_period, docs[1])
            far_baseline["method"] = "以上一份已公開第一季的營收、毛利及費用作基準。兩組模型同時取得各年第四季歷史營收。"
            event = Event.model_validate({
                "research_target": ticker, "research_horizon": far_period.isoformat(), "as_of": cutoff,
                "search_mode": "off", "event_text": f"{ticker} 公布截至 {current['end']} 的第二季申報，預估同財年的第三、四季。",
                "documents": docs, "earnings_plan": {"event_at": cutoff, "basis": "US_GAAP", "currency": "USD",
                                                      "quarters": [near_baseline, far_baseline], "generate_drivers": True},
            })
            record = {"published_on": row["outlook_date"], "quarter_ahead": "1", "basis": "US_GAAP", "currency": "USD",
                      "source": row["outlook_source"]}
            lo, hi = (str(int(row[f"guide_{side}_m"]) * 1_000_000) for side in ("low", "high"))
            guide = [{**record, "metric": "revenue", "low": lo, "high": hi,
                      "summary": f"第三季合併營收公司指引為 {lo} 至 {hi} 美元。"}]
            if row["margin_low"]:
                gm_low, gm_high = row["margin_low"], row["margin_high"]
                guide.append({**record, "metric": "gross_margin", "low": gm_low, "high": gm_high,
                              "summary": f"第三季 GAAP 合併毛利率指引為 {gm_low} 至 {gm_high}（比例）。"})
            event = add_eps_assumptions(add_guidance(event, guide), ticker, eps, guide, cik=cik)
            event = add_revenue_history(event, ticker, history[ticker], (3, 4), method)
            if row["mix_up"]:
                when = oneday(row["outlook_date"])
                source = Document(id="public-mix-signal", source=row["outlook_source"], kind="disclosure",
                                  availability_basis="replay_day_end", text_format="summary",
                                  published_at=when, obtained_at=when, paragraphs={"mix": row["mix_up"]})
                signal = RevenueTurnSignal(driver="mix", direction="up", available_at=when,
                                           evidence_ids=["public-mix-signal:mix"], observation=row["mix_up"])
                bridge = event.earnings_plan.revenue_bridge.model_copy(update={"operating_signals": [signal]})
                event = event.model_copy(update={"documents": [*event.documents, source], "earnings_plan":
                                         event.earnings_plan.model_copy(update={"revenue_bridge": bridge})})
            rev, gross, op = (Decimal(row[field]) * 1_000_000
                              for field in ("revenue_m", "gross_profit_m", "op_income_m"))
            third = {name: pair[0] for name, pair in upcoming["values"].items()}
            near_source = disclosure(cik, "actual-q3", upcoming)["source"]
            actual = {
                upcoming["end"].isoformat(): far_actual(upcoming["end"],
                    {"revenue": third["revenue"], "gross_margin": third["gross"] / third["revenue"],
                     "operating_income": third["operating_income"], "eps": third["eps"]},
                    end_of_day(upcoming["filed"]), near_source, "actual-q3"),
                far_period.isoformat(): far_actual(far_period, {"revenue": rev, "gross_margin": gross / rev,
                    "operating_income": op, "eps": Decimal(row["eps"])}, far_filed, row["actual_source"], "actual-q4"),
            }
            yield {"id": case_id, "event": event, "context": build_context(event),
                   "accession": current["accession"], "actual": actual}


def diagnose(case, baseline_revenue=None):
    event = case["event"]
    plan = event.earnings_plan
    guide = issuer_guidance(plan).get((min(row.period_end for row in plan.quarters), "revenue"))
    bridge = plan.revenue_bridge
    candidates = anchors(bridge, guide)
    season = candidates["guided_absolute"][0]
    revised, audit = turn_forecast(bridge, guide, baseline_revenue if baseline_revenue is not None else season)
    actual = case["actual"][max(case["actual"])]
    observed = Decimal(actual["values"]["revenue"])
    residual = observed / season - 1
    outcome = "up" if residual >= OUTCOME_CUTOFF else "down" if residual <= -OUTCOME_CUTOFF else "quiet"
    sources = {row["id"]: row["source"] for row in case["context"]["evidence"]}
    return {"case": case["id"], "cutoff": event.as_of.isoformat(), "outcome_label": outcome, "actual": str(observed),
            "seasonal_anchor": str(season), "before": str(baseline_revenue if baseline_revenue is not None else season),
            "after": str(revised), "observed_deviation": str(residual), "turn": audit,
            "actual_source": actual["document"]["source"], "signal_sources": {ref: sources[ref] for ref in audit["evidence_ids"]}}


def diagnostic_sample(sec_dir, history):
    categories = {case: label for label, ids in DIAGNOSIS.items() for case in ids}
    rows = []
    for case in prepare(sec_dir, DEVELOPMENT_GUIDE):
        if case["id"] not in categories:
            continue
        ticker = case["id"].split("-")[0]
        event = add_revenue_history(case["event"], ticker, history[ticker], (2, 3), "confirmed_turn")
        row = diagnose({**case, "event": event, "context": build_context(event)})
        if row["outcome_label"] != categories[case["id"]]:
            raise ValueError(f"診斷標籤不符：{case['id']}")
        rows.append(row)
    return rows


def classify(rows):
    counts = Counter((row["outcome_label"], row["turn"]["status"]) for row in rows)
    quiet = sum(value for (actual, _), value in counts.items() if actual == "quiet")
    false = counts["quiet", "up"] + counts["quiet", "down"]
    active = sum(value for (_, status), value in counts.items() if status in {"up", "down"})
    return {"active": active, "correct_turns": counts["up", "up"] + counts["down", "down"],
            "actual_turns": len(rows) - quiet, "quiet": quiet, "false_positive": false,
            "false_positive_rate": false / quiet if quiet else None,
            "counts": {f"{act}/{pred}": count for (act, pred), count in sorted(counts.items())}}


def export(output, dev, cases, forecasts, detail):
    by_horizon = {str(step): score_group(cases, forecasts, ARMS, lambda c: [sorted(c["actual"])[step - 1]]) for step in (1, 2)}
    far = by_horizon["2"]
    confusion = classify(detail)
    full = len(forecasts) == len(cases)
    accepted = (full and far["revenue"]["turn"] <= (1 - PRIMARY_EDGE) * far["revenue"]["astra"]
                and far["revenue"]["turn"] < far["revenue"]["harness"]
                and far["eps"]["turn"] <= far["eps"]["harness"] and confusion["correct_turns"] > 0
                and confusion["false_positive_rate"] is not None
                and confusion["false_positive_rate"] <= MAX_QUIET_FALSE_POSITIVE)
    write_json(output / "summary.json", {"diagnosis": classify(dev), "reserved": len(cases), "paired": len(forecasts),
                                         "horizon_mae": by_horizon, "classification": confusion, "passed": accepted})
    write_json(output / "heldout-results.json", detail)
    write_json(output / "forecast-points.json", forecasts)
    with (output / "signals.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(("case", "cutoff", "guidance_surprise", "reported_surprise", "decision", "reason",
                         "before_usd", "delta_usd", "after_usd", "t2_actual_usd", "outcome_label", "evidence_urls", "actual_url"))
        writer.writerows((r["case"], r["cutoff"], r["turn"]["guidance_surprise"], r["turn"]["reported_surprise"],
                          r["turn"]["status"], r["turn"]["reason"], r["before"], r["turn"]["delta"], r["after"],
                          r["actual"], r["outcome_label"],
                          " | ".join(dict.fromkeys(r["signal_sources"].values())), r["actual_source"]) for r in dev)
    report = ["# T+2 轉折訊號｜驗收紀錄", "",
              "診斷集為四個上行、四個下行及四個接近季節基準的案例。較季節基準高低至少 10% 用於事後標記。"
              "偵測使用當時資料。第一預測季指引須偏離歷史季節基準至少 12%，且當期已公布營收偏離至少 8% 或公開營運訊號提供同向支持。"
              "觸發時只假設指引偏離金額的一半延續至第二預測季，自動調整上限是原營收預測的 15%。"
              "兩種支持互相矛盾或資料不足時，維持原稿預測。", "",
              "## 12 案診斷", "", "| 案例 | 指引偏離 | 已公布營收偏離 | 判定 | 事後類型 |",
              "|---|---:|---:|---|---|"]
    labels = {"up": "上行", "down": "下行", "quiet": "正常", "unconfirmed": "未確認", "missing_signal": "缺資料"}
    for row in dev:
        signal = row["turn"]
        p = lambda x: f"{Decimal(x):+.1%}" if x is not None else "—"
        report.append(f"| {row['case']} | {p(signal['guidance_surprise'])} | {p(signal['reported_surprise'])} | "
                      f"{labels[signal['status']]} | {labels[row['outcome_label']]} |")
    report += ["", "## 新的保留事件", "", f"同一份時點證據，完成 {len(forecasts)}/{len(cases)} 案配對。"
               "這些是先前兩輪未使用的第二季披露事件；T+2 實績取自另外存檔的公司第四季公告。", "",
               "| T+2 平均絕對誤差 | 純 Astra | 現版 Harness | 加入轉折偵測 |", "|---|---:|---:|---:|"]
    for key, name in (("revenue", "營收（百萬美元）"), ("eps", "稀釋 EPS（美元／股）")):
        report.append(f"| {name} | " + " | ".join(f"{far[key][arm]:,.3f}" if arm in far[key] else "—" for arm in ARMS) + " |")
    report += ["", f"共觸發 {confusion['active']} 案，{confusion['actual_turns']} 個實際轉折中判對方向 {confusion['correct_turns']} 案。"
               f"{confusion['quiet']} 個正常季度中誤判 {confusion['false_positive']} 案。",
               f"預先設定的門檻{'通過' if accepted else '未通過'}。所有資料仍屬歷史回放。"]
    if detail and all(row["outcome_label"] != "down" for row in detail):
        report.append("保留集沒有下行結果。下行行為在診斷與程式測例中測試。")
    if example := next((row for row in detail if row["case"] == "NVDA-2023-Q2"), None):
        audit = example["turn"]
        report.extend(["", "## NVIDIA 為何未觸發", "",
                       f"截至事件日，當期合併營收比季節基準高 {Decimal(audit['reported_surprise']):.1%}，"
                       f"下一季公司指引只高 {Decimal(audit['guidance_surprise']):.1%}。{audit['reason']} "
                       f"[第四季實績]({example['actual_source']})"])
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sec-dir", type=Path, default=Path("output/earnings-benchmark/sec"))
    parser.add_argument("--output", type=Path, default=Path("output/earnings-turns"))
    parser.add_argument("--run-model", action="store_true")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    history = revenue_history(args.sec_dir, CIKS)
    dev = diagnostic_sample(args.sec_dir, history)
    cases = list(reserved_cases(args.sec_dir, history))
    freeze_json(output / "protocol.json", {
        "diagnosis": DIAGNOSIS, "reserved_accessions": {case["id"]: case["accession"] for case in cases},
        "model": MODEL, "reasoning_effort": EFFORT, "guidance_threshold": str(GUIDANCE_THRESHOLD),
        "reported_threshold": str(MOMENTUM_THRESHOLD), "multiplier": str(TURN_PASS_THROUGH), "cap": str(TURN_CAP),
        "outcome_cutoff": str(OUTCOME_CUTOFF), "min_improvement_vs_astra": PRIMARY_EDGE,
        "max_quiet_false_positive": MAX_QUIET_FALSE_POSITIVE, "source_sha256": sha256(HELD_OUT.read_bytes()).hexdigest(),
    })
    freeze_json(output / "inputs.json", {case["id"]: case["event"].model_dump(mode="json") for case in cases})
    write_json(output / "diagnosis.json", dev)
    raw = output / "forecasts"
    raw.mkdir(exist_ok=True)
    forecasts, detail = {}, []
    if args.run_model:
        os.environ["RESEARCH_CODEX_MODEL"] = MODEL
        with ThreadPoolExecutor(max_workers=6) as pool:
            jobs = [pool.submit(history_arm, raw, active_case(case), arm)
                    for case in cases for arm in ("astra", "harness")]
            for job in jobs:
                print(*job.result(), flush=True)
    for case in cases:
        old = {arm: read(raw / case["id"] / f"{arm}.json").get("points") for arm in ("astra", "harness")}
        if not all(old.values()):
            continue
        plan = case["event"].earnings_plan.model_copy(update={"calibrate_guidance": False})
        event = case["event"].model_copy(update={"earnings_plan": plan})
        result = {**old, "turn": recalculate_direct(event, case["context"], old["harness"])}
        far = max(case["actual"])
        row = diagnose(case, revenue_row(result, "harness", far))
        forecasts[case["id"]] = result
        detail.append(row | {"predictions": {arm: str(revenue_row(result, arm, far)) for arm in ARMS}})
    if forecasts:
        freeze_json(output / "outcomes.json", {case["id"]: case["actual"] for case in cases})
    export(output, dev, cases, forecasts, detail)


if __name__ == "__main__":
    main()
