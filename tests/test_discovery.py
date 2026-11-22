import pytest

from research_app.adapters import AdapterError, Fixture
from research_app.api import apply_search_defaults
from research_app.schema import CompanyExposure, Event, PublicCheck
from research_app.store import Store


class SearchFixture(Fixture):
    def __init__(self):
        self.calls = []

    def search(self, schema, instruction, context):
        self.calls.append(context)
        if len(self.calls) == 1:
            sources = [
                ("https://issuer.example/results", "2024-10-15", "主要財報摘要。"),
                ("https://issuer.example/later", "2024-10-16", "不能出現在報告的未來值。"),
                ("https://issuer.example/unseen", "2024-10-15", "沒有搜尋紀錄。"),
                ("https://issuer.example.evil.test/fake", "2024-10-15", "非核准網域。"),
            ]
            observed = [sources[index][0] for index in (0, 1, 3)]
        elif len(self.calls) == 2:
            sources = [
                ("https://www.issuer.example/results/", "2024-10-15", "重複財報。"),
                ("https://ir.issuer.example/timing", "2024-10-15", "發布時點補充聲明。"),
            ]
            observed = [source[0] for source in sources]
        else:
            sources = [("https://issuer.example/supply", "2024-10-15", "北辰光學供應公司精密光學元件。")]
            observed = [source[0] for source in sources]
        return schema.model_validate({
            "sources": [{"url": url, "published_on": day, "summary": summary} for url, day, summary in sources],
            "gaps": ["確認發布時點"],
        }), [{"results": [{"url": url} for url in observed]}]

    def hypotheses(self, context):
        result = super().hypotheses(context)
        result.assessment.public_checks.append(PublicCheck(
            metric="公開季報新增訂單", source_to_watch="公司季報", window="下次財報",
            impact_on_thesis="接單回升提高上行情境可信度。", evidence_ids=[context["evidence"][0]["id"]],
        ))
        supply = next((item for item in context["evidence"] if "北辰光學" in item["quote"]), None)
        if supply:
            result.assessment.supply_chain.append(CompanyExposure(
                company="北辰光學", role="upstream", status="disclosed_relationship",
                product_scope="精密光學元件", relationship="北辰光學供應公司精密光學元件。",
                transmission="設備產能變動可能影響元件採購。",
                materiality="缺少客戶收入占比。", public_check="查閱下一次公司財報。",
                gap="未公布調整後的採購量。", evidence_ids=[supply["id"]],
            ))
        return result


def event():
    return Event.model_validate({
        "event_text": "公司財報", "as_of": "2024-10-15T23:59:59Z",
        "search_mode": "historical_replay", "search_domains": ["issuer.example"],
    })


def test_search_rounds_filter_and_build_supply_chain_without_question(tmp_path):
    engine = SearchFixture()
    store = Store(tmp_path / "test.sqlite3")
    uploaded = event()
    run = store.create(uploaded, engine)
    report = store.revision(run["report_id"], 1)
    assert store.create(uploaded, engine) == run
    assert len(engine.calls) == 3
    assert engine.calls[1]["prior_gaps"] == ["確認發布時點"]
    assert engine.calls[1]["accepted_urls"] == ["https://issuer.example/results"]
    assert len(report["evidence"]) == 3
    assert engine.calls[2]["previous_public_summaries"] == ["主要財報摘要。", "發布時點補充聲明。"]
    assert report["discovery"]["rounds"][2]["stage"] == "supply_chain"
    assert report["discovery"]["rounds"][2]["accepted"] == 1
    assert report["discovery"]["rounds"][0]["after_cutoff"] == 1
    assert report["discovery"]["rounds"][0]["unverified_url"] == 2
    assert report["discovery"]["rounds"][1]["duplicate"] == 1
    assert "來源摘要" in report["markdown"]
    assert "原文　主要財報摘要" not in report["markdown"]
    assert "未來值" not in report["markdown"]
    assert "公開查核點" in report["markdown"]
    assert report["assessment"]["supply_chain"][0]["company"] == "北辰光學"
    assert "上游關鍵供應商" in report["markdown"]
    assert "財務重要性" in report["markdown"]


@pytest.mark.parametrize(("field", "value"), [
    ("evidence_ids", ["absent:1"]), ("company", "未出現於來源的公司"),
])
def test_supply_chain_requires_visible_evidence_naming_company(tmp_path, field, value):
    class BadExposure(SearchFixture):
        def hypotheses(self, context):
            result = super().hypotheses(context)
            setattr(result.assessment.supply_chain[0], field, value)
            return result

    with pytest.raises(AdapterError, match="供應鏈公司"):
        Store(tmp_path / "test.sqlite3").create(event(), BadExposure())


def test_server_can_enable_search_without_event_search_options(monkeypatch):
    monkeypatch.setenv("RESEARCH_SEARCH_MODE", "historical_replay")
    monkeypatch.setenv("RESEARCH_SEARCH_DOMAINS", "issuer.example, sec.gov")
    payload = {"event_text": "公司財報", "as_of": "2024-10-15T23:59:59Z"}
    configured = apply_search_defaults(Event.model_validate(payload))
    assert configured.search_mode == "historical_replay"
    assert configured.search_domains == ["issuer.example", "sec.gov"]
    assert apply_search_defaults(Event.model_validate({**payload, "search_mode": "off"})).search_mode == "off"


def test_public_check_rejects_unavailable_evidence(tmp_path):
    class BadReference(SearchFixture):
        def hypotheses(self, context):
            result = super().hypotheses(context)
            result.assessment.public_checks[0].evidence_ids = ["absent:1"]
            return result

    store = Store(tmp_path / "test.sqlite3")
    with pytest.raises(AdapterError, match="公開查核點"):
        store.create(event(), BadReference())
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 0


def test_search_mode_requires_qualified_adapter(tmp_path):
    store = Store(tmp_path / "test.sqlite3")
    with pytest.raises(AdapterError, match="codex"):
        store.create(event(), Fixture())


def test_live_search_does_not_backdate_freshly_obtained_documents():
    from research_app.discovery import collect

    documents, audit = collect(event().model_copy(update={"search_mode": "live"}), SearchFixture())
    assert documents == []
    assert sum(round_["after_cutoff"] for round_ in audit["rounds"]) == 5
