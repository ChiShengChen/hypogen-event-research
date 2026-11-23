from datetime import datetime
from decimal import Decimal
from pathlib import Path
import json

from fastapi.testclient import TestClient
import pytest

from research_app.adapters import Fixture
from research_app.api import create_app
from research_app.full_revision import FilingExtraction, check_filing_revision, parse_filing
from research_app.store import Store


EVENT = "2024-01-08T13:00:00Z"
QUARTER = "2023-12-30"
KEY = {"period_end": QUARTER, "metric": "revenue", "duration": "quarter", "scope": "consolidated",
       "basis": "US_GAAP", "currency": "USD"}
SOURCE = "https://www.businesswire.com/news/home/20240107245505/en/Hologic-Announces-Preliminary-Revenue-Results-for-First-Quarter-of-Fiscal-2024"


def release(html):
    return {"id": "release", "source_url": SOURCE, "published_at": EVENT, "obtained_at": EVENT,
            "blocks": parse_filing(html, document_id="release")}


def inspect(document, *, amount, context, header=None, column=None, estimate="972500000"):
    selection = {"amount_ref": amount, "context_ref": context, "header_ref": header, "column": column}
    return check_filing_revision(key=KEY, incumbent=estimate, event_at=EVENT, as_of=EVENT,
                                 documents=[document], selection=selection)


def test_hologic_known_plural_revenues_regression():
    # Published fragments from the previous holdout, used here only as a regression fixture.
    document = release("<p>Preliminary revenue results for its first fiscal quarter ended December 30, 2023.</p>"
                       "<p>The Company expects to report total revenues of approximately $1,013.1 million.</p>")
    audit = inspect(document, amount="release:p0002", context="release:p0001")
    assert audit["status"] == "eligible"
    assert Decimal(audit["new_low"]) == Decimal("1013100000")
    assert audit["new_high"] == audit["new_low"]
    assert Decimal(audit["remaining_delta"]) == Decimal("40600000")
    assert [item["id"] for item in audit["citations"]] == ["release:p0002", "release:p0001"]


@pytest.fixture
def full_table():
    return release("<nav>Site menu</nav><h1>Preliminary update</h1>"
                   "<p>The first fiscal quarter ended December 30, 2023.</p>"
                   "<table><tr><th></th><th>Previous Guidance</th><th>Updated Guidance</th></tr>"
                   "<tr><td><b>Total Revenues</b></td><td>$1.2 billion</td>"
                   "<td>$1.0 billion, plus or minus 2%</td></tr></table>"
                   "<p>Other released information.</p>"
                   "<table><tr><th>Another table</th></tr><tr><td>Unexpected unrelated content</td></tr></table>")


def test_selects_active_column_and_keeps_unrelated_document_body(full_table):
    blocks = full_table["blocks"]
    assert "Site menu" not in [line["text"] for line in blocks]
    assert "Other released information." in [line["text"] for line in blocks]
    audit = inspect(full_table, amount="release:p0004", context="release:p0002", header="release:p0003", column=1)
    assert audit["status"] == "eligible"
    assert Decimal(audit["remaining_delta"]) == Decimal("7500000")
    assert Decimal(audit["new_high"]) == Decimal("1020000000")
    assert "1.0%20billion" in audit["citations"][0]["link"]
    assert inspect(full_table, amount="release:p0004", context="release:p0002", header="release:p0003", column=0)["status"] == "blocked"
    assert inspect(full_table, amount="release:p0004", context="release:p0002", header="release:p0006", column=1)["status"] == "blocked"


@pytest.mark.parametrize("amount", [
    "The company expects second quarter revenue of $1.0 billion.",
    "The company expects annual revenue of $1.0 billion.",
    "The company expects revenue around or below $1.0 billion.",
    "The company reports revenue of $1.0 billion.",
])
def test_unrelated_or_one_sided_prose_does_not_produce_an_adjustment(amount):
    document = release(f"<p>The first fiscal quarter ended December 30, 2023.</p><p>{amount}</p>")
    audit = inspect(document, amount="release:p0002", context="release:p0001")
    assert audit["status"] == "blocked"
    assert audit["remaining_delta"] is None


def test_document_published_after_cutoff_cannot_support_a_revision(full_table):
    full_table.update(obtained_at="2024-01-08T13:00:01Z")
    assert inspect(full_table, amount="release:p0004", context="release:p0002",
                   header="release:p0003", column=1)["status"] == "blocked"


def test_ondas_comparison_does_not_hide_the_new_complete_range():
    text = "For the fourth quarter of 2025, we expect to report revenues between $29.1 and $30.1 million"
    old = "which is above our prior guidance of $27 to $29 million"
    document = release(f"<p>{text}, {old}.</p>")
    selection = {"amount_ref": "release:p0001", "context_ref": "release:p0001", "header_ref": None, "column": None}
    options = {"key": {**KEY, "period_end": "2025-12-31"}, "incumbent": "28000000", "event_at": EVENT,
               "as_of": EVENT, "selection": selection, "fiscal_label": "fourth quarter of 2025"}
    audit = check_filing_revision(**options, documents=[document])
    assert Decimal(audit["remaining_delta"]) == Decimal("1100000")
    assert Decimal(audit["new_high"]) == Decimal("30100000")
    assert audit["location"]["value_span"] == text
    assert "prior" not in audit["citations"][0]["link"]

    for wording in (
        "For the fourth quarter of 2025, we expect revenues above the high end of prior guidance of $27 to $29 million.",
        "For the fourth quarter of 2025, we expect revenues above $29.1 million, versus prior guidance of $27 million.",
        "For the fourth quarter of 2025, we previously expected revenues between $27 and $29 million.",
    ):
        rejected = check_filing_revision(**options, documents=[release(f"<p>{wording}</p>")])
        assert rejected["status"] == "blocked" and rejected["remaining_delta"] is None


def test_saic_joins_preliminary_and_fiscal_headers_in_the_same_physical_column():
    table = ("<p>Preliminary Q4 FY26 and FY26 results</p><table>"
             "<tr><th colspan='3'></th><th colspan='3'>PRELIMINARY</th><th colspan='3'>PRELIMINARY</th>"
             "<th colspan='3'>PRIOR Fiscal Year</th></tr>"
             "<tr><th colspan='3'></th><th colspan='3'>Q4 FY26 Results</th><th colspan='3'>FY26 Results</th>"
             "<th colspan='3'>2026 Guidance</th></tr>"
             "<tr><td colspan='3'>Revenue</td><td colspan='3'>~$1.745B</td><td colspan='3'>~$7.26B</td>"
             "<td colspan='3'>$7.275B - $7.325B</td></tr></table>")
    selection = {"amount_ref": "release:p0004", "context_ref": "release:p0001", "header_ref": "release:p0003", "column": 0}
    options = {"key": {**KEY, "period_end": "2026-01-30"}, "incumbent": "1788000000", "event_at": EVENT,
               "as_of": EVENT, "fiscal_label": "Q4 FY26"}
    audit = check_filing_revision(**options, documents=[release(table)], selection=selection)
    assert Decimal(audit["remaining_delta"]) == Decimal("-43000000")
    assert audit["location"]["header_refs"] == ["release:p0002", "release:p0003"]
    assert "release:p0002" in audit["evidence_ids"]
    assert any("1.745B" in item["link"] for item in audit["citations"])
    for column in (1, 2):
        assert check_filing_revision(**options, documents=[release(table)],
                                     selection={**selection, "column": column})["status"] == "blocked"
    adjusted = table.replace("PRELIMINARY", "PRELIMINARY Non-GAAP", 1)
    assert check_filing_revision(**options, documents=[release(adjusted)], selection=selection)["status"] == "blocked"


def test_grouped_updated_headers_use_rowspan_and_keep_gaap_column_separate():
    html = ("<p>For the first fiscal quarter ending December 30, 2023.</p><table>"
            "<tr><th rowspan='2'>Metric</th><th colspan='2'>Updated Guidance</th><th rowspan='2'>Prior Guidance</th></tr>"
            "<tr><th>GAAP</th><th>Non-GAAP</th></tr>"
            "<tr><td>Revenue</td><td>$1.04B</td><td>$1.05B</td><td>$1.02B</td></tr></table>")
    document = release(html)
    audit = inspect(document, amount="release:p0004", context="release:p0001", header="release:p0003", column=0)
    assert Decimal(audit["new_low"]) == Decimal("1040000000")
    assert audit["location"]["header_refs"] == ["release:p0002", "release:p0003"]
    assert inspect(document, amount="release:p0004", context="release:p0001", header="release:p0003", column=1)["status"] == "blocked"


def units_table(*, left_unit="", caption="", column_unit="", value="$244 - $250"):
    return release(
        "<p>Guidance for the first fiscal quarter ending December 30, 2023.</p><table>"
        + (f"<caption>{caption}</caption>" if caption else "")
        + "<tr><th></th><th colspan='2'>Q1 2023 Guidance</th><th>Actual</th></tr>"
        + f"<tr><th>{left_unit}</th><th>GAAP {column_unit}</th><th>Non-GAAP (in thousands)</th><th>GAAP</th></tr>"
        + f"<tr><td>Revenue</td><td>{value}</td><td>$244 - $250</td><td>$238</td></tr></table>"
    )


def inspect_units(document):
    header, amount = document["blocks"][-2:]
    return check_filing_revision(
        key=KEY, incumbent="238015000", event_at=EVENT, as_of=EVENT, fiscal_label="Q1 2023",
        documents=[document], selection={"amount_ref": amount["id"], "context_ref": "release:p0001",
                                        "header_ref": header["id"], "column": 0},
    )


@pytest.mark.parametrize(("left_unit", "multiplier"), [
    ("(in dollars, except per share amounts)", 1),
    ("(in thousands, except per share amounts)", 1_000),
    ("(in millions, except per share amounts)", 1_000_000),
])
def test_same_tabular_numbers_follow_only_their_scoped_units(left_unit, multiplier):
    audit = inspect_units(units_table(left_unit=left_unit))
    assert Decimal(audit["new_low"]) == 244 * multiplier
    assert Decimal(audit["new_high"]) == 250 * multiplier
    proof = audit["unit_proof"]
    assert proof["raw_text"] == "$244 - $250" and proof["currency"] == "USD"
    assert proof["multipliers"] == [multiplier, multiplier]
    assert any(source["scope"] == "shared_left_label" and source["quote"] == left_unit
               and "#:~:text=" in source["link"] for source in proof["sources"])
    if multiplier == 1_000_000:
        assert Decimal(audit["remaining_delta"]) == 5_985_000  # Progress regression.


@pytest.mark.parametrize("options", [
    {},
    {"left_unit": "(in millions)", "column_unit": "(in thousands)"},
    {"caption": "Revenue outlook (in Canadian dollars)", "left_unit": "(in millions)"},
    {"left_unit": "(in millions)", "value": "$244 thousand - $250 thousand"},
    {"left_unit": "(in millions)", "value": "-$244"},
    {"left_unit": "(in millions)", "value": "$244 to 250%"},
])
def test_unknown_or_conflicting_units_do_not_emit_a_delta(options):
    audit = inspect_units(units_table(**options))
    assert audit["status"] == "blocked" and audit["remaining_delta"] is None
    assert audit["block_stage"] == "units"
    assert audit["unit_proof"]["normalized_low"] is None


def test_caption_and_matching_column_can_supply_units():
    for options, scope in [({"caption": "Revenue outlook (USD in millions)"}, "table_title"),
                           ({"column_unit": "(in millions)"}, "column_header")]:
        audit = inspect_units(units_table(**options))
        assert Decimal(audit["remaining_delta"]) == 5_985_000
        assert any(source["scope"] == scope for source in audit["unit_proof"]["sources"])


def test_merged_amount_cell_cannot_inherit_a_unit_from_only_part_of_its_span():
    document = units_table(left_unit="(in millions)", column_unit="(in millions)")
    amount = document["blocks"][-1]
    amount["cell_spans"][1] = [1, 3]
    audit = inspect_units(document)
    assert audit["status"] == "blocked" and audit["remaining_delta"] is None


class StubFilingAdapter(Fixture):
    identity = {"mode": "codex", "model": "test-fixture"}

    def _generate(self, schema, instructions, payload):
        assert schema is FilingExtraction
        assert payload["target"]["period_end"] == "2024-12-31"
        assert payload["baseline"]["amount"] == "9000000000"
        assert payload["documents"][0]["blocks"][-1]["text"] == "Other financial disclosures."
        return schema.model_validate_json(json.dumps({"selection": {
            "amount_ref": "release:p0002", "context_ref": "release:p0001", "header_ref": None, "column": None,
        }, "evidence_ids": ["release:p0002", "release:p0001"], "reason": "test source selection"}))


def test_full_check_endpoint_uses_stored_estimate_and_does_not_write(tmp_path):
    event = json.loads(Path("research_app/examples/asml-earnings.json").read_text())
    plan = event["earnings_plan"]
    plan["currency"], plan["references"], plan["event_values"], plan["valuation"] = "USD", [], [], None
    quarter = "2024-12-31"
    request_date = datetime.fromisoformat(event["as_of"]).isoformat()
    body = {"period_end": quarter, "source_url": SOURCE, "published_at": request_date, "obtained_at": request_date,
            "html": "<p>Fourth quarter ending December 31, 2024.</p>"
                    "<p>The company expects revenue of $8.4 billion.</p><p>Other financial disclosures.</p>"}

    with TestClient(create_app(Store(tmp_path / "research.sqlite3"), StubFilingAdapter())) as client:
        created = client.post("/events", json=event)
        assert created.status_code == 200, created.text
        root = f"/reports/{created.json()['report_id']}/revisions/1"
        before = client.get(root).json()
        checked = client.post(f"{root}/earnings/full-revision-check", json=body)
        assert checked.status_code == 200, checked.text
        audit = checked.json()["audit"]
        assert Decimal(audit["remaining_delta"]) == -600_000_000
        assert client.get(root).json() == before
        assert client.post(f"{root}/earnings/full-revision-check", json={**body, "source_url": "file:///bad.html"}).status_code == 422
