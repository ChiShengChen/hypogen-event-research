import pytest

from research_app.adapters import AdapterError, Fixture
from research_app.schema import CompanyExposure, Event, Question, SupplyEdge, TradeOpportunity
from research_app.store import Store


class OpportunityFixture(Fixture):
    exposure_status = "disclosed_relationship"
    symbol = "NOPT"

    def hypotheses(self, context):
        generated = super().hypotheses(context)
        generated.assessment.supply_chain.append(CompanyExposure(
            company="北辰光學", role="upstream", status=self.exposure_status, product_scope="光學件",
            relationship="北辰光學供應辰星設備的光學件。",
            transmission="新增設備出貨若帶動採購，有機會提高供應商營收。",
            materiality="未公布供貨數量與客戶營收占比。", public_check="查看後續季報。",
            gap="仍需確認實際新增採購。", evidence_ids=["supply:1"],
        ))
        generated.assessment.trade_opportunities.append(TradeOpportunity(
            company="北辰光學", direction="long_if",
            earnings_path="已確認的光學件新增交付，可能提高營收。",
            catalyst="北辰光學下一份季報。", trigger="公司確認新增訂單並提高同產品交付展望。",
            invalidation="公司確認原定採購沒有增加。",
            evidence_gap="缺少新增訂單大小與可比較的市場預期。",
            ticker=self.symbol, listing_evidence_id="supply:1", evidence_ids=["supply:1"],
        ))
        return generated


def make_event(event_text):
    return Event.model_validate({
        "event_text": event_text,
        "research_target": "辰星設備",
        "as_of": "2025-01-15T18:00:00+08:00",
        "documents": [{
            "id": "supply", "source": "虛構公司文件", "kind": "disclosure", "synthetic": True,
            "published_at": "2025-01-15T09:00:00+08:00",
            "obtained_at": "2025-01-15T09:00:00+08:00",
            "paragraphs": {"1": "北辰光學（NOPT）向辰星設備供應光學件。"},
        }],
    })


def test_opportunity_in_first_report_for_unmentioned_supplier(tmp_path):
    store = Store(tmp_path / "research.sqlite3")
    run = store.create(make_event("辰星設備提高交付展望。"), OpportunityFixture())
    report = store.revision(run["report_id"], 1)
    ideas = report["assessment"]["trade_opportunities"]
    assert [(item["company"], item["direction"], item["ticker"]) for item in ideas] == [
        ("北辰光學", "long_if", "NOPT"),
    ]
    assert "## 延伸交易機會" in report["markdown"]
    assert "觸發條件" in report["markdown"]
    assert "失效條件" in report["markdown"]


def test_opportunity_omits_company_already_named_in_intake(tmp_path):
    store = Store(tmp_path / "research.sqlite3")
    run = store.create(make_event("辰星設備與北辰光學公布交付展望。"), OpportunityFixture())
    assert store.revision(run["report_id"], 1)["assessment"]["trade_opportunities"] == []


def test_uncovered_counterparty_from_visible_edge_becomes_watch(tmp_path):
    event = make_event("辰星設備發布財報。")
    other_doc = event.documents[0].model_copy(update={
        "id": "mechanics", "paragraphs": {"1": "南方機械向辰星設備供應定位零件。"},
    })
    event = event.model_copy(update={
        "documents": [*event.documents, other_doc],
        "supply_edges": [SupplyEdge(supplier="南方機械", customer="辰星設備", product="定位零件", evidence_id="mechanics:1")],
    })
    store = Store(tmp_path / "research.sqlite3")
    engine = OpportunityFixture()
    ref = store.create(event, engine)["report_id"]
    assessment = store.revision(ref, 1)["assessment"]
    assert [(item["company"], item["direction"]) for item in assessment["trade_opportunities"]] == [
        ("北辰光學", "long_if"), ("南方機械", "watch"),
    ]
    answer = store.question(ref, Question(parent_revision=1, question="哪裡有未確認的資訊？"), engine)
    assert answer["trade_opportunities"] == assessment["trade_opportunities"]
    assert answer["trade_opportunities_gap"] is None


def test_opportunity_section_states_missing_evidence_even_without_sources(tmp_path):
    store = Store(tmp_path / "research.sqlite3")
    run = store.create(Event(event_text="只有事件標題", as_of="2025-01-15T00:00:00Z"), Fixture())
    report = store.revision(run["report_id"], 1)
    assert report["assessment"]["trade_opportunities"] == []
    assert "產品關係證據" in report["assessment"]["trade_opportunities_gap"]
    assert "## 延伸交易機會" in report["markdown"]


@pytest.mark.parametrize(("field", "value", "message"), [
    ("exposure_status", "comparable_only", "只能列為觀察"),
    ("symbol", "MADEUP", "交易代號"),
])
def test_opportunity_rejects_unsupported_direction_or_symbol(tmp_path, field, value, message):
    engine = OpportunityFixture()
    setattr(engine, field, value)
    with pytest.raises(AdapterError, match=message):
        Store(tmp_path / "research.sqlite3").create(make_event("辰星設備公布財報。"), engine)
