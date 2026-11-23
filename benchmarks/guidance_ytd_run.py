"""Seal and run equal-budget paired cumulative-revenue evaluations."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import signal
from threading import Event
from time import monotonic

from benchmarks import guidance_arithmetic as b
from benchmarks import guidance_ytd as y
from research_app.schema import Nonempty

OUT = Path("output/guidance-ytd")
GENERATION = ("extract", "astra")
ARMS = ("current", "revised", "astra")
V2_SHA = "ec3463791b7bc018c831452d1e23c07817b2bd6e98bc952bbf264300406ddab1"
CALC_SHA = "554af69edec311b28a286f7264c12893e803c9259133d70600f6aec7eece7982"
DIRECTION = "implied_remainder"


class Direct(b.Answers):
    figures_used: list[b.ExtractedFigure]
    missing_reason: Nonempty | None


def read(path):
    return b.equal.hypothesis.read(path)


def seal(root, inputs, *, extra_protocol=None, gold_for=None, direct_instruction='', both_directions=True):
    if (root / "protocol.json").exists():
        raise ValueError("本批已封存")
    sealed, requests = {}, {}
    if sha256(Path(b.__file__).read_bytes()).hexdigest() != V2_SHA:
        raise ValueError("v2 擷取提示原始碼不同")
    if sha256(Path("research_app/guidance_arithmetic.py").read_bytes()).hexdigest() != CALC_SHA:
        raise ValueError("算式原始碼不同")
    for row in inputs:
        case = b.Case.model_validate(row["case"])
        blocks = b.case_blocks(case)
        gold = {name: str(value) for name, value in (gold_for(row, case, blocks) if gold_for else b.gold(case, blocks)).items()}
        v2 = b.requests_for(case, blocks)
        direct_json = json.loads(v2["astra"]["prompt"].rsplit("\n\n", 1)[-1])
        extract_json = json.loads(v2["harness"]["prompt"].rsplit("\n\n", 1)[-1])
        assert direct_json["documents"] == extract_json["documents"]
        instruction = b.DIRECT + (
            " In figures_used cite each original operand used for your answer, using its exact document ID, "
            "block ID and amount. Name them new (latest fiscal-year outlook), prior (previous fiscal-year outlook), "
            "prior_interim (the previous Q3 outlook), reported_in_period (latest actuals to date), or "
            "prior_reported_in_period (previous actuals to date). Include the exact units heading for tables. "
            "If the first monetary row supplies the currency marker, the same-table units quote may include "
            "the contiguous span from the scale heading up to that currency marker. List exact evidence_ids. "
            "When the outlook comparison cannot be supported, name the specifically missing evidence in missing_reason. "
            "Perform the calculation yourself in this same response."
        ) + direct_instruction
        requests[case.id] = {"extract": v2["harness"],
                             "astra": b.equal.make_request(Direct, instruction, direct_json)}
        sealed[case.id] = row | {"case": case.model_dump(mode="json"), "gold": gold}
    by_split = {split: [row for row in sealed.values() if row["case"]["split"] == split]
                for split in ("pilot", "holdout")}
    if len(by_split["pilot"]) != 4 or len(by_split["holdout"]) != 8:
        raise ValueError("must use 4 pilot cases and 8 holdout cases")
    if len({row["case"]["ticker"] for row in sealed.values()}) != 12:
        raise ValueError("issuer overlap")
    if sum(bool(row["case"]["undetermined"]) for row in by_split["holdout"]) != 4:
        raise ValueError("holdout must be balanced")
    if both_directions and not {"raised", "lowered", "unknown"} <= {row["gold"].get(DIRECTION) for row in by_split["pilot"]}:
        raise ValueError("pilot needs positive revisions both directions and an unsupported case")
    protocol = {
        "sealed_at": b.equal.journal.now(), "hypothesis": "累計期間與財務欄位證據可增加可計算案例全對而維持零誤調。",
        "model": b.equal.hypothesis.MODEL, "effort": b.equal.hypothesis.EFFORT, "search": False,
        "timeout_seconds": b.TIMEOUT, "single_worker": True, "one_attempt_per_arm": True,
        "source_sha256": {name: sha256(Path(name).read_bytes()).hexdigest() for name in (
            b.__file__, y.__file__, __file__, "research_app/guidance_arithmetic.py", "research_app/financial_units.py")},
        "cases_sha256": b.equal.digest(sealed), "requests_sha256": b.equal.digest(requests),
        "primary": "新舊隱含金額、差額、方向及來源欄位或證據不足理由須同時正確。時間及幣別錯不可得分。",
        "tolerance": "金額採既有 1% 或封存精度 1/100 的較大者。方向完全一致。Astra 逐欄給引用。",
        "citation": "正例須支持五項可見的金額基礎，核對封存原文字面與可接受欄位。"
                    "負例須明確 unknown、提出本案缺少的條件並指向點時公告。",
        "pilot_gate": {"complete": 4, "new_exact_min": 3, "new_positive_min": 1, "false_adjustments_max": 0},
        "holdout_gate": {"complete": 8, "new_positive_min": 3, "new_negative_min": 3, "false_adjustments_max": 0},
        "improvement": "通過保留集基本門檻、正例比現版多至少一案且負例不退步。",
        "lead": "通過保留集基本門檻、全對數比純 Astra 多至少兩案。",
        "stop": "先導未過立即停止，保留失敗回傳並輸出未開始的保留集。先導通過後跑完八個保留集即停止。"
                "同一次擷取並行經兩版驗證器，純 Astra 獨立回覆。服務容量或限流時停止派發，已開始者計入預算。",
    }
    protocol.update(extra_protocol or {})
    root.mkdir(parents=True, exist_ok=True)
    for targ, value in (("cases", sealed), ("requests", requests), ("protocol", protocol)):
        b.equal.journal.atomic(root / f"{targ}.json", value)
    return protocol


def inputs_at(root):
    cases, requests = b.read_sealed(root)
    return cases, requests, read(root / "protocol.json")


def refs_for(raw):
    groups = {}
    for row in raw:
        figure = b.FigureRef.model_validate({key: value for key, value in row.items() if key != "name"})
        groups.setdefault(row["name"], []).append(figure)
    return groups


def current_errors(errors):
    categories = []
    for name, value in errors.items():
        if any(token in value for token in ("倍率", "幣別", "單位", "scale", "currency")):
            categories.append("單位錯")
        elif name == "inputs":
            categories.append("缺季或重疊")
        else:
            categories.append("引文不足")
    return categories


def positive_citations(case, blocks, model_figures):
    proposed = refs_for(model_figures)
    wrong = []
    for name, approved in case.figures.items():
        selected = proposed.get(name, [])
        if not selected:
            wrong.append((name, "引文不足"))
            continue
        try:
            left = b.figure_value(name, selected, blocks)
            right = b.figure_value(name, approved, blocks)
        except ValueError as exc:
            wrong.append((name, "單位錯" if any(s in str(exc) for s in ("倍率", "幣別", "單位")) else "引文不足"))
            continue
        available = {ref.document for ref in approved}
        same_column = {ref.block for ref in approved}.issubset({ref.block for ref in selected})
        if left != right or {ref.document for ref in selected} != available:
            wrong.append((name, "期間選錯" if name in b.REMAINDER[2:4] else "口徑不符"))
        elif not same_column:
            wrong.append((name, "引文不足"))
    return wrong


def grade(row, case, blocks, answers, figures, errors, rationale, missing_source=False, categories=()):
    gold = b.gold(case, blocks)
    marks = b.grade(case, gold, answers)
    false_adjustment = bool(case.undetermined and any(
        str(value).strip().casefold() not in {"", "unknown"} for value in answers.values()))
    if case.undetermined:
        if missing_source or not any(token.casefold() in rationale.casefold() for token in row["gap_terms"]):
            citation_failures = [("missing_reason", "引文不足")]
        else:
            citation_failures = []
    else:
        citation_failures = positive_citations(case, blocks, figures)
    flags = [*categories, *current_errors(errors), *(kind for _, kind in citation_failures)]
    if not marks["exact"] and not flags:
        flags.append("口徑不符" if false_adjustment else "算錯")
    return marks | {"numeric_exact": marks["exact"], "exact": marks["exact"] and not citation_failures,
                    "citation_failures": citation_failures, "false_adjustment": false_adjustment,
                    "failure_dimensions": sorted(set(flags)) if not (marks["exact"] and not citation_failures) else []}


def normalize(arm, payload, response):
    row, case, blocks = payload
    if arm == "astra":
        direct = Direct.model_validate(response).model_dump(mode="json")
        answers = {answer["item"]: answer["value"] for answer in direct["answers"]}
        cited = any(ref in blocks and ref.startswith(case.documents[0].id + ":") for ref in direct["evidence_ids"])
        return {"raw": direct, "arms": {"astra": grade(row, case, blocks, answers, direct["figures_used"],
                    {}, direct["missing_reason"] or direct["reason"], missing_source=not cited)}}
    ext = b.Extraction.model_validate(response)
    raw = ext.model_dump(mode="json")
    current, errors = b.harness_answers(case, blocks, ext)
    new = y.revised(case, blocks, ext, row["vintages"])
    # A removed unresolved required operand also gives the analyst a specific missing-field explanation.
    gaps = lambda info: " ".join(f"{k} {v}" for k, v in info.items())
    return {"raw": raw, "validation": new, "arms": {
        "current": grade(row, case, blocks, current, raw["figures"], errors, gaps(errors)),
        "revised": grade(row, case, blocks, new["answers"], new["figures"], new["errors"],
                         gaps(new["errors"]), categories=new["categories"].values()),
    }}


def phase_status(root, cases, split):
    ids = [key for key, row in cases.items() if row["case"]["split"] == split]
    data, failed = {}, []
    paired = 0
    for key in ids:
        outcomes = [b.equal.receipt(root, key, arm) for arm in GENERATION]
        data[key] = dict(item for outcome in outcomes if outcome.get("status") == "completed"
                         for item in outcome["arms"].items())
        paired += len(data[key]) == 3
        failed.extend({"case": key, "call": arm, "status": (result or {}).get("status", "not_started"),
                       "reason": (result or {}).get("reason")}
                      for arm, result in zip(GENERATION, outcomes) if result.get("status") != "completed")
    metrics = {}
    for arm in ARMS:
        marks = [(key, by_arm[arm]) for key, by_arm in data.items() if arm in by_arm]
        metrics[arm] = {
            "exact": sum(m["exact"] for _, m in marks),
            "positive": sum(m["exact"] and not cases[key]["case"]["undetermined"] for key, m in marks),
            "negative": sum(m["exact"] and bool(cases[key]["case"]["undetermined"]) for key, m in marks),
            "false_adjustments": sum(m["false_adjustment"] for _, m in marks),
            "numeric_exact": sum(m["numeric_exact"] for _, m in marks),
            "numeric_with_bad_citation": sum(m["numeric_exact"] and not m["exact"] for _, m in marks),
            "false_abstentions": sum(m.get("false_abstention", False) for _, m in marks),
        }
    new, old, astra = (metrics[arm] for arm in ("revised", "current", "astra"))
    if split == "pilot":
        passed = paired == 4 and new["exact"] >= 3 and new["positive"] >= 1 and new["false_adjustments"] == 0
    else:
        passed = paired == 8 and new["positive"] >= 3 and new["negative"] >= 3 and new["false_adjustments"] == 0
    return {"planned": len(ids), "paired": paired, "metrics": metrics, "passed": passed, "scores": data,
            "improved": split == "holdout" and passed and new["positive"] > old["positive"] and new["negative"] >= old["negative"],
            "leads": split == "holdout" and passed and new["exact"] - astra["exact"] >= 2, "failed": failed}


def run(root, split, stop, *, transform=normalize):
    cases, requests, _ = inputs_at(root)
    if split == "holdout" and not phase_status(root, cases, "pilot")["passed"]:
        print("先導未通過，保留集維持未開始", flush=True)
        return
    keys = [key for key, row in cases.items() if row["case"]["split"] == split]
    for index, key in enumerate(keys):
        row = cases[key]
        case = b.Case.model_validate(row["case"])
        payload = row, case, b.case_blocks(case)
        for arm in (GENERATION if index % 2 == 0 else GENERATION[::-1]):
            if stop.is_set():
                return
            job = b.equal.queue_job(root, key, arm)
            record = b.equal.attempt(root, job, payload, requests[key][arm], stop,
                monotonic() + b.equal.journal.budget(1, 1, b.TIMEOUT), b.TIMEOUT,
                transform=transform, model=b.equal.hypothesis.MODEL)
            print(key, arm, record["status"], record.get("reason") or "", flush=True)
            if record.get("reason") in b.equal.AVAILABILITY_ERRORS:
                stop.set()
                return


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--phase", choices=("seal", "run", "report"), required=True)
    cli.add_argument("--out", type=Path, default=OUT)
    cli.add_argument("--cases", type=Path, default=OUT / "case-input.json")
    args = cli.parse_args()
    signal_stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: signal_stop.set())
    with b.equal.journal.exclusive(args.out):
        if args.phase == "seal":
            print(seal(args.out, read(args.cases))["sealed_at"])
        elif args.phase == "run":
            for split in ("pilot", "holdout"):
                if not signal_stop.is_set():
                    run(args.out, split, signal_stop)
            for split in ("pilot", "holdout"):
                cases, _, _ = inputs_at(args.out)
                summary = phase_status(args.out, cases, split)
                b.equal.journal.atomic(args.out / f"summary-{split}.json", summary)
                print(split, {key: value for key, value in summary.items() if key not in ("failed", "scores")}, flush=True)
        else:
            from benchmarks.guidance_ytd_report import publish
            publish(args.out)


if __name__ == "__main__":
    main()
