from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from benchmarks.earnings_demo import scenario_path
from research_app.adapters import Fixture
from research_app.api import create_app
from research_app.schema import DriverDraft, Event
from research_app.store import Store


def asml():
    return Event.model_validate_json(Path("research_app/examples/asml-earnings.json").read_text())


def test_earnings_workflow_preserves_parent_sources_and_recomputes(tmp_path):
    event = asml()
    engine = Store(tmp_path / "earnings.sqlite3")
    with TestClient(create_app(engine, Fixture())) as client:
        run = scenario_path(client, tmp_path, event)
        url = f"/reports/{run['report_id']}/revisions/"
        original = client.get(url + "1").json()
        child = client.get(url + str(run["branch"])).json()
        old = original["earnings"]["quarters"][0]["scenarios"]["base"]
        new = child["earnings"]["quarters"][0]["scenarios"]["base"]
        assert Decimal(new["revised"]["revenue"]) - Decimal(old["revised"]["revenue"]) == 150_000_000
        assert Decimal(new["delta"]["eps"]) > Decimal(old["delta"]["eps"])
        assert child["earnings"]["valuation"] == original["earnings"]["valuation"]  # Q4 belongs to FY2024.
        values = original["earnings"]["valuation"]
        for scenario in values["scenarios"].values():
            explanations = Decimal(scenario["earnings_effect"]) + Decimal(scenario["multiple_effect"])
            assert explanations.quantize(Decimal("0.00000001")) == Decimal(scenario["total_delta"]).quantize(Decimal("0.00000001"))
        assert {row["relation"] for row in original["earnings"]["comparisons"]} == {"above", "overlaps", "below"}
        assert run["resolutions"] == ["miss", "miss"]
        assert client.get(url + str(run["branch"]) + "/earnings").json()["reviews"] == []
        assert client.get(url + "1/earnings").json()["reviews"][0]["decision"] == "changes_requested"


def test_post_event_baseline_is_rejected(tmp_path):
    event = asml().model_dump(mode="json")
    baseline = event["earnings_plan"]["quarters"][0]
    baseline["evidence_ids"] = ["asml-q3:guidance"]
    with TestClient(create_app(Store(tmp_path / "reject.sqlite3"), Fixture())) as client:
        result = client.post("/events", json=event)
        assert result.status_code == 422
        assert "時點" in result.json()["detail"]


def test_forecast_accounting_scope_and_resolution_are_immutable(tmp_path):
    event = asml().model_dump(mode="json")
    with TestClient(create_app(Store(tmp_path / "forecast.sqlite3"), Fixture())) as client:
        report_id = client.post("/events", json=event).json()["report_id"]
        root = f"/reports/{report_id}/revisions/1/forecasts"
        key = {"metric": "revenue", "period_end": "2024-12-31", "duration": "quarter",
               "scope": "consolidated", "basis": "US_GAAP", "currency": "EUR"}
        spec = {"key": key, "low": "9000000000", "high": "9500000000", "deadline": "2025-01-31T23:59:59Z",
                "resolution_source": "ASML 2024 Q4", "purpose": "historical_replay",
                "probability": "0.75", "evidence_ids": ["asml-q3:guidance"]}
        registration = client.post(root, json=spec).json()
        assert registration == client.post(root, json=spec).json()
        payload = {"status": "reported", "document": next(d for d in event["documents"] if d["id"] == "asml-q4"),
                   "paragraph_id": "actual", "key": deepcopy(key), "value": "9263000000", "note": "原始公布"}
        resolve = f"{root}/{registration['id']}/resolve"
        payload["key"]["basis"] = "IFRS"
        assert client.post(resolve, json=payload).status_code == 422
        payload["key"] = key
        actual = client.post(resolve, json=payload).json()
        assert actual["outcome"] == "hit" and actual["brier_score"] == "0.0625"
        assert actual == client.post(resolve, json=payload).json()
        payload["value"] = "9264000000"
        assert client.post(resolve, json=payload).status_code == 422
        assert client.post(root, json={**spec, "purpose": "live"}).status_code == 422


def test_model_draft_uses_frozen_public_input_and_typed_scenarios(tmp_path):
    event = asml().model_dump(mode="json")
    event["earnings_plan"].update(drivers=[], generate_drivers=True)

    class DraftFixture(Fixture):
        def earnings_drivers(self, context):
            assert "asml-q4:actual" not in {row["id"] for row in context["evidence"]}
            assert "asml-q1-2025:actual" not in {row["id"] for row in context["evidence"]}
            assert {item["stance"] for item in context["hypotheses"]} >= {"bull", "bear"}
            return DriverDraft.model_validate({"drivers": [
                {"period_end": period["period_end"], "scenario": stance, "segments": [],
                 "gross_margin_delta": "0.01" if stance == "bull" else "0", "opex_delta": "0",
                 "rationale": "多方假設組合改善，待披露查核。", "evidence_ids": ["asml-q3:guidance"]}
                for period in context["baseline"]["quarters"] for stance in ("bear", "base", "bull")
            ]})

    store = Store(tmp_path / "draft.sqlite3")
    result = store.create(Event.model_validate(event), DraftFixture())
    report = store.revision(result["report_id"], 1)
    assert report["earnings"]["driver_origin"] == "model_draft"
    assert all(len(row["scenarios"]) == 3 for row in report["earnings"]["quarters"])
    assert len(report["earnings"]["driver_audit"]) == 2
    assert all(row["origin"] == "model_draft" and row["hypothesis_stance"] == "bull"
               for row in report["earnings"]["driver_audit"])
    assert all(Decimal(row["scenarios"]["bull"]["delta"]["gross_margin"]) == Decimal("0.01")
               for row in report["earnings"]["quarters"])
