"""Run ASML's earnings revision, immutable branch, and replay-resolution workflow."""

import argparse
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from benchmarks.public_pilot import write_json
from research_app.adapters import configured_adapter
from research_app.api import create_app
from research_app.schema import Event
from research_app.store import Store


def scenario_path(client, folder, event):
    def post(path, data):
        response = client.post(path, json=data)
        if not response.is_success:
            raise ValueError(f"{path}: {response.status_code} {response.json()}")
        return response.json()

    payload = event.model_dump(mode="json")
    run = post("/events", payload)
    root = f"/reports/{run['report_id']}"
    original_path = f"{root}/revisions/1"
    original = client.get(original_path).json()
    assert "asml-q4:actual" not in {row["id"] for row in original["evidence"]}
    assert "asml-q1-2025:actual" not in {row["id"] for row in original["evidence"]}

    driver = deepcopy(next(row for row in original["earnings"]["inputs"]["drivers"]
                           if row["period_end"] == "2024-12-31" and row["scenario"] == "base"))
    driver["shipment_changes"]["net_system_sales"]["incremental_recognized_units"] += 1
    child = post(f"{root}/earnings/branches", {"parent_revision": 1, "drivers": [driver]})
    assert child["parent_revision"] == 1
    assert client.get(original_path).json()["earnings"]["quarters"] == original["earnings"]["quarters"]

    actuals = [
        ("2024-12-31", "2025-01-31", "8800000000", "9200000000", "9263000000", "asml-q4"),
        ("2025-03-31", "2025-04-30", "5800000000", "6300000000", "7742000000", "asml-q1-2025"),
    ]
    for period, deadline, lower, upper, actual, doc_id in actuals:
        key = {"metric": "revenue", "period_end": period, "duration": "quarter",
               "scope": "consolidated", "basis": "US_GAAP", "currency": "EUR"}
        forecast = post(f"{original_path}/forecasts", {
            "key": key, "low": lower, "high": upper, "deadline": deadline + "T23:59:59Z",
            "resolution_source": "ASML US GAAP 同期財報", "purpose": "historical_replay",
            "evidence_ids": ["asml-q3:guidance", "asml-q1-2024:history"],
        })
        document = next(row for row in payload["documents"] if row["id"] == doc_id)
        resolution = post(f"{original_path}/forecasts/{forecast['id']}/resolve", {
            "status": "reported", "document": document, "paragraph_id": "actual",
            "key": key, "value": actual, "note": "歷史回放流程驗證，使用首次公布的 ASML 季報。",
        })
        assert resolution["outcome"] == "miss"
    # A workflow exercise rather than a signature or an external analyst approval.
    post(f"{original_path}/reviews", {
        "reviewer": "本機流程驗證", "decision": "changes_requested",
        "note": "示範紀錄。請覆核單台收入、年度 EPS 情境及本益比的依據。",
    })
    ledger = client.get(f"{original_path}/earnings").json()
    for name, value in (("original", original), ("branch", child), ("ledger", ledger)):
        write_json(folder / f"{name}.json", value)
    for name, value in (("original", original), ("branch", child)):
        (folder / f"{name}.md").write_text(value["markdown"], encoding="utf-8")
    return {"report_id": run["report_id"], "branch": child["revision"],
            "resolutions": [row["status"] for row in ledger["forecasts"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/earnings-asml"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve().parents[1] / "research_app" / "examples" / "asml-earnings.json"
    event = Event.model_validate_json(source.read_text(encoding="utf-8"))
    with TestClient(create_app(Store(args.output / "asml.sqlite3"), configured_adapter())) as client:
        print(scenario_path(client, args.output, event))


if __name__ == "__main__":
    main()
