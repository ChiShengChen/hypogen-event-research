from pathlib import Path

from fastapi.testclient import TestClient

from research_app.adapters import Fixture, ScenarioCodex
from research_app.api import create_app
from research_app.schema import Event
from research_app.store import Store


class ScriptedScenarioCodex(ScenarioCodex):
    def _generate(self, schema, instruction, data):
        if schema is not self.hypothesis_schema:
            return schema(answer="公開證據仍待確認。", evidence_ids=["asml-q3:actual"],
                          gaps=[], coverage=[{"requirement": "情境推翻條件", "status": "answered"}],
                          business_linkages=[], business_linkage_gap=None, calculation_ids=[])
        assert "stance_cases" in instruction
        base = Fixture().hypotheses(data).model_dump()
        case = {
            "title": "先進客戶恢復設備採購",
            "driver": "先進邏輯客戶完成設備驗收",
            "conditions": ["客戶公開確認先進邏輯產線驗收"],
            "mechanism": "設備驗收讓訂單轉為收入",
            "financial_metric": "EUV 設備營收", "direction": "up",
            "scale_basis_or_gap": "設備台數及價格待查", "baseline": "客戶維持目前推遲的驗收時程",
            "public_metric": "EUV 銷售台數", "public_source": "ASML 季報",
            "observation_period": "2025 上半年", "review_by": "2025-10-22",
            "prediction": "驗收批次增加後，同口徑 EUV 銷售台數較去年同期增加",
            "falsifier": "驗收批次增加後，同口徑 EUV 銷售台數較去年同期持平或減少",
            "evidence_ids": ["asml-q3:guidance"],
        }
        second = case | {"title": "光學供應瓶頸緩解", "mechanism": "光學元件擴產提高可交付設備數",
                         "evidence_ids": ["asml-annual:supplier"]}
        return schema(**base, business_linkages=[], business_linkage_gap=None, stance_cases=[
            {"stance": "bull", "cases": [case, second], "evidence_gap": None},
            {"stance": "base", "cases": [case | {"mechanism": "延期", "evidence_ids": ["asml-q4:actual"]}],
             "evidence_gap": None},
            {"stance": "bear", "cases": [case | {"mechanism": "設備驗收延遲", "review_by": "2026-01-01"}],
             "evidence_gap": None},
            {"stance": "wait", "cases": [], "evidence_gap": "客戶分批驗收的台數仍待查。"},
        ])


def test_scenarios_available_in_normal_report_and_followup(tmp_path):
    event = Event.model_validate_json(Path("research_app/examples/asml-q3.json").read_text())
    event = event.model_copy(update={"research_horizon": "2025-12-31"})
    with TestClient(create_app(Store(tmp_path / "report.sqlite"), ScriptedScenarioCodex())) as client:
        result = client.post("/events", json=event.model_dump(mode="json"))
        assert result.status_code == 200, result.text
        report_id = result.json()["report_id"]
        report = client.get(f"/reports/{report_id}/revisions/1").json()
        groups = {group["stance"]: group for group in report["stance_cases"]}
        assert list(groups) == ["bull", "base", "bear", "wait"]
        assert len(groups["bull"]["cases"]) == 2
        assert not groups["base"]["cases"] and groups["base"]["evidence_gap"]
        assert not groups["bear"]["cases"] and groups["bear"]["evidence_gap"]
        assert groups["wait"]["evidence_gap"] == "客戶分批驗收的台數仍待查。"
        assert "光學供應瓶頸緩解" in report["markdown"]
        assert "asml-annual:supplier" in report["markdown"]
        answer = client.post(f"/reports/{report_id}/questions", json={
            "question": "什麼能推翻現在的情境？", "parent_revision": 1, "evidence_search": "off"})
        assert answer.status_code == 200, answer.text
        assert answer.json()["stance_cases"] == report["stance_cases"]
