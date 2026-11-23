"""Validate duration and fiscal vintage before passing revenue to the sealed arithmetic."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
import re

from benchmarks import guidance_arithmetic as bench
from research_app.financial_units import declaration_factors

TITLE = re.compile(r"\bconsolidated (?:statements? of (?:operations|earnings|income)|(?:results of|statements? of results of) operations)\b", re.I)
NEXT_TITLE = re.compile(r"\bconsolidated (?:balance sheets?|statements? of (?:cash flows|equity|financial position))\b", re.I)
DURATION = re.compile(
    r"(?P<n>three|six|nine)\s+months\s+ended"
    r"|(?:first\s+)?(?P<q>two|three)\s+quarters\s+(?:of|ended)"
    r"|(?P<single>first|second|third)\s+quarter\s+(?:of|ended)", re.I)
REVENUE = re.compile(r"^\s*(?P<label>(?:total\s+)?(?:(?:net\s+)?revenues?|net\s+sales))(?:\s+\.{2,})?\s{2,}(?P<data>.+)$", re.I)
AMOUNT = re.compile(r"(?<![\w.,])(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?(?![\w.,%])")
YEAR = re.compile(r"(?<!\d)20\d{2}(?!\d)")
MONEY_MARK = re.compile(r"[$€£¥]|\b(?:USD|CAD|EUR|GBP)\b", re.I)
DATES = re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2}\b", re.I)


@dataclass(frozen=True)
class Vintage:
    report_end: date
    fiscal_year: int
    quarter: int


@dataclass(frozen=True)
class Cell:
    ref: bench.FigureRef
    table: str
    header: str
    row: str
    column: int
    cumulative: bool
    multiplier: int
    value: Decimal
    published_at: str
    source_url: str
    fiscal_year: int
    report_end: str
    quarters: tuple[int, ...]


def groups_found(lines):
    for i, line in enumerate(lines):
        groups = list(DURATION.finditer(line))
        if not groups:
            continue
        for j in range(i, min(i + 4, len(lines))):
            years = [int(match[0]) for match in YEAR.finditer(lines[j])]
            if len(years) == len(groups) * 2:
                header = " ".join(part.strip() for part in lines[i:j + 1])
                return groups, years, header
    return (), (), ""


def group_duration(match):
    if match["q"]:
        return {"two": 2, "three": 3}[match["q"].lower()], True
    if match["single"]:
        return 1, False
    duration = {"three": 1, "six": 2, "nine": 3}[match["n"].lower()]
    return duration, duration != 1


def date_supported(header, vintage):
    if re.search(r"\bfiscal\b", header, re.I) and not DATES.search(header):
        return True
    normalized = " ".join(header.replace(".", "").casefold().split())
    endings = (vintage.report_end.strftime("%B").lower(), vintage.report_end.strftime("%b").lower())
    return any(re.search(rf"\b{month}\s+0?{vintage.report_end.day}\b", normalized) for month in endings)


def unit_evidence(lines, unit_index, row_index):
    first = lines[unit_index]
    if MONEY_MARK.search(first):
        return first.strip()
    # A currency mark on the first financial row can apply to this same table.
    for i in range(unit_index + 1, row_index + 1):
        if match := MONEY_MARK.search(lines[i]):
            return " ".join(part.strip() for part in lines[unit_index:i] + [lines[i][:match.end()]])
    return first.strip()


def scan_document(document, vintage, blocks, root=bench.ROOT):
    """Read printed layout, match period groups to actual columns and verify all literal references."""
    if document.content_type != "text/plain":
        return [], {"引文不足"}
    path = root / document.path
    text = path.read_text(encoding="utf-8")
    result, issues, tail = [], set(), []
    for page in re.split(r"(?m)(?=^\[PDF page \d+\]$)", text):
        marker = re.match(r"\[PDF page (\d+)\]", page)
        if not marker:
            continue
        number = int(marker[1])
        block = f"{document.id}:p{number:04d}"
        lines = page.splitlines()[1:]
        continuation = next((value for value in reversed(tail[-4:]) if TITLE.search(value)), None)
        tail = lines
        for index, line in enumerate(lines):
            row = REVENUE.match(line)
            if row is None:
                continue
            titles = [i for i, label in enumerate(lines[:index]) if TITLE.search(label) or NEXT_TITLE.search(label)]
            if titles and not TITLE.search(lines[titles[-1]]):
                continue
            if not titles and (not continuation or index > 25):
                continue
            start = titles[-1] if titles else 0
            table_title = lines[start].strip() if titles else continuation.strip()
            prefix = lines[start:index]
            period_groups, years, header = groups_found(prefix)
            amounts = AMOUNT.findall(row["data"])
            if not period_groups or len(amounts) != len(years):
                issues.add("引文不足")
                continue
            if not date_supported(header, vintage):
                issues.add("期間選錯")
                continue
            expected = vintage.fiscal_year if "fiscal" in header.casefold() and not DATES.search(header) else vintage.report_end.year
            units = [i for i in range(start, index) if declaration_factors(lines[i])]
            inferred_scales = set().union(*(declaration_factors(lines[i]) for i in units))
            if len(inferred_scales) != 1:
                issues.add("單位錯")
                continue
            unit = unit_evidence(lines, units[-1], index)
            for i, group in enumerate(period_groups):
                span, cumulative = group_duration(group)
                if years[i * 2:i * 2 + 2] != [expected, expected - 1]:
                    issues.add("期間選錯")
                    continue
                if cumulative and span != vintage.quarter:
                    continue
                if group["single"] and {"first": 1, "second": 2, "third": 3}[group["single"].lower()] != vintage.quarter:
                    continue
                raw = amounts[i * 2]
                # Identical displayed cells on one PDF page cannot be uniquely cited by this schema.
                if amounts.count(raw) != 1:
                    issues.add("引文不足")
                    continue
                ref = bench.FigureRef(document=document.id, block=block, quote=raw, tabular=True,
                                      unit_block=block, unit_quote=unit)
                try:
                    value, _ = bench.read_figure(ref, blocks)
                except ValueError:
                    issues.add("單位錯")
                    continue
                quarters = tuple(range(1, span + 1)) if cumulative else (vintage.quarter,)
                result.append(Cell(ref, table_title, header, line.strip(), i * 2 + 1, cumulative,
                                   next(iter(inferred_scales)), value, document.published_at.isoformat(),
                                   f"{document.source_url}#page={number}", vintage.fiscal_year,
                                   vintage.report_end.isoformat(), quarters))
    return result, issues


def matches_ref(cell, ref, blocks):
    if cell.ref.document != ref.document or cell.ref.block != ref.block:
        return False
    if len(AMOUNT.findall(ref.quote)) != 1 or AMOUNT.findall(ref.quote)[0] != cell.ref.quote:
        return False
    try:
        value, high = bench.read_figure(ref, blocks)
    except ValueError:
        return False
    return value == high == cell.value


def resolve(vintage_doc, vintages, scans, refs, blocks, visible):
    target = vintages[vintage_doc.id]
    direct = [cell for cell in scans[vintage_doc.id][0] if cell.cumulative and len(cell.quarters) == target.quarter]
    if len(direct) == 1:
        return direct, None, None
    if len(direct) > 1:
        return [], "口徑不符", "同財年與期間出現多個累計欄，無法確認唯一口徑"
    if "單位錯" in scans[vintage_doc.id][1]:
        return [], "單位錯", "累計表的幣別或單位無法核對"
    picked = []
    for ref in refs:
        vintage = vintages.get(ref.document)
        if ref.document not in visible or vintage is None or vintage.fiscal_year != target.fiscal_year:
            return [], "期間選錯", "單季引文在該版公告時點不可見或財年不符"
        possible = [cell for cell in scans[ref.document][0]
                    if len(cell.quarters) == 1 and matches_ref(cell, ref, blocks)]
        if len(possible) != 1:
            return [], "引文不足", "指定單季數值無法唯一定位至合併營收欄"
        picked.append(possible[0])
    covered = sorted(cell.quarters[0] for cell in picked)
    if covered != list(range(1, target.quarter + 1)):
        return [], "缺季或重疊", f"需完整且互不重疊地涵蓋第 1 至第 {target.quarter} 季，實際涵蓋 {covered}"
    if len({cell.multiplier for cell in picked}) != 1:
        return [], "單位錯", "單季來源的金額倍率不一致"
    return picked, None, None


def serialize(cell):
    from dataclasses import asdict
    data = asdict(cell)
    data["ref"] = cell.ref.model_dump(mode="json")
    data["value"] = str(cell.value)
    return data


def revised(case, blocks, extraction, vintage_spec):
    vintages = {name: Vintage(date.fromisoformat(row["report_end"]), row["fiscal_year"], row["quarter"])
                for name, row in vintage_spec.items()}
    scans = {doc.id: scan_document(doc, vintages[doc.id], blocks) for doc in case.documents}
    documents = {doc.id: doc for doc in case.documents}
    targets = {
        "prior_reported_in_period": [doc for doc in case.documents if vintages[doc.id].quarter == 2],
        "reported_in_period": [doc for doc in case.documents if vintages[doc.id].quarter == 3],
    }
    original = extraction.model_dump(mode="json")["figures"]
    preserved = [row for row in original if row["name"] not in targets]
    proofs, errors, categories = {}, {}, {}
    for name, choices in targets.items():
        if len(choices) != 1:
            errors[name] = "缺少唯一的公告時點"
            categories[name] = "期間選錯"
            continue
        vintage_doc, = choices
        refs = [bench.FigureRef.model_validate({key: val for key, val in row.items() if key != "name"})
                for row in original if row["name"] == name]
        visible = {key for key, doc in documents.items() if doc.obtained_at <= vintage_doc.obtained_at}
        cells, category, error = resolve(vintage_doc, vintages, scans, refs, blocks, visible)
        if error:
            errors[name], categories[name] = error, category
            continue
        proofs[name] = [serialize(cell) for cell in cells]
        preserved.extend({"name": name, **cell.ref.model_dump(mode="json")} for cell in cells)
    answers, legacy_errors = bench.harness_answers(case, blocks,
        bench.Extraction(figures=preserved, reason=extraction.reason))
    return {"answers": answers, "errors": legacy_errors | errors,
            "categories": categories, "proofs": proofs, "figures": preserved}
