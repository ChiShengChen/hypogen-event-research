"""Seal an equal-budget transmission benchmark and prepare anonymous human review."""

import argparse
from pathlib import Path
import signal
import sqlite3
from statistics import median
from threading import Event
from time import monotonic

from benchmarks import v9_equal as equal
from benchmarks import v9_equal_review as review
from benchmarks.hypothesis_pilot import read
from research_app.schema import Nonempty, Schema
from pydantic import Field

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "docs/v9-equal-recovery"
HELD_OUT = ROOT / "docs/v9-equal"
COHORTS = ("earnings-prospective", "earnings-horizon-prospective", "earnings-residual-prospective")

COMMON = (
    "Draft an earnings-event research first page in Traditional Chinese. Include a primary financial transmission, "
    "necessary condition, financial effect and basis for the magnitude, strongest alternative explanation, "
    "one public observation that distinguishes them, falsifier, and original evidence IDs. Separate disclosed facts "
    "from inference. Indicate any change to a frozen estimate only when a comparable estimate is present. "
    "Use null for a transmission that cannot be supported, and state what is missing."
)
HARNESS = (
    " Before choosing the primary link, inspect disclosed commitments, named counterparties, resource movements, "
    "operating arrangements and distribution changes. Compare candidates by both endpoints, known economic size, "
    "necessary conditions and a public observation. Check that timing versus demand, reported versus adjusted, "
    "and product versus consolidated revenue are separately testable."
)
PROTOCOL = {
    "design": "research_memo_primary_transmission_v1", "model": equal.hypothesis.MODEL,
    "reasoning_effort": equal.hypothesis.EFFORT, "search": "disabled", "workers": 1,
    "max_calls_per_arm_case": 1, "per_call_seconds": equal.TIMEOUT, "token_hard_cap": None,
    "calibration": "4 complete archived V9 pairs, requiring 4 paired human ratings before dispatch",
    "holdout": "8 already sealed V9 issuers with no generation in the prior V9 flow",
    "endpoint": "at least 6/8 usable and two more usable than Astra, with no more major errors",
    "secondary": "paired median active edit time, complete pair rate, input/output tokens, wall time",
    "scope": "qualitative transmission; the sealed cases have no contemporaneous financial workbook or consensus",
    "stop": "stop dispatch on CLI rate limits or capacity. Preserve attempts. No resampling or replacing launched calls.",
}


class Transmission(Schema):
    mechanism: Nonempty
    necessary_condition: Nonempty
    financial_effect: Nonempty
    alternative: Nonempty
    public_discriminator: Nonempty
    falsifier: Nonempty
    evidence_ids: list[Nonempty] = Field(min_length=1, max_length=8)


class Draft(Schema):
    point_in_time_facts: list[Nonempty] = Field(max_length=3)
    primary: Transmission | None
    gaps: list[Nonempty] = Field(max_length=5)


def sealed(out, *, write=False):
    cases = {key: {name: case[name] for name in ("name", "split", "input")}
             for key, case in read(HELD_OUT / "cases.json").items() if case["split"] == "holdout"}
    old = read(CALIBRATION / "cases.json")
    targets = {case["event"]["research_target"].casefold() for case in old.values()}
    held_targets = [case["event"]["research_target"].casefold() for case in read(HELD_OUT / "cases.json").values()
                    if case["split"] == "holdout"]
    if len(set(held_targets)) != 8 or targets.intersection(held_targets):
        raise ValueError("保留集案數或發行人不符。")
    requests = {key: {arm: equal.make_request(Draft, COMMON + (HARNESS if arm == "v9" else ""), case["input"])
                      for arm in equal.ARMS} for key, case in cases.items()}
    manifest = PROTOCOL | {"case_sha256": equal.digest(cases), "requests_sha256": equal.digest(requests),
                           "implementation_sha256": equal.digest(Path(__file__).read_text(encoding="utf-8"))}
    stored = read(out / "memo-protocol.json")
    if not stored and write:
        equal.journal.atomic(out / "memo-cases.json", cases)
        equal.journal.atomic(out / "memo-requests.json", requests)
        equal.journal.atomic(out / "memo-protocol.json", manifest)
    elif (stored != manifest or read(out / "memo-cases.json") != cases
          or read(out / "memo-requests.json") != requests):
        raise ValueError("正式案例、請求或程式和封存不一致。")
    return cases, requests


def calibration(out, ratings_path=None):
    cases = read(CALIBRATION / "cases.json")
    summary = read(CALIBRATION / "summary.json")
    chosen = {}
    for key, name in summary["per_case_selected_round"].items():
        if name:
            pairs = {arm: read(CALIBRATION / "raw" / name / "calls" / f"{key}-{arm}.json")["hypotheses"]
                     for arm in equal.ARMS}
            chosen[key] = cases[key], pairs
    key = review.anonymous_keys(out, chosen)
    package = out / "calibration"
    package.mkdir(exist_ok=True)
    review.blind_files(package, chosen, key)
    entered = review.import_ratings(ratings_path, chosen, key)
    return {"pairs_ready": len(chosen), "human_completed_pairs": sum(
        all((case, arm) in entered for arm in equal.ARMS) for case in chosen)}


def normalize(arm, case, response):
    candidate = Draft.model_validate(response).model_dump(mode="json")
    if arm == "v9" and candidate["primary"]:
        refs = {row["id"] for row in case["input"]["evidence"]}
        if not set(candidate["primary"]["evidence_ids"]) <= refs:
            candidate["primary"] = None
            candidate["gaps"].append("主要傳導引用在封存證據中找不到。")
    return {"candidate": candidate, "original": response}


def run(out, cases, requests, stop):
    pending = []
    for key, arms in equal.stage_jobs(cases, "holdout"):
        for arm in arms:
            job = equal.queue_job(out, key, arm)
            state = equal.journal.restore(out, job)
            if state.get("reason") in equal.AVAILABILITY_ERRORS:
                return
            if state["status"] == "queued":
                pending.append((job, key, arm))
    deadline = monotonic() + equal.journal.budget(len(pending), 1, equal.TIMEOUT)
    for job, key, arm in pending:
        if stop.is_set() or monotonic() >= deadline:
            break
        result = equal.attempt(out, job, cases[key], requests[key][arm], stop, deadline, equal.TIMEOUT, transform=normalize)
        if result.get("reason") in equal.AVAILABILITY_ERRORS or result["status"] == "queued":
            break


def formal_review(out, cases, ratings_path):
    pairs = {key: {arm: equal.receipt(out, key, arm) or read(out / "jobs" / f"{key}-{arm}" / "state.json")
                   for arm in equal.ARMS} for key in cases}
    completed = {key: row for key, row in pairs.items() if all(row[arm].get("status") == "completed" for arm in equal.ARMS)}
    hashable = {key: (cases[key], {arm: {"memo": {"candidate": record["candidate"]}}
                                   for arm, record in row.items()}) for key, row in completed.items()}
    keys = review.anonymous_keys(out / "holdout", hashable)
    lines = ["# 財報預估修正稿｜匿名傳導覆核", ""]
    for key, mapping in keys.items():
        case = cases[key]["input"]
        lines.extend([f"## {key}", "", cases[key]["name"], "", "### 封存證據", ""])
        for item in case["evidence"]:
            lines.append(f"- {item['id']}　{item.get('quote', item.get('text', ''))}　{item.get('source', '')}")
        for label, entry in mapping.items():
            draft = completed[key][entry["arm"]]["candidate"]
            lines.extend(["", f"### {label}", "", *[f"- 事實　{fact}" for fact in draft["point_in_time_facts"]]])
            if draft["primary"]:
                lines.extend(f"- {field}　{value}" for field, value in draft["primary"].items())
            lines.extend(f"- 缺口　{gap}" for gap in draft["gaps"])
    review.write_text(out / "holdout" / "analyst-review.md", lines)
    review.write_csv(out / "holdout" / "review-form.csv", review.REVIEW_FIELDS,
                     ({"case": case, "code": label} for case, mapping in keys.items() for label in mapping))
    entered = review.import_ratings(ratings_path, completed, keys)
    complete = [key for key in completed if all((key, arm) in entered for arm in equal.ARMS)]
    metrics = {arm: {"ready": sum(entered[key, arm]["ready"] for key in complete),
                     "major_errors": sum(entered[key, arm]["major_errors"] for key in complete),
                     "median_edit_seconds": median(entered[key, arm]["edit_seconds"] for key in complete) if complete else None}
               for arm in equal.ARMS}
    h, a = metrics["v9"], metrics["astra"]
    return {"planned": len(cases), "paired": len(completed), "human_completed_pairs": len(complete),
            "human_metrics": metrics if complete else None,
            "passed": (h["ready"] >= 6 and h["ready"] >= a["ready"] + 2 and h["major_errors"] <= a["major_errors"])
            if len(complete) == 8 else None,
            "model_calls": sum(bool(call.get("started_at")) for row in pairs.values() for call in row.values()),
            "execution": {arm: {
                "completed_calls": sum(row[arm].get("status") == "completed" for row in pairs.values()),
                "started_calls": sum(bool(row[arm].get("started_at")) for row in pairs.values()),
                "observed_seconds": sum(row[arm].get("elapsed_seconds") or 0 for row in pairs.values()),
                "measured_tokens": {field: sum((row[arm].get("usage") or {}).get(field, 0) for row in pairs.values())
                                    for field in review.USAGE},
            } for arm in equal.ARMS}}


def prospective():
    summary = {}
    for name in COHORTS:
        path = ROOT / "output" / name / "cohort.sqlite3"
        if path.is_file():
            with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
                summary[name] = {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                                 for table in ("cases", "submissions", "actuals")}
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "output/revision-memo-review")
    parser.add_argument("--phase", choices=("seal", "run", "report"), required=True)
    parser.add_argument("--calibration-ratings", type=Path)
    parser.add_argument("--holdout-ratings", type=Path)
    args = parser.parse_args()
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with equal.journal.exclusive(args.out):
        cases, requests = sealed(args.out, write=args.phase == "seal")
        ready = calibration(args.out, args.calibration_ratings)
        (args.out / "holdout").mkdir(exist_ok=True)
        if args.phase == "run":
            if ready["human_completed_pairs"] != 4:
                parser.exit(2, "人工校準尚未完成四案，正式呼叫維持未啟動。\n")
            run(args.out, cases, requests, stop)
        result = {"calibration": ready, "formal": formal_review(args.out, cases, args.holdout_ratings),
                  "prospective": prospective()}
        equal.journal.atomic(args.out / "summary.json", result)
        print(result)


if __name__ == "__main__":
    main()
