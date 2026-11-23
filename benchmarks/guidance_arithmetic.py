"""Deterministically scored guidance-revision arithmetic on archived issuer announcements.

Every input figure cites an archived block and its exact wording. Gold answers are computed by
research_app.guidance_arithmetic from those verified figures, never typed by hand.
"""

import argparse
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from research_app import full_revision
from research_app.financial_units import UnitSource, read_units
from research_app.guidance_arithmetic import ITEM_KINDS, GuidanceInputs, compute
from research_app.schema import Nonempty, Schema

from .earnings_full_revision import normalize, source_url

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
    "separators or symbols, for example -1500000. For a percent give the signed percent number with two "
    "decimals and without the sign, for example -0.82 for minus 0.82 percent. For a direction give raised, "
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


def figure_inputs(figures, blocks):
    values = {}
    for name, refs in figures.items():
        readings = [read_figure(ref, blocks) for ref in refs]
        if name in INTERVALS:
            low, high = readings[0]
            values[name] = {"low": low, "high": high}
        else:
            if any(low != high for low, high in readings):
                raise ValueError(f"figure {name} must cite point amounts")
            values[name] = sum(low for low, _ in readings)
    return GuidanceInputs.model_validate(values)


def gold(case):
    blocks = {}
    for document in case.documents:
        blocks |= load_blocks(document)
    items = compute(figure_inputs(case.figures, blocks))
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=CASES)
    args = parser.parse_args()
    for case in load_cases(args.cases):
        answers = gold(case)
        print(f"{case.id}\t{case.split}\t" + "\t".join(f"{item}={value}" for item, value in answers.items()))


if __name__ == "__main__":
    main()
