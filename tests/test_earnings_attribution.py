from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from benchmarks.earnings_prospective import ARMS, INITIAL_ACCESSIONS, ActualQuarter, Cohort
from research_app.adapters import Fixture
from research_app.api import create_app
from research_app.earnings import EarningsError
from research_app.schema import Event
from research_app.store import Store


def asml():
    return Event.model_validate_json(Path("research_app/examples/asml-earnings.json").read_text())


def shift():
    return {
        "id": "euv-transfer", "hypothesis_stance": "bear", "scenario": "bear",
        "hypothesis_summary": "認列延後一季", "assumption": "一台已在原情境，期別延後",
        "evidence_ids": ["asml-q3:guidance"], "public_check": "核對兩季同口徑系統收入",
        "falsifier": "披露指出設備仍於較早季度認列",
        "recognition_shift": {"from_period": "2024-12-31", "to_period": "2025-03-31",
                              "segment": "net_system_sales", "units": 1, "revenue_per_unit": "150000000",
                              "recognition_basis": "明列單價情境假設"},
    }


def test_linked_shift_moves_same_revenue_between_quarters_and_preserves_parent(tmp_path):
    event = asml()
    store = Store(tmp_path / "test.sqlite3")
    with TestClient(create_app(store, Fixture())) as client:
        result = client.post("/events", json=event.model_dump(mode="json")).json()
        root = f"/reports/{result['report_id']}"
        before = client.get(f"{root}/revisions/1").json()
        route = f"{root}/earnings/branches"
        # The old plan explicitly counted a shipment in this slot. It cannot be counted twice.
        invalid = client.post(route, json={"parent_revision": 1, "driver_links": [shift()]})
        assert invalid.status_code == 422
        driver = deepcopy(next(row for row in before["earnings"]["inputs"]["drivers"]
                               if row["period_end"] == "2024-12-31" and row["scenario"] == "bear"))
        units = driver["shipment_changes"].pop("net_system_sales")
        driver["segment_revenue_delta"]["net_system_sales"] = str(
            Decimal(driver["segment_revenue_delta"]["net_system_sales"])
            + units["incremental_recognized_units"] * Decimal(units["revenue_per_unit"])
        )
        response = client.post(route, json={"parent_revision": 1, "drivers": [driver], "driver_links": [shift()]})
        assert response.status_code == 200, response.text
        after = response.json()
        audit = after["earnings"]["driver_audit"][0]
        assert audit["hypothesis_prediction"]
        assert [Decimal(row["revenue"]) for row in audit["effects"]] == [-150_000_000, 150_000_000]
        assert [q["period_end"] for q in audit["effects"]] == ["2024-12-31", "2025-03-31"]
        assert Decimal(audit["effects"][0]["eps"]) < 0 < Decimal(audit["effects"][1]["eps"])
        assert client.get(f"{root}/revisions/1").json() == before


def consensus_csv():
    columns = "metric,period_end,duration,scope,basis,currency,unit,low,high,available_at"
    return columns + "\nrevenue,2024-09-30,quarter,consolidated,US_GAAP,EUR,currency_millions,7000,7200,2024-10-14T16:00:00Z\n"


def test_consensus_import_preserves_capture_and_same_scope(tmp_path):
    with TestClient(create_app(Store(tmp_path / "consensus.sqlite3"), Fixture())) as client:
        result = client.post("/events", json=asml().model_dump(mode="json")).json()
        root = f"/reports/{result['report_id']}"
        request = {"parent_revision": 1, "provider": "測試快照", "target": "ASML",
                   "source_url": "https://consensus.example/asml", "captured_at": "2024-10-14T20:00:00Z",
                   "purpose": "historical_replay", "csv_text": consensus_csv()}
        response = client.post(f"{root}/earnings/consensus", json=request)
        assert response.status_code == 200, response.text
        child = response.json()
        comparison = next(row for row in child["earnings"]["comparisons"] if row["baseline"]["kind"] == "consensus")
        assert Decimal(comparison["baseline"]["low"]) == 7_000_000_000
        assert comparison["relation"] == "above"
        assert child["consensus_imports"][0]["imported_at"] > child["consensus_imports"][0]["captured_at"]
        old = client.get(f"{root}/revisions/1").json()
        assert "consensus_imports" not in old
        response = client.post(f"{root}/earnings/consensus", json={**request, "captured_at": "2024-10-16T01:00:00Z"})
        assert response.status_code == 422
        mismatched = client.post(f"{root}/earnings/consensus", json={
            **request, "csv_text": consensus_csv().replace("US_GAAP", "IFRS"),
        }).json()
        assert all(row["baseline"]["kind"] != "consensus" for row in mismatched["earnings"]["comparisons"])


def test_prospective_ledger_locks_complete_forecasts_before_result(tmp_path):
    source = "https://www.sec.gov/Archives/edgar/data/2488/000000248826000191/amd-20260926.htm"
    event_at = "2026-11-04T23:59:59Z"
    period = "2026-12-26"
    baseline_date = "2026-08-05T23:59:59Z"
    plan = Event.model_validate({
        "event_text": "本機測試資料", "as_of": event_at, "research_target": "AMD", "documents": [
            {"id": "event", "source": source, "kind": "disclosure", "published_at": event_at,
             "obtained_at": event_at, "paragraphs": {"fact": "專用測試"}},
            {"id": "baseline", "source": "https://www.sec.gov/", "kind": "disclosure",
             "published_at": baseline_date, "obtained_at": baseline_date, "paragraphs": {"ref": "測試基準"}},
        ],
        "earnings_plan": {"event_at": event_at, "currency": "USD", "basis": "US_GAAP", "generate_drivers": True,
                          "quarters": [{"period_end": end, "available_at": baseline_date, "segment_revenue": {"consolidated": 100},
                                        "gross_margin": "0.5", "opex": 20, "tax_rate": "0.2", "diluted_shares": 10,
                                        "evidence_ids": ["baseline:ref"], "method": "測試資料"}
                                       for end in (period, "2027-03-27")]},
    })
    now = datetime(2026, 11, 23, tzinfo=timezone.utc)
    cohort = Cohort(tmp_path)
    case = cohort.enroll("AMD", INITIAL_ACCESSIONS["AMD"], plan, now)
    assert case == "AMD-01"
    assert cohort.enroll("AMD", INITIAL_ACCESSIONS["AMD"], plan, now) == case
    with pytest.raises(EarningsError, match="不可覆寫"):
        cohort.enroll("AMD", INITIAL_ACCESSIONS["AMD"], plan.model_copy(update={"event_text": "after edit"}), now)
    points = [{"period_end": end, "scenario": scenario, "revenue": "100", "gross_margin": "0.5",
               "operating_income": "30", "eps": "2.4", "rationale": "測試", "evidence_ids": ["event:fact"]}
              for end in (period, "2027-03-27") for scenario in ("bear", "base", "bull")]
    outputs = {arm: {"points": points} for arm in ARMS}
    with pytest.raises(EarningsError, match="三組"):
        cohort.seal(case, {"astra": outputs["astra"]}, now)
    cohort.seal(case, outputs, now)
    result = ActualQuarter(period_end=period, duration="quarter", currency="USD", basis="US_GAAP", scope="consolidated",
                           source="https://www.sec.gov/Archives/edgar/data/2488/000000248827000001/example.htm",
                           accession="0000002488-27-000001", published_at="2027-01-25T20:00:00Z",
                           revenue=100, gross_margin="0.5", operating_income=30, eps="2.4")
    with pytest.raises(EarningsError, match="期末後"):
        cohort.resolve(case, result, now)
    later = datetime(2027, 1, 26, tzinfo=timezone.utc)
    cohort.resolve(case, result, later)
    with pytest.raises(EarningsError, match="不可覆寫"):
        cohort.resolve(case, result.model_copy(update={"eps": Decimal("2.5")}), later)
    summary = cohort.export()
    assert (summary["planned"], summary["sealed"], summary["resolved_quarters"]) == (30, 1, 1)
    assert summary["metrics"]["eps"] == {arm: 0 for arm in ARMS}
