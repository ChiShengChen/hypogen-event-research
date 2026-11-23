from decimal import Decimal

import pytest
from pydantic import ValidationError

from research_app.guidance_arithmetic import ITEM_KINDS, GuidanceInputs, compute

M = Decimal(1_000_000)


def interval(low, high):
    return {"low": Decimal(low) * M, "high": Decimal(high) * M}


def test_narrowed_range_raises_midpoint_although_high_end_falls():
    items = compute(GuidanceInputs(new=interval(179, 189), prior=interval(175, 190)))
    assert items["new_midpoint"] == Decimal("184") * M
    assert items["prior_midpoint"] == Decimal("182.5") * M
    assert items["midpoint_change"] == Decimal("1.5") * M
    assert items["revision"] == "raised"
    assert items["low_change"] == 4 * M and items["high_change"] == -1 * M
    assert items["width_change"] == -5 * M
    assert items["midpoint_change_ratio"] == Decimal("1.5") / Decimal("182.5")


def test_year_over_year_growth_can_hide_a_sequential_decline():
    items = compute(GuidanceInputs(new=interval(2_100, 2_300), last_actual=Decimal(2_400) * M,
                                   year_ago_actual=Decimal(1_900) * M))
    assert items["year_over_year"] == "raised" and items["year_over_year_change"] == 300 * M
    assert items["sequential"] == "lowered" and items["sequential_change"] == -200 * M
    assert items["sequential_change_ratio"] == Decimal(-200) / Decimal(2_400)
    assert "revision" not in items


def test_full_year_raise_smaller_than_interim_beat_lowers_implied_remainder():
    items = compute(GuidanceInputs(
        new=interval(105, 109), prior=interval(100, 110),
        reported_in_period=Decimal(80) * M, prior_reported_in_period=Decimal(50) * M,
        prior_interim=interval(26, 28),
    ))
    assert items["revision"] == "raised" and items["midpoint_change"] == 2 * M
    assert items["interim_surprise"] == 3 * M
    assert items["implied_remainder_prior"] == 28 * M
    assert items["implied_remainder_new"] == 27 * M
    assert items["implied_remainder_change"] == -1 * M
    assert items["implied_remainder"] == "lowered"


def test_unchanged_midpoint_and_zero_base():
    items = compute(GuidanceInputs(new=interval(10, 20), prior=interval(12, 18), last_actual=Decimal(0)))
    assert items["revision"] == "unchanged" and items["width_change"] == 4 * M
    assert items["sequential"] == "raised" and "sequential_change_ratio" not in items


def test_every_item_has_a_known_kind():
    items = compute(GuidanceInputs(
        new=interval(105, 109), prior=interval(100, 110), last_actual=Decimal(30) * M,
        year_ago_actual=Decimal(25) * M, reported_in_period=Decimal(80) * M,
        prior_reported_in_period=Decimal(50) * M, prior_interim=interval(26, 28),
    ))
    assert set(items) == set(ITEM_KINDS)


@pytest.mark.parametrize("payload", [
    {"new": interval(20, 10)},
    {"new": interval(105, 109), "prior": interval(100, 110), "reported_in_period": Decimal(80)},
    {"new": interval(105, 109), "reported_in_period": Decimal(80), "prior_reported_in_period": Decimal(50),
     "prior_interim": interval(26, 28)},
    {"new": interval(105, 109), "prior": interval(100, 110), "reported_in_period": Decimal(40),
     "prior_reported_in_period": Decimal(50), "prior_interim": interval(26, 28)},
])
def test_invalid_inputs_are_rejected(payload):
    with pytest.raises(ValidationError):
        GuidanceInputs.model_validate(payload)
