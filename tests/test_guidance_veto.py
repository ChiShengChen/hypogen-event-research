import json
from pathlib import Path

import pytest

from benchmarks import guidance_arithmetic as bench
from benchmarks import guidance_harness as harness
from benchmarks import guidance_veto as veto

ITEMS = ["implied_remainder_prior", "implied_remainder_new", "implied_remainder_change", "implied_remainder"]
PRIOR_TEXT = ("Financial Outlook: For the third quarter, Acme expects: Total revenue of $243 million to $247 million. "
              "For the full year, Acme expects: Total revenue of $956 million to $961 million.")


def document(name, day):
    stamp = f"2024-{day}T23:59:59-04:00"
    return {"id": name, "source_url": f"https://example.com/{name}.pdf", "path": f"{name}.txt", "sha256": "0" * 64,
            "content_type": "text/plain", "published_at": stamp, "obtained_at": stamp}


def ref(doc, block, quote):
    return [{"document": doc, "block": f"{doc}:{block}", "quote": quote}]


def make_case(negative=False):
    payload = {
        "id": "acme", "split": "pilot", "issuer": "Acme", "ticker": "ACME", "precision": "1000",
        "event_at": "2024-11-07T23:59:59-05:00", "as_of": "2024-11-07T23:59:59-05:00",
        "documents": [document("prior", "08-07"), document("latest", "11-07")],
        "labels": {"period": "fiscal 2024", "interim": "the third quarter of fiscal 2024",
                   "remainder": "the fourth quarter of fiscal 2024"},
        "style": "implicit", "trap": "trap", "items": ITEMS if not negative else ITEMS[:1] + ITEMS[2:],
    }
    if negative:
        gap = "No comparable total revenue outlook."
        return bench.Case.model_validate(payload | {"figures": {}, "undetermined": dict.fromkeys(payload["items"], gap)})
    figures = {"prior": ref("prior", "p0001", "$956 million to $961 million"),
               "prior_interim": ref("prior", "p0001", "$243 million to $247 million"),
               "new": ref("latest", "p0001", "$964 million to $966 million"),
               "prior_reported_in_period": ref("prior", "p0002", "453,019"),
               "reported_in_period": ref("latest", "p0002", "704,019")}
    return bench.Case.model_validate(payload | {"figures": figures})


def blocks(prior=PRIOR_TEXT, latest="For the full year, Acme expects: Total revenue of $964 million to $966 million."):
    return {"prior:p0001": {"text": prior}, "prior:p0002": {"text": "Total revenue 453,019"},
            "latest:p0001": {"text": latest}, "latest:p0002": {"text": "Total revenue 704,019"}}


def reply(quotes=None, answers=None, drop=()):
    quotes = {"prior": ("prior", "$956 million to $961 million"),
              "prior_interim": ("prior", "$243 million to $247 million"),
              "new": ("latest", "$964 million to $966 million"),
              "prior_reported_in_period": ("prior", "453,019"),
              "reported_in_period": ("latest", "704,019")} | (quotes or {})
    blocks_for = {"prior": "p0001", "prior_interim": "p0001", "new": "p0001",
                  "prior_reported_in_period": "p0002", "reported_in_period": "p0002"}
    figures = [{"name": name, "document": doc, "block": f"{doc}:{blocks_for[name]}", "quote": quote,
                "tabular": False, "unit_block": None, "unit_quote": None}
               for name, (doc, quote) in quotes.items() if name not in drop]
    answers = answers or {"implied_remainder_prior": "260481000", "implied_remainder_new": "260981000",
                          "implied_remainder_change": "500000", "implied_remainder": "raised"}
    return {"answers": [{"item": key, "value": value} for key, value in answers.items()],
            "evidence_ids": ["prior:p0001", "latest:p0001"], "reason": "computed", "figures_used": figures,
            "missing_reason": None}


def test_total_revenue_outlook_keeps_the_model_answer():
    result = veto.apply(make_case(), blocks(), reply())
    assert result["answers"]["implied_remainder_change"] == "500000"
    assert result["vetoes"] == [] and result["reason"] is None


def test_component_outlook_named_in_the_quote_is_vetoed():
    quotes = {"prior": ("prior", "Subscription revenue between $956 million and $961 million")}
    result = veto.apply(make_case(), blocks(), reply(quotes))
    assert result["answers"]["implied_remainder_prior"] == "unknown"
    assert result["answers"]["implied_remainder_change"] == "unknown"
    # The latest-only item does not depend on the prior outlook and stays.
    assert result["answers"]["implied_remainder_new"] == "260981000"
    assert "subscription revenue" in result["reason"] and "prior" in result["reason"]
    assert "prior:p0001" in result["evidence_ids"]


def test_metric_is_read_from_the_block_when_the_quote_has_none():
    text = PRIOR_TEXT.replace("Total revenue of $956", "Product revenue of $956")
    result = veto.apply(make_case(), blocks(prior=text), reply())
    assert result["answers"]["implied_remainder_prior"] == "unknown"
    assert result["vetoes"][0]["rule"] == "metric"


def test_constant_currency_growth_rate_is_vetoed():
    quotes = {"new": ("latest", "Consolidated net sales (cc) Increase 4.8% to 5.1%")}
    result = veto.apply(make_case(), blocks(), reply(quotes))
    rules = {flag["rule"] for flag in result["vetoes"]}
    assert rules == {"rate", "currency"}
    assert result["answers"]["implied_remainder_new"] == "unknown"
    assert result["answers"]["implied_remainder_prior"] == "260481000"


def test_unverifiable_quote_is_not_a_veto():
    quotes = {"prior": ("prior", "$900 million to $910 million")}
    result = veto.apply(make_case(), blocks(), reply(quotes))
    assert result["answers"]["implied_remainder_prior"] == "260481000"


def test_unrelated_constant_currency_sentence_does_not_veto():
    text = "Revenue grew 10% in constant currency. " + PRIOR_TEXT
    result = veto.apply(make_case(), blocks(prior=text), reply())
    assert result["vetoes"] == []


def test_answer_without_a_cited_operand_is_vetoed():
    result = veto.apply(make_case(), blocks(), reply(drop=("prior_interim",)))
    assert result["vetoed_items"]["implied_remainder_prior"].endswith("without citing prior_interim")
    assert result["answers"]["implied_remainder_new"] == "260981000"


def test_document_outside_the_case_is_vetoed():
    quotes = {"new": ("later", "$964 million to $966 million")}
    result = veto.apply(make_case(), blocks(), reply(quotes))
    assert result["vetoes"][0]["rule"] == "visibility"
    assert result["answers"]["implied_remainder_new"] == "unknown"


def test_negative_case_keeps_an_explicit_unknown_and_vetoes_component_answers():
    case = make_case(negative=True)
    unknown = {"implied_remainder_prior": "unknown", "implied_remainder_change": "unknown", "implied_remainder": "unknown"}
    assert veto.apply(case, blocks(), reply(answers=unknown))["answers"] == unknown
    quotes = {name: (doc, "Subscription revenue of $1.955 billion")
              for name, doc in (("prior", "prior"), ("prior_interim", "prior"), ("new", "latest"))}
    answered = {"implied_remainder_prior": "2038500000", "implied_remainder_change": "-13500000",
                "implied_remainder": "lowered"}
    assert veto.apply(case, blocks(), reply(quotes, answered))["answers"] == unknown


def test_mode_comes_from_config(monkeypatch):
    monkeypatch.delenv(harness.ENV, raising=False)
    assert harness.configured_mode() == "extract"
    monkeypatch.setenv(harness.ENV, "Veto")
    assert harness.configured_mode() == "veto"
    assert harness.configured_mode("extract") == "extract"
    monkeypatch.setenv(harness.ENV, "judge")
    with pytest.raises(ValueError, match=harness.ENV):
        harness.configured_mode()


def test_veto_mode_dispatches_on_the_direct_reply(monkeypatch):
    monkeypatch.setenv(harness.ENV, "veto")
    quotes = {"prior": ("prior", "Subscription revenue between $956 million and $961 million")}
    result = harness.answer(None, make_case(), blocks(), reply(quotes))
    assert result["answers"]["implied_remainder_prior"] == "unknown"
    assert "implied_remainder_prior" in result["errors"]
    assert harness.CALLS == {"extract": "extract", "veto": "astra"}


ARCHIVED = all(Path(path).exists() for path in ("output/guidance-ytd/filings", "output/guidance-table/filings"))


@pytest.mark.skipif(not ARCHIVED, reason="archived filings are kept locally under output/")
def test_development_replay_vetoes_only_the_scope_errors(tmp_path):
    from benchmarks import guidance_veto_run
    summary = guidance_veto_run.replay(tmp_path)
    assert summary["all"]["vetoed_cases"] == ["wday", "wmt", "snow"]
    assert summary["all"]["false_vetoes"] == []
    published = json.loads((tmp_path / "dev-replay.json").read_text())
    assert published["all"]["metrics"]["astra"]["numeric_exact"] == 20
