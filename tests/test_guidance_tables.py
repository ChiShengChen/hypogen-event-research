from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from benchmarks import guidance_tables as verifier


VINTAGE = verifier.previous.Vintage(date(2024, 9, 30), 2024, 3)
TITLE = "CONSOLIDATED STATEMENTS OF OPERATIONS"
SCALE = "(in USD thousands)"
DURATION = f"{'Three Months Ended':>73}{'Nine Months Ended':>28}"
DATES = f"{'September 30,':>73}{'September 30,':>28}"
YEARS = f"{2024:>64}{2023:>14}{2024:>14}{2023:>14}"


def row(label, *numbers):
    return f"{label:<51} " + "".join(f"${value:>12,} " for value in numbers)


def scan(monkeypatch, *pages):
    document = SimpleNamespace(id="test", source_url="https://example.com/release.pdf",
                               published_at=date(2024, 11, 6), content_type="text/plain")
    layout = [(page, [verifier.Line(page, i, line) for i, line in enumerate(lines, 1)])
              for page, lines in enumerate(pages, 1)]
    monkeypatch.setattr(verifier, "pages_of", lambda doc: layout)
    return verifier.scan_document(document, VINTAGE)


def test_cross_page_continuation_retains_printed_proof(monkeypatch):
    cells, issues = scan(monkeypatch, [TITLE, SCALE, DURATION], [
        DATES, YEARS, row("Revenue", 11, 9, 33, 27)])
    assert not issues
    last = cells[-1]
    assert last.value == Decimal(33000)
    assert last.quarters == (1, 2, 3)
    assert last.proof["column"] == 3
    assert last.proof["table"]["url"].endswith("#page=1")
    assert last.proof["row"]["url"].endswith("#page=2")
    assert {ref["block"] for ref in last.proof["heading_sources"]} == {"test:p0001", "test:p0002"}


def test_new_table_must_not_inherit_title_or_scale(monkeypatch):
    cells, _ = scan(monkeypatch, [TITLE, SCALE], [
        "Segment Results", DURATION, DATES, YEARS, row("Revenue", 11, 9, 33, 27)])
    assert not cells


def test_conflicting_scales_across_same_table_block_all_cells(monkeypatch):
    cells, issues = scan(monkeypatch, [TITLE, SCALE, DURATION], [
        TITLE + " (continued)", "(in USD millions)", DATES, YEARS, row("Revenue", 11, 9, 33, 27)])
    assert not cells
    assert issues == {"單位錯"}


def test_revenue_composition_proves_unusual_total(monkeypatch):
    cells, issues = scan(monkeypatch, [TITLE, SCALE, DURATION, DATES, YEARS, "Revenue:",
        row("Subscription and support", 10, 8, 30, 24),
        row("Term licenses", 1, 1, 3, 3),
        row("Total subscription revenue", 11, 9, 33, 27),
        "Cost of revenue"])
    assert not issues
    assert cells[-1].value == Decimal(33000)
    assert len(cells[-1].proof["component_rows"]) == 2


def test_subscription_subtotal_before_other_business_is_rejected(monkeypatch):
    cells, _ = scan(monkeypatch, [TITLE, SCALE, DURATION, DATES, YEARS, "Revenue:",
        row("Cloud subscriptions", 10, 8, 30, 24), row("Term subscriptions", 1, 1, 3, 3),
        row("Total subscription revenue", 11, 9, 33, 27),
        row("Services", 5, 4, 15, 12), "Cost of revenue"])
    assert not cells


def test_duplicate_period_columns_do_not_reconcile(monkeypatch):
    cells, issues = scan(monkeypatch, [TITLE, SCALE, DURATION, DATES,
        f"{2023:>64}{2024:>14}{2024:>14}{2024:>14}", row("Revenue", 11, 9, 33, 27)])
    assert not cells
    assert "表頭對齊" in issues
