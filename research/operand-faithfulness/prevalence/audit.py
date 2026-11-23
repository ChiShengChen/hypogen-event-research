"""Seal, execute and report a matched full-document operand audit."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import signal
import subprocess
import sys
from threading import Event
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "full-document"))
import study

OUT = HERE / "results"
FIELDS = ("prior_q4", "latest_q4", "change")
TOLERANCE = Decimal(100_000)
LOCKED = [HERE / name for name in ("audit.py", "annotations.json", "html-layout.py", "protocol.md", "test_audit.py")]
LOCKED += [Path(study.__file__), Path(study.layout.__file__), Path(study.runner.__file__)]


def snapshot(source):
    path = HERE / source["path"]
    if path.suffix == ".pdf":
        rows = [asdict(line) for line in study.layout.pages(path)]
    else:
        command = ["/usr/bin/python3", str(HERE / "html-layout.py"), str(path), source["selector"]]
        if source.get("omit"):
            command += ["--omit", source["omit"]]
        rows = json.loads(subprocess.check_output(command, timeout=30))
    if not rows or not any("consolidated statements" in row["text"].lower() for row in rows):
        raise ValueError(f"No consolidated statements in {path}")
    ready = datetime.fromisoformat(source["date"] + "T23:59:59").replace(tzinfo=ZoneInfo("America/New_York"))
    return {"url": source["url"], "format": path.suffix[1:], "sha256": study.file_sha(path),
            "date": ready.isoformat(), "source_path": source["path"], "lines": rows}


def annotate(case, docs):
    gold = study.labels(case, docs)
    for role, labels in gold.items():
        side = study.layout.ROLES[role][0]
        if docs[side]["format"] != "pdf":
            for proof in labels:
                proof["url"] = docs[side]["url"]
    expected = study.compute({role: study.midpoint(entries[0]) for role, entries in gold.items()})
    if any(value is None for value in expected.values()):
        raise ValueError(f"Unanswerable case: {case['id']}")
    return gold, expected


def load_cases():
    cases = {}
    old = study.read(study.OUT / "cases.json")
    old_issuers = {c["issuer"].casefold() for c in old.values()}
    for case in study.read(HERE / "annotations.json"):
        if case["id"] in cases or case["issuer"].casefold() in old_issuers:
            raise ValueError(f"Repeated issuer: {case['id']}")
        docs = {side: snapshot(source) for side, source in case["sources"].items()}
        if docs["prior"]["date"] >= docs["latest"]["date"]:
            raise ValueError(f"Invalid document order: {case['id']}")
        gold, expected = annotate(case, docs)
        cases[case["id"]] = case | {"docs": docs, "gold": gold, "expected": expected}
    return cases


def request_for(case):
    docs = {}
    for side, doc in case["docs"].items():
        rows = []
        for r in doc["lines"]:
            tokens = [value[0] for value in study.layout.amount_spans(r["text"])]
            index = " [indices: " + " | ".join(tokens) + "]" if tokens else ""
            rows.append(f"[{r['page']}:{r['row']}] {r['text']}{index}")
        docs[side] = {"date": doc["date"], "pages": "\n".join(rows)}
    context = {"issuer": case["issuer"], "fiscal_year": case["fiscal_year"],
               "as_of": docs["latest"]["date"], "documents": docs}
    instruction = study.PROMPT + (
        "\nEach original row is followed by a mechanically generated list of numeric tokens, when present. "
        "Use this list for the 1-based citation indices. Dates and source number formatting may cause omissions "
        "relative to informal counting. The list is for citation indexing and does not identify any operand."
    )
    return study.runner.make_request(study.Reply, instruction, context)


def freeze(out):
    if (out / "protocol.json").exists():
        raise ValueError("Batch already sealed")
    cases = load_cases()
    if len(cases) < 6:
        raise ValueError("Prespecified minimum is six new complete cases")
    tasks = []
    for key, case in cases.items():
        request = request_for(case)
        for family in study.MODELS:
            tasks.append({"id": f"{key}-{family}", "key": key, "family": family, "mode": "full", "request": request})
    spec = {"sealed_at": study.runner.journal.now(), "model_ids": study.MODELS, "per_call_seconds": study.TIMEOUT,
            "max_calls": len(tasks), "evidence": "same full documents, original task prompt with mechanical token indices",
            "primary_tolerance_usd": 0, "sensitivity_tolerance_usd": int(TOLERANCE),
            "hashes": {str(path.relative_to(HERE.parents[2])): study.file_sha(path) for path in LOCKED},
            "case_sha256": study.sha(cases), "calls_sha256": study.sha(tasks)}
    for name, data in (("cases", cases), ("requests", tasks), ("protocol", spec)):
        study.runner.journal.atomic(out / f"{name}.json", data)


def load_frozen(out):
    spec, cases, tasks = (study.read(out / f"{name}.json") for name in ("protocol", "cases", "requests"))
    if any(study.file_sha(HERE.parents[2] / key) != value for key, value in spec["hashes"].items()):
        raise ValueError("A sealed source changed")
    if (study.sha(cases), study.sha(tasks)) != (spec["case_sha256"], spec["calls_sha256"]):
        raise ValueError("A sealed case or request changed")
    return cases, tasks


def run_family(out, tasks, family, stop):
    for task in tasks:
        if task["family"] != family:
            continue
        if stop.is_set():
            return
        blocked = set(study.runner.AVAILABILITY_ERRORS) | {"auth"}
        previous = study.receipt(out, task)
        if previous:
            if previous.get("reason") in blocked:
                return
            continue
        state = {"case": task["key"], "family": family, "status": "started",
                 "started_at": study.runner.journal.now(), "request_sha256": study.sha(task["request"])}
        target = out / "calls" / f"{task['id']}.json"
        study.runner.journal.atomic(target, state)
        run = study.run_astra if family == "astra" else study.run_claude
        reply = run(out, task, stop)
        row = state | reply | {"case": task["key"], "family": family}
        study.runner.journal.atomic(target, row)
        print(task["id"], row["status"], row.get("reason") or "", flush=True)
        if row.get("reason") in blocked:
            return


def money(raw):
    if isinstance(raw, str) and raw.startswith('"'):
        try:
            raw = json.loads(raw)
        except ValueError:
            return None
    return study.number(raw) if isinstance(raw, str) else None


def score(case, reply):
    values = {field: money(reply[field]) for field in FIELDS}
    expected = {field: study.number(case["expected"][field]) for field in FIELDS}
    errors = {field: values[field] - expected[field] if values[field] is not None else None for field in FIELDS}
    operands = {}
    for role, gold in case["gold"].items():
        picks = [pick for pick in reply["evidence"] if pick["role"] == role]
        if len(picks) != 1:
            operands[role] = "missing" if not picks else "duplicate"
            continue
        pick = picks[0]
        observed = money(pick["low_usd"]), money(pick["high_usd"])
        exact = tuple(study.number(gold[0]["amounts"][index]) for index in (0, -1))
        locations = {(proof["at"], tuple(proof["tokens"])) for proof in gold}
        match_at = study.candidate_key(pick) in locations
        operands[role] = "ok" if observed == exact and match_at else (
            "unparseable_amount" if None in observed else
            "citation" if observed == exact else "amount" if match_at else "amount_and_location")
    delta_exact = errors["change"] == 0
    levels_exact = errors["prior_q4"] == 0 and errors["latest_q4"] == 0
    delta_near = errors["change"] is not None and abs(errors["change"]) <= TOLERANCE
    wrong_level_at_tolerance = any(errors[f] is not None and abs(errors[f]) > TOLERANCE for f in FIELDS[:2])
    self_consistent = all(v is not None for v in values.values()) and values["latest_q4"]-values["prior_q4"] == values["change"]
    same_shift = errors["prior_q4"] not in (None, 0) and errors["prior_q4"] == errors["latest_q4"]
    known_wrong = any(d in {"amount", "amount_and_location"} for d in operands.values())
    unsupported = any(d != "ok" for d in operands.values())
    all_grounded = not unsupported and delta_exact and levels_exact and case["expected"]["direction"] == reply["direction"]
    exact_cancel = delta_exact and self_consistent and same_shift
    numeric_mask = delta_exact and (known_wrong or any(errors[f] not in (None,0) for f in FIELDS[:2]))
    return {
        "values_usd": {f: study.money(v) for f, v in values.items()},
        "signed_errors_usd": {f: study.money(v) for f, v in errors.items()},
        "operand_status": operands, "delta_exact": delta_exact, "levels_exact": levels_exact,
        "direction_exact": case["expected"]["direction"] == reply["direction"], "all_grounded": all_grounded,
        "exact_cancel": exact_cancel, "numeric_mask": numeric_mask, "delta_self_consistent": self_consistent,
        "delta_within_tolerance": delta_near,
        "tolerance_only_masks_wrong_level": delta_near and not delta_exact and wrong_level_at_tolerance,
        "delta_with_unsupported_evidence": delta_exact and unsupported,
        "delta_with_citation_problem_only": delta_exact and levels_exact and any(d == "citation" for d in operands.values())
        and all(d in {"ok","citation"} for d in operands.values()),
    }


def interval(k, n):
    return {"k": k, "n": n, "wilson95": study.interval95(k, n)}


def summarize(grades):
    count = len(grades)
    correct = sum(row["delta_exact"] for row in grades)
    near = sum(row["delta_within_tolerance"] for row in grades)
    full = sum(row["all_grounded"] for row in grades)
    return {
        "completed": count, "delta_exact": interval(correct, count), "fully_grounded": interval(full, count),
        "absolute_pair_correct": interval(sum(r["levels_exact"] for r in grades), count),
        "delta_only_overcredit": interval(correct-full, count),
        "numeric_mask_given_exact_delta": interval(sum(r["numeric_mask"] for r in grades), correct),
        "exact_cancellation_given_exact_delta": interval(sum(r["exact_cancel"] for r in grades), correct),
        "unsupported_given_exact_delta": interval(sum(r["delta_with_unsupported_evidence"] for r in grades), correct),
        "citation_only_given_exact_delta": interval(sum(r["delta_with_citation_problem_only"] for r in grades), correct),
        "tolerance_only_masks_wrong_level": interval(sum(r["tolerance_only_masks_wrong_level"] for r in grades), near),
    }


def report(out, cases, tasks):
    ledger, scores = [], []
    for task in tasks:
        receipt = study.receipt(out, task) or {"status": "unstarted"}
        ledger.append({k: v for k,v in task.items() if k != "request"} | {k: v for k,v in receipt.items() if k != "response"})
        if receipt["status"] == "completed":
            case = cases[task["key"]]
            result = score(case, receipt["response"])
            scores.append({"id": task["id"], "case": task["key"], "family": task["family"],
                           "response": receipt["response"], "expected": case["expected"], **result})
    matched = {case for case in cases if sum(r["case"] == case for r in scores) == len(study.MODELS)}
    families = {family: {subset: summarize([r for r in scores if r["family"] == family
                                             and (subset == "available" or r["case"] in matched)])
                         for subset in ("available", "matched")} for family in study.MODELS}
    order = {}
    for metric in ("delta_exact", "fully_grounded"):
        counts = {family: s["matched"][metric]["k"] for family,s in families.items()}
        best = max(counts.values())
        order[metric] = [family for family, value in counts.items() if value == best] if len(matched) >= 6 else []
    summary = {"planned": len(tasks), "started": sum(r["status"] != "unstarted" for r in ledger),
               "matched_issuers": sorted(matched), "model_results": families, "leader": order}
    failures = [r for r in scores if not r["all_grounded"]] + [r for r in ledger if r["status"] != "completed"]
    for name, data in (("execution", ledger), ("scores", scores), ("failures", failures), ("summary", summary)):
        study.runner.journal.atomic(out / f"{name}.json", data)
    print("Matched", len(matched), "/", len(cases), "leaders", order, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("seal", "run", "report"))
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with study.runner.journal.exclusive(args.out):
        if args.phase == "seal":
            freeze(args.out)
            return
        cases, tasks = load_frozen(args.out)
        if args.phase == "run":
            with ThreadPoolExecutor(max_workers=len(study.MODELS)) as pool:
                futures = [pool.submit(run_family, args.out, tasks, family, stop) for family in study.MODELS]
                for future in futures:
                    future.result()
        report(args.out, cases, tasks)


if __name__ == "__main__":
    main()
