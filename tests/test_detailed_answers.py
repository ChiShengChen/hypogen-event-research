import json
from pathlib import Path

import pytest

from research_app.adapters import AdapterError, Fixture, ModelAdapter
from research_app.research import build_context
from research_app.schema import DetailedAnswer, Event, Question
from research_app.store import Store

EXAMPLE = Path(__file__).resolve().parents[1] / "research_app" / "examples" / "asml-q3.json"


class ScriptedAdapter(ModelAdapter):
    identity = {"mode": "fixture", "version": "detailed-test"}

    def __init__(self):
        self.calls = []
        self.calculation_ids = ["asml-bookings-qoq", "asml-euv-share"]

    def hypotheses(self, context):
        return Fixture().hypotheses(context)

    def _generate(self, schema, instruction, data):
        assert schema is DetailedAnswer
        self.calls.append(data)
        if "missing_requirements" in data:
            assert data["missing_requirements"] == ["交付與驗收"]
            return schema(
                answer="要查實際整機交付及客戶驗收。", evidence_ids=["high-na-order:order"], gaps=[],
                coverage=[{"requirement": "交付與驗收", "status": "answered"}], calculation_ids=[],
            )
        return schema(
            answer="先確認採購，再查實際里程碑。", evidence_ids=["high-na-order:order"], gaps=[],
            coverage=[{"requirement": "財報比率", "status": "answered"},
                      {"requirement": "交付與驗收", "status": "missing"}],
            calculation_ids=self.calculation_ids,
        )


def load_event():
    return Event.model_validate_json(EXAMPLE.read_text(encoding="utf-8"))


def test_answer_reads_first_draft_and_appends_evidence_bound_calculations(tmp_path):
    store = Store(tmp_path / "test.sqlite3")
    engine = ScriptedAdapter()
    report_id = store.create(load_event(), engine)["report_id"]
    parent = store.revision(report_id, 1)
    answer = store.question(report_id, Question(parent_revision=1, question="比率和驗收應如何核對？"), engine)
    assert engine.calls[0]["stored_research"]["trade_opportunities"] == parent["assessment"]["trade_opportunities"]
    assert engine.calls[0]["stored_hypotheses"] == parent["hypotheses"]
    assert len(engine.calls) == 2
    assert [part["status"] for part in answer["coverage"]] == ["answered", "answered"]
    assert "整機交付及客戶驗收" in answer["answer"]
    assert "(2,633 − 5,567) ÷ 5,567 × 100% ≈ -52.70%" in answer["answer"]
    assert "1,400 ÷ 2,633 × 100% ≈ 53.17%（來源金額為約數）" in answer["answer"]
    assert answer["evidence_ids"] == ["high-na-order:order", "asml-q3:actual"]


def test_disclosed_calculations_skip_invalid_or_invisible_operands():
    event = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    row = event["reported_calculations"][0]
    alternate = json.loads(json.dumps(row))
    alternate["id"] = "future"
    alternate["baseline"]["evidence_id"] = "asml-q4:actual"
    mismatch = json.loads(json.dumps(row))
    mismatch["id"] = "mismatch"
    mismatch["baseline"]["unit"] = "百萬美元"
    zero = json.loads(json.dumps(row))
    zero["id"] = "zero"
    zero["baseline"]["value"] = "0"
    event["reported_calculations"] += [alternate, mismatch, zero]
    calculations = build_context(Event.model_validate(event))["disclosed_calculations"]
    assert [item["id"] for item in calculations] == ["asml-bookings-qoq", "asml-euv-share"]


def test_answer_cannot_attach_unknown_calculation(tmp_path):
    store = Store(tmp_path / "test.sqlite3")
    engine = ScriptedAdapter()
    engine.calculation_ids = ["missing"]
    report_id = store.create(load_event(), engine)["report_id"]
    with pytest.raises(AdapterError, match="不可見的計算資料"):
        store.question(report_id, Question(parent_revision=1, question="給我比率"), engine)
