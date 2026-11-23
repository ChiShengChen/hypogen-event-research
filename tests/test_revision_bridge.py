from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from research_app.revision_bridge import RevisionQuote, RevisionRequest, evaluate_revision
from research_app.schema import MetricKey


KEY = MetricKey(metric="revenue", duration="quarter", scope="consolidated", basis="US_GAAP",
                period_end="2024-06-29", currency="USD")
ORIGINAL = "2024-05-01T20:00:00+00:00"
EVENT = "2024-06-04T12:00:00+00:00"
AVAILABLE = "2024-06-04T13:00:00+00:00"
CUTOFF = datetime.fromisoformat("2024-06-04T14:00:00+00:00")
GUIDANCE = "U.S. GAAP consolidated revenue guidance for the quarter ending 2024-06-29 is USD 5.6 billion."


def quote(value, ref, at, high=None, key=KEY):
    return RevisionQuote(key=key, available_at=at, low=value, high=high or value, evidence_ids=[ref])


def public(ref, text, published, obtained=None):
    return {
        "id": ref, "source": f"https://example.com/{ref}", "kind": "disclosure", "synthetic": False,
        "quote": text, "published_at": published, "obtained_at": obtained or published,
    }


@pytest.fixture
def replay():
    prior = public("prior", "US GAAP consolidated revenue guidance for fiscal quarter ending June 29, 2024 is "
                            "USD 6.7 billion ± $200 million.", ORIGINAL)
    driver = public("driver", "A supporting disclosure for the existing model forecast.", ORIGINAL)
    new = public("new", GUIDANCE, EVENT, AVAILABLE)
    request = RevisionRequest(
        key=KEY, event_at=EVENT,
        original=quote("6500000000", "prior", ORIGINAL, "6900000000"),
        incumbent=quote("6541250200", "driver", AVAILABLE),
        disclosure=quote("5600000000", "new", AVAILABLE),
    )
    return request, [prior, driver, new]


def test_only_unincorporated_revision_is_applied(replay):
    request, evidence = replay
    result = evaluate_revision(request, evidence, as_of=CUTOFF)
    assert result["status"] == "eligible"
    assert result["revised"] == "5600000000"
    assert result["remaining_delta"] == "-941250200"
    assert result["event_change"] == {
        "low": "-1300000000", "high": "-900000000", "midpoint_delta": "-1100000000",
    }
    assert result["evidence_ids"] == ["prior", "driver", "new"]

    updated = request.model_copy(update={"incumbent": quote(result["revised"], "driver", AVAILABLE)})
    again = evaluate_revision(updated, evidence, as_of=CUTOFF)
    assert again["status"] == "noop"
    assert again["remaining_delta"] == "0"


def test_preliminary_issuer_estimate_uses_reported_point(replay):
    request, evidence = replay
    evidence[-1]["quote"] = (
        "Quarter ending 2024-06-29, US GAAP, consolidated preliminary net revenue estimate (USD): "
        "approximately $5.6 billion. Segment revenue declined."
    )
    assert evaluate_revision(request, evidence, as_of=CUTOFF)["status"] == "eligible"


@pytest.mark.parametrize(("incumbent", "status", "delta"), [
    ("7200000000", "eligible", "200000000"),
    ("7400000000", "noop", "0"),
    ("7510000000", "noop", "0"),
    ("8100000000", "eligible", "-100000000"),
])
def test_interval_uses_nearest_edge_only_outside(replay, incumbent, status, delta):
    _, evidence = replay
    evidence[-1]["quote"] = (
        "US GAAP consolidated net sales outlook for fiscal quarter ending June 29, 2024 is between "
        "USD $7.4 billion and $8.0 billion."
    )
    request = RevisionRequest(
        key=KEY, event_at=EVENT, incumbent=quote(incumbent, "driver", AVAILABLE),
        disclosure=quote("7400000000", "new", AVAILABLE, "8000000000"),
    )
    result = evaluate_revision(request, evidence, as_of=CUTOFF)
    assert result["status"] == status
    assert result["remaining_delta"] == delta
    assert result["event_change"] is None


@pytest.mark.parametrize("text", [
    GUIDANCE.replace("5.6", "5.5"),
    GUIDANCE.replace("consolidated", "data center segment"),
    GUIDANCE.replace("U.S. GAAP", "non-GAAP"),
    GUIDANCE.replace("USD", "CAD"),
    GUIDANCE.replace("USD", "$"),
    GUIDANCE.replace("2024-06-29", "2024-09-28"),
    GUIDANCE.replace("quarter", "fiscal year"),
    "U.S. GAAP consolidated revenue for quarter ending 2024-06-29 was USD 5.6 billion. EPS guidance was unchanged.",
    "U.S. GAAP consolidated revenue for quarter ending 2024-06-29 was USD 5.6 billion, and EPS guidance was unchanged.",
    "U.S. GAAP consolidated revenue guidance for quarter ending 2024-06-29 is USD 5.6 to 6.0 billion.",
])
def test_statement_must_match_all_dimensions_and_full_interval(replay, text):
    request, evidence = replay
    evidence[-1]["quote"] = text
    result = evaluate_revision(request, evidence, as_of=CUTOFF)
    assert result["status"] == "blocked"
    assert result["remaining_delta"] is None
    assert Decimal(result["revised"]) == request.incumbent.low


@pytest.mark.parametrize("wrong_evidence", [
    {"obtained_at": "2024-06-04T14:00:01+00:00"},
    {"published_at": "2024-06-04T11:59:59+00:00"},
    {"published_at": "2024-06-04T12:00:00"},
    {"synthetic": True},
    {"kind": "scenario"},
    {"source": "file:///private/a"},
    {"text_format": "summary"},
])
def test_inaccessible_or_non_source_evidence_is_blocked(replay, wrong_evidence):
    request, evidence = replay
    evidence[-1].update(wrong_evidence)
    assert evaluate_revision(request, evidence, as_of=CUTOFF)["status"] == "blocked"


def test_original_cannot_be_retroactively_updated(replay):
    request, evidence = replay
    original = quote("6500000000", "prior", EVENT, "6900000000")
    request = request.model_copy(update={"original": original})
    assert evaluate_revision(request, evidence, as_of=CUTOFF)["status"] == "blocked"


def test_mismatched_quote_key_is_blocked_before_arithmetic(replay):
    request, evidence = replay
    key = KEY.model_copy(update={"currency": "EUR"})
    request = request.model_copy(update={"disclosure": quote("5600000000", "new", AVAILABLE, key=key)})
    assert evaluate_revision(request, evidence, as_of=CUTOFF)["status"] == "blocked"


def test_conflicting_duplicate_id_cannot_shadow_evidence(replay):
    request, evidence = replay
    duplicate = {**evidence[-1], "quote": "Different text for same ID"}
    assert evaluate_revision(request, [*evidence, duplicate], as_of=CUTOFF)["status"] == "blocked"
    assert evaluate_revision(request, [*evidence, evidence[-1].copy()], as_of=CUTOFF)["status"] == "eligible"


def test_no_disclosure_preserves_incumbent(replay):
    request, evidence = replay
    result = evaluate_revision(request.model_copy(update={"disclosure": None}), evidence, as_of=CUTOFF)
    assert result["status"] == "blocked"
    assert result["remaining_delta"] is None
    assert Decimal(result["revised"]) == request.incumbent.low


def test_incumbent_must_be_one_value():
    with pytest.raises(ValidationError, match="現版營收預估須為單點"):
        RevisionRequest(key=KEY, event_at=EVENT, incumbent=quote("5000000000", "driver", AVAILABLE, "6000000000"))


@pytest.fixture
def native_replay():
    lead = public("lead", "The issuer updated guidance for the second quarter ended June 29, 2024.", EVENT)
    row = public("table", "Previous Guidance | Updated Guidance\nRevenue | $3.0 billion | $2.20 billion, plus or minus 2%", EVENT)
    for excerpt in (lead, row):
        excerpt.update(source="https://example.com/release", document_id="release", text_format="excerpt")
    proof = {"amount_ref": "table", "header_ref": "table", "context_ref": "lead", "column": 1}
    disclosure = RevisionQuote(key=KEY, available_at=AVAILABLE, low="2156000000", high="2244000000",
                               evidence_ids=["table", "lead"], native_proof=proof)
    request = RevisionRequest(key=KEY, event_at=EVENT, incumbent=quote("3000000000", "driver", AVAILABLE),
                              disclosure=disclosure)
    return request, [lead, row, public("driver", "Current scenario evidence", ORIGINAL)]


def test_native_table_uses_active_header_and_percent_tolerance(native_replay):
    request, evidence = native_replay
    strict = request.model_copy(update={"disclosure": request.disclosure.model_copy(update={"native_proof": None})})
    assert evaluate_revision(strict, evidence, as_of=CUTOFF)["status"] == "blocked"
    preview = evaluate_revision(request, evidence, as_of=CUTOFF)
    assert preview["status"] == "eligible"
    assert Decimal(preview["revised"]) == Decimal("2244000000")
    assert Decimal(preview["remaining_delta"]) == Decimal("-756000000")
    assert preview["disclosure"]["native_proof"]["column"] == 1


@pytest.mark.parametrize(("row", "replacement"), [
    (0, {"source": "https://example.com/different-release"}),
    (0, {"document_id": "other-document"}),
    (0, {"quote": "Third quarter ended September 28, 2024."}),
    (1, {"text_format": "summary"}),
    (1, {"quote": "Previous Guidance | Year-to-Date Actual\nRevenue | $3.0 billion | $2.20 billion, plus or minus 2%"}),
    (1, {"quote": "Previous Guidance | Updated Guidance\nSegment Revenue | $3.0 billion | $2.20 billion, plus or minus 2%"}),
    (1, {"quote": "Previous Guidance | Updated Guidance\nRevenue | $3.0 billion | C$2.20 billion, plus or minus 2%"}),
    (1, {"quote": "Previous Guidance | Updated Guidance\nRevenue | $3.0 billion | up to $2.20 billion, plus or minus 2%"}),
])
def test_native_proof_rejects_mismatched_provenance_and_scope(native_replay, row, replacement):
    request, evidence = native_replay
    evidence[row].update(replacement)
    assert evaluate_revision(request, evidence, as_of=CUTOFF)["status"] == "blocked"


def test_native_proof_rejects_previous_guidance_column(native_replay):
    request, evidence = native_replay
    data = request.disclosure.model_dump()
    data.update(low="3000000000", high="3000000000")
    data["native_proof"]["column"] = 0
    old = request.model_copy(update={"disclosure": RevisionQuote.model_validate(data)})
    assert evaluate_revision(old, evidence, as_of=CUTOFF)["status"] == "blocked"
