"""Read a complete issuer HTML release and verify the model's source locations."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from html.parser import HTMLParser
import re
from urllib.parse import quote, urldefrag, urlsplit

from pydantic import Field, model_validator

from .financial_units import UnitSource, common_unit_label, declaration_factors, read_units
from .revision_bridge import (
    _FISCAL_QUARTER, _GUIDANCE_CONTEXT, _matches_period, _NOT_NEW, _OFF_SCOPE, _ONE_SIDED, _SENTENCE_BREAK,
)
from .schema import MetricKey, Nonempty, Schema


FILING_SELECTION_PROMPT = (
    "Read the complete archived issuer release, using only the supplied evidence. Locate its current, companywide "
    "quarterly revenue outlook, range, or preliminary point for the exact target fiscal quarter. The issuer's "
    "reporting convention is USD US GAAP consolidated unless the document identifies a different basis. "
    "Return no selection for a one-sided indication, reported actual, segment, annual outlook, or if the target "
    "quarter is unsupported. Do not reconstruct an implied forecast by subtraction. Cite the IDs that show why. "
    "For a usable selection, choose amount_ref carrying the stated range or point and context_ref from the same "
    "release carrying that fiscal quarter. For prose use null header_ref and column. For a table, choose the "
    "header row in the same table that identifies the current column, or its attached outlook title if the "
    "table has one value column and no header. Use the zero-based value column after the metric label. "
    "Prefer the detailed outlook row when the headline omits a disclosed tolerance. "
    "Use actual block IDs. Leave numerical extraction and arithmetic to the verifier."
)


class FilingSelection(Schema):
    amount_ref: Nonempty
    context_ref: Nonempty
    header_ref: Nonempty | None
    column: int | None = Field(ge=0)

    @model_validator(mode="after")
    def column_has_header(self):
        if (self.header_ref is None) != (self.column is None):
            raise ValueError("表格引用須同時指定表頭和數值欄")
        return self


class FilingExtraction(Schema):
    selection: FilingSelection | None
    evidence_ids: list[Nonempty]
    reason: Nonempty


_VOID = set("area base br col embed hr img input link meta param source track wbr".split())
_OMIT = set("head script style nav footer svg template noscript".split())
_BOUNDARIES = set("address article blockquote br dd div dl dt h1 h2 h3 h4 h5 h6 header hr li p pre section".split())
_METRIC = re.compile(r"(?:(?:total|net|consolidated)\s+)*(?:revenues?|net sales|sales)(?:\s*\(\s*\d+\s*\)|[*†]+)?$", re.I)
_REVENUE = r"\b(?:revenues?|net sales)\b"
_FORWARD = re.compile(
    rf"{_REVENUE}\s+(?:is\s+)?(?:guidance|outlook|forecast|expect(?:ed|ation)|will be|to be)\b"
    rf"|\b(?:expects?|expected|forecasts?|preliminary|estimates?|guidance for|outlook for|anticipates?)\b[^,;]{{0,88}}{_REVENUE}",
    re.I,
)
_PRIOR = r"(?:(?:its|our|the company[’']s|the|management[’']s)\s+)?(?:prior|previous(?:ly)?)\b"
_PRIOR_COMPARISON = re.compile(
    rf"\s*,?\s*(?:which\s+(?:is|was)\s+)?(?:above|below|lower than|higher than|"
    rf"up from|down from|versus|vs\.?|compared\s+(?:with|to)|relative to|from)\s+"
    rf"(?:the\s+(?:(?:high|low|upper|lower)\s+end|midpoint)\s+of\s+)?(?:{_PRIOR}|"
    r"(?:earlier\s+)?(?:guidance|outlook|expectations?)\b)", re.I,
)
_CURRENT_TRANSITION = re.compile(r"(?:,\s*(?:but\s+)?|\s+(?:but|and)\s+)\s*(?=now\b)", re.I)
_CURRENCY_CELL = re.compile(r"^(?:USD|US\$|\$)$", re.I)
_HEADER_TERMS = re.compile(r"\b(?:results|gaap|revenue outlook|low end|high end)\b", re.I)
_ANNUAL_HEADER = re.compile(r"\b(?:FY\s*\d{2,4}|20\d{2}\s+(?:results|guidance|outlook)|fiscal year)\b", re.I)
_FISCAL_YEAR_LABEL = re.compile(r"\b(?:FY\s*['’]?\d{2,4}|20\d\d)\b", re.I)
_TITLE_TAGS = {"b", "div", "h1", "h2", "h3", "h4", "h5", "h6", "p", "strong"}


@dataclass
class _Element:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Element("")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Element(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _omitted(node):
    return (node.tag in _OMIT or "hidden" in node.attrs or node.attrs.get("aria-hidden") == "true"
            or re.search(r"(?:^|;)\s*display\s*:\s*none\b", node.attrs.get("style") or "", re.I))


def _normalize(text):
    return " ".join(text.replace("\u200b", "").replace("\u00ad", "").split())


def _text(node):
    if isinstance(node, str):
        return node
    if _omitted(node):
        return ""
    if node.tag in _VOID:
        return " " if node.tag in {"br", "hr"} else ""
    value = "".join(_text(child) for child in node.children)
    return f" {value} " if node.tag in _BOUNDARIES else value


def _descendants(node, tag):
    for child in node.children:
        if isinstance(child, str) or _omitted(child):
            continue
        if child.tag == tag:
            yield child
        else:
            yield from _descendants(child, tag)


def _cell_extent(cell, name):
    value = cell.attrs.get(name) or "1"
    return min(1000, max(1, int(value))) if value.isdecimal() and len(value) <= 4 else 1


def _table_cells(row, occupied, row_index):
    cells, spans = [], []
    start, column = None, 0
    for cell in row.children:
        if isinstance(cell, str) or cell.tag not in {"th", "td"} or _omitted(cell):
            continue
        width, height = (_cell_extent(cell, name) for name in ("colspan", "rowspan"))
        while any(occupied.get(slot, 0) > row_index for slot in range(column, column + width)):
            column += 1
        span = [column, column + width]
        if height > 1:
            occupied.update({slot: row_index + height for slot in range(*span)})
        column += width
        value = _normalize(_text(cell))
        if not value:
            continue
        if start and re.match(r"\(?\d", value):
            marker, marker_span = start
            cells.append(f"{marker}{value}" if marker.endswith("$") else f"{marker} {value}")
            spans.append([marker_span[0], span[1]])
            start = None
            continue
        if start:
            marker, marker_span = start
            cells.append(marker)
            spans.append(marker_span)
            start = None
        if _CURRENCY_CELL.fullmatch(value):
            start = (value, span)
        else:
            cells.append(value)
            spans.append(span)
    if start:
        marker, marker_span = start
        cells.append(marker)
        spans.append(marker_span)
    return cells, spans


def parse_filing(html: str, *, document_id: str) -> list[dict]:
    """Produce ordered, source-addressable text and rows without subject-matter filtering."""
    tree = _Tree()
    tree.feed(html)
    tree.close()
    blocks, buffer = [], []
    table_counter = 0

    def append(text, *, table=None, cells=None, cell_spans=None, table_title_refs=()):
        if text:
            block = {"id": f"{document_id}:p{len(blocks) + 1:04d}", "text": text,
                     "kind": "row" if table is not None else "text", "table": table, "cells": cells}
            if cell_spans is not None:
                block["cell_spans"] = cell_spans
            if table_title_refs:
                block["table_title_refs"] = list(table_title_refs)
            blocks.append(block)
            return block["id"]
        return None

    def flush():
        append(_normalize("".join(buffer)))
        buffer.clear()

    def visit(node, preceding_title=None):
        nonlocal table_counter
        if isinstance(node, str):
            buffer.append(node)
            return
        if _omitted(node):
            return
        if node.tag == "table" and next(_descendants(node, "table"), None) is None:
            flush()
            table_counter += 1
            titles = [preceding_title] if preceding_title else []
            for caption in _descendants(node, "caption"):
                ref = append(_normalize(_text(caption)))
                if ref:
                    titles.append(ref)
            occupied = {}
            for row_index, row in enumerate(_descendants(node, "tr")):
                cells, spans = _table_cells(row, occupied, row_index)
                append(" | ".join(cells), table=table_counter, cells=cells, cell_spans=spans, table_title_refs=titles)
            return
        boundary = node.tag in _BOUNDARIES or node.tag in {"td", "th"}
        if boundary:
            flush()
        title = None
        for child in node.children:
            if isinstance(child, str) and not child.strip():
                visit(child)
                continue
            before = len(blocks)
            visit(child, title)
            title = None
            if isinstance(child, _Element) and child.tag in _TITLE_TAGS and len(blocks) == before + 1:
                block = blocks[-1]
                text = block["text"]
                if block["kind"] == "text" and len(text) <= 160 and (
                    declaration_factors(text) or (_FISCAL_QUARTER.search(text) and _GUIDANCE_CONTEXT.search(text))
                ):
                    title = block["id"]
        if boundary:
            flush()

    visit(tree.root)
    flush()
    return blocks


def _instant(value):
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def _source_url(url):
    try:
        parsed = urlsplit(url)
        return bool(parsed.scheme == "https" and parsed.hostname and not (parsed.username or parsed.password))
    except (TypeError, ValueError):
        return False


def _visible_documents(documents, event_at, as_of):
    visible = []
    for document in documents:
        published, obtained = (_instant(document[field]) for field in ("published_at", "obtained_at"))
        if (published.utcoffset() is not None and obtained.utcoffset() is not None
                and event_at <= published <= obtained <= as_of and _source_url(document["source_url"])):
            visible.append(document)
    return visible


def filing_citation(document, block, *, anchor=None):
    anchor = anchor or next((text for text in (block.get("cells") or []) if len(text) >= 12), block["text"])
    fragment = anchor[:135].rsplit(" ", 1)[0] if len(anchor) > 135 else anchor
    source = document["source_url"]
    return {"id": block["id"], "document_id": document["id"], "quote": block["text"], "source_url": source,
            "link": f"{urldefrag(source)[0]}#:~:text={quote(fragment, safe='').replace('-', '%2D')}"}


def _period(text, key, label):
    if not _FISCAL_QUARTER.search(text):
        return False
    if _matches_period(text, key.period_end, label):
        return True
    return bool(label and _FISCAL_QUARTER.search(label) and _FISCAL_YEAR_LABEL.search(label)
                and re.search(rf"(?<!\w){re.escape(label)}(?!\w)", text, re.I))


def _ordinals(text):
    words = {"first": 1, "second": 2, "third": 3, "fourth": 4}
    return {int(digit) if digit else words[term.lower()] for digit, term in re.findall(
        r"\bq([1-4])\b|\b(first|second|third|fourth)\s+(?:fiscal\s+)?quarter\b", text, flags=re.I,
    )}


def _prose_interval(text, context, key, label, amount_ref):
    readings = []
    for sentence in _SENTENCE_BREAK.split(text):
        before, *after = _CURRENT_TRANSITION.split(sentence, maxsplit=1)
        current = after[0] if after and re.search(_PRIOR, before, re.I) else sentence
        statement = _PRIOR_COMPARISON.split(current, maxsplit=1)[0].strip().rstrip(",")
        if (not _FORWARD.search(statement) or _NOT_NEW.search(statement) or _OFF_SCOPE.search(statement)
                or re.search(_PRIOR, statement, re.I)):
            continue
        if not (_period(statement, key, label) or _period(context, key, label)):
            continue
        qualifiers, expected = _ordinals(statement), _ordinals(label or "") or _ordinals(context)
        if qualifiers and expected and qualifiers != expected:
            continue
        if _FISCAL_QUARTER.search(statement) and re.search(r"\b20\d{2}\b", statement) and not _period(statement, key, label):
            continue
        if not _ONE_SIDED.search(statement):
            readings.append((statement, read_units(statement, amount_ref=amount_ref, currency=key.currency)))
    return readings


def _header_like(row):
    text = row["text"]
    return not re.search(r"\$\s*\d|\bUSD\s+\d|\d\s*%", text, re.I) and bool(
        _FISCAL_QUARTER.search(text) or _GUIDANCE_CONTEXT.search(text) or _HEADER_TERMS.search(text)
        or _NOT_NEW.search(text) or _OFF_SCOPE.search(text) or declaration_factors(text)
    )


def _header_value(row, value_span):
    overlaps = [(text, (left, right)) for text, (left, right) in zip(row["cells"], row.get("cell_spans", []))
                if left < value_span[1] and right > value_span[0]]
    if len(overlaps) == 1 and overlaps[0][1][0] <= value_span[0] and overlaps[0][1][1] >= value_span[1]:
        return overlaps[0][0]
    return None


def _header_chain(blocks, amount, header, column):
    if not amount.get("cell_spans") or not header.get("cell_spans"):
        headings = header["cells"][-(len(amount["cells"]) - 1):]
        return ([(header, headings[column])], [header]) if len(headings) == len(amount["cells"]) - 1 else ([], [])
    rows = [row for row in blocks if row["table"] == amount["table"]]
    row_index = rows.index(header)
    selected = amount["cell_spans"][column + 1]
    if not _header_like(header) or _header_value(header, selected) is None:
        return [], []
    first = row_index
    while first and _header_like(rows[first - 1]):
        first -= 1
    last = row_index + 1
    while rows[last] is not amount and _header_like(rows[last]):
        last += 1
    for row in rows[last:rows.index(amount)]:
        if _header_like(row):
            return [], []
    group = rows[first:last]
    return [(row, value) for row in group if (value := _header_value(row, selected))], group


def _left_labels(rows, amount):
    first_value_start = amount.get("cell_spans", [[0, 1], [1, 2]])[1][0]
    return [(row, text) for row in rows for text, (_, right) in zip(row["cells"], row.get("cell_spans", []))
            if right <= first_value_start]


def _unit_sources(amount, column, headers, group, titles):
    sources = [UnitSource(row["id"], value, "column_header") for row, value in headers if row["kind"] == "row"]
    sources.extend(UnitSource(row["id"], text, "shared_left_label") for row, text in _left_labels(group, amount)
                   if common_unit_label(text))
    sources.extend(UnitSource(row["id"], row["text"], "table_title") for row in titles)
    sources.append(UnitSource(amount["id"], amount["cells"][0], "row_label"))
    if not amount.get("cell_spans"):
        return sources, False
    value_left, value_right = amount["cell_spans"][column + 1]
    ambiguous = any(left < value_right and right > value_left and (left > value_left or right < value_right)
                    and declaration_factors(text) for row in group
                    for text, (left, right) in zip(row["cells"], row.get("cell_spans", [])))
    return sources, ambiguous


def _table_interval(blocks, amount, header, context, column, key, label):
    if amount["kind"] != "row" or header["id"] >= amount["id"]:
        return None, []
    metric = amount["cells"][0]
    metric_label = re.sub(r"\s*\(([^()]*)\)\s*$", lambda m: "" if declaration_factors(m[1]) else m[0], metric)
    if not _METRIC.fullmatch(metric_label) or _OFF_SCOPE.search(metric):
        return None, []
    values = amount["cells"][1:]
    if column >= len(values):
        return None, []
    titles = [row for row in blocks if row["id"] in amount.get("table_title_refs", [])]
    if header["kind"] == "row" and amount["table"] == header["table"]:
        headers, group = _header_chain(blocks, amount, header, column)
    elif header in titles and len(values) == 1:
        headers, group = [(header, header["text"])], []
    else:
        return None, []
    headings = [value for _, value in headers]
    if not headings or any(_NOT_NEW.search(value) or _OFF_SCOPE.search(value) for value in headings):
        return None, headers
    quarter_headings = [value for value in headings if _FISCAL_QUARTER.search(value)]
    if any(not _period(value, key, label) for value in quarter_headings):
        return None, headers
    if any(_ANNUAL_HEADER.search(value) and not _FISCAL_QUARTER.search(value)
           and not (quarter_headings and _FISCAL_YEAR_LABEL.fullmatch(value)) for value in headings):
        return None, headers
    if not quarter_headings and not _period(context, key, label):
        return None, headers
    scoped_guidance = [text for _, text in _left_labels(group, amount) if _period(text, key, label) and not _NOT_NEW.search(text)]
    if not (any(_GUIDANCE_CONTEXT.search(value) for value in [*headings, *scoped_guidance]) or (_GUIDANCE_CONTEXT.search(context)
            and any(re.fullmatch(r"(?:US |U\.S\. )?GAAP|Approximately", value, re.I) for value in headings))):
        return None, headers
    value = values[column]
    if _ONE_SIDED.search(value) or _NOT_NEW.search(value) or _OFF_SCOPE.search(value) or value.lstrip().startswith(("<", ">", "≤", "≥")):
        return None, headers
    sources, ambiguous = _unit_sources(amount, column, headers, group, titles)
    return read_units(value, amount_ref=amount["id"], currency=key.currency, sources=sources,
                      tabular=True, ambiguous=ambiguous), headers


def check_filing_revision(*, key, incumbent, event_at, as_of, documents, selection, fiscal_label=None):
    key = MetricKey.model_validate(key)
    estimate = Decimal(incumbent["amount"] if isinstance(incumbent, dict) else incumbent)
    event_at, as_of = map(_instant, (event_at, as_of))
    audit = {"status": "blocked", "remaining_delta": None, "new_low": None, "new_high": None,
             "revised": format(estimate, "f"), "evidence_ids": [], "citations": [], "reason": ""}

    def block(reason):
        return {**audit, "reason": reason}

    if (key.metric, key.duration, key.scope, key.basis, key.currency) != ("revenue", "quarter", "consolidated", "US_GAAP", "USD"):
        return block("完整公告試算只接受美元、美國 GAAP 與合併單季營收。")
    if event_at.utcoffset() is None or as_of.utcoffset() is None or event_at > as_of:
        return block("事件與研究截止時間須可核對且含時區。")
    if not estimate.is_finite() or estimate < 0:
        return block("封存現估須為非負營收。")
    if selection is None:
        return block("未找到可核對的同季營收指引。")
    selection = FilingSelection.model_validate(selection)
    refs = list(dict.fromkeys(ref for ref in (selection.amount_ref, selection.context_ref, selection.header_ref) if ref))
    visible = _visible_documents(documents, event_at, as_of)
    matching = []
    for document in visible:
        blocks = {b["id"]: b for b in document["blocks"]}
        if all(ref in blocks for ref in refs):
            matching.append((document, blocks))
    if len(matching) != 1:
        return block("財季、表頭與金額須來自同一份點時可見公告。")
    document, blocks = matching[0]
    amount, context = blocks[selection.amount_ref], blocks[selection.context_ref]["text"]
    reading, headers, statement = None, [], None
    if selection.column is None:
        if amount["kind"] == "text":
            candidates = _prose_interval(amount["text"], context, key, fiscal_label, amount["id"])
            verified = {(result.low, result.high): (span, result) for span, result in candidates if result.reason is None}
            failed = [result for _, result in candidates if result.reason and result.sources]
            if len(verified) == 1 and not failed:
                statement, reading = next(iter(verified.values()))
            elif failed:
                reading = failed[0]
    else:
        reading, headers = _table_interval(document["blocks"], amount, blocks[selection.header_ref], context,
                                           selection.column, key, fiscal_label)
    refs.extend(row["id"] for row, _ in headers)
    anchors = {row["id"]: text for row, text in headers}
    if reading:
        sources = [{"id": source.id, "scope": source.scope, "quote": source.quote,
                    "link": filing_citation(document, blocks[source.id], anchor=source.quote)["link"]}
                   for source in reading.sources]
        refs.extend(source["id"] for source in sources)
        anchors[amount["id"]] = reading.raw_text
        audit["unit_proof"] = {"raw_text": reading.raw_text, "currency": key.currency if not reading.reason else None,
                               "multipliers": list(reading.multipliers), "sources": sources,
                               "normalized_low": format(reading.low, "f") if reading.low is not None else None,
                               "normalized_high": format(reading.high, "f") if reading.high is not None else None}
        if selection.column is not None:
            audit["unit_proof"]["column_span"] = amount["cell_spans"][selection.column + 1] if amount.get("cell_spans") else None
    audit["evidence_ids"] = list(dict.fromkeys(refs))
    audit["citations"] = [filing_citation(document, blocks[ref], anchor=anchors.get(ref)) for ref in audit["evidence_ids"]]
    if reading is None:
        return block("所選原文未能唯一核對同季公司營收點估或完整區間。")
    if reading.reason:
        audit["block_stage"] = "units"
        return block(reading.reason)
    low, high = reading.low, reading.high
    if selection.column is not None:
        audit["location"] = {"amount_ref": amount["id"], "column": selection.column,
                             "header_refs": [row["id"] for row, _ in headers]}
    else:
        audit["location"] = {"amount_ref": amount["id"], "value_span": statement}
    revised = min(max(estimate, low), high)
    delta = revised - estimate
    return {**audit, "status": "eligible" if delta else "noop", "remaining_delta": format(delta, "f"),
            "new_low": format(low, "f"), "new_high": format(high, "f"), "revised": format(revised, "f"),
            "reason": "現版預估在指引區間外，試算至最近邊界。" if delta else "現版預估位於已核對區間內，維持原估。"}
