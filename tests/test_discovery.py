import pytest

from research_app.adapters import AdapterError, Fixture
from research_app.api import apply_search_defaults
from research_app.schema import Answer, CompanyExposure, Event, PublicCheck, Question
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


class QuestionSearchFixture(SearchFixture):
    match = "https://ir.issuer.example/calendar"
    fail = False
    answer_stays_unresolved = False
    date = "2024-09-30"

    def search(self, schema, instruction, context):
        if "question" not in context:
            return super().search(schema, instruction, context)
        self.calls.append(context)
        if self.fail:
            raise AdapterError("model timeout")
        sources = [
            (self.match, self.date, "公司財務行事曆原定 10 月 16 日發布。"),
            ("https://issuer.example/future", "2024-10-17", "截止後資料。"),
            ("https://issuer.example/results", "2024-10-15", "已有來源。"),
        ]
        return schema.model_validate({
            "sources": [{"url": url, "published_on": day, "summary": summary} for url, day, summary in sources],
            "gaps": [],
        }), [{"results": [{"url": url} for url, _, _ in sources]}]

    def answer(self, context, question):
        if question == "問已知結果":
            return Answer(answer="已確認", evidence_ids=[context["evidence"][0]["id"]], gaps=[])
        for item in context["evidence"]:
            if item["source"] == self.match and not self.answer_stays_unresolved:
                return Answer(answer="原定 10 月 16 日", evidence_ids=[item["id"]], gaps=[])
        return Answer(answer="原定日待查", evidence_ids=[], gaps=["缺少公司財務行事曆"])


def test_question_search_saves_new_answer_in_immutable_evidence_child(tmp_path):
    path = tmp_path / "test.sqlite3"
    store = Store(path)
    engine = QuestionSearchFixture()
    run = store.create(event(), engine)
    ref = run["report_id"]
    original = store.revision(ref, 1)
    question = Question(parent_revision=1, question="哪一天原定發布？")

    result = store.question(ref, question, engine)
    assert result["answer"] == "原定 10 月 16 日"
    assert result["evidence_search"]["status"] == "published"
    assert result["evidence_search"]["rounds"][0]["after_cutoff"] == 1
    assert result["evidence_search"]["rounds"][0]["duplicate"] == 1
    assert engine.calls[-1]["as_of"] == "2024-10-15T23:59:59+00:00"
    assert engine.calls[-1]["unanswered_gaps"] == ["缺少公司財務行事曆"]
    assert len(engine.calls) == 4

    reopened = Store(path)
    assert reopened.revision(ref, 1) == original
    child = reopened.revision(ref, result["child_revision"])
    assert child["parent_revision"] == 1
    assert child["as_of"] == original["as_of"]
    assert child["assessment"] == original["assessment"]
    assert child["evidence_followups"][0]["answer"]["evidence_ids"] == result["evidence_ids"]
    assert "截止後資料" not in child["markdown"]
    assert "原定 10 月 16 日" in child["markdown"]
    assert reopened.question(ref, question.model_copy(update={"parent_revision": result["child_revision"]}), engine)[
        "answer"
    ] == result["answer"]
    assert len(engine.calls) == 4


def test_questions_skip_search_when_answer_is_known_or_disabled(tmp_path):
    store = Store(tmp_path / "test.sqlite3")
    engine = QuestionSearchFixture()
    ref = store.create(event(), engine)["report_id"]
    assert store.question(ref, Question(parent_revision=1, question="問已知結果"), engine)["gaps"] == []
    disabled = Question(parent_revision=1, question="哪一天原定發布？", evidence_search="off")
    assert store.question(ref, disabled, engine)["answer"] == "原定日待查"
    assert len(engine.calls) == 3


@pytest.mark.parametrize(("field", "value", "status"), [
    ("fail", True, "failed"),
    ("date", "2024-10-16", "no_new_sources"),
    ("answer_stays_unresolved", True, "unresolved"),
])
def test_unsuccessful_question_search_returns_original_without_revision(tmp_path, field, value, status):
    store = Store(tmp_path / "test.sqlite3")
    engine = QuestionSearchFixture()
    ref = store.create(event(), engine)["report_id"]
    setattr(engine, field, value)
    result = store.question(ref, Question(parent_revision=1, question="哪一天原定發布？"), engine)
    assert result["answer"] == "原定日待查"
    assert result["evidence_search"]["status"] == status
    assert "child_revision" not in result
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM revisions").fetchone()[0] == 1
