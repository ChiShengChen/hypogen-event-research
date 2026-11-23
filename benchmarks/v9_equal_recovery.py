"""Measure first attempts and one symmetric recovery per V9 pilot case."""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from math import ceil
from pathlib import Path
import signal
from threading import Event
from time import monotonic

from benchmarks import v9_equal as equal
from benchmarks.earnings_execution import atomic, budget, exclusive, now, restore
from benchmarks.hypothesis_pilot import read
from benchmarks.v9_equal_admission import wait_hint


BASE = Path("docs/v9-equal-probe")
OUT = Path("output/v9-equal-recovery")
ROUNDS = ("first", "recovery")
TRANSIENT = equal.AVAILABILITY_ERRORS | {"per_call_deadline"}
MAX_COOLDOWN = 900
DEFAULT_COOLDOWN = 30


def seal(root):
    cases, requests = equal.read_sealed(BASE)
    prior = read(BASE / "protocol.json")
    cases = {key: case for key, case in cases.items() if case["split"] == "pilot"}
    requests = {key: requests[key] for key in cases}
    expected = {"generation_model": equal.hypothesis.MODEL, "effort": equal.hypothesis.EFFORT,
                "generation_timeout_seconds": equal.TIMEOUT, "search": "disabled", "workers": 1,
                "review": equal.REVIEW_RULES}
    if any(prior[field] != value for field, value in expected.items()) or len(cases) != 4:
        raise ValueError("正式設定或先導案數與原封存不同")
    first_order = dict(equal.stage_jobs(cases, "pilot"))
    protocol = expected | {
        "baseline_protocol_sha256": equal.digest(prior), "cases_sha256": equal.digest(cases),
        "requests_sha256": equal.digest(requests),
        "source_sha256": {Path(module).name: hashlib.sha256(Path(module).read_bytes()).hexdigest()
                          for module in (__file__, equal.__file__, equal.journal.__file__,
                                         equal.admission.__file__, equal.adapters.__file__,
                                         equal.research.__file__, equal.schema.__file__, equal.hypothesis.__file__)},
        "orders": {key: {"first": list(order), "recovery": list(reversed(order))}
                   for key, order in first_order.items()},
        "transient_reasons": sorted(TRANSIENT), "max_cooldown_seconds": MAX_COOLDOWN,
        "fallback_cooldown_seconds": DEFAULT_COOLDOWN,
        "max_recovery_rounds_per_case": 1, "max_calls_per_arm_per_case": 2, "max_calls": 16,
        "hard_provider_token_cap": None,
        "first_endpoint": "四案中首次兩組均有有效回覆的案數。每個已啟動呼叫占額，缺組保留。",
        "recovery_endpoint": "四案中首次或復原輪各自兩組均有有效回覆的案數。4/4 通過。",
        "selection": "首次配齊採首次；首次缺組且復原配齊才採復原。兩輪回覆不可混用。",
        "transient_policy": "暫時性失敗立即結束該案當輪派發。安排復原或下一案前，至少等待 CLI 宣告的秒數。"
                            "無等待提示時採 30 秒；宣告超過 900 秒則停止整批。"
                            "復原輪暫時性失敗後，若尚有下一案也須先冷卻。一般中斷只接續尚未啟動的呼叫。",
        "stop_scope": "只執行四案。每案最多兩輪。生成以外不發出模型呼叫。",
    }
    previous = read(root / "protocol.json")
    if previous:
        if previous != protocol | {"sealed_at": previous["sealed_at"]}:
            raise ValueError("執行程式、預算或輸入已改變")
        read_sealed(root)
    else:
        atomic(root / "cases.json", cases)
        atomic(root / "requests.json", requests)
        atomic(root / "protocol.json", protocol | {"sealed_at": now()})
    return cases, requests, protocol


def read_sealed(root):
    protocol = read(root / "protocol.json")
    if not protocol:
        raise ValueError("評測尚未封存")
    cases, requests = (read(root / f"{name}.json") for name in ("cases", "requests"))
    if equal.digest(cases) != protocol["cases_sha256"] or equal.digest(requests) != protocol["requests_sha256"]:
        raise ValueError("封存輸入無法核對")
    return cases, requests, protocol


def cooldown(root, key, round_name, receipt, protocol, stop):
    directory = root / "cooldowns"
    directory.mkdir(exist_ok=True)
    path = directory / f"{key}-{round_name}.json"
    decision = read(path)
    if not decision:
        job = root / round_name / "jobs" / f"{key}-{receipt['call']}"
        hint = wait_hint(job)
        seconds = ceil(hint) if hint is not None else protocol["fallback_cooldown_seconds"]
        blocked = seconds > protocol["max_cooldown_seconds"]
        started = datetime.fromisoformat(receipt["finished_at"])
        decision = {"case": key, "round": round_name, "arm": receipt["call"], "cause": receipt["reason"],
                    "reported_wait_seconds": hint, "scheduled_seconds": seconds,
                    "status": "blocked" if blocked else "waiting", "started_at": started.isoformat(),
                    "resume_at": None if blocked else (started + timedelta(seconds=seconds)).isoformat()}
        atomic(path, decision)
    if decision["status"] != "waiting":
        return decision["status"] == "completed"
    resume_at = datetime.fromisoformat(decision["resume_at"])
    remaining = max(0, (resume_at - datetime.now(timezone.utc)).total_seconds())
    print(f"{key} {round_name}: cooldown {remaining:.1f}s", flush=True)
    if stop.wait(remaining):
        return False
    finished = datetime.now(timezone.utc)
    atomic(path, decision | {"status": "completed", "finished_at": finished.isoformat(),
                             "elapsed_seconds": round((finished - datetime.fromisoformat(
                                 decision["started_at"])).total_seconds(), 3)})
    return True


def run_round(root, key, case, requests, order, stop, timeout):
    jobs = [equal.queue_job(root, key, arm) for arm in order]
    deadline = monotonic() + budget(len(jobs), 1, timeout)
    for arm, job in zip(order, jobs):
        receipt = equal.attempt(root, job, case, requests[arm], stop, deadline, timeout)
        print(f"{root.name} {key} {arm} {receipt['status']} {receipt.get('reason') or ''}", flush=True)
        if stop.is_set() or receipt["status"] == "queued" or receipt.get("reason") in TRANSIENT:
            return receipt
    return None


def run(root, cases, requests, protocol, stop):
    keys = list(cases)
    for index, key in enumerate(keys):
        if stop.is_set():
            break
        for round_name in ROUNDS:
            receipt = run_round(root / round_name, key, cases[key], requests[key],
                                protocol["orders"][key][round_name], stop, protocol["generation_timeout_seconds"])
            if stop.is_set() or (receipt and receipt["status"] == "queued"):
                return
            if not receipt or receipt.get("reason") not in TRANSIENT:
                break
            if round_name == "first" or index + 1 < len(keys):
                if not cooldown(root, key, round_name, receipt, protocol, stop):
                    return


def records(root, cases):
    result = {}
    for key in cases:
        for round_name in ROUNDS:
            for arm in equal.ARMS:
                directory = root / round_name
                job = directory / "jobs" / f"{key}-{arm}"
                row = restore(directory, job) if (job / "state.json").exists() else {"status": "unplanned"}
                result[key, round_name, arm] = {"case": key, "round": round_name, "call": arm} | row
    return result


def complete_round(calls, key, round_name):
    return all(calls[key, round_name, arm]["status"] == "completed" for arm in equal.ARMS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("seal", "run", "report"))
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--ratings", type=Path)
    args = parser.parse_args()
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with exclusive(args.out):
        if args.phase == "report":
            from benchmarks.v9_equal_recovery_review import publish

            cases, _, protocol = read_sealed(args.out)
            if protocol["review"] != equal.REVIEW_RULES:
                raise ValueError("封存的覆核規格與程式不符")
            publish(args.out, cases, args.report_dir or args.out / "publication", args.ratings)
            return
        cases, requests, protocol = seal(args.out)
        if args.phase == "run":
            run(args.out, cases, requests, protocol, stop)
            calls = records(args.out, cases)
            first = sum(complete_round(calls, key, "first") for key in cases)
            final = sum(any(complete_round(calls, key, name) for name in ROUNDS) for key in cases)
            print(f"First {first}/4; within recovery budget {final}/4", flush=True)
            if final != len(cases):
                parser.exit(2, "四案復原門檻未達。\n")
        else:
            print(f"Sealed four cases in {args.out}", flush=True)


if __name__ == "__main__":
    main()
