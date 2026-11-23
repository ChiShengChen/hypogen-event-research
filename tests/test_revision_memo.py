from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from benchmarks import revision_memo_review
from research_app.adapters import Fixture
from research_app.api import create_app
from research_app.store import Store


def test_freezes_guidance_trial_and_recalculable_workbook(tmp_path, monkeypatch):
    actors = {role: {"role": role, "token_sha256": sha256(role.encode()).hexdigest()}
              for role in ("author", "reviewer", "approver")}
    monkeypatch.setenv("RESEARCH_MEMO_IDENTITIES", json.dumps(actors))
    event = json.loads(Path("research_app/examples/asml-earnings.json").read_text())
    disclosure = next(doc for doc in event["documents"] if doc["id"] == "asml-q3")
    event["documents"].append({
        **disclosure, "id": "test-guidance", "text_format": "excerpt",
        "paragraphs": {"range": "ASML expects consolidated US GAAP revenue for the quarter ending "
                       "2024-12-31 to be EUR 8.8–9.2 billion.", "formula": "=1+1"},
    })
    key = {"metric": "revenue", "period_end": "2024-12-31", "duration": "quarter",
           "scope": "consolidated", "basis": "US_GAAP", "currency": "EUR"}
    quote = {"key": key, "available_at": event["as_of"], "low": "8800000000", "high": "9200000000",
             "evidence_ids": ["test-guidance:range"]}
    with TestClient(create_app(Store(tmp_path / "research.sqlite3"), Fixture())) as client:
        created = client.post("/events", json=event).json()
        root = f"/reports/{created['report_id']}"
        prior = client.get(f"{root}/revisions/1").json()
        driver = next(item for item in prior["earnings"]["inputs"]["drivers"]
                      if item["period_end"] == key["period_end"] and item["scenario"] == "base")
        driver["segment_revenue_delta"]["net_system_sales"] = "0"
        child = client.post(f"{root}/earnings/branches", json={"parent_revision": 1, "drivers": [driver]}).json()
        revision = f"{root}/revisions/{child['revision']}"
        url = f"{revision}/revision-memos"
        inputs = {"quotes": {"period_end": key["period_end"], "disclosure": quote}}
        author = {"Authorization": "Bearer author"}
        response = client.post(url, json=inputs, headers=author)
        assert response.status_code == 200, response.text
        issued = response.json()
        memo = issued["memo"]
        assert memo["author"] == "author" and memo["prior_revision"] == 1
        assert memo["guidance_audit"]["status"] == "eligible"
        assert Decimal(memo["model"]["proposed"]["revenue"]) == Decimal(quote["low"])
        assert Decimal(memo["model"]["proposed"]["revenue"]) - Decimal(memo["model"]["current"]["revenue"]) == Decimal(
            memo["guidance_audit"]["remaining_delta"])
        assert client.post(url, json=inputs, headers=author).json()["memo_id"] == issued["memo_id"]
        record = f"{url}/{issued['memo_id']}"
        assert client.get(record).json()["outcomes"]["live"]["reported"] == 0
        html = client.get(record + "/exports/html")
        assert html.status_code == 200 and "ASML" in html.text
        book = load_workbook(BytesIO(client.get(record + "/exports/xlsx").content))
        assert book["預估變動"]["D15"].value == "=D14/D8"
        assert next(cell for row in book["引文"].iter_rows() for cell in row if cell.value == "=1+1").data_type == "s"
        statement = {"decision": "approved", "note": "已逐欄覆核", "conflict_check": "clear"}
        assert client.post(record + "/signoffs", json=statement).status_code == 401
        assert client.post(record + "/signoffs", json=statement, headers=author).status_code == 403
        assert client.post(record + "/signoffs", json=statement,
                           headers={"Authorization": "Bearer reviewer"}).json()["status"] == "reviewed"
        assert client.post(record + "/signoffs", json=statement,
                           headers={"Authorization": "Bearer approver"}).status_code == 422
        bad = {**quote, "low": "8700000000"}
        refusal = client.post(url, json={"quotes": {"period_end": key["period_end"], "disclosure": bad}}).json()["memo"]
        assert refusal["guidance_audit"]["status"] == "blocked" and refusal["model"]["proposed"] is None
        assert client.get(revision).json()["earnings"] == child["earnings"]


def test_blind_review_requires_complete_real_pairs_and_keeps_key_separate(tmp_path):
    cases, requests = revision_memo_review.sealed(tmp_path, write=True)
    assert len(cases) == 8 and len(requests) == 8
    assert revision_memo_review.calibration(tmp_path) == {"pairs_ready": 4, "human_completed_pairs": 0}
    assert (tmp_path / "review-key.restricted.json").is_file()
    assert not (tmp_path / "calibration/review-key.restricted.json").exists()
    (tmp_path / "holdout").mkdir()
    initial = revision_memo_review.formal_review(tmp_path, cases, None)
    assert initial["paired"] == initial["human_completed_pairs"] == initial["model_calls"] == 0
    candidate = {"point_in_time_facts": ["待驗證"], "primary": None, "gaps": []}
    for arm in revision_memo_review.equal.ARMS:
        receipt = revision_memo_review.equal.journal.receipt(tmp_path, "E-01", arm)
        receipt.parent.mkdir(exist_ok=True)
        receipt.write_text(json.dumps({"status": "completed", "candidate": candidate, "started_at": "observed"}))
    result = revision_memo_review.formal_review(tmp_path, cases, None)
    assert result["paired"] == 1 and result["model_calls"] == 2 and result["passed"] is None
    anonymized = (tmp_path / "holdout/analyst-review.md").read_text()
    assert "E-01" in anonymized and "### R" in anonymized and "### astra" not in anonymized
