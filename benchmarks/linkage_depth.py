"""Run the sealed point-in-time business linkage comparison."""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from math import ceil
from pathlib import Path
import signal
from threading import Event
from time import monotonic
from typing import Literal

from pydantic import Field

from benchmarks import v9_equal as equal
from benchmarks.hypothesis_cases import freeze
from benchmarks.linkage_depth_cases import CASES
from research_app.adapters import AdapterError
from research_app.business_linkage import BusinessLinkageGeneration, LinkedHypotheses, linkage_fields
from research_app.research import build_report
from research_app.schema import Event as ResearchEvent, Nonempty, Schema

OUT = Path("output/linkage-depth")
ARMS = ("astra", "harness")
CHECKS = ("evidence", "mechanism", "financial_effect", "falsifier")
DIRECT = "根據這份事件和截止時點可用的資料，寫一份可供研究員覆核的繁體中文研究首稿。"
GRADE = (
    "Independently audit each anonymous report against the supplied point-in-time evidence and frozen case standard. "
    "Check all submitted linkages in listed order. Report one CandidateGrade per displayed linkage, with 1-based index. "
    "For evidence check both endpoints and whether the factual premise is actually supported, not just cited. "
    "For mechanism check a precise directional operating step and a necessary observable condition. "
    "For financial_effect check the direction and metric at the correct business, calibrated to the available amounts. "
    "For falsifier check a named public source and same-period observable result that discriminates the mechanism "
    "from at least one plausible alternate explanation. A milestone may verify the mechanism without certifying "
    "financial materiality if the limitations are clear. A missing disclosure is not a falsifier. "
    "target_path means the link genuinely addresses the specified standard or an equally supported equivalent. "
    "major_error is reserved for an affirmative unsupported claim of resource transfer, cross-company order or "
    "customer diversion, an assertion that concurrent guidance proves causation, or material false facts, money "
    "or attribution. Mark every such error even if another linkage passes. A hypothesis explicitly conditional on "
    "unconfirmed evidence is not an affirmative claim. Evaluate the entire submission for major_error, including "
    "the gap. On a negative case set gap_ok only if the gap or a path names missing evidence specific to the trap "
    "and explicitly withholds its attribution. A separate evidenced transmission is compatible with that judgment. "
    "On a positive case gap_ok is informational only. Score evidence and logic, not style, size, labels or known "
    "later results. Return concise Traditional Chinese notes and one verdict per anonymous label."
)
COOLDOWN_CAP = 900


class CandidateGrade(Schema):
    index: int = Field(ge=1, le=3)
    target_path: bool
    evidence: bool
    mechanism: bool
    financial_effect: bool
    falsifier: bool
    major_error: bool
    note: Nonempty


class Verdict(Schema):
    label: Literal["A", "B"]
    gap_ok: bool
    major_error: bool
    candidates: list[CandidateGrade] = Field(max_length=3)
    note: Nonempty


class Comparison(Schema):
    verdicts: list[Verdict] = Field(min_length=2, max_length=2)


class CaptureLinked(BusinessLinkageGeneration, equal.Capture):
    pass


class ReplayLinked(BusinessLinkageGeneration, equal.Replay):
    identity = equal.Replay.identity | {"prompt_version": 10}


def capture(event):
    try:
        build_report(event, CaptureLinked())
    except equal.Captured as exc:
        response_schema, instruction, context = exc.request
        return equal.make_request(response_schema, instruction, context), context
    raise ValueError("未取得正式 Harness 請求")


def prepared():
    cases, requests = {}, {}
    for key, case in CASES.items():
        event = ResearchEvent.model_validate(case["event"])
        base = freeze(event)
        harness, actual = capture(event)
        if any(actual[field] != value for field, value in base.items()) or event.search_mode != "off":
            raise ValueError("兩組點時資料不同")
        cases[key] = case | {"input": base}
        requests[key] = {"harness": harness, "astra": equal.make_request(LinkedHypotheses, DIRECT, base)}
    issuers = {case["issuer"] for case in cases.values()}
    if len(issuers) != 12 or issuers & {"Ford", "ASML", "Disney"}:
        raise ValueError("正式案例須為互異的新發行人")
    return cases, requests


def seal(root):
    cases, requests = prepared()
    code = [__file__, Path(__file__).with_name("linkage_depth_cases.py"), equal.__file__,
            equal.journal.__file__, equal.research.__file__, equal.adapters.__file__,
            Path(equal.adapters.__file__).with_name("business_linkage.py"), equal.schema.__file__,
            equal.admission.__file__]
    rules = {
        "source_sha256": {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in code},
        "cases_sha256": equal.digest(cases), "requests_sha256": equal.digest(requests),
        "generation_model": equal.hypothesis.MODEL, "grading_model": equal.hypothesis.JUDGE,
        "effort": equal.hypothesis.EFFORT, "search": "disabled", "workers": 1, "max_paths": 3,
        "generation_timeout_seconds": equal.TIMEOUT, "grading_timeout_seconds": equal.JUDGE_TIMEOUT,
        "generation_attempts_per_arm": 1, "grading_attempts_per_pair": 1, "hard_token_cap": None,
        "grading_prompt": GRADE,
        "rubric": {
            "rule_check": "每條另核對非空、可見的起點與受影響引文及期限。Harness 使用產品實際發布的欄位，另保留被過濾的候選。",
            "positive": "至少一條同時通過程式核對、對應預註冊路徑及模型四項語義判讀，且全稿零重大錯誤。",
            "negative": "指出預註冊陷阱缺少的證據、保留歸因、稿中各條引文均有效，且零重大錯誤。",
            "gate_pilot": {"pairs": 4, "graded": 4, "harness_exact": 3, "harness_major_max": 0},
            "gate_holdout": {"pairs": 8, "graded": 8, "harness_positive_exact": 3, "harness_negative_exact": 3,
                             "harness_major_max": 0, "minimum_lead": 2},
            "truth": "先導與保留集先以已封存裁定加匿名 Sol 單次判讀作流程門檻。人工獨立覆核另計。每案的呈現順序交替。",
        },
        "stop": "先導配對與評分通過後才啟動保留集。已開始的失敗呼叫占用額度且不重試。"
                "容量或用量錯誤只對尚未開始的工作依公告冷卻，最多 900 秒，缺提示採 30 秒。"
                "等待超限即停止該批。未取得完整配對不做模型比較評分。一般中斷只接續未開始的工作。",
        "max_provider_wait_seconds": COOLDOWN_CAP,
        "regression": "Ford 和 ASML 使用已保留的 V10 原始有效連動離線驗證，排除計分。",
    }
    manifest = root / "protocol.json"
    if old := equal.hypothesis.read(manifest):
        if old != rules | {"sealed_at": old["sealed_at"]}:
            raise ValueError("此批次的封存內容或程式已更動")
        return read_sealed(root)
    if (root / "calls").exists():
        raise ValueError("已有執行紀錄但缺封存檔")
    equal.journal.atomic(root / "cases.json", cases)
    equal.journal.atomic(root / "requests.json", requests)
    manifest_data = rules | {"sealed_at": equal.journal.now()}
    equal.journal.atomic(manifest, manifest_data)
    return cases, requests, manifest_data


def read_sealed(root):
    rules = equal.hypothesis.read(root / "protocol.json")
    cases = equal.hypothesis.read(root / "cases.json")
    requests = equal.hypothesis.read(root / "requests.json")
    if equal.digest(cases) != rules["cases_sha256"] or equal.digest(requests) != rules["requests_sha256"]:
        raise ValueError("封存輸入無法核對")
    return cases, requests, rules


def normalize(arm, case, response):
    if arm == "judge":
        grades = Comparison.model_validate(response).verdicts
        if {row.label for row in grades} != {"A", "B"}:
            raise AdapterError("評判未覆蓋兩份匿名稿")
        return {"verdicts": {row.label: row.model_dump(mode="json") for row in grades}}
    output = LinkedHypotheses.model_validate(response).model_dump(mode="json")
    report = output
    if arm == "harness":
        report = build_report(ResearchEvent.model_validate(case["event"]), ReplayLinked(response))
    return {"raw_findings": linkage_fields(output), "findings": linkage_fields(report)}


def labels(key):
    return dict(zip(("A", "B"), ARMS if int(key[-2:]) % 2 else ARMS[::-1]))


def completed(root, key, arms):
    return all(equal.receipt(root, key, arm).get("status") == "completed" for arm in arms)


def judge_request(root, key, case):
    return equal.make_request(Comparison, GRADE, case["input"] | {
        "preregistered_standard": case["gold"],
        "anonymous_drafts": [{"label": label, **equal.receipt(root, key, arm)["findings"]}
                             for label, arm in labels(key).items()],
    })


def capacity_pause(root, job, record, stop):
    directory = root / "cooldowns"
    directory.mkdir(exist_ok=True)
    path = directory / f"{job.name}.json"
    decision = equal.hypothesis.read(path)
    if not decision:
        hint = equal.admission.wait_hint(job)
        seconds = ceil(hint) if hint is not None else 30
        end = datetime.fromisoformat(record["finished_at"])
        decision = {"job": job.name, "hint_seconds": hint, "wait_seconds": seconds,
                    "started_at": record["finished_at"], "status": "waiting" if seconds <= COOLDOWN_CAP else "blocked",
                    "resume_at": (end + timedelta(seconds=seconds)).isoformat()}
        equal.journal.atomic(path, decision)
    if decision["status"] != "waiting":
        return decision["status"] == "completed"
    remaining = max(0.0, (datetime.fromisoformat(decision["resume_at"]) - datetime.now(timezone.utc)).total_seconds())
    print(f"{job.name} cooldown {remaining:.1f}s", flush=True)
    if stop.wait(remaining):
        return False
    equal.journal.atomic(path, decision | {"status": "completed", "finished_at": equal.journal.now()})
    return True


def run_phase(root, cases, requests, split, stop):
    for key, case in cases.items():
        if case["split"] != split:
            continue
        for arm in (*labels(key).values(), "judge"):
            if stop.is_set():
                return
            if arm == "judge" and not completed(root, key, ARMS):
                continue
            job = equal.queue_job(root, key, arm)
            timeout = equal.JUDGE_TIMEOUT if arm == "judge" else equal.TIMEOUT
            request = judge_request(root, key, case) if arm == "judge" else requests[key][arm]
            model = equal.hypothesis.JUDGE if arm == "judge" else equal.hypothesis.MODEL
            result = equal.attempt(root, job, case, request, stop, monotonic() + equal.journal.budget(1, 1, timeout),
                                   timeout, transform=normalize, model=model)
            print(key, arm, result["status"], result.get("reason") or "", flush=True)
            if result.get("reason") in equal.AVAILABILITY_ERRORS and not capacity_pause(root, job, result, stop):
                return


def rule_check(paths, case):
    evidence = {row["id"] for row in case["input"]["evidence"]}
    start = case["input"]["as_of"][:10]
    return [
        {"index": number, "evidence": bool(path["origin_evidence_ids"] and path["affected_evidence_ids"])
         and (set(path["origin_evidence_ids"]) | set(path["affected_evidence_ids"])) <= evidence,
         "time": start <= path["deadline"] <= case["input"]["horizon"]}
        for number, path in enumerate(paths, 1)
    ]


def adjudicate(root, key, case):
    if not completed(root, key, (*ARMS, "judge")):
        return None
    grades = equal.receipt(root, key, "judge")["verdicts"]
    result = {}
    for label, arm in labels(key).items():
        verdict = grades[label]
        receipt = equal.receipt(root, key, arm)
        paths = receipt["findings"]["business_linkages"]
        rules = rule_check(paths, case)
        candidates = sorted(verdict["candidates"], key=lambda row: row["index"])
        if [row["index"] for row in candidates] != list(range(1, len(paths) + 1)):
            return None
        major = verdict["major_error"] or any(row["major_error"] for row in candidates)
        qualifying = [row["index"] for check, row in zip(rules, candidates)
                      if check["evidence"] and check["time"] and row["target_path"] and all(row[col] for col in CHECKS)]
        grounded = all(row["evidence"] and row["time"] for row in rules)
        exact = (bool(qualifying) if case["gold"]["positive"] else verdict["gap_ok"] and grounded) and not major
        failures = []
        if not exact:
            closest = max((row for row in candidates if row["target_path"]),
                          key=lambda row: sum(row[col] for col in CHECKS), default={})
            failures = [col for col in CHECKS if not closest.get(col)]
            if not grounded and "evidence" not in failures:
                failures.insert(0, "evidence")
            if not case["gold"]["positive"]:
                failures = ["mechanism"] if grounded else ["evidence", "mechanism"]
            if major and not failures:
                failures = ["mechanism"]
        result[arm] = {
            "rules": rules, "verdict": verdict, "qualifying": qualifying, "exact": exact, "major": major,
            "failure_dimensions": failures, "submitted": len(paths),
            "raw_submitted": len(receipt["raw_findings"]["business_linkages"]),
        }
    return result


def stats(root, cases, evaluated, split):
    ids = [key for key, case in cases.items() if case["split"] == split]
    pair_count = sum(completed(root, key, ARMS) for key in ids)
    graded = [key for key in ids if evaluated.get(key) is not None]
    metrics = {}
    for arm in ARMS:
        good = [key for key in graded if evaluated[key][arm]["exact"]]
        metrics[arm] = {"exact": len(good), "positive": sum(cases[key]["gold"]["positive"] for key in good),
                        "negative": sum(not cases[key]["gold"]["positive"] for key in good),
                        "major": sum(evaluated[key][arm]["major"] for key in graded)}
    gate = pair_count == len(ids) == len(graded) and metrics["harness"]["major"] == 0
    if split == "pilot":
        gate = gate and metrics["harness"]["exact"] >= 3
    else:
        gate = gate and min(metrics["harness"]["positive"], metrics["harness"]["negative"]) >= 3 and (
            metrics["harness"]["exact"] - metrics["astra"]["exact"] >= 2)
    return {"planned": len(ids), "paired": pair_count, "graded": len(graded), "metrics": metrics, "pass": gate}


def summary(root, cases):
    grades = {key: adjudicate(root, key, case) for key, case in cases.items()}
    counts = {split: stats(root, cases, grades, split) for split in ("pilot", "holdout")}
    return grades, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("seal", "pilot", "holdout", "report"), required=True)
    parser.add_argument("--out", default=OUT, type=Path)
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with equal.journal.exclusive(args.out):
        if args.phase == "report":
            from benchmarks.linkage_depth_report import publish
            cases, _, _ = read_sealed(args.out)
            publish(args.out, cases, args.report_dir or args.out / "publication")
            return
        cases, requests, _ = seal(args.out)
        if args.phase == "seal":
            print(f"Sealed {len(cases)} cases in {args.out}", flush=True)
            return
        if args.phase == "holdout" and not summary(args.out, cases)[1]["pilot"]["pass"]:
            parser.exit(2, "先導未過，保留集不執行。\n")
        run_phase(args.out, cases, requests, args.phase, stop)
        result = summary(args.out, cases)[1][args.phase]
        print(result, flush=True)
        if not result["pass"]:
            parser.exit(2, "階段門檻未過。\n")


if __name__ == "__main__":
    main()
