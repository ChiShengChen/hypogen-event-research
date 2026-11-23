from decimal import Decimal

import pytest

import pilot


@pytest.fixture(scope="module")
def cases():
    return pilot.read(pilot.ARTIFACTS / "inputs.json") if (pilot.ARTIFACTS / "inputs.json").exists() else pilot.construct_inputs()


def test_counterfactual_changes_are_distinct(cases):
    for issuer in pilot.ISSUERS:
        base = cases[f"{issuer}-base"]["gold"]
        common = cases[f"{issuer}-common_shift"]["gold"]
        latest = cases[f"{issuer}-latest_shift"]["gold"]
        assert all(Decimal(base[key]) - Decimal(common[key]) == pilot.COMMON_SHIFT
                   for key in ("prior_q4", "latest_q4"))
        assert base["change"] == common["change"]
        assert base["prior_q4"] == latest["prior_q4"]
        assert Decimal(base["change"]) - Decimal(latest["change"]) == pilot.LATEST_SHIFT
        assert base["direction"] == "raised" and latest["direction"] == "lowered"


def test_missing_latest_preserves_prior_but_never_publishes_difference(cases):
    case = cases["gitlab-missing_latest"]
    result = pilot.evaluate(pilot.injected(case, "clean"), case)["grades"]
    assert result["fieldwise"]["prior_q4"]["supported_correct"]
    assert result["all_or_nothing"]["prior_q4"]["actual"] is None
    assert all(result["fieldwise"][key]["actual"] is None for key in ("latest_q4", "change", "direction"))


def test_wrong_year_and_error_cancellation_leave_unverifiable_values(cases):
    case = cases["gitlab-base"]
    for fault in ("wrong_year_citation", "common_operand_error"):
        result = pilot.evaluate(pilot.injected(case, fault), case)["grades"]
        assert result["direct"]["change"]["numeric_exact"] and not result["direct"]["change"]["grounded"]
        assert result["fieldwise"]["change"]["actual"] is None


def test_ledger_reproduces_masking_counts():
    root = pilot.ARTIFACTS if (pilot.ARTIFACTS / "scores.csv").exists() else pilot.ARCHIVE
    stats = pilot.archive_summary(pilot.archived_masking(root))
    assert stats["harness"]["masked_errors"] == stats["harness"]["change_correct"] == 8
    assert stats["harness"]["both_components_correct"] == stats["astra"]["masked_errors"] == 0
