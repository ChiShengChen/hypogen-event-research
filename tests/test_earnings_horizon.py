from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from research_app.adapters import Fixture
from research_app.api import create_app
from research_app.earnings import EarningsError, calculate_earnings
from research_app.research import build_context
from research_app.schema import Event, RevenueBridge
from research_app.store import Store


def setup_case():
    event = Event.model_validate_json(Path("research_app/examples/asml-earnings.json").read_text())
    source = {"available_at": "2024-04-17T23:59:59Z", "evidence_ids": ["asml-q1-2024:history"], "method": "測試用時點資料"}
    bridge = RevenueBridge(
        period_end="2025-03-31", currency="EUR", basis="US_GAAP", near_fiscal_quarter=4, far_fiscal_quarter=1,
        method="guided_absolute",
        history=[{**source, "period_end": "2023-12-31", "fiscal_quarter": 4, "value": "7000000000"},
                 {**source, "period_end": "2024-03-31", "fiscal_quarter": 1, "value": "8000000000"}],
        adjustments=[{**source, "id": "new-volume", "segment": "net_system_sales", "driver": "volume",
                      "value": "50000000", "public_check": "核對次季系統營收", "falsifier": "未如期認列"}],
    )
    guide = {"key": {"period_end": "2024-12-31", "metric": "revenue", "duration": "quarter",
                     "scope": "consolidated", "basis": "US_GAAP", "currency": "EUR"}, "kind": "issuer_guidance",
             "label": "公司指引", "available_at": event.as_of.isoformat(), "low": "8800000000",
             "high": "9200000000", "evidence_ids": ["asml-q3:guidance"]}
    return event, bridge, guide


def test_revenue_bridge_via_workbench_branch_and_exact_reconciliation(tmp_path):
    event, bridge, guide = setup_case()
    with TestClient(create_app(Store(tmp_path / "bridge.sqlite3"), Fixture())) as client:
        published = client.post("/events", json=event.model_dump(mode="json"))
        root = f"/reports/{published.json()['report_id']}"
        orig = client.get(f"{root}/revisions/1").json()
        result = client.post(f"{root}/earnings/branches", json={"parent_revision": 1, "revenue_bridge": bridge.model_dump(mode="json"),
                                                              "issuer_guidance": [guide], "calibrate_guidance": False})
        assert result.status_code == 200, result.text
        child = result.json()["earnings"]
        assert child["quarters"][0]["scenarios"] == orig["earnings"]["quarters"][0]["scenarios"]
        far = child["quarters"][1]["scenarios"]["base"]["revised"]
        assert Decimal(far["revenue"]) == Decimal(10_050_000_000)
        assert sum(map(Decimal, far["segment_revenue"].values())) == Decimal(far["revenue"])
        assert Decimal(child["revenue_bridge"]["anchor"]) == Decimal(10_000_000_000)
        assert "asml-q3:guidance" in child["revenue_bridge"]["anchor_evidence_ids"]
        assert child["revenue_bridge"]["adjustments"][0]["id"] == "new-volume"
        assert "未取得同口徑點時市場共識" in result.json()["markdown"]
        assert client.get(f"{root}/revisions/1").json() == orig


def test_revenue_bridge_rejects_future_observation():
    event, bridge, _ = setup_case()
    bridge = bridge.model_copy(update={"history": [bridge.history[0].model_copy(update={
        "period_end": event.earnings_plan.quarters[0].period_end,
    })]})
    plan = event.earnings_plan.model_copy(update={"revenue_bridge": bridge})
    with pytest.raises(EarningsError, match="早於首個預測季"):
        calculate_earnings(plan, event.as_of, build_context(event)["evidence"])


def test_direct_second_quarter_guidance_precedes_bridge(tmp_path):
    event, bridge, guide = setup_case()
    direct = {**guide, "key": {**guide["key"], "period_end": "2025-03-31"}}
    with TestClient(create_app(Store(tmp_path / "guide.sqlite3"), Fixture())) as client:
        initial = client.post("/events", json=event.model_dump(mode="json"))
        root = f"/reports/{initial.json()['report_id']}"
        response = client.post(f"{root}/earnings/branches", json={"parent_revision": 1, "revenue_bridge": bridge.model_dump(mode="json"),
                                                                "issuer_guidance": [direct], "calibrate_guidance": True})
        assert response.status_code == 200, response.text
        result = response.json()["earnings"]
        assert "revenue_bridge" not in result
        assert Decimal(result["quarters"][1]["scenarios"]["base"]["revised"]["revenue"]) == Decimal("9000000000")
