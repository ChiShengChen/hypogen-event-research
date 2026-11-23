import json

from benchmarks import linkage_depth as run


def test_questions_use_identical_frozen_evidence_and_response_budget():
    cases, requests = run.prepared()
    assert {case["split"] for case in cases.values()} == {"pilot", "holdout"}
    assert len({case["issuer"] for case in cases.values()}) == 12
    for split, expected in (("pilot", 2), ("holdout", 4)):
        batch = [case for case in cases.values() if case["split"] == split]
        assert len(batch) == 2 * expected
        assert sum(case["gold"]["positive"] for case in batch) == expected
    for key, case in cases.items():
        bodies = {arm: json.loads(request["prompt"].split("\n\n", 1)[1])
                  for arm, request in requests[key].items()}
        assert all(body["evidence"] == case["input"]["evidence"] and "gold" not in body for body in bodies.values())
        assert requests[key]["harness"]["schema"] == requests[key]["astra"]["schema"]
        assert {row["paragraph"] for row in case["input"]["evidence"]}.issuperset({"original"})


def test_positive_qualification_requires_same_candidate_and_no_major_error(tmp_path):
    key = "P-01"
    case = run.prepared()[0][key]
    refs = [row["id"] for row in case["input"]["evidence"][:2]]
    good_path = {"origin_evidence_ids": refs[:1], "affected_evidence_ids": refs[1:], "deadline": case["input"]["horizon"]}
    invalid_path = good_path | {"deadline": "2100-01-01"}
    findings = {"business_linkages": [good_path, invalid_path], "business_linkage_gap": None}
    record = {"status": "completed", "findings": findings, "raw_findings": findings}
    checks = {"target_path": True, "major_error": False, **dict.fromkeys(run.CHECKS, True)}

    (tmp_path / "calls").mkdir()
    for arm in run.ARMS:
        run.equal.journal.atomic(run.equal.journal.receipt(tmp_path, key, arm), record)
    positive = {"index": 1, **checks, "note": "fixture"}
    adverse = {"index": 2, **checks, "note": "fixture"}
    verdict = {"gap_ok": False, "major_error": False, "note": "fixture"}
    judge = {"status": "completed", "verdicts": {
        "A": verdict | {"candidates": [positive | {"falsifier": False}, adverse]},
        "B": verdict | {"candidates": [positive, adverse]},
    }}
    path = run.equal.journal.receipt(tmp_path, key, "judge")
    run.equal.journal.atomic(path, judge)
    grade = run.adjudicate(tmp_path, key, case)
    assert not grade["astra"]["exact"] and grade["harness"]["exact"]
    assert not grade["astra"]["rules"][1]["time"]
    judge["verdicts"]["B"]["candidates"][1]["major_error"] = True
    run.equal.journal.atomic(path, judge)
    assert not run.adjudicate(tmp_path, key, case)["harness"]["exact"]


def test_holdout_gate_checks_paired_scope_and_margin(monkeypatch, tmp_path):
    cases, _ = run.prepared()
    monkeypatch.setattr(run, "completed", lambda *_: True)
    evaluated = {key: {"astra": {"exact": key != "H-01", "major": False},
                       "harness": {"exact": True, "major": False}} for key in cases}
    assert run.stats(tmp_path, cases, evaluated, "pilot")["pass"]
    assert not run.stats(tmp_path, cases, evaluated, "holdout")["pass"]
    evaluated["H-02"]["astra"]["exact"] = False
    assert run.stats(tmp_path, cases, evaluated, "holdout")["pass"]
    evaluated["H-03"]["harness"]["major"] = True
    assert not run.stats(tmp_path, cases, evaluated, "holdout")["pass"]
