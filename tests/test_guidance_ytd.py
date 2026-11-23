from datetime import date
from decimal import Decimal

from benchmarks.guidance_arithmetic import FigureRef
from benchmarks.guidance_ytd import Cell, Vintage, resolve


def make_cell(doc, quarter, amount, multiplier=1000, cumulative=False):
    tag = f"{doc}:p0001"
    ref = FigureRef(document=doc, block=tag, quote=str(amount), tabular=True,
                    unit_block=tag, unit_quote="(in USD thousands)")
    quarters = tuple(range(1, quarter + 1)) if cumulative else (quarter,)
    return Cell(ref, "Consolidated statements of operations", "period", "Revenue", 1, cumulative,
                multiplier, Decimal(amount * 1000), "2024-10-31T12:00:00Z", "https://issuer.test/",
                2025, "2024-10-31", quarters)


def test_unique_explicit_ytd_beats_quarteral_model_references():
    from types import SimpleNamespace
    doc = SimpleNamespace(id="q3")
    quarters = {"q3": Vintage(date(2024, 10, 31), 2025, 3)}
    correct = make_cell("q3", 3, 900, cumulative=True)
    scan = {"q3": ([make_cell("q3", 3, 300), correct], set())}
    result, reason, _ = resolve(doc, quarters, scan, [], {}, {"q3"})
    assert result == [correct] and reason is None


def test_conflicting_ytd_yields_explicit_gap():
    from types import SimpleNamespace
    doc = SimpleNamespace(id="q3")
    quarters = {"q3": Vintage(date(2024, 10, 31), 2025, 3)}
    scan = {"q3": ([make_cell("q3", 3, 900, cumulative=True),
                    make_cell("q3", 3, 950, cumulative=True)], set())}
    result, reason, _ = resolve(doc, quarters, scan, [], {}, {"q3"})
    assert not result and reason == "口徑不符"


def test_quarter_fallback_covers_whole_vintage_without_overlap():
    from types import SimpleNamespace
    doc = SimpleNamespace(id="q3")
    quarters = {f"q{q}": Vintage(date(2024, q + 1, 1), 2025, q) for q in (1, 2, 3)}
    slots = {name: make_cell(name, period.quarter, 200 + period.quarter) for name, period in quarters.items()}
    scans = {name: ([cell], set()) for name, cell in slots.items()}
    blocks = {cell.ref.block: {"text": f"(in USD thousands) Revenue {cell.ref.quote}"} for cell in slots.values()}
    one, two, three = (slots[f"q{i}"].ref for i in (1, 2, 3))
    for references in ([two, three], [one, two, two, three]):
        result, reason, _ = resolve(doc, quarters, scans, references, blocks, set(quarters))
        assert not result and reason == "缺季或重疊"
    result, reason, _ = resolve(doc, quarters, scans, [one, two, three], blocks, set(quarters))
    assert reason is None and sum(cell.value for cell in result) == 606000
    _, reason, _ = resolve(doc, quarters, scans, [one, two, three], blocks, {"q1", "q2"})
    assert reason == "期間選錯"
    scans["q3"] = ([make_cell("q3", 3, 203, 1000000)], set())
    _, reason, _ = resolve(doc, quarters, scans, [one, two, three], blocks, set(quarters))
    assert reason == "單位錯"
