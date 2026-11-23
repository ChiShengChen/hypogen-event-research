from datetime import date
from decimal import Decimal

import pytest

from research_app.earnings import EarningsError, calculate_earnings
from research_app.research import document_evidence
from research_app.schema import Document, EarningsPlan, RevenueBridge


AS_OF = "2025-05-09T18:00:00Z"
BASELINE_AT = "2025-05-08T18:00:00Z"
FAR = "2025-09-30"


def evidence(doc_id, available_at=AS_OF, source=None):
    return document_evidence(Document(
        id=doc_id, source=source or f"https://company.example/{doc_id}",
        kind="disclosure", published_at=available_at, obtained_at=available_at,
        paragraphs={"data": f"測試披露 {doc_id}。"},
    ))


def residual_item(**changes):
    return {
        "id": "new-volume", "segment": "consolidated", "driver": "volume", "period_end": FAR,
        "incremental_revenue": "10", "incremental_gross_margin": "0.7", "incremental_opex": "1",
        "basis_incremental_to_incumbent": True, "source_family": "named-source", "mechanism": "incremental ship volume",
        "available_at": AS_OF, "evidence_ids": ["volume:data"], "rationale": "目標季度新增出貨量",
        "public_check": "核對公告的出貨數量", "falsifier": "新增出貨未於該季度認列", **changes,
    }


def plan_data(method="residual_a", *, inputs=()):
    history = []
    for year in (2022, 2023, 2024):
        for month, day, fquarter in ((3, 31, 1), (6, 30, 2), (9, 30, 3), (12, 31, 4)):
            history.append({"period_end": date(year, month, day), "fiscal_quarter": fquarter,
                            "value": "100", "available_at": AS_OF, "evidence_ids": ["history:data"],
                            "method": "可比歷史單季營收"})
    history.append({"period_end": "2025-03-31", "fiscal_quarter": 1, "value": "160",
                    "available_at": AS_OF, "evidence_ids": ["latest:data"], "method": "最近公告單季營收"})
    quarter = {"available_at": BASELINE_AT, "segment_revenue": {"consolidated": "100"},
               "gross_margin": "0.4", "opex": "30", "tax_rate": "0.2", "diluted_shares": "100",
               "evidence_ids": ["baseline:data"], "method": "既有預測"}
    driver = {"scenario": "base", "segment_revenue_delta": {}, "shipment_changes": {},
              "gross_margin_delta": "0", "opex_delta": "0", "rationale": "基準保留",
              "evidence_ids": ["latest:data"]}
    return {
        "event_at": AS_OF, "currency": "USD", "basis": "US_GAAP",
        "quarters": [dict(quarter, period_end=p) for p in ("2025-06-30", FAR)],
        "drivers": [dict(driver, period_end=p) for p in ("2025-06-30", FAR)],
        "revenue_bridge": {"period_end": FAR, "currency": "USD", "basis": "US_GAAP",
                           "near_fiscal_quarter": 2, "far_fiscal_quarter": 3, "method": method,
                           "history": history, "residual_inputs": inputs},
    }


def inputs_evidence():
    return [*evidence("baseline", BASELINE_AT), *evidence("history"), *evidence("latest"), *evidence("volume")]


def run_plan(data, visible=None, **kwargs):
    ready = EarningsPlan.model_validate(data)
    return calculate_earnings(ready, ready.event_at, inputs_evidence() if visible is None else visible, **kwargs)


def audit(result):
    return result["revenue_bridge"]["residual"]


def test_residual_a_has_no_hard_guidance_gate_and_audits_ablation():
    result = run_plan(plan_data())
    row = audit(result)
    assert row["status"] == "applied"
    assert {key: Decimal(row[key]) for key in ("baseline", "normal_far", "recent_far", "reference_far", "estimate", "delta")} == {
        "baseline": Decimal(100), "normal_far": Decimal(100), "recent_far": Decimal(160),
        "reference_far": Decimal(115), "estimate": Decimal("107.5"), "delta": Decimal("7.5"),
    }
    assert Decimal(row["revised_financials"]["eps"]) == Decimal("0.104")
    assert row["ablation"][0]["id"] == "persistence"
    assert Decimal(row["ablation"][0]["without"]["eps"]) == Decimal("0.08")
    assert set(row["evidence_ids"]) == {"history:data", "latest:data"}
    assert Decimal(result["quarters"][0]["scenarios"]["base"]["revised"]["revenue"]) == Decimal(100)


def test_residual_b_reconciles_gross_profit_opex_eps_and_each_counterfactual():
    result = run_plan(plan_data("residual_b", inputs=[residual_item()]))
    row = audit(result)
    revised = row["revised_financials"]
    assert Decimal(revised["revenue"]) == Decimal("117.5")
    assert Decimal(revised["gross_profit"]) == Decimal(50)
    assert Decimal(revised["opex"]) == Decimal(31)
    assert Decimal(revised["eps"]) == Decimal("0.152")
    assert {item["id"]: Decimal(item["without"]["revenue"]) for item in row["ablation"]} == {
        "persistence": Decimal(110), "new-volume": Decimal("107.5"),
    }
    assert row["components"][-1]["public_check"] == "核對公告的出貨數量"
    assert "volume:data" in row["evidence_ids"]


def test_residual_b_rejects_duplicate_document_aliases_even_with_different_ids():
    accession = "000104581023000017"
    source = f"https://www.sec.gov/Archives/edgar/data/1045810/{accession}"
    first = residual_item(evidence_ids=["first:data"])
    second = residual_item(id="same-shock", mechanism="another shipment mechanism", source_family="renamed-source",
                           evidence_ids=["second:data"])
    result = run_plan(plan_data("residual_b", inputs=[first, second]),
                      [*inputs_evidence(), *evidence("first", source=f"{source}/8-k.htm"),
                       *evidence("second", source=f"{source}/earnings.htm?utm_source=copy")])
    row = audit(result)
    assert Decimal(row["estimate"]) == Decimal("107.5")
    assert [item["status"] for item in row["components"]] == ["applied", "skipped", "skipped"]
    assert all("重複" in item["reason"] for item in row["components"][1:])


def test_missing_incrementality_does_not_change_candidate_b_persistence():
    estimate = audit(run_plan(plan_data("residual_b", inputs=[residual_item(basis_incremental_to_incumbent=False)])))
    assert Decimal(estimate["estimate"]) == Decimal("107.5")
    assert estimate["components"][-1]["status"] == "skipped"


def test_t2_issuer_guidance_supersedes_both_residual_candidates():
    data = plan_data("residual_b", inputs=[residual_item()])
    data.update(calibrate_guidance=True, event_values=[{
        "key": {"period_end": FAR, "metric": "revenue", "duration": "quarter", "scope": "consolidated",
                "basis": "US_GAAP", "currency": "USD"},
        "kind": "issuer_guidance", "label": "公司第二預測季指引", "available_at": AS_OF,
        "low": "139", "high": "141", "evidence_ids": ["guide:data"],
    }])
    estimate = audit(run_plan(data, [*inputs_evidence(), *evidence("guide")]))
    assert estimate["status"] == "issuer_guidance"
    assert Decimal(estimate["estimate"]) == Decimal(140)
    assert estimate["components"][-1]["status"] == "skipped"
    assert estimate["ablation"] == []


def test_residual_late_disclosure_is_rejected_and_infeasible_input_falls_back():
    data = plan_data("residual_b", inputs=[residual_item(available_at="2025-06-20T18:00:00Z")])
    with pytest.raises(EarningsError, match="晚於研究截止時點"):
        run_plan(data)
    applied = audit(run_plan(plan_data("residual_b", inputs=[residual_item(incremental_revenue="-200")])))
    assert applied["status"] == "infeasible"
    assert Decimal(applied["estimate"]) == Decimal("107.5")
    assert applied["components"][-1]["status"] == "skipped"


def test_no_residual_when_incumbent_already_contains_recent_upside():
    data = plan_data()
    data["drivers"][-1]["segment_revenue_delta"] = {"consolidated": "15"}
    estimate = audit(run_plan(data))
    assert estimate["status"] == "no_adjustment"
    assert Decimal(estimate["estimate"]) == Decimal(115)
    assert estimate["ablation"] == []


def test_non_residual_bridge_omit_empty_residual_data_for_archived_hashes():
    data = plan_data()["revenue_bridge"]
    data["method"] = "guided_absolute"
    assert "residual_inputs" not in RevenueBridge.model_validate(data).model_dump(mode="json")
