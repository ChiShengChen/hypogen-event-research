import json
from pathlib import Path

from fastapi.testclient import TestClient

from benchmarks.hypothesis_cases import load_cases
from benchmarks.v9_equal import frozen_cases
from research_app.adapters import Fixture, LinkedCodex, RankedCodex, configured_adapter
from research_app.api import create_app
from research_app.business_linkage import LinkedAnswer, LinkedHypotheses
from research_app.discovery import collect
from research_app.schema import DriverDraft, Event
from research_app.store import Store


def ford_linkage():
    return {
        "linked_stance": "bull", "scope": "internal",
        "origin_business": "純電三排座 SUV", "origin_evidence_ids": ["ford-ev-8k:charges"],
        "affected_company": "Ford", "affected_business": "商用廂型車",
        "affected_evidence_ids": ["ford-ev-strategy:plans"],
        "mechanism": "取消三排座 SUV 可釋放工程與模具資本，但只有在資源可轉用時才有利廂型車。",
        "baseline": "依原定 2026 年投產時間與既定投入資源比較。",
        "condition": "需核對被取消專案的資金或工程人力實際移入商用廂型車。",
        "financial_effect": "若確實移轉，廂型車投產前現金支出結構改變，規模未披露。",
        "alternative_explanation": "廂型車排程維持可能來自原本已編列的預算。查專案資源移轉的揭露。",
        "metric": "廂型車投產排程與專案資源調整", "observation_period": "2025 年上半年",
        "public_source": "Ford 電動車策略更新", "deadline": "2025-10-15",
        "prediction": "在觀察期間披露資源移轉，且廂型車仍按原訂窗口推進。",
        "invalidation": "同一更新確認騰出的資源撤回，而廂型車由原預算維持。",
    }


class ScriptedRankedCodex(RankedCodex):
    def _generate(self, response_schema, instruction, context):
        assert "second-order business hypotheses" in instruction
        assert "primary financially consequential transmission first" in instruction
        draft = Fixture().hypotheses(context).model_dump()
        linkage = ford_linkage() | {"ranking_reason": "發布資料明列廂型車排程，先查實際轉入的工程預算。"}
        return response_schema(**draft, business_linkages=[
            linkage,
            linkage | {"affected_evidence_ids": ["missing:reference"]},
            linkage | {"deadline": "2025-11-01"},
        ], business_linkage_gap="廂型車的實際增量預算仍待查。")


def test_linkages_publish_by_default_and_filter_unsupported_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_MODE", "codex")
    assert configured_adapter().identity["prompt_version"] == 12
    _, event = load_cases(holdout=True)["V-04"]
    store = Store(tmp_path / "reports.sqlite3")
    previous = store.create(event, Fixture())
    with TestClient(create_app(store, ScriptedRankedCodex())) as client:
        response = client.post("/events", json=event.model_dump(mode="json"))
        assert response.status_code == 200
        report_id = response.json()["report_id"]
        assert report_id != previous["report_id"]
        report = client.get(f"/reports/{report_id}/revisions/1").json()
        assert report["business_linkages"] == [
            ford_linkage() | {"ranking_reason": "發布資料明列廂型車排程，先查實際轉入的工程預算。"}
        ]
        assert "2 條候選未通過" in report["business_linkage_gap"]
        assert "連動業務假說" in report["markdown"]
        assert "排序理由" in report["markdown"]
        assert "商用廂型車" in report["markdown"]
        assert "ford-ev-strategy:plans" in report["markdown"]
        prior = client.get(f"/reports/{previous['report_id']}/revisions/1").json()
        assert "business_linkages" not in prior


def test_discovery_looks_for_adjacent_business_with_only_visible_inputs():
    event = Event.model_validate_json(Path("research_app/examples/asml-q3.json").read_text()).model_copy(
        update={"search_mode": "historical_replay", "search_domains": ["sec.gov"]},
    )
    original = event.documents[0]

    class SearchRecorder:
        supports_business_linkages = True

        def __init__(self):
            self.calls = []

        def search(self, response_schema, instruction, context):
            self.calls.append((instruction, context))
            if len(self.calls) == 2:
                supplement = {"url": original.source, "published_on": original.published_at.date(),
                              "summary": "補查到同一公告內的另一段。"}
                return response_schema(sources=[supplement, supplement], gaps=[]), [
                    {"results": [{"url": original.source}]},
                ]
            return response_schema(sources=[], gaps=[]), []

    adapter = SearchRecorder()
    found, log = collect(event, adapter)
    assert len(adapter.calls) == 3
    assert len(found) == 1 and found[0].source == original.source and found[0].id != original.id
    assert log["rounds"][1]["duplicate"] == 1
    follow_up, context = adapter.calls[1]
    assert "another named business" in follow_up
    assert any("High-NA" in source for source in context["previous_public_summaries"])
    assert all("7,088" not in source for source in context["previous_public_summaries"])


def test_frozen_v9_requests_do_not_change():
    _, requests = frozen_cases()
    prior = json.loads(Path("docs/v9-equal-probe/requests.json").read_text())
    assert requests == prior


class FollowupCodex(LinkedCodex):
    def __init__(self):
        super().__init__()
        self.answer_payloads = []

    def _generate(self, response_schema, instruction, context):
        if response_schema is not LinkedAnswer:
            draft = Fixture().hypotheses(context).model_dump()
            return response_schema(**draft, business_linkages=[ford_linkage()], business_linkage_gap=None)
        self.answer_payloads.append(context)
        refs = context.get("new_evidence_ids", [])
        linkage = ford_linkage()
        if refs:
            linkage.update(affected_evidence_ids=refs, condition="已補到點時公告，實際資源與金額仍待確認。")
        return response_schema(
            answer="依公告查核商用廂型車的資源與進度。",
            evidence_ids=refs or ["ford-ev-strategy:plans"],
            gaps=[] if refs else ["仍需另一份資源配置公告"],
            coverage=[{"requirement": "商用車資源配置", "status": "answered" if refs else "unavailable"}],
            calculation_ids=[], business_linkages=[linkage], business_linkage_gap=None,
        )

    def search(self, response_schema, instruction, context):
        if "question" not in context:
            return response_schema(sources=[], gaps=[]), []
        assert "transfer, affected operation, public metric" in instruction
        url = "https://issuer.example/van-update"
        return response_schema(sources=[{
            "url": url, "published_on": "2024-08-21", "summary": "Ford 的商用廂型車進度仍列於專案更新。",
        }], gaps=[]), [{"results": [{"url": url}]}]


def test_question_and_search_revision_use_existing_and_new_linkages(tmp_path):
    _, event = load_cases(holdout=True)["V-04"]
    payload = event.model_dump(mode="json") | {"search_mode": "historical_replay", "search_domains": ["issuer.example"]}
    engine = FollowupCodex()
    with TestClient(create_app(Store(tmp_path / "reports.sqlite3"), engine)) as client:
        created = client.post("/events", json=payload).json()
        root = f"/reports/{created['report_id']}"
        parent = client.get(f"{root}/revisions/1").json()
        payload = {"parent_revision": 1, "question": "商用廂型車的配置如何驗證？"}
        plain = client.post(f"{root}/questions", json=payload | {"evidence_search": "off"}).json()
        assert plain["business_linkages"] == parent["business_linkages"]
        assert "child_revision" not in plain
        result = client.post(f"{root}/questions", json=payload).json()
        assert result["evidence_search"]["status"] == "published"
        assert engine.answer_payloads[0]["stored_research"]["business_linkages"] == parent["business_linkages"]
        new_ref, = engine.answer_payloads[-1]["new_evidence_ids"]
        child = client.get(f"{root}/revisions/{result['child_revision']}").json()
        assert child["business_linkages"] == result["business_linkages"]
        assert child["business_linkages"][0]["affected_evidence_ids"] == [new_ref]
        assert f"fact:{new_ref}" in {row["id"] for row in child["claims"]}
        assert new_ref in child["markdown"]
        assert client.get(f"{root}/revisions/1").json() == parent


def test_question_can_add_linkage_to_old_report_and_scenario_retains_it(tmp_path):
    _, event = load_cases(holdout=True)["V-04"]
    sample = json.loads(Path("research_app/fixtures/shutdown.json").read_text())
    inputs = sample["financial_inputs"] | {
        "target": event.research_target, "quarter": event.research_horizon, "evidence_id": "ford-ev-8k:charges",
    }
    event = Event.model_validate(event.model_dump() | {"financial_inputs": inputs})
    store = Store(tmp_path / "reports.sqlite3")
    older = store.create(event, Fixture())
    with TestClient(create_app(store, FollowupCodex())) as client:
        root = f"/reports/{older['report_id']}"
        reply = client.post(f"{root}/questions", json={
            "parent_revision": 1, "question": "廂型車會受到什麼影響？", "evidence_search": "off",
        }).json()
        assert reply["business_linkages"] == [ford_linkage()]
        child = client.get(f"{root}/revisions/{reply['child_revision']}").json()
        assert child["revision_kind"] == "linkage_follow_up"
        assert "業務連動追問" in child["markdown"]
        result = client.post(f"{root}/questions", json={
            "parent_revision": child["revision"], "question": "重算 300 批", "overrides": {"lots": 300},
        }).json()
        assert result["business_linkages"] == reply["business_linkages"]
        report = client.get(f"{root}/revisions/{result['child_revision']}").json()
        assert report["business_linkages"] == child["business_linkages"]
        assert report["model_inputs"]["lots"] == 300
        assert "business_linkages" not in client.get(f"{root}/revisions/1").json()


def test_linkage_flows_through_earnings_draft_branch_consensus_and_review(tmp_path):
    row = ford_linkage() | {
        "origin_business": "EUV 訂單", "origin_evidence_ids": ["asml-q3:actual"],
        "affected_company": "ASML", "affected_business": "Installed Base Management",
        "affected_evidence_ids": ["asml-q1-2024:history"],
        "mechanism": "新設備採購延後時可能繼續使用舊機，延長保養需求。",
        "deadline": "2025-04-30",
    }

    class EarningsCodex(LinkedCodex):
        def _generate(self, response_schema, instruction, context):
            if response_schema is LinkedHypotheses:
                draft = Fixture().hypotheses(context).model_dump()
                return response_schema(**draft, business_linkages=[row], business_linkage_gap=None)
            assert response_schema is DriverDraft
            assert context["business_linkages"] == [row]
            assert "counterparty's results cannot be booked" in instruction
            return response_schema(drivers=[
                {"period_end": quarter["period_end"], "scenario": name, "segments": [],
                 "gross_margin_delta": "0", "opex_delta": "0", "rationale": "保留合併、分部及時點口徑",
                 "evidence_ids": ["asml-q3:guidance"]}
                for quarter in context["baseline"]["quarters"] for name in ("bear", "base", "bull")
            ])

    payload = json.loads(Path("research_app/examples/asml-earnings.json").read_text())
    payload["earnings_plan"].update(drivers=[], generate_drivers=True)
    with TestClient(create_app(Store(tmp_path / "earnings.sqlite3"), EarningsCodex())) as client:
        create = client.post("/events", json=payload)
        assert create.status_code == 200, create.text
        root = f"/reports/{create.json()['report_id']}"
        parent = client.get(f"{root}/revisions/1").json()
        assert parent["business_linkages"] == [row]
        model = parent["earnings"]["quarters"][0]["scenarios"]["bull"]["revised"]
        driver = {"id": "analyst-margin", "hypothesis_stance": "bull", "scenario": "bull",
                  "hypothesis_summary": "保養續用", "assumption": "ERP 情境調整毛利率",
                  "evidence_ids": ["asml-q3:actual", "asml-q1-2024:history"], "public_check": "查保養業務",
                  "falsifier": "保養需求未增", "impacts": [
                      {"period_end": parent["earnings"]["quarters"][0]["period_end"],
                       "metric": "gross_margin", "delta": "0.01"},
                  ]}
        response = client.post(f"{root}/earnings/branches", json={"parent_revision": 1, "driver_links": [driver]})
        assert response.status_code == 200, response.text
        child = response.json()
        assert child["business_linkages"] == [row]
        assert child["earnings"]["driver_audit"][0]["related_business_linkages"][0]["affected_company"] == "ASML"
        assert child["earnings"]["quarters"][0]["scenarios"]["bull"]["revised"]["revenue"] == model["revenue"]
        assert "共用連動證據" in child["markdown"]
        status = client.get(f"{root}/revisions/{child['revision']}/earnings").json()
        assert status["business_linkages"] == [row]
        consensus = client.post(f"{root}/earnings/consensus", json={
            "parent_revision": child["revision"], "provider": "測試快照", "target": "ASML",
            "source_url": "https://consensus.example/asml", "captured_at": "2024-10-14T20:00:00Z",
            "purpose": "historical_replay",
            "csv_text": "metric,period_end,duration,scope,basis,currency,unit,low,high,available_at\n"
                        "revenue,2024-09-30,quarter,consolidated,US_GAAP,EUR,currency_millions,7000,7200,2024-10-14T16:00:00Z\n",
        })
        assert consensus.status_code == 200, consensus.text
        assert consensus.json()["business_linkages"] == [row]
