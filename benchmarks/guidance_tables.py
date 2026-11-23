"""Bind printed table headings to fiscal columns and audit complete revenue aggregates."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
import re

from benchmarks import guidance_arithmetic as bench
from benchmarks import guidance_ytd as previous
from research_app.financial_units import UnitSource, declaration_factors, read_units

TITLE = previous.TITLE
OTHER_TABLE = re.compile(
    r"^(?:table\s+\d+\b.*|.*\b(?:balance sheets?|cash flows|stockholders.? equity|"
    r"shareholders.? equity|segment results|segment information|non-gaap reconciliation)\b.*)$", re.I
)
REVENUE_SECTION = re.compile(r"^\s*(?:net\s+)?revenues?\s*:?\s*$", re.I)
END_REVENUE = re.compile(r"^\s*(?:total\s+)?(?:cost of (?:net\s+)?revenues?|cost of sales|gross profit)\b", re.I)
STANDARD_REVENUE = re.compile(r"^\s*(?:total\s+)?(?:(?:net\s+)?revenues?|net\s+sales)(?:\s*\.{2,}\s*|\s{2,})(?=[$€£¥\d])", re.I)
SUBTOTAL = re.compile(r"^\s*(?:total\s+|subtotal\b)", re.I)
CONTINUED = re.compile(r"\b(?:continued|continuation)\b", re.I)


@dataclass(frozen=True)
class Line:
    page: int
    number: int
    text: str

    def link(self, document):
        return {"block": f"{document.id}:p{self.page:04d}", "line": self.number,
                "quote": self.text.strip(), "url": f"{document.source_url}#page={self.page}"}


@dataclass(frozen=True)
class Table:
    heading: Line
    lines: tuple[Line, ...]


@dataclass(frozen=True)
class Cell:
    document: str
    block: str
    raw: str
    value: Decimal
    multiplier: int
    quarters: tuple[int, ...]
    proof: dict


def pages_of(document):
    body = (bench.ROOT / document.path).read_bytes()
    if sha256(body).hexdigest() != document.sha256:
        raise ValueError(f"archive hash mismatch: {document.id}")
    pages = []
    marker = re.compile(r"^\[PDF page (\d+)\]\s*$")
    for line in body.decode().splitlines():
        if header := marker.match(line):
            pages.append((int(header[1]), []))
        elif pages and line.strip():
            number, lines = pages[-1]
            lines.append(Line(number, len(lines) + 1, line))
    return pages


def same_table_boundary(previous_lines, following):
    """Allow a split printed heading or an explicitly continued statement."""
    if not following:
        return False
    incoming = following[:5]
    if any(OTHER_TABLE.match(line.text.strip()) for line in incoming):
        return False
    if any(TITLE.search(line.text) and CONTINUED.search(line.text) for line in incoming):
        return True
    if len(previous_lines) > 10:
        return False
    # A title followed only by its units, date headings or a footer can continue on the next page.
    return any(previous.DURATION.search(line.text) or declaration_factors(line.text) or
               len(previous.YEAR.findall(line.text)) >= 2 for line in incoming)


def tables(pages):
    open_title, buffered = None, []
    for _, rows in pages:
        if open_title and not same_table_boundary(buffered, rows):
            yield Table(open_title, tuple(buffered))
            open_title, buffered = None, []
        for line in rows:
            if open_title and TITLE.search(line.text) and CONTINUED.search(line.text):
                buffered.append(line)
                continue
            if TITLE.search(line.text) or OTHER_TABLE.match(line.text.strip()):
                if open_title:
                    yield Table(open_title, tuple(buffered))
                open_title, buffered = (line if TITLE.search(line.text) else None), []
            elif open_title:
                buffered.append(line)
    if open_title:
        yield Table(open_title, tuple(buffered))


def amount_slots(line):
    matches = list(previous.AMOUNT.finditer(line.text))
    if len(matches) not in {2, 4}:
        return []
    if re.search(r"\(\s*[\d,]+\s*\)|[-−]\s*[0-9]", line.text[matches[0].start():]):
        return []
    return matches


def period_columns(header, amounts, vintage):
    """Match duration bands and current/prior years using their printed positions."""
    n = len(amounts)
    def center(match):
        return (match.start() + match.end()) / 2

    positions = [center(match) for match in amounts]
    cut = (positions[1] + positions[2]) / 2 if n == 4 else None
    for slot, year_line in enumerate(header):
        years = list(previous.YEAR.finditer(year_line.text))
        if len(years) != n:
            continue
        if cut is not None and ([center(year) < cut for year in years] != [True, True, False, False]):
            continue
        context = header[max(0, slot - 5):slot + 1]
        durations = {}
        for line in context:
            for match in previous.DURATION.finditer(line.text):
                band = 0 if cut is None or center(match) < cut else 1
                durations.setdefault(band, []).append(match)
        result = []
        for band in range(n // 2):
            matches = durations.get(band, [])
            left = max(0, matches[0].start() - 4) if matches else max(0, int(positions[band * 2]) - 12)
            right = max(matches[0].end() + 2 if matches else 0, int(cut)) if band == 0 and cut is not None else None
            printed_band = " ".join(line.text[left:right].strip() for line in context)
            if not matches:
                # A duration may itself occupy two printed lines in the same column band.
                matches = list(previous.DURATION.finditer(printed_band))
            if len(matches) != 1 or not previous.date_supported(printed_band, vintage):
                break
            match, = matches
            duration, cumulative = previous.group_duration(match)
            expected_year = (vintage.fiscal_year if "fiscal" in printed_band.casefold() and
                             not previous.DATES.search(printed_band) else vintage.report_end.year)
            if [int(year[0]) for year in years[band * 2:band * 2 + 2]] != [expected_year, expected_year - 1]:
                break
            if cumulative and duration != vintage.quarter:
                continue
            if match["single"] and {"first": 1, "second": 2, "third": 3}[match["single"].lower()] != vintage.quarter:
                continue
            quarters = tuple(range(1, duration + 1)) if cumulative else (vintage.quarter,)
            result.append((band * 2, quarters, printed_band))
        else:
            if result:
                return result, context
    return [], []


def revenue_lines(table):
    for line in table.lines:
        if STANDARD_REVENUE.match(line.text):
            yield line, []
    # A differently named row can stand for all revenue only when it closes the
    # entire consolidated revenue section and its arithmetic holds in every column.
    lines = table.lines
    starts = [i for i, row in enumerate(lines) if REVENUE_SECTION.match(row.text)]
    for start in starts:
        stop = next((i for i in range(start + 1, len(lines)) if END_REVENUE.match(lines[i].text)), None)
        if stop is None:
            continue
        section = lines[start + 1:stop]
        if len(section) < 3 or len(section) > 12:
            continue
        *components, aggregate = section
        amounts = amount_slots(aggregate)
        if STANDARD_REVENUE.match(aggregate.text) or not SUBTOTAL.match(aggregate.text) or not amounts:
            continue
        if any(SUBTOTAL.match(row.text) or len(amount_slots(row)) != len(amounts) for row in components):
            continue
        subtotal_rows = [amount_slots(row) for row in components]
        totals = [Decimal(value[0].replace(",", "")) for value in amounts]
        if all(sum(Decimal(values[i][0].replace(",", "")) for values in subtotal_rows) == total
               for i, total in enumerate(totals)):
            yield aggregate, components


def monetary_unit(text):
    # Keep declarations applying to money and exclude separately labeled share counts.
    return " ".join(clause for clause in text.split(",")
                    if not re.match(r"\s*(?:(?:except|and)\s+)?(?:weighted average\s+|per\s+)?shares?\b",
                                    clause, re.I))


def amount_and_unit(document, line, raw, scope):
    labels = [(entry, monetary_unit(entry.text)) for entry in scope if declaration_factors(entry.text)]
    labels = [(entry, text) for entry, text in labels if declaration_factors(text)]
    unit_lines = [entry for entry, _ in labels]
    factors = set().union(*(declaration_factors(text) for _, text in labels))
    if len(factors) != 1:
        return None, unit_lines, None, None
    money = next((entry for entry in scope if previous.MONEY_MARK.search(entry.text) and
                  amount_slots(entry)), None)
    sources = [UnitSource(f"{document.id}:p{entry.page:04d}", text, "table") for entry, text in labels]
    if money:
        # The arithmetic reader accepts a composite unit context. The audit retains each exact line separately.
        unit, text = labels[0]
        sources.append(UnitSource(f"{document.id}:p{unit.page:04d}", text + " " + money.text, "table"))
    parsed = read_units(raw, amount_ref=f"{document.id}:p{line.page:04d}", currency="USD",
                        sources=tuple(sources), tabular=True)
    return (parsed.low if not parsed.reason else None), unit_lines, money, next(iter(factors))


def scan_document(document, vintage):
    if document.content_type != "text/plain":
        return [], {"引文不足"}
    cells, errors = [], set()
    for table in tables(pages_of(document)):
        for line, components in revenue_lines(table):
            position = table.lines.index(line)
            amounts = amount_slots(line)
            columns, heading_refs = period_columns(table.lines[:position], amounts, vintage) if amounts else ([], [])
            if not columns:
                errors.add("表頭對齊")
                continue
            for column, quarters, heading in columns:
                raw = amounts[column][0]
                value, units, money, factor = amount_and_unit(document, line, raw, table.lines[:position + 1])
                if value is None:
                    errors.add("單位錯")
                    continue
                proof = {"document": document.id, "published_at": document.published_at.isoformat(),
                         "report_end": vintage.report_end.isoformat(), "fiscal_year": vintage.fiscal_year,
                         "quarters": list(quarters), "header": heading, "table": table.heading.link(document),
                         "heading_sources": [entry.link(document) for entry in heading_refs],
                         "unit_sources": [entry.link(document) for entry in units],
                         "currency_source": money.link(document) if money else None,
                         "row": line.link(document), "column": column + 1, "value": str(value),
                         "raw": raw, "multiplier": factor,
                         "component_rows": [row.link(document) for row in components]}
                cells.append(Cell(document.id, proof["row"]["block"], raw, value, factor, quarters, proof))
    return cells, errors


def located(ref, cell, blocks):
    if ref.document != cell.document or ref.block != cell.block:
        return False
    tokens = previous.AMOUNT.findall(ref.quote)
    if tokens != [cell.raw]:
        return False
    try:
        low, high = bench.read_figure(ref, blocks)
    except ValueError:
        return False
    return low == high == cell.value


def resolve(target, vintage_doc, vintages, visible, scans, refs, blocks):
    candidates, issues = scans[vintage_doc.id]
    cumulative = [cell for cell in candidates if cell.quarters == tuple(range(1, target.quarter + 1))]
    if len(cumulative) == 1 and "單位錯" not in issues:
        return cumulative, None
    if len(cumulative) > 1:
        return [], "營收口徑"
    if issues & {"單位錯", "表頭對齊"}:
        return [], "單位錯" if "單位錯" in issues else "表頭對齊"
    single = []
    for ref in refs:
        if ref.document not in visible or vintages[ref.document].fiscal_year != target.fiscal_year:
            return [], "期間選錯"
        matches = [cell for cell in scans[ref.document][0] if len(cell.quarters) == 1 and located(ref, cell, blocks)]
        if len(matches) != 1:
            return [], "營收口徑"
        single.append(matches[0])
    if sorted(cell.quarters[0] for cell in single) != list(range(1, target.quarter + 1)):
        return [], "缺季或重疊"
    if len({cell.multiplier for cell in single}) != 1:
        return [], "單位錯"
    return single, None


ISSUE_REASONS = {
    "表頭對齊": "表格延續或累計期間與財年無法唯一對應至同一數值欄。",
    "營收口徑": "無法唯一證明該列是完整合併營收，或同期間存在多個候選。",
    "期間選錯": "缺少該財季的唯一公告，或引文在指定公告當時不可見。",
    "缺季或重疊": "無可驗證的累計欄，也未能以不重疊的單季完整涵蓋期間。",
    "單位錯": "所選財務表的美元幣別或金額倍率缺失、不一致或範圍不明。",
}


def revised(case, blocks, extraction, vintage_spec):
    vintages = {name: previous.Vintage(date.fromisoformat(row["report_end"]), row["fiscal_year"], row["quarter"])
                for name, row in vintage_spec.items()}
    scans = {doc.id: scan_document(doc, vintages[doc.id]) for doc in case.documents}
    groups = {}
    for candidate in extraction.figures:
        ref = bench.FigureRef.model_validate(candidate.model_dump(exclude={"name"}))
        groups.setdefault(candidate.name, []).append(ref)
    targets = {"prior_reported_in_period": 2, "reported_in_period": 3}
    values, errors, proofs, categories = {}, {}, {}, {}
    for name in bench.needed(case):
        refs = groups.get(name, [])
        if name not in targets:
            try:
                if not refs:
                    raise ValueError("figure not located")
                values[name] = bench.figure_value(name, refs, blocks)
            except ValueError as exc:
                errors[name] = str(exc)
            continue
        options = [doc for doc in case.documents if vintages[doc.id].quarter == targets[name]]
        if len(options) != 1:
            errors[name], categories[name] = ISSUE_REASONS["期間選錯"], "期間選錯"
            continue
        vintage_doc, = options
        visible = {doc.id for doc in case.documents if doc.obtained_at <= vintage_doc.obtained_at}
        cells, issue = resolve(vintages[vintage_doc.id], vintage_doc, vintages, visible, scans, refs, blocks)
        if issue:
            errors[name], categories[name] = ISSUE_REASONS[issue], issue
            continue
        proofs[name] = [cell.proof for cell in cells]
        values[name] = sum(cell.value for cell in cells)
    if not all(name in values for name in ("prior", *bench.REMAINDER[2:])):
        values = {name: value for name, value in values.items() if name not in bench.REMAINDER[2:]}
    output = {}
    if "new" in values:
        try:
            output = bench.compute(bench.GuidanceInputs.model_validate(values))
        except bench.ValidationError as exc:
            errors["inputs"] = str(exc)
    answers = {item: bench.render(bench.ITEM_KINDS[item], output[item]) if item in output else "unknown"
               for item in case.items}
    figures = [row for row in extraction.model_dump(mode="json")["figures"] if row["name"] not in targets]
    return {"answers": answers, "errors": errors, "categories": categories, "proofs": proofs, "figures": figures}
