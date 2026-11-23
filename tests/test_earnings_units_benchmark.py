import csv
from zipfile import ZipFile

from benchmarks import earnings_units as units


def _measure(exact, *, eligible=False, unsafe=False):
    return {"exact": exact, "delta_exact": exact, "range_exact": exact, "disposition_exact": exact,
            "citations": exact, "unsafe": unsafe, "eligible_exact": eligible, "missing": False}


def _row(index):
    case_id = f"case-{index}"
    record = {"usage": {key: 0 for key in ("input_tokens", "cached_input_tokens", "output_tokens")},
              "elapsed_seconds": 0}
    decision = {"status": "blocked", "new_low": None, "new_high": None,
                "remaining_delta": None, "evidence_ids": ["doc:p1"]}
    return {
        "id": case_id, "split": "pilot", "ticker": case_id, "issuer": case_id,
        "as_of": "2026-01-02T00:00:00Z", "target": {"period_end": "2025-12-31", "currency": "USD"},
        "baseline": {"amount": "123"}, "citations": {"doc:p1": {}},
        "decisions": {arm: decision for arm in units.ARMS},
        "calls": {call: record for call in units.CALLS},
        "scores": {"current": _measure(index == 0), "candidate": _measure(index < 3, eligible=index == 1),
                   "astra": _measure(True)},
        "failures": {"current": None, "candidate": "units" if index == 3 else None, "astra": None},
    }


def test_units_pilot_gate_does_not_swap_candidate_and_current():
    rows = [_row(index) for index in range(4)]
    result = units.match.aggregate(rows)
    assert result["gate"] and result["paired_exact_gain"] == 2 and not result["lead_over_both"]
    rows[2]["scores"]["astra"] = _measure(False)
    rows[3]["scores"]["astra"] = _measure(False)
    result = units.match.aggregate(rows)
    assert result["gate"] and result["lead_over_both"]
    rows[3]["scores"]["candidate"] = _measure(False, unsafe=True)
    result = units.match.aggregate(rows)
    assert not result["gate"] and not result["lead_over_both"] and result["paired_exact_gain"] == 2


def test_units_failure_uses_explicit_block_or_matching_scaling_signature():
    expected = {"new_low": "244000000", "new_high": "250000000", "disposition": "eligible"}
    collapsed = {"status": "eligible", "new_low": "244", "new_high": "250"}
    blocked = {"status": "blocked", "new_low": None, "new_high": None, "audit": {"block_stage": "units"}}
    assert units.explain("current", collapsed, _measure(False), expected, True) == "units"
    assert units.explain("candidate", blocked, _measure(False), expected, True) == "units"
    assert units.explain("candidate", blocked, _measure(False), expected, False) == "model_location"
    assert not units.unit_failure({**collapsed, "new_high": "240"}, expected)


def test_units_report_and_blind_review_pack(tmp_path):
    rows = [_row(index) for index in range(4)]
    pilot = units.match.aggregate(rows)
    inputs = {row["id"]: {"documents": [{"id": "doc", "published_at": row["as_of"],
                                        "source_url": "https://www.example.com/filing",
                                        "blocks": [{"id": "doc:p1", "text": "Amounts in thousands"}]}]} for row in rows}
    units.render(tmp_path, rows, {"splits": {"pilot": pilot}})
    units.delivery_pack(tmp_path, rows, inputs, {"model_input_sha256": "test"})
    report = (tmp_path / "report.md").read_text()
    assert "新版 Harness 金額單位" in report and "新版比現版多全對 +2 案" in report
    with ZipFile(tmp_path / "analyst-review.zip") as bundle:
        assert bundle.testzip() is None
        assert sorted(bundle.namelist()) == ["review-form.csv", "review.html"]
        form = list(csv.DictReader(bundle.read("review-form.csv").decode("utf-8-sig").splitlines()))
        assert len(form) == 12 and all("unit_ok" in row and "arm" not in row for row in form)
        html = bundle.read("review.html").decode()
        assert "金額單位" not in html and "unit_ok" in html and "Amounts in thousands" in html
