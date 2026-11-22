import json
import sqlite3
import subprocess
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from research_app.adapters import Fixture, Live, configured_adapter
from research_app.api import create_app
from research_app.store import Store

FIXTURES = Path(__file__).resolve().parents[1] / "research_app" / "fixtures"


def load(name="shutdown"):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture
def api(tmp_path):
    return TestClient(create_app(Store(tmp_path / "research.db"), Fixture()))


def create(api, payload=None):
    response = api.post("/events", json=payload if payload is not None else load())
    assert response.status_code == 200, response.text
    return response.json()


def report(api, run, revision=1):
    response = api.get(f"/reports/{run['report_id']}/revisions/{revision}")
    assert response.status_code == 200
    return response.json()


def ask(api, run, **overrides):
    return api.post(f"/reports/{run['report_id']}/questions", json={
        "parent_revision": 1, "question": "客戶已認證乙嗎？", **overrides,
    })


def test_scenario_revision_survives_reopening(tmp_path):
    path = tmp_path / "research.db"
    with TestClient(create_app(Store(path), Fixture())) as client:
        run = create(client)
        assert create(client) == run
        assert client.get(f"/runs/{run['run_id']}").json() == run
        original = report(client, run)
        changed = ask(client, run, question="300 批還受益嗎？", overrides={"lots": 300})
        assert changed.status_code == 200
        branch = changed.json()
        assert branch["incremental_eps_delta"] == "-0.072"
        assert "400 批" in branch["answer"]
        grandchild = ask(client, run, parent_revision=branch["child_revision"], overrides={"lots": 600})
        assert grandchild.json()["incremental_eps_delta"] == "0.072"

    with TestClient(create_app(Store(path), Fixture())) as client:
        assert report(client, run) == original
        child = report(client, run, branch["child_revision"])
        assert child["parent_revision"] == 1
        assert original["model_outputs"]["incremental_eps"] == "0.048"
        assert child["model_outputs"]["incremental_eps"] == "-0.024"
        assert child["model_outputs"]["incremental_net_income"] == "-2400000.00"
        assert child["model_outputs"]["break_even_lots"] == 400
        assert child["model_outputs"]["min_profitable_lots"] == 401
        assert child["hypotheses"] == original["hypotheses"]
        assert child["assessment"] == original["assessment"]
        assert child["evidence"] == original["evidence"]
        assert not any(entry["field"] in {"hypotheses", "assessment"} for entry in branch["changes"])
        assert "本季全數交付並認列" in child["markdown"]
        assert "-0.024" in child["markdown"]
        assert client.get("/reports/unknown/revisions/1").status_code == 404
        assert client.get(f"/reports/{run['report_id']}/revisions/999").status_code == 404
        assert ask(client, run, parent_revision=999).status_code == 404


def test_publication_and_acquisition_cutoffs(api):
    payload = load()
    original = create(api, payload)
    unavailable = ask(api, original).json()
    assert not unavailable["evidence_ids"] and unavailable["gaps"]
    payload["as_of"] = "2025-01-20T18:00:00+08:00"
    assert ask(api, create(api, payload)).json() == unavailable
    payload["as_of"] = "2025-01-21T09:00:00+08:00"
    available = create(api, payload)
    answer = ask(api, available).json()
    assert answer["evidence_ids"] == ["qualification:1"]
    assert "已完成乙公司" in answer["answer"]
    assert ask(api, original).json() == unavailable
    assert "qualification:1" not in report(api, original)["markdown"]


def test_distinct_positions_and_missing_supply_evidence(api):
    payload = load()
    supported = report(api, create(api, payload))
    assert supported["supply_edges"][0]["status"] == "evidenced"
    positions = {item["stance"]: item for item in supported["hypotheses"]}
    for field in ("mechanism", "prediction", "invalidation"):
        assert positions["bull"][field] != positions["bear"][field]
    payload["documents"] = [doc for doc in payload["documents"] if doc["id"] != "supply"]
    reduced = report(api, create(api, payload))
    assert reduced["supply_edges"][0]["status"] == "unknown"
    assert reduced["supply_edges"][0]["evidence_id"] is None


@pytest.mark.parametrize("invalid_part", ["hypothesis", "assessment", "scope"])
def test_reject_model_references_without_writing(tmp_path, invalid_part):
    class InvalidFixture(Fixture):
        invalid_generation = False

        def hypotheses(self, context):
            result = super().hypotheses(context)
            if self.invalid_generation:
                if invalid_part == "hypothesis":
                    result.hypotheses[0].claim_ids = ["nonexistent"]
                elif invalid_part == "assessment":
                    result.assessment.evidence_limits[0].evidence_id = "qualification:1"
                else:
                    result.hypotheses[0].target = "其他公司"
            return result

        def answer(self, context, question):
            result = super().answer(context, question)
            result.evidence_ids = ["qualification:1"]
            return result

    path = tmp_path / "research.db"
    engine = InvalidFixture()
    client = TestClient(create_app(Store(path), engine))
    run = create(client)
    assert ask(client, run).status_code == 502
    engine.invalid_generation = True
    assert client.post("/events", json=load("demand")).status_code == 502
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM revisions").fetchone()[0] == 1
    assert ask(client, run, overrides={"lots": 300}).status_code == 200


def test_fractional_threshold_and_no_tax_shield(api):
    payload = load()
    payload["financial_inputs"].update(fixed_cost="12000001", full_tax_shield=False, lots=400)
    result = report(api, create(api, payload))
    outputs = result["model_outputs"]
    assert outputs["incremental_operating_profit"] == "-1"
    assert outputs["incremental_net_income"] == "-1.00"
    assert outputs["break_even_lots"] == outputs["min_profitable_lots"] == 401
    assert "最低不虧損量為 **401 批**" in result["markdown"]
    assert "虧損情境不認列稅盾" in result["markdown"]


@pytest.mark.parametrize(("section", "field", "value"), [
    (None, "as_of", "2025-01-15T18:00:00"),
    ("financial_inputs", "unit", "thousands"),
    ("financial_inputs", "lots", -1),
])
def test_invalid_event_data(api, section, field, value):
    payload = load()
    (payload[section] if section else payload)[field] = value
    assert api.post("/events", json=payload).status_code == 422


def test_live_request_uses_each_events_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_LLM_API_KEY", "test")
    monkeypatch.setenv("RESEARCH_LLM_MODEL", "test-model")
    requests = []

    def post(url, **kwargs):
        request = kwargs["json"]
        assert request["model"] == "test-model"
        context = json.loads(request["messages"][-1]["content"])
        requests.append(context)
        result = Fixture().hypotheses(context).model_dump_json()
        return httpx.Response(200, json={"choices": [{"message": {"content": result}}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", post)
    api = TestClient(create_app(Store(tmp_path / "research.db"), Live()))
    original = report(api, create(api))
    demand = load("demand")
    # Even a visible source cannot make another target's model applicable.
    demand["financial_inputs"] = {**load()["financial_inputs"], "evidence_id": "demand:2"}
    alternative_run = create(api, demand)
    alternative = report(api, alternative_run)
    assert requests[0]["target"] != requests[1]["target"]
    assert [context["horizon"] for context in requests] == ["2025Q1", "2025Q2"]
    assert [entry["id"] for entry in requests[1]["evidence"]] == ["demand:2"]
    assert "qualification:1" not in {entry["id"] for entry in requests[0]["evidence"]}
    assert "financials:1" not in {entry["id"] for entry in requests[0]["evidence"]}
    assert "model_outputs" not in requests[0]
    assert "lots" not in {claim["id"] for claim in requests[0]["claims"]}
    scenario_source = next(claim for claim in original["claims"] if claim.get("evidence_id") == "financials:1")
    assert scenario_source["kind"] == "assumption"
    assert "[`shutdown:1`](#evidence-1)" in original["markdown"]
    assert alternative["model_outputs"] is None
    assert "丙公司（SYN-C）" in alternative["markdown"]
    assert "下修 2025Q2" in alternative["markdown"]
    assert "SYN-A" not in alternative["markdown"]
    assert original["adapter"]["mode"] == "live"
    assert ask(api, alternative_run, overrides={"lots": 300}).status_code == 422


@pytest.mark.parametrize(("failure", "detail"), [
    ("missing", "RESEARCH_LLM_API_KEY"),
    ("parse", "無法解析"),
    ("timeout", "逾時"),
])
def test_live_errors(tmp_path, monkeypatch, failure, detail):
    monkeypatch.setenv("RESEARCH_LLM_MODEL", "test-model")
    if failure == "missing":
        monkeypatch.delenv("RESEARCH_LLM_API_KEY", raising=False)
    else:
        monkeypatch.setenv("RESEARCH_LLM_API_KEY", "test")

    def post(url, **kwargs):
        if failure == "timeout":
            raise httpx.ReadTimeout("simulated")
        return httpx.Response(200, json={"choices": [{"message": {"content": "bad json"}}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", post)
    api = TestClient(create_app(Store(tmp_path / "research.db"), Live()))
    response = api.post("/events", json=load())
    assert response.status_code == 502
    assert detail in response.json()["detail"]


def test_codex_cli_accepts_snapshot_and_validates_response(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_MODE", "codex")
    monkeypatch.setenv("RESEARCH_CODEX_MODEL", "test-gpt")
    requests = []

    def run(command, *, cwd, input, **options):
        assert command[:4] == ["codex", "-a", "never", "exec"]
        assert command[command.index("--sandbox") + 1] == "read-only"
        assert command[command.index("--model") + 1] == "test-gpt"
        assert options["timeout"] > 0
        _, serialized = input.split("\n\n", 1)
        data = json.loads(serialized)
        requests.append(data)
        schema = json.loads(Path(command[command.index("--output-schema") + 1]).read_text())
        if "hypotheses" in schema["properties"]:
            response = Fixture().hypotheses(data)
        else:
            response = Fixture().answer(data["report"], data["question"])
        output = Path(command[command.index("--output-last-message") + 1])
        assert output.parent == cwd
        output.write_text(response.model_dump_json(), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)
    api = TestClient(create_app(Store(tmp_path / "research.db"), configured_adapter()))
    created = create(api)
    assert report(api, created)["adapter"]["model"] == "test-gpt"
    assert ask(api, created).json()["gaps"]
    assert "qualification:1" not in {entry["id"] for entry in requests[0]["evidence"]}
    assert requests[1]["question"] == "客戶已認證乙嗎？"
