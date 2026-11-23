"""Preregister and run a three-arm comparison of financial-transmission ranking."""

import argparse
import hashlib
from itertools import permutations
from pathlib import Path
import signal
from threading import Event
from time import monotonic
from typing import Literal

from pydantic import Field

from benchmarks import linkage_depth as depth
from benchmarks import v9_equal as equal
from benchmarks.hypothesis_cases import freeze
from benchmarks.linkage_rank_cases import CASES
from research_app.adapters import AdapterError
from research_app.business_linkage import (
    LinkedHypotheses, RankedBusinessLinkageGeneration, RankedHypotheses, linkage_fields,
)
from research_app.schema import Event as ResearchEvent, Schema

OUT = Path("output/linkage-rank-v11")
PREVIOUS = Path("docs/linkage-depth")
ARMS = ("astra", "current", "ranked")
LABELS = ("A", "B", "C")
GRADE = depth.GRADE + (
    " Assess target_path separately from the four quality checks. At least identify the parties, relevant "
    "businesses, and direction of the specified principal transmission to mark target_path. A plausible link "
    "to a different financial lever is insufficient. Retain ordinal indices even when the selected path has "
    "a quality defect. The three anonymous drafts are independent. Do not look up later outcomes."
)
ORDERS = tuple(permutations(ARMS))


class RankedVerdict(depth.Verdict):
    label: Literal["A", "B", "C"]


class Comparison(Schema):
    verdicts: list[RankedVerdict] = Field(min_length=3, max_length=3)


class CaptureRanked(RankedBusinessLinkageGeneration, equal.Capture):
    pass


class ReplayRanked(RankedBusinessLinkageGeneration, equal.Replay):
    identity = equal.Replay.identity | {"prompt_version": RankedBusinessLinkageGeneration.prompt_version}


def capture(event, adapter):
    try:
        depth.build_report(event, adapter())
    except equal.Captured as exc:
        schema, instruction, context = exc.request
        return equal.make_request(schema, instruction, context), context
    raise ValueError("未取得正式 Harness 請求")


def schedule(key):
    offset = {"P": 0, "H": 2, "R": 4}[key[0]]
    return ORDERS[(int(key[-2:]) - 1 + offset) % len(ORDERS)]


def labels(key):
    return dict(zip(LABELS, schedule(key)))


def prepared():
    cases, requests = {}, {}
    old_cases = equal.hypothesis.read(PREVIOUS / "cases.json")
    old_requests = equal.hypothesis.read(PREVIOUS / "requests.json")
    for key, case in CASES.items():
        event = ResearchEvent.model_validate(case["event"])
        base = freeze(event)
        current, old_context = capture(event, depth.CaptureLinked)
        ranked, new_context = capture(event, CaptureRanked)
        if event.search_mode != "off" or any(old_context[field] != value for field, value in base.items()):
            raise ValueError(f"{key} 點時證據未對齊")
        if old_context != new_context:
            raise ValueError(f"{key} 新舊 Harness 的內容不一致")
        astra = equal.make_request(LinkedHypotheses, depth.DIRECT, base)
        if previous := case.get("previous_case"):
            if old_cases[previous]["input"] != base or old_requests[previous] != {"harness": current, "astra": astra}:
                raise ValueError(f"{key} 無法重現封存對照請求")
        cases[key] = case | {"input": base}
        requests[key] = {"current": current, "ranked": ranked, "astra": astra}
    for split, count in (("pilot", 4), ("holdout", 8), ("regression", 4)):
        cases_in_split = [case for case in cases.values() if case["split"] == split]
        if len(cases_in_split) != count or sum(case["gold"]["positive"] for case in cases_in_split) * 2 != count:
            raise ValueError(f"{split} 案件數或正負例不符")
    issuers = {case["issuer"] for case in cases.values()}
    if len(issuers) != 16 or {case["issuer"] for case in cases.values() if case["split"] != "regression"} & {
        case["issuer"] for case in old_cases.values()
    }:
        raise ValueError("正式案例發行人重疊")
    return cases, requests


def seal(root):
    cases, requests = prepared()
    code = [__file__, Path(__file__).with_name("linkage_rank_cases.py"), depth.__file__, equal.__file__,
            equal.journal.__file__, equal.research.__file__, equal.adapters.__file__, equal.schema.__file__,
            equal.admission.__file__, Path(equal.adapters.__file__).with_name("business_linkage.py")]
    rules = {
        "hypothesis": "新版先比較公告明示的合約、資源及具名運作安排，再排序。保留集正例應比現版多答對至少一案，負例不退步。",
        "amendment": {
            "initial_seal_commit": "fbb016d",
            "scope": "保留集推論前將曾用於 V9 服務探針的 IBM 換成 Corning。沿用原封存四案先導的輸入、請求、門檻及執行回傳。",
            "unchanged_pilot_cases_sha256": equal.digest({key: cases[key] for key in cases if key.startswith("P-")}),
            "unchanged_pilot_requests_sha256": equal.digest({key: requests[key] for key in requests if key.startswith("P-")}),
        },
        "source_sha256": {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in code},
        "cases_sha256": equal.digest(cases), "requests_sha256": equal.digest(requests),
        "generation_model": equal.hypothesis.MODEL, "grading_model": equal.hypothesis.JUDGE,
        "effort": equal.hypothesis.EFFORT, "search": "disabled", "workers": 1, "max_paths": 3,
        "generation_timeout_seconds": equal.TIMEOUT, "grading_timeout_seconds": equal.JUDGE_TIMEOUT,
        "generation_attempts_per_arm": 1, "grading_attempts_per_case": 1, "hard_token_cap": None,
        "grading_prompt": GRADE,
        "rubric": {
            "rule_check": "逐條核對點時引文 ID 及期限，新版另有非空排序理由。保留原稿及實際發布候選。",
            "positive": "至少一條對應主要財務路徑，同一條通過兩端證據、必要機制、財務方向、可區分的公開反證，且全稿零重大錯誤。",
            "negative": "指出預註冊陷阱缺少的證據並保留歸因，稿中各條引文和期限均有效，全稿零重大錯誤。",
            "ranking": "正例首個 target_path 在發布稿的位置。排名第一與前三分開計，分母涵蓋所有預註冊正例；另列完整通過路徑的位置。",
            "gate_pilot": {"complete_triplets_and_grades": 4, "ranked_exact_min": 3, "ranked_major_max": 0},
            "gate_holdout": {"complete_triplets_and_grades": 8, "ranked_positive_min": 3, "ranked_negative_min": 3,
                             "ranked_major_max": 0},
            "ranking_improvement": {"additional_positives_vs_current": 1, "negative_delta_min": 0},
            "leadership": {"additional_exact_vs_astra": 2},
            "human": "匿名、逐案打亂三份稿件，隱藏排序理由與來源標籤以降低辨識，保留稿件內連動排序。獨立分析師實際收回另計。",
        },
        "stop": "先導配對與評分過門檻才開保留集；已啟動的正式呼叫皆計入且不重試。"
                "429 或容量不足後，對未啟動工作依服務端提示等待；單次最多 900 秒，無提示等待 30 秒，"
                "超限停止主批。收到中斷保存紀錄，僅接續未啟動的工作；不完整三稿不評分。回歸最後執行並另計。",
        "max_provider_wait_seconds": depth.COOLDOWN_CAP,
        "regression": "Microsoft、lululemon、FedEx、NIKE 排除正式計分。重用之前封存且請求逐位元一致的 V10 與純 Astra，"
                      "每案只生成一份新版稿，三份一同盲評。Microsoft 主要路徑是最低雲端承諾與 Azure 遷移。"
                      "lululemon 接受 Peloton 的具名服飾通路或 Studio 內容安排，均需可區分的公開查核。",
    }
    manifest = root / "protocol.json"
    if old := equal.hypothesis.read(manifest):
        if old != rules | {"sealed_at": old["sealed_at"]}:
            raise ValueError("批次封存內容或程式已更動")
        return read_sealed(root)
    if (root / "calls").exists():
        raise ValueError("已有執行紀錄但缺封存檔")
    equal.journal.atomic(root / "cases.json", cases)
    equal.journal.atomic(root / "requests.json", requests)
    equal.journal.atomic(manifest, rules | {"sealed_at": equal.journal.now()})
    return read_sealed(root)


def read_sealed(root):
    return depth.read_sealed(root)


def receipt(root, key, arm, case):
    if arm in {"astra", "current"} and case.get("previous_case"):
        original = "harness" if arm == "current" else arm
        return equal.receipt(PREVIOUS / "raw", case["previous_case"], original)
    return equal.receipt(root, key, arm)


def completed(root, key, case, arms=ARMS):
    return all(receipt(root, key, arm, case).get("status") == "completed" for arm in arms)


def normalize(arm, case, response):
    if arm == "judge":
        verdicts = Comparison.model_validate(response).verdicts
        if {verdict.label for verdict in verdicts} != set(LABELS):
            raise AdapterError("匿名評分未覆蓋三份稿")
        return {"verdicts": {verdict.label: verdict.model_dump(mode="json") for verdict in verdicts}}
    if arm != "ranked":
        return depth.normalize("harness" if arm == "current" else arm, case, response)
    output = RankedHypotheses.model_validate(response).model_dump(mode="json")
    report = depth.build_report(ResearchEvent.model_validate(case["event"]), ReplayRanked(response))
    return {"raw_findings": linkage_fields(output), "findings": linkage_fields(report)}


def anonymous(findings):
    return findings | {"business_linkages": [
        {name: value for name, value in path.items() if name != "ranking_reason"}
        for path in findings["business_linkages"]
    ]}


def judge_request(root, key, case):
    return equal.make_request(Comparison, GRADE, case["input"] | {
        "preregistered_standard": case["gold"],
        "anonymous_drafts": [{"label": label, **anonymous(receipt(root, key, arm, case)["findings"])}
                             for label, arm in labels(key).items()],
    })


def run_phase(root, cases, requests, split, stop):
    for key, case in cases.items():
        if case["split"] != split:
            continue
        generation = ("ranked",) if split == "regression" else schedule(key)
        for arm in (*generation, "judge"):
            if stop.is_set():
                return False
            if arm == "judge" and not completed(root, key, case):
                continue
            job = equal.queue_job(root, key, arm)
            timeout = equal.JUDGE_TIMEOUT if arm == "judge" else equal.TIMEOUT
            model = equal.hypothesis.JUDGE if arm == "judge" else equal.hypothesis.MODEL
            request = judge_request(root, key, case) if arm == "judge" else requests[key][arm]
            result = equal.attempt(root, job, case, request, stop, monotonic() + equal.journal.budget(1, 1, timeout),
                                   timeout, transform=normalize, model=model)
            print(key, arm, result["status"], result.get("reason") or "", flush=True)
            if result.get("reason") in equal.AVAILABILITY_ERRORS and not depth.capacity_pause(root, job, result, stop):
                return False
    return True


def adjudicate(root, key, case):
    if not completed(root, key, case, (*ARMS, "judge")):
        return None
    model_grades = receipt(root, key, "judge", case)["verdicts"]
    result = {}
    for label, arm in labels(key).items():
        row = receipt(root, key, arm, case)
        verdict = model_grades[label]
        paths = row["findings"]["business_linkages"]
        rules = depth.rule_check(paths, case)
        if arm == "ranked":
            for check, path in zip(rules, paths):
                check["ranking_reason"] = bool(path["ranking_reason"].strip())
        candidates = sorted(verdict["candidates"], key=lambda grade: grade["index"])
        if [grade["index"] for grade in candidates] != list(range(1, len(paths) + 1)):
            return None
        major = verdict["major_error"] or any(grade["major_error"] for grade in candidates)
        targets = [grade for grade in candidates if grade["target_path"]]
        qualifying = [grade["index"] for grade in targets
                      if all(value for name, value in rules[grade["index"] - 1].items() if name != "index")
                      and all(grade[col] for col in depth.CHECKS)]
        grounded = all(check["evidence"] and check["time"] for check in rules)
        positive = case["gold"]["positive"]
        exact = (bool(qualifying) if positive else verdict["gap_ok"] and grounded) and not major
        failures = []
        if not exact:
            if not positive:
                failures = ["mechanism"] if grounded else ["evidence", "mechanism"]
            elif not targets:
                failures = ["selection"]
                if len(row["raw_findings"]["business_linkages"]) > len(paths):
                    failures.append("evidence")
            else:
                closest = max(targets, key=lambda grade: sum(grade[col] for col in depth.CHECKS))
                failures = [col for col in depth.CHECKS if not closest[col]]
                if not all(rules[closest["index"] - 1][col] for col in ("evidence", "time")):
                    failures = list(dict.fromkeys(["evidence", *failures]))
                if major and not failures:
                    failures = ["mechanism"]
        result[arm] = {
            "rules": rules, "verdict": verdict, "qualifying": qualifying, "exact": exact, "major": major,
            "principal_rank": targets[0]["index"] if positive and targets else None,
            "qualified_rank": qualifying[0] if positive and qualifying else None,
            "failure_dimensions": failures, "submitted": len(paths),
            "raw_submitted": len(row["raw_findings"]["business_linkages"]),
        }
    return result


def stats(root, cases, grades, split, protocol):
    selected = {key: case for key, case in cases.items() if case["split"] == split}
    graded = [key for key in selected if grades[key] is not None]
    paired = sum(completed(root, key, case) for key, case in selected.items())
    pos_planned = sum(case["gold"]["positive"] for case in selected.values())
    metrics = {}
    for arm in ARMS:
        good = [key for key in graded if grades[key][arm]["exact"]]
        ranks = [grades[key][arm]["principal_rank"] for key in graded]
        metrics[arm] = {
            "exact": len(good), "positive": sum(cases[key]["gold"]["positive"] for key in good),
            "negative": sum(not cases[key]["gold"]["positive"] for key in good),
            "major": sum(grades[key][arm]["major"] for key in graded),
            "rank1": ranks.count(1), "top3": sum(rank is not None for rank in ranks),
        }
    result = {"planned": len(selected), "positive_planned": pos_planned, "paired": paired,
              "graded": len(graded), "metrics": metrics}
    ranked, current, astra = (metrics[arm] for arm in ("ranked", "current", "astra"))
    rubric = protocol["rubric"]
    if split == "pilot":
        gate = rubric["gate_pilot"]
        result["pass"] = paired == len(graded) == gate["complete_triplets_and_grades"] and (
            ranked["exact"] >= gate["ranked_exact_min"] and ranked["major"] <= gate["ranked_major_max"])
    if split == "holdout":
        gate = rubric["gate_holdout"]
        result["pass"] = paired == len(graded) == gate["complete_triplets_and_grades"] and (
            ranked["positive"] >= gate["ranked_positive_min"] and ranked["negative"] >= gate["ranked_negative_min"]
            and ranked["major"] <= gate["ranked_major_max"])
        gain = rubric["ranking_improvement"]
        result["positive_delta_vs_current"] = ranked["positive"] - current["positive"] if len(graded) == 8 else None
        result["negative_delta_vs_current"] = ranked["negative"] - current["negative"] if len(graded) == 8 else None
        result["exact_delta_vs_astra"] = ranked["exact"] - astra["exact"] if len(graded) == 8 else None
        result["ranking_improved"] = result["pass"] and (
            result["positive_delta_vs_current"] >= gain["additional_positives_vs_current"]
            and result["negative_delta_vs_current"] >= gain["negative_delta_min"])
        result["leads_astra"] = result["pass"] and (
            result["exact_delta_vs_astra"] >= rubric["leadership"]["additional_exact_vs_astra"])
    return result


def summary(root, cases, protocol):
    grades = {key: adjudicate(root, key, case) for key, case in cases.items()}
    return grades, {split: stats(root, cases, grades, split, protocol)
                    for split in ("pilot", "holdout", "regression")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("seal", "pilot", "holdout", "regression", "run", "report"), required=True)
    parser.add_argument("--out", default=OUT, type=Path)
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with equal.journal.exclusive(args.out):
        if args.phase == "report":
            from benchmarks.linkage_rank_report import publish
            cases, _, protocol = read_sealed(args.out)
            publish(args.out, cases, protocol, args.report_dir or args.out / "publication")
            return
        cases, requests, protocol = seal(args.out)
        if args.phase == "seal":
            print(f"Sealed {len(cases)} cases in {args.out}", flush=True)
            return
        phases = ("pilot", "holdout", "regression") if args.phase == "run" else (args.phase,)
        for phase in phases:
            if phase == "holdout" and not summary(args.out, cases, protocol)[1]["pilot"]["pass"]:
                print("先導未過，保留集不執行。", flush=True)
                if args.phase == "holdout":
                    parser.exit(2)
                continue
            proceeded = run_phase(args.out, cases, requests, phase, stop)
            result = summary(args.out, cases, protocol)[1][phase]
            print(phase, result, flush=True)
            if not proceeded:
                parser.exit(2, "中斷或等待超過封存上限。\n")


if __name__ == "__main__":
    main()
