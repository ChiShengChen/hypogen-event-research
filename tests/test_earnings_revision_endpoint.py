from decimal import Decimal
import json
from pathlib import Path

from fastapi.testclient import TestClient

from research_app.adapters import Fixture
from research_app.api import create_app
from research_app.store import Store


def test_revenue_revision_preview_checks_saved_estimate_without_writing_a_revision(tmp_path):
    event = json.loads(Path("research_app/examples/asml-earnings.json").read_text())
    disclosure = next(row for row in event["documents"] if row["id"] == "asml-q3")
    event["documents"].append({
        **disclosure, "id": "test-guidance", "text_format": "excerpt",
        "paragraphs": {"q4-revenue-range": (
            "ASML expects consolidated US GAAP revenue for the quarter ending 2024-12-31 to be EUR 8.8–9.2 billion."
        )},
    })
    key = {"metric": "revenue", "period_end": "2024-12-31", "duration": "quarter",
           "scope": "consolidated", "basis": "US_GAAP", "currency": "EUR"}
    quote = {"key": key, "available_at": event["as_of"], "low": "8800000000", "high": "9200000000",
             "evidence_ids": ["test-guidance:q4-revenue-range"]}
    body = {"period_end": key["period_end"], "disclosure": quote}

    with TestClient(create_app(Store(tmp_path / "revision-preview.sqlite3"), Fixture())) as client:
        created = client.post("/events", json=event)
        assert created.status_code == 200, created.text
        root = f"/reports/{created.json()['report_id']}"
        revision = f"{root}/revisions/1"
        before = client.get(revision).json()

        response = client.post(f"{revision}/earnings/revision-check", json=body)
        assert response.status_code == 200, response.text
        preview = response.json()
        assert preview["audit"]["status"] == "noop", preview["audit"]
        assert Decimal(preview["audit"]["remaining_delta"]) == 0
        assert all(values["before"] == values["after"] for values in preview["financial_impact"].values())

        driver = next(row for row in before["earnings"]["inputs"]["drivers"]
                      if row["period_end"] == key["period_end"] and row["scenario"] == "base")
        driver["segment_revenue_delta"]["net_system_sales"] = "0"
        created_child = client.post(f"{root}/earnings/branches", json={"parent_revision": 1, "drivers": [driver]})
        assert created_child.status_code == 200, created_child.text
        child = created_child.json()
        quarter = next(row for row in child["earnings"]["quarters"] if row["period_end"] == key["period_end"])
        current = quarter["scenarios"]["base"]["revised"]
        child_revision = f"{root}/revisions/{child['revision']}"
        response = client.post(f"{child_revision}/earnings/revision-check", json=body)
        assert response.status_code == 200, response.text
        preview = response.json()
        assert preview["audit"]["status"] == "eligible", preview["audit"]
        assert Decimal(preview["audit"]["remaining_delta"]) == Decimal(quote["low"]) - Decimal(current["revenue"])
        assert Decimal(preview["financial_impact"]["revenue"]["after"]) == Decimal(quote["low"])
        assert preview["financial_impact"]["eps"]["before"] == current["eps"]
        assert Decimal(preview["financial_impact"]["eps"]["after"]) > Decimal(current["eps"])
        assert client.get(child_revision).json()["earnings"] == child["earnings"]
        assert client.get(f"{root}/revisions/{child['revision'] + 1}").status_code == 404

        wrong_quote = {**quote, "low": "8700000000"}
        response = client.post(f"{child_revision}/earnings/revision-check", json={**body, "disclosure": wrong_quote})
        assert response.status_code == 200, response.text
        assert response.json()["audit"]["status"] == "blocked"
        assert response.json()["financial_impact"] is None
