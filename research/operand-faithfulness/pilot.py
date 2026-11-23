"""Pilot on answer-preserving perturbations and field-wise numerical verification."""

import argparse
import csv
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import re
import signal
import sys
from threading import Event
from time import monotonic
from typing import Literal

from pydantic import Field

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import guidance_arithmetic as arithmetic, v9_equal as runner
from research_app.schema import Schema

ARTIFACTS = HERE / "artifacts"
ARCHIVE = ROOT / "output/guidance-arithmetic-v2"
ARCHIVED_ITEMS = {
    "prior_q4": "implied_remainder_prior", "latest_q4": "implied_remainder_new",
    "change": "implied_remainder_change", "direction": "implied_remainder",
}
DEPENDENCIES = {
    "prior_q4": ("prior_annual", "prior_ytd", "prior_q3"),
    "latest_q4": ("latest_annual", "latest_ytd"),
}
DEPENDENCIES["change"] = DEPENDENCIES["direction"] = DEPENDENCIES["prior_q4"] + DEPENDENCIES["latest_q4"]
ROLES = {
    "prior_annual": ("prior", "outlook", "full_year", "prior"),
    "prior_ytd": ("prior", "actual", "six_months", "prior_reported_in_period"),
    "prior_q3": ("prior", "outlook", "third_quarter", "prior_interim"),
    "latest_annual": ("latest", "outlook", "full_year", "new"),
    "latest_ytd": ("latest", "actual", "nine_months", "reported_in_period"),
}
Role = Literal["prior_annual", "prior_ytd", "prior_q3", "latest_annual", "latest_ytd"]
ISSUERS = ("gitlab", "sprinklr")
VARIANTS = ("base", "common_shift", "latest_shift", "missing_latest")
FAULTS = ("clean", "common_operand_error", "unit_error", "wrong_year_citation", "missing_prior_operand", "arithmetic_error")
ARMS = ("direct", "all_or_nothing", "fieldwise")
COMMON_SHIFT = Decimal(11_000_000)
LATEST_SHIFT = Decimal(6_000_000)
TIMEOUT = 90

INSTRUCTION = (
    "Answer using only the supplied research cards about two announcement vintages. Cards are the sole source of truth. "
    "Use consolidated USD revenue for the requested fiscal year. Lower/upper fields on each card are expressed in "
    "that card's stated unit. Convert all submitted operands and outputs to full USD, as plain decimal strings. "
    "For each verified operand submit its role, card_id, and the normalized lower and upper amount. Omit an operand "
    "if unavailable. Report the implied fourth-quarter revenue under the earlier announcement and under the latest "
    "announcement, their difference (latest minus prior), and the direction. Use guidance midpoints. Earlier embedded Q4 "
    "uses reported first six months and earlier Q3 guidance. Latest embedded Q4 uses reported first nine months. "
    "Return null for each result whose required evidence is missing. Independently supported results can still be returned."
)


class Operand(Schema):
    role: Role
    card_id: str
    low: str
    high: str


class Answer(Schema):
    operands: list[Operand] = Field(max_length=10)
    prior_q4: str | None
    latest_q4: str | None
    change: str | None
    direction: Literal["raised", "lowered", "unchanged"] | None


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj):
    return sha256(dump(obj).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def amount(value):
    try:
        number = Decimal(value)
    except (TypeError, ValueError, InvalidOperation):
        return None
    return number if number.is_finite() and abs(number) <= Decimal("1e18") else None


def text(value):
    return format(value, "f") if isinstance(value, Decimal) else value


def direction(n):
    return "raised" if n > 0 else "lowered" if n < 0 else "unchanged"


def outputs(prior, latest):
    change = latest - prior if prior is not None and latest is not None else None
    return {"prior_q4": text(prior), "latest_q4": text(latest), "change": text(change),
            "direction": direction(change) if change is not None else None}


def normalized(card):
    scale = {"USD": 1, "USD thousands": 1000, "USD millions": 1000000}[card["unit"]]
    return Decimal(card["low"]) * scale, Decimal(card["high"]) * scale


def operand(role, card):
    low, high = normalized(card)
    return {"role": role, "card_id": card["id"], "low": text(low), "high": text(high)}


def archived_cases(path=ARCHIVE):
    records = read(path / "cases.json")
    return {key: records[key] for key in ISSUERS}


def construct_inputs(archive=ARCHIVE):
    results = {}
    for case_id, record in archived_cases(archive).items():
        case = arithmetic.Case.model_validate(record["case"])
        blocks = arithmetic.case_blocks(case)
        year = int(re.search(r"\d{4}", case.labels["period"])[0])
        sources = {source.id: source for source in case.documents}
        legit = {}
        origin = {}
        for role, (vintage, metric, period, source_role) in ROLES.items():
            refs = case.figures[source_role]
            value = arithmetic.figure_value(source_role, refs, blocks)
            low, high = (value["low"], value["high"]) if isinstance(value, dict) else (value, value)
            document = sources[refs[0].document]
            unit, scale = ("USD thousands", 1000) if metric == "actual" else ("USD millions", 1000000)
            legit[role] = {"id": "C" + digest([case_id, role, year])[:8], "vintage": vintage,
                           "metric": metric, "period": period,
                           "fiscal_year": year, "scope": "consolidated", "available_at": document.obtained_at.isoformat(),
                           "unit": unit, "low": text(low / scale), "high": text(high / scale)}
            origin[role] = {"document_sha256": document.sha256, "url": document.source_url,
                            "published_at": document.published_at.isoformat(),
                            "locators": [ref.model_dump(mode="json") for ref in refs]}
        for variant in VARIANTS:
            facts = deepcopy(legit)
            if variant == "common_shift":
                shifts = {"prior_ytd": COMMON_SHIFT, "latest_ytd": COMMON_SHIFT}
                expected_prior = Decimal(record["gold"][ARCHIVED_ITEMS["prior_q4"]]) - COMMON_SHIFT
                expected_latest = Decimal(record["gold"][ARCHIVED_ITEMS["latest_q4"]]) - COMMON_SHIFT
            elif variant == "latest_shift":
                shifts = {"latest_ytd": LATEST_SHIFT}
                expected_prior = Decimal(record["gold"][ARCHIVED_ITEMS["prior_q4"]])
                expected_latest = Decimal(record["gold"][ARCHIVED_ITEMS["latest_q4"]]) - LATEST_SHIFT
            else:
                shifts = {}
                expected_prior = Decimal(record["gold"][ARCHIVED_ITEMS["prior_q4"]])
                expected_latest = Decimal(record["gold"][ARCHIVED_ITEMS["latest_q4"]])
            for role, delta in shifts.items():
                for bound in ("low", "high"):
                    facts[role][bound] = text(Decimal(facts[role][bound]) + delta / 1000)
            if variant == "missing_latest":
                facts.pop("latest_ytd")
                expected_latest = None
            distractors = []
            for role, card in legit.items():
                # Adjacent fiscal-year values remain easy to quote but are ineligible.
                distractors.append({**card, "id": "C" + digest([case_id, role, year - 1])[:8], "fiscal_year": year - 1,
                                    "low": text(Decimal(card["low"]) * Decimal("0.92")),
                                    "high": text(Decimal(card["high"]) * Decimal("0.92"))})
            cards = sorted([*facts.values(), *distractors], key=lambda item: digest([case_id, item["id"]]))
            context = {"issuer": case.issuer, "fiscal_year": year, "as_of": case.as_of.isoformat(), "cards": cards}
            results[f"{case_id}-{variant}"] = {"issuer": case_id, "variant": variant, "context": context,
                                               "origins": origin, "valid_ids": {role: card["id"] for role, card in facts.items()},
                                               "changed_records": sorted(shifts) + (["latest_ytd:removed"] if expected_latest is None else []),
                                               "gold": outputs(expected_prior, expected_latest)}
    return results


def verify(reported, context):
    refs = {row["id"]: row for row in context["cards"]}
    accepted, rejected = {}, {}
    for role, (vintage, metric, period, _) in ROLES.items():
        records = [row for row in reported["operands"] if row["role"] == role]
        if len(records) != 1:
            rejected[role] = "missing" if not records else "duplicate"
            continue
        row = records[0]
        card = refs.get(row["card_id"])
        if card is None:
            rejected[role] = "unknown_locator"
            continue
        evidence_key = (card["vintage"], card["metric"], card["period"], card["fiscal_year"], card["scope"])
        if evidence_key != (vintage, metric, period, context["fiscal_year"], "consolidated"):
            rejected[role] = "scope_period_or_vintage"
            continue
        if datetime.fromisoformat(card["available_at"]) > datetime.fromisoformat(context["as_of"]):
            rejected[role] = "future_evidence"
            continue
        low, high = normalized(card)
        if (amount(row["low"]), amount(row["high"])) != (low, high):
            rejected[role] = "amount_or_unit"
            continue
        if low < 0 or high < low or (metric == "actual" and low != high):
            rejected[role] = "invalid_range"
            continue
        accepted[role] = (low + high) / 2
    prior, latest = None, None
    if set(DEPENDENCIES["prior_q4"]) <= accepted.keys():
        prior = accepted["prior_annual"] - accepted["prior_ytd"] - accepted["prior_q3"]
    if set(DEPENDENCIES["latest_q4"]) <= accepted.keys():
        latest = accepted["latest_annual"] - accepted["latest_ytd"]
    if prior is not None and prior < 0:
        rejected["prior_q4"], prior = "negative_remainder", None
    if latest is not None and latest < 0:
        rejected["latest_q4"], latest = "negative_remainder", None
    result = outputs(prior, latest)
    if (prior is not None and latest is not None
            and accepted["prior_ytd"] > accepted["latest_ytd"]):
        result["change"] = result["direction"] = None
        rejected["change"] = "cumulative_period_conflict"
    return result, rejected


def equal(actual, expected, key):
    if actual is None or expected is None or key == "direction":
        return actual == expected
    return amount(actual) is not None and amount(actual) == amount(expected)


def evaluate(candidate, case):
    verified, rejected = verify(candidate, case["context"])
    modes = {"direct": {key: candidate[key] for key in DEPENDENCIES},
             "all_or_nothing": verified if verified["change"] is not None else dict.fromkeys(DEPENDENCIES),
             "fieldwise": verified}
    evaluation = {}
    for arm, fields in modes.items():
        grades = {}
        for key, actual in fields.items():
            gold = case["gold"][key]
            numeric = equal(actual, gold, key)
            grounded = actual is not None and verified[key] is not None and equal(actual, verified[key], key)
            grades[key] = {"actual": actual, "expected": gold, "numeric_exact": numeric,
                           "grounded": grounded, "supported_correct": actual is not None and numeric and grounded}
        evaluation[arm] = grades
    return {"verification_reasons": rejected, "grades": evaluation}


def injected(case, fault):
    valid_ids = case["valid_ids"]
    cards = {row["id"]: row for row in case["context"]["cards"]}
    result = {"operands": [operand(role, cards[ref]) for role, ref in valid_ids.items()], **case["gold"]}
    by_role = {row["role"]: row for row in result["operands"]}
    if fault == "common_operand_error":
        for role, field in (("prior_ytd", "prior_q4"), ("latest_ytd", "latest_q4")):
            if role in by_role:
                for bound in ("low", "high"):
                    by_role[role][bound] = text(Decimal(by_role[role][bound]) + 5_000_000)
                result[field] = text(Decimal(result[field]) - 5_000_000)
    elif fault == "unit_error" and "latest_ytd" in by_role:
        wrong = Decimal(by_role["latest_ytd"]["low"]) * 1000
        actual = Decimal(by_role["latest_ytd"]["low"])
        by_role["latest_ytd"].update(low=text(wrong), high=text(wrong))
        result.update(outputs(Decimal(result["prior_q4"]), Decimal(result["latest_q4"]) + actual - wrong))
    elif fault == "wrong_year_citation":
        card = cards[by_role["prior_ytd"]["card_id"]]
        wrong = next(row for row in cards.values() if row["fiscal_year"] == card["fiscal_year"] - 1
                     and all(row[key] == card[key] for key in ("vintage", "metric", "period")))
        by_role["prior_ytd"]["card_id"] = wrong["id"]
    elif fault == "missing_prior_operand":
        result["operands"].remove(by_role["prior_q3"])
        result.update(prior_q4=None, change=None, direction=None)
    elif fault == "arithmetic_error":
        if result["change"] is not None:
            result["change"] = text(Decimal(result["change"]) + 1_000_000)
            result["direction"] = direction(Decimal(result["change"]))
        else:
            result["prior_q4"] = text(Decimal(result["prior_q4"]) + 1_000_000)
    return result


def aggregate(records):
    metrics = {}
    for arm in ARMS:
        rows = [item for record in records for item in record["grades"][arm].values()]
        answered = [row for row in rows if row["actual"] is not None]
        possible = sum(row["expected"] is not None for row in rows)
        correct = sum(row["supported_correct"] for row in answered)
        metrics[arm] = {"total_fields": len(rows), "answerable_fields": possible, "emitted": len(answered),
                        "supported_correct": correct, "unsupported_or_wrong": len(answered) - correct,
                        "numeric_errors_among_emitted": sum(not row["numeric_exact"] for row in answered),
                        "effective_coverage": correct / possible if possible else None,
                        "observed_risk": 1 - correct / len(answered) if answered else None}
    return metrics


def archived_masking(path=ARCHIVE):
    groups = {}
    with (path / "scores.csv").open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            if row["item"] in ARCHIVED_ITEMS.values() and row["gold"] not in {"", "unknown"}:
                groups.setdefault((row["case"], row["repeat"], row["arm"]), {})[row["item"]] = row["correct"] == "True"
    rows = []
    for (case, repeat, arm), observed in groups.items():
        if not set(ARCHIVED_ITEMS.values()) <= observed.keys():
            continue
        prior, latest, change, sign = (observed[value] for value in ARCHIVED_ITEMS.values())
        rows.append({"case": case, "repeat": int(repeat), "arm": arm, "prior_correct": prior,
                     "latest_correct": latest, "change_correct": change, "direction_correct": sign,
                     "masked_error": change and not (prior and latest)})
    return rows


def archive_summary(rows):
    return {arm: {"issuers": len({row["case"] for row in rows if row["arm"] == arm}),
                  "responses": sum(row["arm"] == arm for row in rows),
                  "change_correct": sum(row["arm"] == arm and row["change_correct"] for row in rows),
                  "both_components_correct": sum(row["arm"] == arm and row["prior_correct"] and row["latest_correct"] for row in rows),
                  "masked_errors": sum(row["arm"] == arm and row["masked_error"] for row in rows)}
            for arm in ("astra", "harness")}


def seal(out, archive):
    cases = construct_inputs(archive)
    if any(not all(row["numeric_exact"] for row in evaluate(injected(case, "clean"), case)["grades"]["fieldwise"].values())
           for case in cases.values()):
        raise ValueError("Normalized source cards and independent expected values disagree.")
    requests = {key: runner.make_request(Answer, INSTRUCTION, row["context"]) for key, row in cases.items()}
    # Alternate the perturbation order by issuer; the order is fixed before CLI inference.
    order = [f"{issuer}-{variant}" for pair in zip(VARIANTS, VARIANTS[::-1])
             for issuer, variant in zip(ISSUERS, pair)]
    protocol = {"design": "operand-faithfulness-pilot-v1", "model": runner.hypothesis.MODEL,
                "reasoning_effort": runner.hypothesis.EFFORT, "timeout_seconds": TIMEOUT, "workers": 1,
                "search": "disabled", "maximum_started_calls": len(cases), "order": order,
                "inputs_sha256": digest(cases), "requests_sha256": digest(requests),
                "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                "archive_score_sha256": sha256((archive / "scores.csv").read_bytes()).hexdigest(),
                "offline_faults": FAULTS, "common_shift_usd": text(COMMON_SHIFT), "latest_shift_usd": text(LATEST_SHIFT),
                "primary": "masked error in archive; grounded correct coverage and observed publication risk in matched trials",
                "stop": "Stop on 429/capacity or batch interruption. Each started job stays counted; only queued work may resume.",
                "scope": "Development pilot, two previously used issuers and counterfactual research cards; no raw-PDF or unseen-issuer claim."}
    paths = {"inputs": cases, "requests": requests}
    manifest = out / "preregistration.json"
    if manifest.exists():
        raise ValueError("This folder already contains a preregistered batch. Use a fresh output directory.")
    for key, value in paths.items():
        runner.journal.atomic(out / f"{key}.json", value)
    (out / "scores.csv").write_bytes((archive / "scores.csv").read_bytes())
    runner.journal.atomic(manifest, json.loads(dump(protocol)) | {"sealed_at": runner.journal.now()})


def frozen(out):
    protocol = read(out / "preregistration.json")
    cases, requests = (read(out / f"{name}.json") for name in ("inputs", "requests"))
    if (digest(cases) != protocol["inputs_sha256"] or digest(requests) != protocol["requests_sha256"]
            or sha256(Path(__file__).read_bytes()).hexdigest() != protocol["source_sha256"]
            or sha256((out / "scores.csv").read_bytes()).hexdigest() != protocol["archive_score_sha256"]):
        raise ValueError("Source, archive inputs, or prompts differ from the pre-registration.")
    return protocol, cases, requests


def validate_reply(arm, case, response):
    return {"response": Answer.model_validate(response).model_dump()}


def run(out, protocol, cases, requests, stop):
    jobs = [(key, runner.queue_job(out, key, "astra")) for key in protocol["order"]]
    states = [(key, job, runner.journal.restore(out, job)) for key, job in jobs]
    if any(row.get("reason") in runner.AVAILABILITY_ERRORS for _, _, row in states):
        print("Availability stop already recorded. No new calls dispatched.", flush=True)
        return
    pending = [(key, job) for key, job, row in states if row["status"] == "queued"]
    deadline = monotonic() + runner.journal.budget(len(pending), 1, TIMEOUT)
    for key, job in pending:
        if stop.is_set() or monotonic() >= deadline:
            break
        row = runner.attempt(out, job, cases[key], requests[key], stop, deadline, TIMEOUT,
                             transform=validate_reply, model=protocol["model"])
        print(key, row["status"], row.get("reason", ""), flush=True)
        if row.get("reason") in runner.AVAILABILITY_ERRORS or row["status"] == "queued":
            break


def perturbations(cases, records):
    by_id = {row["case"]: row for row in records}
    rows = []
    for issuer, variant, arm in product(ISSUERS, VARIANTS[1:], ARMS):
        baseline, treated = f"{issuer}-base", f"{issuer}-{variant}"
        if baseline not in by_id or treated not in by_id:
            continue
        a, b = (by_id[key]["grades"][arm] for key in (baseline, treated))
        if variant == "missing_latest":
            followed = (b["prior_q4"]["numeric_exact"] and all(b[key]["actual"] is None
                                                              for key in ("latest_q4", "change", "direction")))
        else:
            differences = {key: amount(b[key]["actual"]) - amount(a[key]["actual"])
                           if amount(b[key]["actual"]) is not None and amount(a[key]["actual"]) is not None else None
                           for key in ("prior_q4", "latest_q4", "change")}
            followed = all(differences[key] == Decimal(cases[treated]["gold"][key]) - Decimal(cases[baseline]["gold"][key])
                           for key in differences)
        rows.append({"issuer": issuer, "variant": variant, "arm": arm, "followed": followed})
    return rows


def report(out, protocol, cases):
    archived = archived_masking(out)
    offline = [{"case": key, "fault": fault, **evaluate(injected(case, fault), case)}
               for (key, case), fault in product(cases.items(), FAULTS)]
    calls, responses = [], []
    for key in protocol["order"]:
        row = runner.receipt(out, key, "astra")
        if not row:
            state = out / "jobs" / f"{key}-astra" / "state.json"
            row = read(state) if state.is_file() else {"status": "unstarted"}
        calls.append({"case": key, **{field: row.get(field) for field in
                     ("status", "reason", "started_at", "elapsed_seconds", "usage", "error")}})
        if row.get("status") == "completed":
            responses.append({"case": key, "response": row["response"], **evaluate(row["response"], cases[key])})
    summary = {"archive": archive_summary(archived), "offline_injections": aggregate(offline),
               "live": {"planned": len(cases), "started": sum(bool(row["started_at"]) for row in calls),
                        "completed": len(responses), "by_arm": aggregate(responses),
                        "paired_perturbations": perturbations(cases, responses)}, "calls": calls}
    for name, value in (("summary", summary), ("archive-masking", archived), ("offline-rows", offline), ("live-rows", responses)):
        runner.journal.atomic(out / f"{name}.json", value)
    print(json.dumps({key: summary[key] for key in ("archive", "offline_injections", "live")}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("seal", "report", "run"))
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--out", type=Path, default=ARTIFACTS)
    args = parser.parse_args()
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with runner.journal.exclusive(args.out):
        if args.phase == "seal":
            seal(args.out, args.archive)
        else:
            protocol, cases, requests = frozen(args.out)
            if args.phase == "run":
                run(args.out, protocol, cases, requests, stop)
            report(args.out, protocol, cases)


if __name__ == "__main__":
    main()
