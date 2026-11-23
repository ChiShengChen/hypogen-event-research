"""Deterministic arithmetic for revisions to company revenue guidance.

Amounts share one currency unit. Ratios are fractions, so 0.05 means 5%.
"""
from decimal import Decimal
from typing import Literal

from pydantic import model_validator

from research_app.schema import Schema

Direction = Literal["raised", "lowered", "unchanged"]

ITEM_KINDS = {
    "new_midpoint": "amount",
    "prior_midpoint": "amount",
    "midpoint_change": "amount",
    "midpoint_change_ratio": "ratio",
    "revision": "direction",
    "low_change": "amount",
    "high_change": "amount",
    "width_change": "amount",
    "sequential_change": "amount",
    "sequential_change_ratio": "ratio",
    "sequential": "direction",
    "year_over_year_change": "amount",
    "year_over_year_change_ratio": "ratio",
    "year_over_year": "direction",
    "interim_surprise": "amount",
    "implied_remainder_new": "amount",
    "implied_remainder_prior": "amount",
    "implied_remainder_change": "amount",
    "implied_remainder_change_ratio": "ratio",
    "implied_remainder": "direction",
}


class Interval(Schema):
    low: Decimal
    high: Decimal

    @model_validator(mode="after")
    def check_order(self):
        if self.low > self.high:
            raise ValueError("low must not exceed high")
        return self

    @property
    def midpoint(self) -> Decimal:
        return (self.low + self.high) / 2


class GuidanceInputs(Schema):
    """Disclosed figures for one guided period.

    `prior` is earlier guidance for the same period. For full-year guidance, `reported_in_period`
    is the actual already reported inside the guided period at the new date, `prior_reported_in_period`
    the same at the prior date, and `prior_interim` the prior guidance for the periods reported since.
    """

    new: Interval
    prior: Interval | None = None
    last_actual: Decimal | None = None
    year_ago_actual: Decimal | None = None
    reported_in_period: Decimal | None = None
    prior_reported_in_period: Decimal | None = None
    prior_interim: Interval | None = None

    @model_validator(mode="after")
    def check_remainder(self):
        remainder = (self.reported_in_period, self.prior_reported_in_period, self.prior_interim)
        if any(value is not None for value in remainder):
            if self.prior is None or any(value is None for value in remainder):
                raise ValueError("implied remainder needs prior guidance, both reported amounts and prior interim guidance")
            if self.reported_in_period < self.prior_reported_in_period:
                raise ValueError("reported amount cannot shrink between guidance dates")
        return self


def direction(change: Decimal) -> Direction:
    return "raised" if change > 0 else "lowered" if change < 0 else "unchanged"


def _compare(prefix, new, base):
    change = new - base
    return {
        f"{prefix}_change": change,
        f"{prefix}_change_ratio": change / abs(base) if base else None,
        prefix: direction(change),
    }


def compute(inputs: GuidanceInputs) -> dict[str, Decimal | str]:
    """Return every item the inputs determine; items without the needed inputs are omitted."""
    new = inputs.new.midpoint
    items = {"new_midpoint": new}
    if inputs.prior is not None:
        prior = inputs.prior.midpoint
        items |= {
            "prior_midpoint": prior,
            "midpoint_change": new - prior,
            "midpoint_change_ratio": (new - prior) / abs(prior) if prior else None,
            "revision": direction(new - prior),
            "low_change": inputs.new.low - inputs.prior.low,
            "high_change": inputs.new.high - inputs.prior.high,
            "width_change": (inputs.new.high - inputs.new.low) - (inputs.prior.high - inputs.prior.low),
        }
    if inputs.last_actual is not None:
        items |= _compare("sequential", new, inputs.last_actual)
    if inputs.year_ago_actual is not None:
        items |= _compare("year_over_year", new, inputs.year_ago_actual)
    if inputs.reported_in_period is not None:
        remainder_new = new - inputs.reported_in_period
        remainder_prior = inputs.prior.midpoint - inputs.prior_reported_in_period - inputs.prior_interim.midpoint
        interim_actual = inputs.reported_in_period - inputs.prior_reported_in_period
        items |= {
            "interim_surprise": interim_actual - inputs.prior_interim.midpoint,
            "implied_remainder_new": remainder_new,
            "implied_remainder_prior": remainder_prior,
            **_compare("implied_remainder", remainder_new, remainder_prior),
        }
    return {key: value for key, value in items.items() if value is not None}
