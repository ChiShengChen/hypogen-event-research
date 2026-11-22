from benchmarks import hypothesis_pilot
from benchmarks.hypothesis_cases import freeze, future_disclosures, load_cases
from benchmarks.hypothesis_pilot import compare, disqualified


def test_replays_hide_later_results_from_generation():
    cases = load_cases() | load_cases(holdout=True)
    for case_id, hidden in (
        ("H-01", {"asml-q4:actual"}),
        ("H-03", {"nvidia-q1:charge", "nvidia-q1:margin", "nvidia-q1:eps"}),
        ("V-03", {"novo-cleared:update"}),
    ):
        _, event = cases[case_id]
        visible = {row["id"] for row in freeze(event)["evidence"]}
        assert visible.isdisjoint(hidden)
        assert {row["id"] for row in future_disclosures(event)} == hidden


def test_gate_requires_visible_references_and_matching_later_evidence():
    pair = {"first": {"evidence_ids": ["unknown"]}, "second": {"evidence_ids": ["known"]}}
    flag = {"candidate": 2, "kind": "lookahead", "evidence_id": "later", "rationale": "confirmed"}
    empty = {"disqualifiers": []}
    affirmative = {"disqualifiers": [flag]}
    one_review = disqualified(pair, [affirmative, empty], {"known"}, {"later"})
    assert one_review["invalid_references"] == {"1": ["unknown"]}
    assert one_review["candidates"] == [1]
    assert disqualified(pair, [affirmative] * 2, {"known"}, set())["candidates"] == [1]
    assert disqualified(pair, [affirmative] * 2, {"known"}, {"later"})["candidates"] == [1, 2]


def test_valid_pair_has_priority_over_higher_unqualified_score():
    eligible = {"score": 6, "gate": {"candidates": []}}
    ineligible = {"score": 9, "gate": {"candidates": [1]}}
    assert compare(eligible, ineligible) == 1
    assert compare(ineligible, eligible) == -1
    assert compare(eligible, eligible) == 0


def test_harness_comparison_uses_frozen_excerpts_and_preserves_claim_citations(monkeypatch):
    _, original = load_cases()["H-01"]
    evidence_id = freeze(original)["evidence"][0]["id"]
    claim_id = f"fact:{evidence_id}"

    def report(event, adapter):
        assert freeze(event) == freeze(original)
        assert len(event.documents) < len(original.documents)
        assert not event.supply_edges and not event.reported_calculations
        assert event.search_mode == "off"
        return {
            "claims": [{"id": claim_id, "evidence_id": evidence_id}, {"id": "assumption"}],
            "hypotheses": [{
                "stance": stance, "target": "ASML", "mechanism": "mechanism", "catalyst": "catalyst",
                "prediction": "prediction", "invalidation": "invalidation",
                "claim_ids": [claim_id, "assumption", claim_id],
            } for stance in ("bear", "bull")],
        }

    monkeypatch.setattr(hypothesis_pilot, "build_report", report)
    result = hypothesis_pilot.generate_harness(original, object())
    assert result["hypotheses"]["first"]["evidence_ids"] == [evidence_id]
    assert result["hypotheses"]["second"]["evidence_ids"] == [evidence_id]
    assert result["original_report"]["hypotheses"][0]["stance"] == "bear"
