from decimal import Decimal
import re
from hashlib import sha256

import pytest
from pydantic import ValidationError

from benchmarks import guidance_arithmetic as bench

HTML = (
    "<html><body><p>Acme expects revenue for the fourth quarter to be between $179 million and $189 million, "
    "compared to prior guidance of $175 million to $190 million.</p>"
    "<p>(U.S. $ in thousands)</p><table><tr><td>Total revenues</td><td>180,250</td></tr></table></body></html>"
)


@pytest.fixture
def archive(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    path = tmp_path / "acme.htm"
    path.write_text(HTML)
    return {
        "id": "acme", "source_url": "https://example.com/acme.htm", "path": "acme.htm",
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "published_at": "2024-01-31T16:00:00-05:00", "obtained_at": "2024-01-31T16:00:00-05:00",
    }


def case(document, **changes):
    payload = {
        "id": "acme_q4", "split": "pilot", "issuer": "Acme", "ticker": "ACME",
        "event_at": "2024-01-31T16:00:00-05:00", "as_of": "2024-01-31T16:00:00-05:00",
        "precision": "1000000",
        "labels": {"period": "the fourth quarter", "last_period": "the third quarter"},
        "documents": [document],
        "figures": {
            "new": [{"document": "acme", "block": "acme:p0001", "quote": "between $179 million and $189 million"}],
            "prior": [{"document": "acme", "block": "acme:p0001", "quote": "$175 million to $190 million"}],
            "last_actual": [{"document": "acme", "block": "acme:p0003", "quote": "180,250", "tabular": True,
                             "unit_block": "acme:p0002", "unit_quote": "(U.S. $ in thousands)"}],
        },
        "items": ["revision", "midpoint_change", "midpoint_change_ratio", "high_change", "sequential"],
        "trap": "High end falls while the midpoint rises.",
    }
    return bench.Case.model_validate(payload | changes)


def test_gold_comes_from_cited_wording(archive):
    expected = bench.gold(case(archive))
    assert expected["revision"] == "raised"
    assert expected["midpoint_change"] == Decimal(1_500_000)
    assert expected["high_change"] == Decimal(-1_000_000)
    assert expected["sequential"] == "raised"


def test_grading_tolerances(archive):
    item = case(archive)
    expected = bench.gold(item)
    result = bench.grade(item, expected, {
        "revision": "Raised", "midpoint_change": "1,510,000", "midpoint_change_ratio": "0.82%",
        "high_change": "unknown",
    })
    rows = result["items"]
    assert rows["revision"]["correct"] and rows["midpoint_change"]["correct"]
    assert rows["midpoint_change_ratio"]["correct"]
    assert not rows["high_change"]["correct"] and not rows["sequential"]["correct"]
    assert not result["exact"]

    def correct(item_name, value):
        return bench.grade(item, expected, {item_name: value})["items"][item_name]["correct"]

    assert not correct("midpoint_change", "1520000")
    assert not correct("midpoint_change", "2000000")
    assert not correct("midpoint_change_ratio", "0.85")
    assert not correct("midpoint_change_ratio", "0.8")


def test_zero_gold_uses_the_floor(archive):
    item = case(archive, items=["width_change"])
    expected = {"width_change": Decimal(0)}
    assert bench.grade(item, expected, {"width_change": "10000"})["exact"]
    assert not bench.grade(item, expected, {"width_change": "10001"})["exact"]


def test_exact_case_needs_every_item(archive):
    item = case(archive)
    expected = bench.gold(item)
    answers = {"revision": "raised", "midpoint_change": "1500000", "midpoint_change_ratio": "0.8219",
               "high_change": "-1000000", "sequential": "raised"}
    assert bench.grade(item, expected, answers)["exact"]


def test_quote_must_appear_in_the_cited_block(archive):
    figures = case(archive).model_dump()["figures"]
    figures["new"][0]["quote"] = "between $180 million and $189 million"
    with pytest.raises(ValueError, match="quote is not in block"):
        bench.gold(case(archive, figures=figures))


def test_archive_hash_is_checked(archive):
    with pytest.raises(ValueError, match="hash mismatch"):
        bench.gold(case(archive | {"sha256": "0" * 64}))


@pytest.mark.parametrize("changes, message", [
    ({"items": ["year_over_year"]}, "needs figures"),
    ({"labels": {"period": "the fourth quarter"}}, "needs labels"),
    ({"as_of": "2024-01-30T16:00:00-05:00"}, "event must precede"),
])
def test_invalid_cases_are_rejected(archive, changes, message):
    with pytest.raises(ValidationError, match=message):
        case(archive, **changes)


def test_questions_use_case_labels(archive):
    rows = bench.questions(case(archive))
    assert rows[0]["item"] == "revision" and "the fourth quarter" in rows[0]["question"]
    assert rows[-1]["kind"] == "direction" and "the third quarter" in rows[-1]["question"]


def extraction(**overrides):
    figures = {
        "new": {"document": "acme", "block": "acme:p0001", "quote": "between $179 million and $189 million",
                "tabular": False, "unit_block": None, "unit_quote": None},
        "prior": {"document": "acme", "block": "acme:p0001", "quote": "$175 million to $190 million",
                  "tabular": False, "unit_block": None, "unit_quote": None},
        "last_actual": {"document": "acme", "block": "acme:p0003", "quote": "180,250", "tabular": True,
                        "unit_block": "acme:p0002", "unit_quote": "(U.S. $ in thousands)"},
    } | overrides
    return bench.Extraction.model_validate({
        "figures": [{"name": name, **figure} for name, figure in figures.items() if figure is not None],
        "reason": "已定位",
    })


def test_harness_computes_from_verified_wording(archive):
    item = case(archive)
    blocks = bench.case_blocks(item)
    answers, errors = bench.harness_answers(item, blocks, extraction())
    assert not errors
    assert bench.grade(item, bench.gold(item, blocks), answers)["exact"]
    assert answers["midpoint_change"] == "1500000" and answers["revision"] == "raised"


def test_harness_leaves_unproven_items_unknown(archive):
    item = case(archive)
    blocks = bench.case_blocks(item)
    wrong = {"document": "acme", "block": "acme:p0001", "quote": "$176 million to $190 million",
             "tabular": False, "unit_block": None, "unit_quote": None}
    answers, errors = bench.harness_answers(item, blocks, extraction(prior=wrong))
    assert "prior" in errors and answers["revision"] == "unknown"
    assert answers["sequential"] == "raised"
    answers, errors = bench.harness_answers(item, blocks, extraction(new=None))
    assert errors["new"] == "figure not located" and set(answers.values()) == {"unknown"}


def test_requests_share_documents_and_hide_gold(archive):
    item = case(archive)
    requests = bench.requests_for(item, bench.case_blocks(item))
    direct, harness = (requests[arm]["prompt"] for arm in bench.ARMS)
    assert direct.split("\n\n", 1)[1].count("acme:p0001") == harness.split("\n\n", 1)[1].count("acme:p0001") == 1
    assert "Compared with the prior guidance" in direct and "Compared with the prior guidance" not in harness
    assert "the issuer's prior guidance for the fourth quarter revenue" in harness
    assert "1500000" not in direct + harness and "trap" not in direct + harness


def test_prompt_examples_match_no_pilot_case():
    examples = bench.ANSWER_RULES + bench.EXTRACT
    for item in bench.load_cases():
        for refs in item.figures.values():
            assert all(ref.quote not in examples for ref in refs)
    for number in re.findall(r"-?\d+(?:\.\d+)?", bench.ANSWER_RULES):
        assert number.lstrip("-") not in {"1500000", "0.82", "7500000", "13500000", "1600000", "2716000"}


def test_direct_answers_are_read_by_item(archive):
    item = case(archive)
    record = bench.transform("astra", (item, {}), {
        "answers": [{"item": "revision", "value": "raised"}, {"item": "midpoint_change", "value": "1500000"}],
        "evidence_ids": ["acme:p0001"], "reason": "中點上修",
    })
    assert record["answers"] == {"revision": "raised", "midpoint_change": "1500000"}


def test_mcnemar_and_holdout_size():
    assert bench.mcnemar(6, 0) == 0.03125 and bench.mcnemar(5, 0) == 0.0625 and bench.mcnemar(2, 2) == 1.0
    assert bench.holdout_size(0, 1, 8) is None and bench.holdout_size(2, 2, 8) is None
    size = bench.holdout_size(3, 0, 8)
    assert size is not None and 4 <= size <= 30
    assert bench.holdout_size(2, 1, 8) > size
