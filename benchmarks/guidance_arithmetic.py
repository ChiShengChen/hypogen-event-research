"""Deterministically scored guidance-revision arithmetic on archived issuer announcements.

Every input figure cites an archived block and its exact wording. Gold answers are computed by
research_app.guidance_arithmetic from those verified figures, never typed by hand.
"""

import argparse
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html import escape
import json
from math import comb
from pathlib import Path
import re
import signal
from threading import Event
from time import monotonic
from typing import Literal

from pydantic import AwareDatetime, Field, ValidationError, model_validator

from research_app import full_revision
from research_app.financial_units import UnitSource, read_units
from research_app.guidance_arithmetic import ITEM_KINDS, GuidanceInputs, compute
from research_app.schema import Nonempty, Schema

from . import v9_equal as equal
from .earnings_full_revision import normalize, source_url
from .linkage_depth import capacity_pause

ROOT = Path(__file__).resolve().parents[1]
CASES = Path(__file__).with_name("guidance_arithmetic_cases.json")
INTERVALS = ("new", "prior", "prior_interim")
AMOUNTS = ("last_actual", "year_ago_actual", "reported_in_period", "prior_reported_in_period")
FIGURES = INTERVALS + AMOUNTS
LABELS = ("period", "last_period", "year_ago_period", "interim", "remainder")
DIRECTIONS = ("raised", "lowered", "unchanged")
RELATIVE_TOLERANCE = Decimal("0.01")
RATIO_FLOOR = Decimal("0.0001")
REMAINDER = ("new", "prior", "reported_in_period", "prior_reported_in_period", "prior_interim")
NEEDS = {
    "new_midpoint": ("new",),
    **{item: ("new", "prior") for item in (
        "prior_midpoint", "midpoint_change", "midpoint_change_ratio", "revision",
        "low_change", "high_change", "width_change")},
    **{item: ("new", "last_actual") for item in ("sequential_change", "sequential_change_ratio", "sequential")},
    **{item: ("new", "year_ago_actual") for item in (
        "year_over_year_change", "year_over_year_change_ratio", "year_over_year")},
    **{item: REMAINDER for item in (
        "interim_surprise", "implied_remainder_new", "implied_remainder_prior",
        "implied_remainder_change", "implied_remainder_change_ratio", "implied_remainder")},
}
QUESTIONS = {
    "new_midpoint": "What is the midpoint of the latest guidance for {period} revenue?",
    "prior_midpoint": "What is the midpoint of the prior guidance for {period} revenue?",
    "midpoint_change": "Latest guidance midpoint minus prior guidance midpoint for {period} revenue.",
    "midpoint_change_ratio": "That midpoint change as a percent of the prior guidance midpoint.",
    "revision": "Compared with the prior guidance for the same period, was the {period} revenue guidance "
                "midpoint raised, lowered or unchanged?",
    "low_change": "Change in the low end of the {period} revenue guidance range.",
    "high_change": "Change in the high end of the {period} revenue guidance range.",
    "width_change": "Change in the width (high minus low) of the {period} revenue guidance range.",
    "sequential_change": "Latest {period} revenue guidance midpoint minus actual revenue for {last_period}.",
    "sequential_change_ratio": "That difference as a percent of actual revenue for {last_period}.",
    "sequential": "Is the latest {period} revenue guidance midpoint above (raised), below (lowered) or equal "
                  "to (unchanged) actual revenue for {last_period}?",
    "year_over_year_change": "Latest {period} revenue guidance midpoint minus actual revenue for {year_ago_period}.",
    "year_over_year_change_ratio": "That difference as a percent of actual revenue for {year_ago_period}.",
    "year_over_year": "Is the latest {period} revenue guidance midpoint above (raised), below (lowered) or equal "
                      "to (unchanged) actual revenue for {year_ago_period}?",
    "interim_surprise": "Actual revenue for {interim} minus the midpoint of the prior guidance for {interim}.",
    "implied_remainder_new": "Latest {period} revenue guidance midpoint minus revenue already reported within "
                             "{period}: the implied revenue for {remainder}.",
    "implied_remainder_prior": "Prior {period} revenue guidance midpoint minus revenue reported within {period} "
                               "at that time and minus the prior guidance midpoint for {interim}: the implied "
                               "revenue for {remainder} under the prior guidance.",
    "implied_remainder_change": "Change in the implied revenue for {remainder} from the prior to the latest guidance.",
    "implied_remainder_change_ratio": "That change as a percent of the prior implied revenue for {remainder}.",
    "implied_remainder": "Was the implied revenue for {remainder} raised, lowered or unchanged?",
}
ANSWER_RULES = (
    "Answer every listed item. For an amount give the exact signed value in full currency units without "
    "separators or symbols, for example -2345000. For a percent give the signed percent number with two "
    "decimals and without the sign, for example -1.23 for minus 1.23 percent. For a direction give raised, "
    "lowered or unchanged. "
    "Give unknown only when the supplied documents do not determine the item."
)


class FigureRef(Schema):
    document: Nonempty
    block: Nonempty
    quote: Nonempty
    tabular: bool = False
    unit_block: Nonempty | None = None
    unit_quote: Nonempty | None = None

    @model_validator(mode="after")
    def check_unit(self):
        if (self.unit_block is None) != (self.unit_quote is None):
            raise ValueError("unit_block and unit_quote go together")
        return self


class ArchivedDocument(Schema):
    id: Nonempty
    source_url: Nonempty
    path: Nonempty
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_type: Literal["text/html", "text/plain"] = "text/html"
    published_at: AwareDatetime
    obtained_at: AwareDatetime


class Case(Schema):
    id: Nonempty
    split: Literal["pilot", "holdout"]
    issuer: Nonempty
    ticker: Nonempty
    event_at: AwareDatetime
    as_of: AwareDatetime
    currency: Literal["USD"] = "USD"
    precision: Decimal = Field(gt=0)
    labels: dict[Literal[LABELS], Nonempty]
    documents: list[ArchivedDocument] = Field(min_length=1)
    figures: dict[Literal[FIGURES], list[FigureRef]]
    items: list[Literal[tuple(ITEM_KINDS)]] = Field(min_length=1)
    trap: Nonempty

    @model_validator(mode="after")
    def check_case(self):
        if not self.event_at <= self.as_of:
            raise ValueError("event must precede the cutoff")
        for document in self.documents:
            source_url(document.source_url)
            if not document.published_at <= document.obtained_at <= self.as_of:
                raise ValueError(f"document {document.id} is not visible at the cutoff")
        for name, refs in self.figures.items():
            if not refs or (name in INTERVALS and len(refs) != 1):
                raise ValueError(f"figure {name} needs {'one reference' if name in INTERVALS else 'references'}")
        if len(set(self.items)) != len(self.items):
            raise ValueError("items repeat")
        for item in self.items:
            if missing := set(NEEDS[item]) - set(self.figures):
                raise ValueError(f"item {item} needs figures {sorted(missing)}")
            if missing := set(re.findall(r"{(\w+)}", QUESTIONS[item])) - set(self.labels):
                raise ValueError(f"item {item} needs labels {sorted(missing)}")
        return self


def load_blocks(document):
    path = (ROOT / document.path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"archive path escapes the repository: {document.id}")
    body = path.read_bytes()
    if sha256(body).hexdigest() != document.sha256:
        raise ValueError(f"archive hash mismatch: {document.id}")
    text = body.decode("utf-8-sig")
    if document.content_type == "text/plain":
        paragraphs = re.split(r"\r?\n[ \t]*\r?\n", text.strip())
        text = "<html><body>" + "".join(f"<p>{escape(part)}</p>" for part in paragraphs) + "</body></html>"
    blocks = full_revision.parse_filing(text, document_id=document.id)
    if not blocks:
        raise ValueError(f"archive has no readable text: {document.id}")
    return {block["id"]: block for block in blocks}


def read_figure(ref, blocks):
    """Return (low, high) proven by the cited wording, or raise ValueError with the reason."""
    for block_id, quote in ((ref.block, ref.quote), (ref.unit_block, ref.unit_quote)):
        if block_id is None:
            continue
        block = blocks.get(block_id)
        if block is None or not block_id.startswith(ref.document + ":"):
            raise ValueError(f"block {block_id} is not in document {ref.document}")
        if normalize(quote) not in normalize(block["text"]):
            raise ValueError(f"quote is not in block {block_id}: {quote}")
    sources = (UnitSource(ref.unit_block, ref.unit_quote, "table"),) if ref.unit_block else ()
    reading = read_units(ref.quote, amount_ref=ref.block, currency="USD", sources=sources, tabular=ref.tabular)
    if reading.reason:
        raise ValueError(f"{ref.block}: {reading.reason}")
    return reading.low, reading.high


def figure_value(name, refs, blocks):
    readings = [read_figure(ref, blocks) for ref in refs]
    if name in INTERVALS:
        if len(readings) != 1:
            raise ValueError(f"figure {name} needs exactly one reference")
        low, high = readings[0]
        return {"low": low, "high": high}
    if any(low != high for low, high in readings):
        raise ValueError(f"figure {name} must cite point amounts")
    return sum(low for low, _ in readings)


def figure_inputs(figures, blocks):
    return GuidanceInputs.model_validate({name: figure_value(name, refs, blocks) for name, refs in figures.items()})


def case_blocks(case):
    blocks = {}
    for document in case.documents:
        blocks |= load_blocks(document)
    return blocks


def gold(case, blocks=None):
    items = compute(figure_inputs(case.figures, blocks or case_blocks(case)))
    return {item: items[item] for item in case.items}


def questions(case):
    return [{"item": item, "kind": ITEM_KINDS[item], "question": QUESTIONS[item].format(**case.labels)}
            for item in case.items]


def parse_answer(kind, value):
    text = str(value).strip().casefold()
    if kind == "direction":
        return text if text in DIRECTIONS else None
    text = re.sub(r"[\s,$%]", "", text)
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return number / 100 if kind == "ratio" else number


def tolerance(case, kind, expected):
    floor = RATIO_FLOOR if kind == "ratio" else case.precision / 100
    return max(abs(expected) * RELATIVE_TOLERANCE, floor)


def grade(case, expected, answers):
    """Score each item deterministically; a missing or unparseable answer is wrong.

    Amounts and percents pass within 1% of the gold value. The floor is one hundredth of the
    disclosure unit for amounts and 0.01 percentage point for percents.
    """
    rows = {}
    for item in case.items:
        kind = ITEM_KINDS[item]
        answer = parse_answer(kind, answers.get(item, ""))
        if answer is None:
            correct = False
        elif kind == "direction":
            correct = answer == expected[item]
        else:
            correct = abs(answer - expected[item]) <= tolerance(case, kind, expected[item])
        rows[item] = {"kind": kind, "answer": answers.get(item), "gold": str(expected[item]), "correct": correct}
    return {"items": rows, "exact": all(row["correct"] for row in rows.values())}


def load_cases(path=CASES):
    cases = [Case.model_validate(row) for row in json.loads(path.read_text())]
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("case IDs repeat")
    return cases


# --- Paired runs: plain Astra answers directly; the harness only locates wording and computes. ---

OUT = Path("output/guidance-arithmetic")
ARMS = ("astra", "harness")
REPEATS = 3
TIMEOUT = 180
FIGURE_HINTS = {
    "new": "the latest issuer guidance or preliminary estimate for {period} revenue",
    "prior": "the issuer's prior guidance for {period} revenue as stated in the documents",
    "prior_interim": "the issuer's prior guidance for {interim} revenue",
    "last_actual": "reported actual revenue for {last_period}",
    "year_ago_actual": "reported actual revenue for {year_ago_period}",
    "reported_in_period": "reported actual revenue for each quarter already completed within {period} "
                          "at the latest guidance date, one entry per quarter",
    "prior_reported_in_period": "reported actual revenue for each quarter completed within {period} "
                                "when the prior guidance was issued, one entry per quarter",
}
DIRECT = (
    "Answer each question about the issuer's revenue guidance using only the supplied archived "
    "announcement blocks. " + ANSWER_RULES + " List the block IDs you relied on in evidence_ids and give "
    "a brief Traditional Chinese reason."
)
EXTRACT = (
    "Locate the issuer's own wording for each requested figure in the supplied archived announcement "
    "blocks. For each figure return its name, the document ID, the block ID and a quote copied exactly "
    "from that block containing the full amount or range with its currency and scale words, for example "
    "'between $412 million and $428 million' or 'approximately $3.4 billion'. For a table cell, quote the "
    "cell exactly, set tabular true, and give the block ID and exact wording of the heading that states "
    "the currency and scale, such as '(U.S. $ in thousands)'. Otherwise set tabular false and both unit "
    "fields null. Omit a figure the documents do not state. Give a brief Traditional Chinese reason."
)


class ItemAnswer(Schema):
    item: Literal[tuple(ITEM_KINDS)]
    value: Nonempty


class Answers(Schema):
    answers: list[ItemAnswer]
    evidence_ids: list[Nonempty]
    reason: Nonempty


class ExtractedFigure(Schema):
    name: Literal[FIGURES]
    document: Nonempty
    block: Nonempty
    quote: Nonempty
    tabular: bool
    unit_block: Nonempty | None
    unit_quote: Nonempty | None


class Extraction(Schema):
    figures: list[ExtractedFigure]
    reason: Nonempty


def needed(case):
    return [name for name in FIGURES if any(name in NEEDS[item] for item in case.items)]


def requests_for(case, blocks):
    documents = [{
        "id": document.id, "source_url": document.source_url, "published_at": document.published_at.isoformat(),
        "blocks": [{"id": block_id, "text": block["text"]} for block_id, block in blocks.items()
                   if block_id.startswith(document.id + ":")],
    } for document in case.documents]
    base = {"issuer": case.issuer, "ticker": case.ticker, "as_of": case.as_of.isoformat(), "documents": documents}
    asked = [{"item": row["item"], "question": row["question"]} for row in questions(case)]
    wanted = [{"name": name, "description": FIGURE_HINTS[name].format(**case.labels)} for name in needed(case)]
    return {
        "astra": equal.make_request(Answers, DIRECT, base | {"questions": asked}),
        "harness": equal.make_request(Extraction, EXTRACT, base | {"figures": wanted}),
    }


def render(kind, value):
    if kind == "direction":
        return value
    return format(value * 100 if kind == "ratio" else value, "f")


def harness_answers(case, blocks, extraction):
    """Verify each located figure and compute answers; unproven inputs leave their items unknown."""
    refs, values, errors = {}, {}, {}
    for figure in extraction.figures:
        refs.setdefault(figure.name, []).append(FigureRef.model_validate(figure.model_dump(exclude={"name"})))
    for name in needed(case):
        try:
            if name not in refs:
                raise ValueError("figure not located")
            values[name] = figure_value(name, refs[name], blocks)
        except ValueError as exc:
            errors[name] = str(exc)
    remainder_only = REMAINDER[2:]
    if not all(name in values for name in ("prior", *remainder_only)):
        values = {name: value for name, value in values.items() if name not in remainder_only}
    items = {}
    if "new" in values:
        try:
            items = compute(GuidanceInputs.model_validate(values))
        except ValidationError as exc:
            errors["inputs"] = str(exc)
    answers = {item: render(ITEM_KINDS[item], items[item]) if item in items else "unknown" for item in case.items}
    return answers, errors


def transform(arm, payload, response):
    case, blocks = payload
    if arm == "astra":
        output = Answers.model_validate(response)
        return {"output": output.model_dump(mode="json"),
                "answers": {answer.item: answer.value for answer in output.answers}}
    output = Extraction.model_validate(response)
    answers, errors = harness_answers(case, blocks, output)
    return {"output": output.model_dump(mode="json"), "answers": answers, "figure_errors": errors}


def seal(root, cases):
    if (root / "protocol.json").exists():
        raise ValueError(f"{root} is already sealed")
    root.mkdir(parents=True, exist_ok=True)
    frozen, requests = {}, {}
    for case in cases:
        blocks = case_blocks(case)
        frozen[case.id] = {"case": case.model_dump(mode="json"),
                           "gold": {item: str(value) for item, value in gold(case, blocks).items()}}
        requests[case.id] = requests_for(case, blocks)
    protocol = {
        "sealed_at": equal.journal.now(), "model": equal.hypothesis.MODEL, "effort": equal.hypothesis.EFFORT,
        "timeout_seconds": TIMEOUT, "repeats": REPEATS, "arms": {
            "astra": "One call answers every item directly from the archived blocks.",
            "harness": "One call returns exact wording for the needed figures; code verifies each quote, reads "
                       "the amount and computes every item. Unproven figures leave dependent items unknown.",
        },
        "grading": {"amount": "within 1% of gold, floor one hundredth of the case precision",
                    "ratio": "within 1% of gold, floor 0.01 percentage point", "direction": "exact",
                    "case": "exact when every item is correct"},
        "primary": "Case-level exact rate per arm. Per case the majority of repeats decides; paired cases are "
                   "compared with an exact two-sided McNemar test on discordant cases.",
        "stop": "Calls run one at a time, repeat by repeat. A 429, usage limit or capacity error waits for the "
                "announced cooldown up to 900 seconds and retries that call once; a second availability error "
                "stops dispatch. Other failures count as wrong answers.",
        "pilot_purpose": "Pilot cases come from announcements used in earlier benchmarks and seen during design. "
                         "They estimate ceiling and discordance only; the holdout size is set from them and "
                         "holdout issuers must be new.",
        "cases_sha256": equal.digest(frozen), "requests_sha256": equal.digest(requests),
    }
    for name, value in (("cases.json", frozen), ("requests.json", requests), ("protocol.json", protocol)):
        equal.journal.atomic(root / name, value)
    return protocol


def read_sealed(root):
    protocol = json.loads((root / "protocol.json").read_text())
    frozen, requests = (json.loads((root / name).read_text()) for name in ("cases.json", "requests.json"))
    if equal.digest(frozen) != protocol["cases_sha256"] or equal.digest(requests) != protocol["requests_sha256"]:
        raise ValueError("sealed inputs changed")
    return frozen, requests


def latest(root, key, arm):
    for suffix in ("~retry", ""):
        path = equal.journal.receipt(root, key + suffix, arm)
        if path.exists():
            return json.loads(path.read_text())
    return None


def run(root, split, stop):
    frozen, requests = read_sealed(root)
    selected = [case_id for case_id, row in frozen.items() if row["case"]["split"] == split]
    loaded = {}
    for repeat in range(1, REPEATS + 1):
        for index, case_id in enumerate(selected):
            if case_id not in loaded:
                case = Case.model_validate(frozen[case_id]["case"])
                loaded[case_id] = (case, case_blocks(case))
            for arm in (ARMS if (repeat + index) % 2 else ARMS[::-1]):
                key = f"{case_id}~r{repeat}"
                for attempt_key in (key, key + "~retry"):
                    if stop.is_set():
                        return
                    if attempt_key.endswith("~retry"):
                        previous = latest(root, key, arm)
                        if not previous or previous.get("reason") not in equal.AVAILABILITY_ERRORS:
                            break
                        if not capacity_pause(root, equal.queue_job(root, key, arm), previous, stop):
                            return
                    job = equal.queue_job(root, attempt_key, arm)
                    deadline = monotonic() + equal.journal.budget(1, 1, TIMEOUT)
                    result = equal.attempt(root, job, loaded[case_id], requests[case_id][arm], stop, deadline,
                                           TIMEOUT, transform=transform, model=equal.hypothesis.MODEL)
                    print(attempt_key, arm, result["status"], result.get("reason") or "", flush=True)
                    if result.get("reason") not in equal.AVAILABILITY_ERRORS:
                        break
                    if attempt_key.endswith("~retry"):
                        return


def mcnemar(wins, losses):
    discordant = wins + losses
    if not discordant:
        return 1.0
    tail = sum(comb(discordant, k) for k in range(max(wins, losses), discordant + 1)) / 2 ** discordant
    return min(1.0, 2 * tail)


def holdout_size(harness_only, astra_only, n, power=0.8, alpha=0.05, limit=200):
    """Smallest case count whose exact McNemar test reaches the power at the pilot discordance rates."""
    if harness_only <= astra_only or not n:
        return None
    rate, share = (harness_only + astra_only) / n, harness_only / (harness_only + astra_only)
    for size in range(4, limit + 1):
        discordant = round(size * rate)
        critical = next((k for k in range(discordant + 1) if mcnemar(k, discordant - k) <= alpha
                         and k > discordant - k), None)
        if critical is None:
            continue
        achieved = sum(comb(discordant, k) * share ** k * (1 - share) ** (discordant - k)
                       for k in range(critical, discordant + 1))
        if achieved >= power:
            return size
    return None


def summarize(root, split):
    frozen, _ = read_sealed(root)
    pairs, cases = [], {}
    for case_id, row in frozen.items():
        if row["case"]["split"] != split:
            continue
        case = Case.model_validate(row["case"])
        expected = {item: value if ITEM_KINDS[item] == "direction" else Decimal(value)
                    for item, value in row["gold"].items()}
        for repeat in range(1, REPEATS + 1):
            pair = {}
            for arm in ARMS:
                record = latest(root, f"{case_id}~r{repeat}", arm)
                status = record["status"] if record else "missing"
                answers = record.get("answers", {}) if status == "completed" else {}
                pair[arm] = {"status": status, "reason": (record or {}).get("reason"),
                             "figure_errors": (record or {}).get("figure_errors", {}),
                             "elapsed_seconds": (record or {}).get("elapsed_seconds"),
                             "usage": (record or {}).get("usage"), **grade(case, expected, answers)}
            pairs.append({"case": case_id, "repeat": repeat, "arms": pair})
            cases.setdefault(case_id, {arm: 0 for arm in ARMS})
            for arm in ARMS:
                cases[case_id][arm] += pair[arm]["exact"]
    majority = {case_id: {arm: count * 2 > REPEATS for arm, count in counts.items()} for case_id, counts in cases.items()}
    harness_only = sum(row["harness"] and not row["astra"] for row in majority.values())
    astra_only = sum(row["astra"] and not row["harness"] for row in majority.values())
    arms = {}
    for arm in ARMS:
        items = [item for pair in pairs for item in pair["arms"][arm]["items"].values()]
        by_kind = {kind: [item["correct"] for item in items if item["kind"] == kind] for kind in ("amount", "ratio", "direction")}
        arms[arm] = {
            "runs_exact": sum(pair["arms"][arm]["exact"] for pair in pairs), "runs": len(pairs),
            "cases_majority_exact": sum(row[arm] for row in majority.values()),
            "items_correct": sum(item["correct"] for item in items), "items": len(items),
            "by_kind": {kind: [sum(values), len(values)] for kind, values in by_kind.items() if values},
            "failed_calls": sum(pair["arms"][arm]["status"] != "completed" for pair in pairs),
            "unstable_cases": sum(0 < counts[arm] < REPEATS for counts in cases.values()),
        }
    return {
        "split": split, "cases": len(cases), "repeats": REPEATS, "arms": arms, "per_case": cases,
        "discordant_cases": {"harness_only": harness_only, "astra_only": astra_only},
        "mcnemar_p": mcnemar(harness_only, astra_only),
        "suggested_holdout_cases": holdout_size(harness_only, astra_only, len(cases)),
        "pairs": pairs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("check", "seal", "pilot", "holdout", "report"), default="check")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--cases", type=Path, default=CASES)
    args = parser.parse_args()
    if args.phase == "check":
        for case in load_cases(args.cases):
            answers = gold(case)
            print(f"{case.id}\t{case.split}\t" + "\t".join(f"{item}={value}" for item, value in answers.items()))
    elif args.phase == "seal":
        protocol = seal(args.out, load_cases(args.cases))
        print(f"sealed {args.out} cases={protocol['cases_sha256'][:12]} requests={protocol['requests_sha256'][:12]}")
    elif args.phase in ("pilot", "holdout"):
        stop = Event()
        signal.signal(signal.SIGTERM, lambda *_: stop.set())
        signal.signal(signal.SIGINT, lambda *_: stop.set())
        run(args.out, args.phase, stop)
    else:
        for split in ("pilot", "holdout"):
            summary = summarize(args.out, split)
            if summary["cases"]:
                equal.journal.atomic(args.out / f"summary-{split}.json", summary)
                print(json.dumps({key: value for key, value in summary.items() if key != "pairs"},
                                 ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
