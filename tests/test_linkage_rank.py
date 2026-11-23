from pathlib import Path

from benchmarks import linkage_rank as rank


def test_sealed_controls_share_evidence_and_holdout_issuers_are_disjoint():
    cases, requests = rank.prepared()
    sealed_cases, sealed_requests, protocol = rank.read_sealed(Path("docs/linkage-rank"))
    assert cases == sealed_cases and requests == sealed_requests
    assert cases["H-01"]["issuer"] == "Corning"
    pilot = {key: case for key, case in cases.items() if case["split"] == "pilot"}
    assert rank.equal.digest(pilot) == protocol["amendment"]["unchanged_pilot_cases_sha256"]
    assert rank.equal.digest({key: requests[key] for key in pilot}) == protocol["amendment"]["unchanged_pilot_requests_sha256"]
    for key, case in cases.items():
        assert sorted(rank.schedule(key)) == sorted(rank.ARMS)
        assert all(value["prompt"].endswith("}") for value in requests[key].values())
        if case["split"] == "regression":
            assert rank.completed(rank.OUT, key, case, ("astra", "current"))


def test_principal_rank_distinguishes_selection_from_all_correct(monkeypatch):
    cases, _ = rank.prepared()
    case = cases["P-01"]
    ref = case["input"]["evidence"][0]["id"]
    path = {"origin_evidence_ids": [ref], "affected_evidence_ids": [ref], "deadline": case["input"]["horizon"],
            "ranking_reason": "先查承諾能否轉為實際營運。"}
    all_checks = dict.fromkeys(rank.depth.CHECKS, True)
    off_target = {"index": 1, "target_path": False, "major_error": False, **all_checks, "note": "其他路徑"}
    principal = {"index": 2, "target_path": True, "major_error": False, **all_checks, "note": "目標路徑"}
    findings = {"business_linkages": [path, path], "business_linkage_gap": None}
    verdicts = {label: {"major_error": False, "candidates": [off_target, principal], "gap_ok": False, "note": "覆核"}
                for label in rank.LABELS}
    verdicts["A"]["candidates"] = [off_target, principal | {"falsifier": False}]
    monkeypatch.setattr(rank, "receipt", lambda _, key, arm, case: {"status": "completed"} | (
        {"verdicts": verdicts} if arm == "judge" else {"findings": findings, "raw_findings": findings}))
    score = rank.adjudicate(None, "P-01", case)
    assert score["ranked"]["principal_rank"] == 2
    assert score["ranked"]["qualified_rank"] == 2
    arm = rank.labels("P-01")["A"]
    assert score[arm]["principal_rank"] == 2
    assert score[arm]["qualified_rank"] is None
    assert score[arm]["failure_dimensions"] == ["falsifier"]
    assert "ranking_reason" not in rank.anonymous(findings)["business_linkages"][0]
