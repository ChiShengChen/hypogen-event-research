from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from research_app.earnings import EarningsError, validate_plan
from research_app.revenue import bridge_forecast, turn_forecast
from research_app.research import build_context
from research_app.schema import EstimateReference, Event, RevenueBridge, RevenueTurnSignal

SOURCE = {"available_at": "2025-05-09T18:00:00Z", "evidence_ids": ["historical:revenue"], "method": "測試資料"}


def make_case(recent, next_quarter_mid):
    values = [(date(year, month, day), quarter, 100)
              for year, month, day, quarter in ((2022, 12, 31, 4), (2023, 3, 31, 1), (2023, 6, 30, 2),
                                                   (2023, 12, 31, 4), (2024, 3, 31, 1), (2024, 6, 30, 2),
                                                   (2024, 12, 31, 4))]
    values.append((date(2025, 3, 31), 1, recent))
    bridge = RevenueBridge(period_end="2025-09-30", currency="USD", basis="US_GAAP", near_fiscal_quarter=2,
                           far_fiscal_quarter=3, method="confirmed_turn",
                           history=[{**SOURCE, "period_end": period, "fiscal_quarter": quarter, "value": value}
                                    for period, quarter, value in values])
    guide = EstimateReference(key={"metric": "revenue", "period_end": "2025-06-30", "duration": "quarter",
                                   "scope": "consolidated", "basis": "US_GAAP", "currency": "USD"},
                              kind="issuer_guidance", label="next", available_at=SOURCE["available_at"],
                              low=next_quarter_mid, high=next_quarter_mid, evidence_ids=["issuer:guide"])
    return bridge, guide


@pytest.mark.parametrize(("actual", "guide", "status", "result"), [
    (120, 180, "up", Decimal("115")), (80, 50, "down", Decimal("85")),
    (105, 113, "unconfirmed", Decimal("100")), (120, 75, "unconfirmed", Decimal("100")),
])
def test_directional_support_and_magnitude_cap(actual, guide, status, result):
    bridge, record = make_case(actual, guide)
    estimate, audit = turn_forecast(bridge, record, Decimal(100))
    assert estimate == result
    assert audit["status"] == status
    assert "issuer:guide" in audit["evidence_ids"]
    assert "historical:revenue" in audit["evidence_ids"]


def test_operating_signal_must_use_separate_evidence_and_not_conflict():
    bridge, record = make_case(100, 125)
    signal = RevenueTurnSignal(driver="capacity", direction="up", available_at=SOURCE["available_at"],
                               evidence_ids=["issuer:guide"], observation="測試用產能方向")
    bridge = bridge.model_copy(update={"operating_signals": [signal]})
    assert turn_forecast(bridge, record, Decimal(100))[1]["status"] == "unconfirmed"
    signal = signal.model_copy(update={"evidence_ids": ["issuer:capacity"]})
    bridge = bridge.model_copy(update={"operating_signals": [signal]})
    assert turn_forecast(bridge, record, Decimal(100))[0] == Decimal("112.5")
    down = signal.model_copy(update={"direction": "down", "evidence_ids": ["issuer:weak-orders"]})
    bridge = bridge.model_copy(update={"operating_signals": [signal, down]})
    assert turn_forecast(bridge, record, Decimal(100))[1]["status"] == "unconfirmed"


def test_missing_guidance_preserves_raw_forecast_and_skips_manual_adjustments():
    bridge, _ = make_case(120, 180)
    assert "operating_signals" not in bridge.model_dump(mode="json")
    bridge = RevenueBridge.model_validate(bridge.model_dump() | {"adjustments": [
        {**SOURCE, "id": "candidate", "segment": "consolidated", "driver": "volume", "value": 10,
         "public_check": "測試用", "falsifier": "測試用"},
    ]})
    estimate, audit = bridge_forecast(bridge, None, Decimal(100))
    assert estimate == 100
    assert audit["turn"]["status"] == "missing_signal"
    assert not audit["adjustments"]


def test_future_operating_signal_cannot_enter_the_plan():
    example = Path("research_app/examples/asml-earnings.json")
    event = Event.model_validate_json(example.read_text())
    signal = RevenueTurnSignal(driver="mix", direction="up", available_at="2024-10-17T23:59:59Z",
                               evidence_ids=["asml-q3:actual"], observation="測試用事後訊號")
    bridge = RevenueBridge(period_end="2025-03-31", currency="EUR", basis="US_GAAP", near_fiscal_quarter=4,
                           far_fiscal_quarter=1, method="confirmed_turn", operating_signals=[signal],
                           history=[{"period_end": "2024-03-31", "fiscal_quarter": 1, "value": "100",
                                     "available_at": "2024-04-17T23:59:59Z",
                                     "evidence_ids": ["asml-q1-2024:history"], "method": "測試用基準"}])
    with pytest.raises(EarningsError, match="來源晚於研究截止時點"):
        validate_plan(event.earnings_plan.model_copy(update={"revenue_bridge": bridge}),
                      event.as_of, build_context(event)["evidence"])
