"""Replay published earnings estimates with point-in-time inputs and run a matched-evidence comparison."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path
from random import Random
from statistics import mean, quantiles

from research_app.adapters import EARNINGS_DRIVER_VERSION
from research_app.earnings import METRICS, issuer_guidance
from research_app.research import build_context

from .earnings_cases import load_cases
from .earnings_equal import history_arm, recalculate_direct, score_rows
from .earnings_inputs import add_eps_assumptions, add_guidance, financial_history, load_guidance
from .earnings_pilot import read
from .public_pilot import EFFORT, MODEL, write_json

SCALES = {"revenue": "百萬 USD", "gross_margin": "百分點", "operating_income": "百萬 USD", "eps": "USD／股"}
UNIT_DIVISORS = {"revenue": 1e6, "gross_margin": 0.01, "operating_income": 1e6, "eps": 1}
ARMS = ("astra", "calculator", "harness", "eps_only", "guidance_only", "both")
NAMES = ("原 Astra", "原 Astra＋計算器", "原 Harness", "只改 EPS", "只加指引", "兩項都加")


def prepare(sec_dir, guide_path):
    history = financial_history(sec_dir)
    guidance = load_guidance(guide_path)
    cases = load_cases(sec_dir)
    if set(guidance) - {row["id"] for row in cases}:
        raise ValueError("指引含未登記案例")
    for case in cases:
        case_id = case["id"]
        issuer_rows = guidance.get(case_id, [])
        event = add_guidance(case["event"], issuer_rows)
        event = add_eps_assumptions(event, case_id.split("-", 1)[0], history, issuer_rows)
        yield {**case, "event": event, "context": build_context(event)}


def legacy_replay(folder, case):
    sources = {name: read(folder / case["id"] / f"{name}.json").get("points") for name in ARMS[:3]}
    if any(not rows for rows in sources.values()):
        raise ValueError(f"{case['id']} 缺少完整的舊版預測")
    event, context = case["event"], case["context"]
    plan = event.earnings_plan
    for name, use_eps, use_guidance in (("eps_only", True, False), ("guidance_only", False, True), ("both", True, True)):
        variant = plan.model_copy(update={"eps_assumptions": plan.eps_assumptions if use_eps else [],
                                          "calibrate_guidance": use_guidance})
        sources[name] = recalculate_direct(event.model_copy(update={"earnings_plan": variant}),
                                           context, sources["harness"])
    return sources


def score_group(cases, results, names, periods=None):
    observations = []
    for case in cases:
        if case["id"] not in results:
            continue
        targets = set(periods(case)) if periods else set(case["actual"])
        for arm in names:
            observations.extend((arm, point, case["actual"][point["period_end"]]["values"])
                                for point in results[case["id"]][arm]
                                if point["scenario"] == "base" and point["period_end"] in targets)
    return score_rows(observations, arms=names)


def add_table(lines, scores, columns, names):
    lines.extend(["| 指標 | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)])
    for key, label in METRICS.items():
        numbers = [f"{scores[key][arm]:.3f}" if arm in scores[key] else "—" for arm in columns]
        lines.append(f"| {label}（{SCALES[key]}） | " + " | ".join(numbers) + " |")
    lines.append("")


def paired_intervals(cases, fresh):
    """Resample complete cases together so a company's two forecast quarters stay paired."""
    selected = [case for case in cases if case["id"] in fresh]
    if len(selected) < 2:
        return {}
    differences = {metric: [] for metric in METRICS}
    for case in selected:
        points = fresh[case["id"]]
        direct = {row["period_end"]: row for row in points["astra"] if row["scenario"] == "base"}
        harness = {row["period_end"]: row for row in points["harness"] if row["scenario"] == "base"}
        for metric, scale in UNIT_DIVISORS.items():
            gaps = []
            for period, outcome in case["actual"].items():
                actual = Decimal(outcome["values"][metric])
                gap = abs(Decimal(harness[period][metric]) - actual) - abs(Decimal(direct[period][metric]) - actual)
                gaps.append(float(gap) / scale)
            differences[metric].append(mean(gaps))
    rng = Random(20261123)
    samples = [rng.choices(range(len(selected)), k=len(selected)) for _ in range(5000)]
    intervals = {}
    for metric, values in differences.items():
        cuts = quantiles((mean(values[index] for index in sampleset) for sampleset in samples), n=40)
        intervals[metric] = [cuts[0], cuts[-1]]
    return intervals


def export(folder, cases, legacy, fresh):
    guidance = {case["id"]: issuer_guidance(case["event"].earnings_plan) for case in cases}
    covered = {case: sorted({period.isoformat() for period, _ in refs}) for case, refs in guidance.items()}
    coverage = {metric: sum(key[1] == metric for refs in guidance.values() for key in refs)
                for metric in ("revenue", "gross_margin")}
    scores = {
        "frozen": score_group(cases, legacy, ARMS),
        "covered_quarters": score_group(cases, legacy, ARMS, lambda case: covered[case["id"]]),
        "equal_information": score_group(cases, fresh, ("astra", "harness")),
        "equal_information_guided": score_group(cases, fresh, ("astra", "harness"), lambda case: covered[case["id"]]),
        "equal_information_unguided": score_group(
            cases, fresh, ("astra", "harness"), lambda case: set(case["actual"]) - set(covered[case["id"]])
        ),
    }
    intervals = paired_intervals(cases, fresh)
    write_json(folder / "summary.json", {"historical_cases": len(cases), "guidance_coverage": coverage,
                                        "quarters_with_guidance": sum(map(len, covered.values())),
                                        "fresh_paired": len(fresh), "scores": scores, "paired_case_intervals_95": intervals})
    lines = [
        "# 盈利預測修正｜公司指引與 EPS 的影響", "",
        f"歷史回放 {len(cases)} 案、{sum(len(case['actual']) for case in cases)} 季。以下均為基準情境平均絕對誤差。",
        f"可用指引覆蓋 {coverage['revenue']} 季營收、{coverage['gross_margin']} 季毛利率。"
        "只有相同季度、幣別、會計口徑的合併指引才進入校準。", "",
        "## 固定原預測，分別套用兩項改動", "",
        "保留舊 Harness 的營業費用。EPS 組使用有來源的常態稅率、稀釋股數及經常性營業外損益，"
        "單列發行人已指明的一次性項目，虧損預設不承認稅務利益。"
        "指引組向區間中點校準營收與毛利率並重算營業利益。兩者都依預測時已公開的資料。", "",
    ]
    add_table(lines, scores["frozen"], ARMS, NAMES)
    lines.extend(["## 有指引的季度", ""])
    add_table(lines, scores["covered_quarters"], ARMS, NAMES)
    lines.extend(["## 相同新增證據，重新呼叫 Astra", "",
                  f"已完成 {len(fresh)}/{len(cases)} 組配對。兩組均拿到相同的公司指引與 SEC 申報資料，"
                  "同模型、同推理額度且停用搜尋。歷史回放仍可能受到模型已知結果與樣本選擇影響。", ""])
    add_table(lines, scores["equal_information"], ("astra", "harness"), ("純 Astra", "新 Harness"))
    if intervals:
        scores_far = scores["equal_information_unguided"]["revenue"]
        lines.append(
            "近一季的營收均有公開指引。沒有同季指引的季度，"
            f"Astra 與 Harness 的營收誤差分別為 {scores_far['astra']:.1f} 和 {scores_far['harness']:.1f} 百萬美元。"
        )
        lines.append("")
        lines.extend(["以事件為單位的 5,000 次配對重抽樣，以下為兩組誤差差額的樣本內 95% 區間。負值表示有利於 Harness。", "",
                      "| 指標 | Harness 減 Astra |", "|---|---:|"])
        for metric, (lo, hi) in intervals.items():
            lines.append(f"| {METRICS[metric]}（{SCALES[metric]}） | {lo:+.3f} 至 {hi:+.3f} |")
        lines.append("")
    lines += ["## 來源", ""]
    for case in cases:
        sources = list(dict.fromkeys(row.source for row in case["event"].documents if row.id.startswith("issuer-guidance-")))
        if sources:
            links = "、".join(f"[公司展望 {index}]({url})" for index, url in enumerate(sources, 1))
            lines.append(f"- {case['id']}。{links}")
    (folder / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sec-dir", type=Path, default=Path("output/earnings-benchmark/sec"))
    parser.add_argument("--legacy", type=Path, default=Path("output/earnings-equal-replay"))
    parser.add_argument("--guidance", type=Path, default=Path(__file__).with_name("earnings_guidance.csv"))
    parser.add_argument("--output", type=Path, default=Path("output/earnings-calibration"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--run-model", action="store_true")
    args = parser.parse_args()
    legacy_manifest = read(args.legacy / "manifest.json")
    if (legacy_manifest.get("driver_prompt_version"), legacy_manifest.get("model"), legacy_manifest.get("effort")) != (
        3, MODEL, EFFORT
    ):
        parser.error("固定預測回放須使用原第 3 版 Astra 對照的輸出資料夾")
    cases = list(prepare(args.sec_dir, args.guidance))
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "inputs.json", {case["id"]: case["event"].model_dump(
        mode="json", exclude={"earnings_plan": {"revenue_bridge"}}
    ) for case in cases})
    legacy = {case["id"]: legacy_replay(args.legacy, case) for case in cases}
    write_json(args.output / "fixed-predictions.json", legacy)
    fresh_dir = args.output / "fresh"
    fresh_dir.mkdir(exist_ok=True)
    manifest = {"model": MODEL, "effort": EFFORT, "driver_version": EARNINGS_DRIVER_VERSION,
                "inputs_sha256": sha256((args.output / "inputs.json").read_bytes()).hexdigest()}
    manifest_path = fresh_dir / "manifest.json"
    if manifest_path.exists() and read(manifest_path) != manifest:
        parser.error("模型或輸入已變更，請使用新的輸出資料夾")
    write_json(manifest_path, manifest)

    def collect_fresh():
        result = {}
        for case in cases:
            rows = {arm: read(fresh_dir / case["id"] / f"{arm}.json").get("points") for arm in ("astra", "harness")}
            if all(rows.values()):
                result[case["id"]] = rows
        return result

    export(args.output, cases, legacy, collect_fresh())
    if args.run_model:
        os.environ["RESEARCH_CODEX_MODEL"] = MODEL
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            jobs = [pool.submit(history_arm, fresh_dir, case, arm) for case in cases for arm in ("astra", "harness")]
            for job in as_completed(jobs):
                print(*job.result(), flush=True)
        fresh = collect_fresh()
        export(args.output, cases, legacy, fresh)
        if len(fresh) != len(cases):
            raise SystemExit("部分新配對未完成，請檢查 fresh 下的個別錯誤")


if __name__ == "__main__":
    main()
