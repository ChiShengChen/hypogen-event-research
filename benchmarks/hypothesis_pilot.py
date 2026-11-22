"""Generate and blind-score financial hypotheses using the signed-in Codex CLI."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import random
from statistics import mean, median
from string import ascii_uppercase
from time import perf_counter
from typing import Literal

from pydantic import Field

from benchmarks.hypothesis_cases import freeze, future_disclosures, load_cases
from benchmarks.public_pilot import EFFORT, MODEL, write_json
from research_app.adapters import AdapterError, Codex
from research_app.research import build_report
from research_app.schema import Nonempty, Schema

JUDGE = "gpt-6.2-sol"
STYLES = {
    "bull-bear": ("傳統多空", "Give one bullish and one bearish operating hypothesis for the research target."),
    "financial": ("財務傳導", "Start from two different earnings drivers. Trace each from the event to a distinct "
                  "revenue, gross profit, cost, or cash flow outcome. Give a formula or sensitivity when inputs "
                  "support it and label unknown quantities."),
    "competing": ("競爭解釋", "Propose two different plausible explanations for the same decision-relevant "
                  "observation in this evidence. State an observable result for each that distinguishes it "
                  "from the other explanation."),
    "expectations": ("預期差", "Identify a disclosed reference point such as management guidance or a published "
                     "milestone. Explore two different ways results could surprise relative to it. Distinguish "
                     "management guidance from market consensus. If no reliable market expectation is visible, "
                     "say so and state what would be needed, or use a clearly labeled operating comparison."),
    "spillover": ("供應鏈外溢", "Study companies not named in the intake. Use a documented link to the event or "
                  "target. Give different event transmission paths. If evidence only supports one counterparty, "
                  "give two distinct paths for it or state the second gap. Do not invent counterparties, "
                  "qualified substitutions, orders, or financial exposure."),
}
DIRECT_GENERATOR = (
    "根據這份事件與資料，從當時可知的資訊提出兩條繁體中文金融研究假說。遵守資料的截止時點和研究期間。"
)
ASTRA_COMPARISON = {
    "astra-direct": ("純 Astra", DIRECT_GENERATOR),
    "current-harness": ("現行 Harness", "Production report generation with web discovery disabled."),
    **STYLES,
}
DIMENSIONS = {
    "evidence": "證據支持",
    "mechanism": "因果傳導",
    "prediction": "預測可驗證",
    "invalidation": "失效條件",
    "distinctness": "組內差異",
}
GENERATOR = (
    "Write two concise financial research hypotheses in Traditional Chinese. Each hypothesis must give a "
    "company, the mechanism, a concrete catalyst, a prediction, a falsifier, materiality, and precise evidence IDs. "
    "Use the given target, horizon, and frozen excerpts. Operate as of the snapshot. Anchor facts only in those "
    "excerpts. Mark deductions as hypotheses and missing facts as unknown. Use distinct mechanisms, not two "
    "directions of the same number. A prediction names a metric, direction or threshold, public source and "
    "deadline within the horizon; if no public observation can test it, identify the gap. "
    "The falsifier uses the same company, metric, and window. An absent or undisclosed result is not a falsifier "
    "without evidence that the observation would have been disclosed. Keep each narrative field brief. "
    "Do not describe your method or mention a style label."
)
JUDGE_RULES = (
    "Blindly evaluate each anonymous pair independently. Use the same strict rubric regardless of company or "
    "analytic angle, and do not reward length or presentation. Rate each dimension 0 (absent, wrong or "
    "mostly inadequate), 1 (materially partial), 2 (both candidates meet the dimension). "
    "Evidence: the cited passage genuinely supports the asserted central fact, and facts and deductions are "
    "separate. Mechanism: an explicit company-level causal chain connects the event to a meaningful operating "
    "effect; missing scale is honestly acknowledged. Prediction: an observation with a defined metric and unit "
    "where relevant, direction or threshold, accessible channel and deadline within the horizon. "
    "Invalidation: an observable contrary result for the same population, metric and period; "
    "inaccessible data and silence do not falsify. Distinctness: candidate mechanisms and diagnostic "
    "observations are meaningfully different, e.g. the second changes which evidence to collect. "
    "Do not reward having guessed a later outcome. Later disclosures are included solely to detect lookahead. "
    "Report a disqualifier only if a core factual assertion is directly contradicted by the supplied evidence, "
    "or the hypothesis presents a supplied post-cutoff disclosure as a fact already known at the cutoff. "
    "Neither an unsupported prediction nor a prediction that later came true constitutes lookahead. "
    "For each disqualifier identify candidate 1 or 2, kind, and the exact supporting excerpt ID. "
    "Use no disqualifier if the necessary counterevidence is unavailable. Provide a concise Traditional "
    "Chinese reason about the strongest limitation for each pair. Include each anonymous label exactly once."
)


class Hypothesis(Schema):
    company: Nonempty
    mechanism: Nonempty
    catalyst: Nonempty
    prediction: Nonempty
    invalidation: Nonempty
    materiality: Nonempty
    evidence_ids: list[str]


class HypothesisPair(Schema):
    first: Hypothesis
    second: Hypothesis


class Disqualifier(Schema):
    candidate: Literal[1, 2]
    kind: Literal["contradicted", "lookahead"]
    evidence_id: str
    rationale: Nonempty


class Evaluation(Schema):
    label: str
    evidence: int = Field(ge=0, le=2)
    mechanism: int = Field(ge=0, le=2)
    prediction: int = Field(ge=0, le=2)
    invalidation: int = Field(ge=0, le=2)
    distinctness: int = Field(ge=0, le=2)
    rationale: Nonempty
    disqualifiers: list[Disqualifier]


class Evaluations(Schema):
    evaluations: list[Evaluation]


def read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def generate_harness(event, adapter):
    # Use the same source excerpts as the controls, without precomputed scenarios or relationship labels.
    event = event.model_copy(update={
        "documents": [doc for doc in event.documents if not doc.synthetic and doc.kind == "disclosure"
                      and max(doc.published_at, doc.obtained_at) <= event.as_of],
        "search_mode": "off", "search_domains": [], "supply_edges": [],
        "financial_inputs": None, "reported_calculations": [],
    })
    report = build_report(event, adapter)
    evidence_by_claim = {row["id"]: row["evidence_id"] for row in report["claims"] if row.get("evidence_id")}
    hypotheses = {row["stance"]: row for row in report["hypotheses"]}
    candidates = {}
    for position, stance in (("first", "bull"), ("second", "bear")):
        row = hypotheses[stance]
        candidates[position] = Hypothesis(
            company=row["target"], mechanism=row["mechanism"], catalyst=row["catalyst"],
            prediction=row["prediction"], invalidation=row["invalidation"], materiality="—",
            evidence_ids=list(dict.fromkeys(
                evidence_by_claim[key] for key in row["claim_ids"] if key in evidence_by_claim
            )),
        )
    return {"hypotheses": HypothesisPair(**candidates).model_dump(), "original_report": report}


def generate(output, case_id, frozen, event, style):
    path = output / case_id / f"{style}.json"
    if read(path).get("hypotheses"):
        return case_id, style, "reused"
    started = perf_counter()
    adapter = Codex(reasoning_effort=EFFORT)
    try:
        if style == "current-harness":
            result = generate_harness(event, adapter)
        else:
            instruction = DIRECT_GENERATOR if style == "astra-direct" else f"{GENERATOR}\n{STYLES[style][1]}"
            generated = adapter._generate(HypothesisPair, instruction, frozen)
            result = {"hypotheses": generated.model_dump()}
    except AdapterError as exc:
        result = {"error": str(exc)}
    write_json(path, {**result, "seconds": round(perf_counter() - started, 2)})
    return case_id, style, "ok" if "hypotheses" in result else "failed"


def disqualified(pair, ratings, visible, future):
    """Apply deterministic citation validation and two-judge agreement on factual flags."""
    candidates = (pair["first"], pair["second"])
    reasons = {
        str(index): sorted(set(hypothesis["evidence_ids"]) - visible)
        for index, hypothesis in enumerate(candidates, 1)
        if set(hypothesis["evidence_ids"]) - visible
    }
    confirmed = []
    for flag in ratings[0]["disqualifiers"]:
        key = (flag["candidate"], flag["kind"], flag["evidence_id"])
        valid_ids = future if flag["kind"] == "lookahead" else visible
        if flag["evidence_id"] in valid_ids and any(
            key == (other["candidate"], other["kind"], other["evidence_id"])
            for other in ratings[1]["disqualifiers"]
        ):
            confirmed.append(flag)
    rejected = {int(index) for index in reasons} | {flag["candidate"] for flag in confirmed}
    return {"invalid_references": reasons, "confirmed_flags": confirmed, "candidates": sorted(rejected)}


def score_case(output, case_id, frozen, later, styles):
    folder = output / case_id
    pairs = {style: read(folder / f"{style}.json").get("hypotheses") for style in styles}
    if not all(pairs.values()):
        return case_id, "incomplete inputs"
    path = folder / "judgment.json"
    labels = dict(zip(ascii_uppercase, pairs))
    order = list(labels)
    random.Random(f"hypothesis-pilot-1:{case_id}").shuffle(order)
    previous = read(path)
    passes = previous.get("passes", [])
    if previous.get("styles"):
        return case_id, "reused"
    adapter = Codex(reasoning_effort=EFFORT)
    for labels_in_pass in (order, order[::-1])[len(passes):]:
        try:
            ratings = adapter._generate(Evaluations, JUDGE_RULES, {
                **frozen, "later_disclosures_for_verification_only": later,
                "anonymous_pairs": [{"label": label, **pairs[labels[label]]} for label in labels_in_pass],
            }).evaluations
            if len(ratings) != len(labels) or {rating.label for rating in ratings} != labels.keys():
                raise AdapterError("評審未對所有匿名標籤評分")
        except AdapterError as exc:
            write_json(path, {"passes": passes, "error": str(exc)})
            return case_id, "failed"
        passes.append({rating.label: rating.model_dump() for rating in ratings})
        write_json(path, {"passes": passes})
    visible = {row["id"] for row in frozen["evidence"]}
    future = {row["id"] for row in later}
    mapped = {}
    for label, style in labels.items():
        ratings = [judge_pass[label] for judge_pass in passes]
        scores = {key: mean(rating[key] for rating in ratings) for key in DIMENSIONS}
        mapped[style] = {
            "score": sum(scores.values()), "dimensions": scores,
            "pass_scores": [sum(rating[key] for key in DIMENSIONS) for rating in ratings],
            "rationales": [rating["rationale"] for rating in ratings],
            "gate": disqualified(pairs[style], ratings, visible, future),
        }
    write_json(path, {"orders": [order, order[::-1]], "passes": passes, "styles": mapped})
    return case_id, "ok"


def compare(style, baseline):
    # A complete valid pair outranks one with either candidate disqualified.
    left = (not style["gate"]["candidates"], style["score"])
    right = (not baseline["gate"]["candidates"], baseline["score"])
    return (left > right) - (left < right)


def export(output, cases, styles, baseline):
    rows = {case_id: read(output / case_id / "judgment.json").get("styles")
            for case_id in cases}
    available = [row for row in rows.values() if row]
    baseline_name = styles[baseline][0]
    report = [
        "# 金融假說風格 benchmark", "",
        f"已完成 {len(available)}/{len(cases)} 案雙順序評分。產生模型為 `{MODEL}`，評審為 `{JUDGE}`。",
        f"每案的 {len(styles)} 種方法用同一份截止日證據及同一模型，各呼叫一次，評估兩條假說。",
        "兩輪評審交換匿名候選的呈現順序。每項 0 至 2 分，表格使用兩輪平均。",
        "完整合格的假說組在配對比較時優先。若合格狀態相同，配對比較使用兩輪平均分。",
        "不在快照內的引用由程式判定。兩輪評審均指出同一候選引用的原文反證或事後事實時，該候選也判不合格。",
        "分數衡量寫出可驗證研究假說的品質。日後是否實現須另以事前固定的結果定義評估。", "",
        f"| 風格 | 平均／10 | 證據 | 機制 | 預測 | 失效 | 差異 | 合格組 | 對{baseline_name}勝／和／負 | 順序反轉* |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    if baseline == "astra-direct":
        report[2:2] = [
            "純 Astra 使用簡短請求和共用結構化輸出。現行 Harness 經正常報告流程產生多空假說，"
            "轉成相同評分欄位，從原稿映射引文。這組保留原始報告，假說若無獨立財務重要性欄位即留空。",
            "所有方法均停用搜尋。評分只看假說及其引用。", "",
        ]
    summary = {"completed_cases": len(available), "planned_cases": len(cases), "baseline": baseline, "styles": {}}
    for style, (name, _) in styles.items():
        scores = [row[style] for row in available]
        outcomes = [compare(row[style], row[baseline]) for row in available]
        means = {key: round(mean(row["dimensions"][key] for row in scores), 2)
                 for key in DIMENSIONS} if scores else {}
        wins_ties_losses = [outcomes.count(value) for value in (1, 0, -1)]
        inversions = sum(
            (row[style]["pass_scores"][0] - row[baseline]["pass_scores"][0])
            * (row[style]["pass_scores"][1] - row[baseline]["pass_scores"][1]) < 0
            for row in available
        )
        seconds = [read(output / case_id / f"{style}.json")["seconds"] for case_id, row in rows.items() if row]
        data = {
            "mean_out_of_10": round(mean(row["score"] for row in scores), 2) if scores else None,
            "dimension_means": means,
            "eligible": sum(not row["gate"]["candidates"] for row in scores),
            "versus_baseline": wins_ties_losses if style != baseline else None,
            "median_seconds": round(median(seconds), 2) if seconds else None,
            "order_inversions_vs_baseline": inversions if style != baseline else None,
            "rating_order_mean_absolute_difference": round(mean(
                abs(row["pass_scores"][0] - row["pass_scores"][1]) for row in scores
            ), 2) if scores else None,
        }
        summary["styles"][style] = data
        cells = [data["mean_out_of_10"], *(means.get(key) for key in DIMENSIONS)]
        values = " | ".join("—" if value is None else f"{value:.2f}" for value in cells)
        contest = "/".join(map(str, wins_ties_losses)) if scores and style != baseline else "—"
        inversion = str(inversions) if scores and style != baseline else "—"
        report.append(f"| {name} | {values} | {data['eligible']}/{len(available)} | {contest} | {inversion} |")

    report += ["", f"*交換匿名呈現順序後，相對{baseline_name}的分差正負號反轉的案數。", "", "## 逐案分數", "",
               "| 案例 | " + " | ".join(name for name, _ in styles.values()) + " |",
               "|---|" + "---:|" * len(styles)]
    records = ["# 完整假說與評語", ""]
    for case_id, (name, frozen) in cases.items():
        grades = rows[case_id]
        scores = [f"{grades[style]['score']:.1f}" + ("†" if grades[style]["gate"]["candidates"] else "")
                  if grades else "—" for style in styles]
        report.append(f"| {case_id} {name} | {' | '.join(scores)} |")
        records.extend([f"## {case_id} {name}", "", frozen["event_text"], "",
                        f"截止時點 {frozen['as_of']}，觀察至 {frozen['horizon']}。", ""])
        for style, (style_name, _) in styles.items():
            result = read(output / case_id / f"{style}.json")
            records += [f"### {style_name}", ""]
            if not result.get("hypotheses"):
                records += [result.get("error", "尚無輸出。"), ""]
                continue
            for index, hypothesis in enumerate(result["hypotheses"].values(), 1):
                records += [f"**{index}. {hypothesis['company']}**", ""]
                for key, label in (("mechanism", "機制"), ("catalyst", "催化劑"), ("prediction", "預測"),
                                   ("invalidation", "失效條件"), ("materiality", "財務重要性")):
                    records.append(f"- **{label}**　{hypothesis[key]}")
                records.extend(["- **來源**　" + ("、".join(hypothesis["evidence_ids"]) or "未引用"), ""])
            if grades:
                grade = grades[style]
                records += [f"評分 {grade['score']:.1f}/10。", ""]
                records.extend(f"- {rationale}" for rationale in grade["rationales"])
                if grade["gate"]["candidates"]:
                    records.append(f"- 不合格候選 {grade['gate']['candidates']}。請見該案的 judgment.json。")
                records.append("")
        records += ["### 凍結證據", ""]
        records.extend(f"- [{row['id']}]({row['source']})　{row['quote']}" for row in frozen["evidence"])
        records.append("")
    report += ["", "† 代表至少一條候選未通過事實、時點或引用檢查。分數仍呈現原始 rubric 評分。"]
    write_json(output / "summary.json", summary)
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (output / "hypotheses-and-reviews.md").write_text("\n".join(records) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    comparison = parser.add_mutually_exclusive_group()
    comparison.add_argument("--compare-astra", action="store_true", help="Add direct Astra and the production Harness.")
    comparison.add_argument("--head-to-head", action="store_true", help="Compare only production Harness and direct Astra.")
    parser.add_argument("--holdout", action="store_true", help="Run the four separate validation cases.")
    parser.add_argument("--case", action="append", help="Filter which case IDs to run. Repeat if needed.")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    compare_astra = args.compare_astra or args.head_to_head
    styles = ASTRA_COMPARISON if compare_astra else STYLES
    if args.head_to_head:
        styles = {name: styles[name] for name in ("astra-direct", "current-harness")}
    baseline = "astra-direct" if compare_astra else "bull-bear"
    default_output = f"hypothesis-astra-v{Codex.prompt_version}" if compare_astra else "hypothesis-benchmark"
    if args.head_to_head:
        default_output = f"hypothesis-head-to-head-v{Codex.prompt_version}"
    if args.holdout:
        default_output += "-holdout"
    output = args.output or Path("output") / default_output
    profiles = load_cases(holdout=args.holdout)
    selected = set(args.case or profiles)
    if selected - profiles.keys() or args.workers < 1:
        parser.error("Use valid case IDs and at least one worker.")
    cases = {case_id: (name, freeze(event)) for case_id, (name, event) in profiles.items()}
    later = {case_id: future_disclosures(event) for case_id, (_, event) in profiles.items()}
    manifest = {
        "model": MODEL, "judge": JUDGE, "effort": EFFORT, "styles": styles,
        "generator": GENERATOR, "rubric": JUDGE_RULES, "cases": cases, "judge_only": later,
    }
    if compare_astra:
        manifest["production_prompt_version"] = Codex.prompt_version
    # A digest protects cached results against prompt, model or evidence changes.
    spec = json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode()
    identity = {"sha256": hashlib.sha256(spec).hexdigest()}
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        if read(manifest_path)["sha256"] != identity["sha256"]:
            parser.error("Benchmark configuration changed. Use a new --output directory.")
    else:
        output.mkdir(parents=True, exist_ok=True)
        write_json(manifest_path, {**identity, **manifest})
    for case_id in cases:
        (output / case_id).mkdir(exist_ok=True)
    if args.prepare_only:
        print(f"Prepared {len(cases)} frozen cases.")
        return
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        os.environ["RESEARCH_CODEX_MODEL"] = MODEL
        generations = [pool.submit(generate, output, case_id, frozen, profiles[case_id][1], style)
                       for case_id, (_, frozen) in cases.items() if case_id in selected for style in styles]
        for future in as_completed(generations):
            print(*future.result(), flush=True)
        os.environ["RESEARCH_CODEX_MODEL"] = JUDGE
        judgments = [pool.submit(score_case, output, case_id, frozen, later[case_id], styles)
                     for case_id, (_, frozen) in cases.items() if case_id in selected]
        for future in as_completed(judgments):
            print("judge", *future.result(), flush=True)
    export(output, cases, styles, baseline)
    if any(not read(output / case_id / "judgment.json").get("styles") for case_id in selected):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
