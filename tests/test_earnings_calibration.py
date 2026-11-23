from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from research_app.adapters import Fixture
from research_app.api import create_app
from research_app.earnings import EarningsError, issuer_guidance, operating_numbers, validate_plan
from research_app.research import build_context
from research_app.schema import EPSAssumptions, Event, EstimateReference
from research_app.store import Store


def asml():
    return Event.model_validate_json(Path("research_app/examples/asml-earnings.json").read_text())


def issuer_record(event, metric, low, high):
    return {"key": {"period_end": "2024-12-31", "scope": "consolidated", "duration": "quarter", "currency": "EUR",
                    "basis": "US_GAAP", "metric": metric}, "kind": "issuer_guidance", "label": "ASML 2024 Q4 展望",
            "available_at": event.as_of.isoformat(), "low": low, "high": high, "evidence_ids": ["asml-q3:guidance"]}


def tax_profile(quarter):
    cited = {"available_at": quarter.available_at, "evidence_ids": quarter.evidence_ids, "method": "測試用模型假設"}
    return EPSAssumptions(period_end=quarter.period_end, tax_rate={**cited, "value": "0.2"},
                          diluted_shares={**cited, "value": 400_000_000},
                          recurring_nonoperating={**cited, "value": 100_000_000}, one_offs=[
                              {**cited, "label": "一次性營業外收入", "treatment": "pretax_nonoperating", "value": 200_000_000},
                              {**cited, "label": "一次性所得稅費用", "treatment": "income_tax_expense", "value": 80_000_000},
                          ])


def test_earnings_branch_calibrates_guidance_and_preserves_original_report(tmp_path):
    event = asml()
    revenue = issuer_record(event, "revenue", "8800000000", "9200000000")
    margin = issuer_record(event, "gross_margin", "0.49", "0.50")
    profile = tax_profile(event.earnings_plan.quarters[0])
    with TestClient(create_app(Store(tmp_path / "earnings.sqlite"), Fixture())) as client:
        response = client.post("/events", json=event.model_dump(mode="json"))
        root = f"/reports/{response.json()['report_id']}"
        before = client.get(f"{root}/revisions/1").json()
        response = client.post(f"{root}/earnings/branches", json={
            "parent_revision": 1, "issuer_guidance": [revenue, margin], "calibrate_guidance": True,
            "eps_assumptions": [profile.model_dump(mode="json")],
        })
        assert response.status_code == 200, response.text
        result = response.json()
        first, second = result["earnings"]["quarters"]
        revised = first["scenarios"]["base"]["revised"]
        assert Decimal(revised["revenue"]) == pytest.approx(Decimal("9000000000"), abs=Decimal("0.000001"))
        assert Decimal(revised["gross_margin"]) == Decimal("0.495")
        assert Decimal(revised["net_income"]) == (
            (Decimal(revised["operating_income"]) + 300_000_000) * Decimal("0.8") - 80_000_000
        )
        assert Decimal(revised["eps"]) == Decimal(revised["net_income"]) / 400_000_000
        assert second == before["earnings"]["quarters"][1]
        assert len(result["earnings"]["guidance_calibration"]) == 2
        assert "一次性所得稅費用" in result["markdown"]
        assert client.get(f"{root}/revisions/1").json() == before


def test_guidance_exact_scope_and_latest_vintage():
    event = asml()
    usable = issuer_record(event, "gross_margin", "0.49", "0.50")
    excluded = []
    for changes in ({"basis": "adjusted"}, {"scope": "net_system_sales"}, {"duration": "year"}, {"currency": "USD"},
                    {"period_end": "2025-07-01"}):
        excluded.append(EstimateReference.model_validate({**usable, "key": {**usable["key"], **changes}}))
    original = EstimateReference.model_validate(usable)
    plan = event.earnings_plan.model_copy(update={"event_values": [*excluded, original]})
    assert list(issuer_guidance(plan).values()) == [original]
    conflicting = original.model_copy(update={"low": Decimal("0.50"), "high": Decimal("0.51")})
    assert issuer_guidance(plan.model_copy(update={"event_values": [original, conflicting]})) == {}
    late = deepcopy(usable)
    late["available_at"] = "2024-10-16T23:59:59Z"
    with pytest.raises(EarningsError, match="事件數字"):
        validate_plan(plan.model_copy(update={"event_values": [EstimateReference.model_validate(late)]}),
                      event.as_of, build_context(event)["evidence"])


def test_loss_tax_benefit_is_an_explicit_assumption():
    event = asml()
    quarter = event.earnings_plan.quarters[0].model_copy(update={"opex": Decimal("9000000000")})
    profile = tax_profile(quarter)
    before = operating_numbers(quarter, profile=profile)
    after = operating_numbers(quarter, profile=profile.model_copy(update={"recognize_loss_tax_benefit": True}))
    assert before["net_income"] == before["operating_income"] + 300_000_000 - 80_000_000
    assert after["net_income"] > before["net_income"]
