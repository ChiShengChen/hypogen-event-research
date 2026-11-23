"""Layout-aware candidate verification. This module never reads the adjudication labels."""

from dataclasses import dataclass, asdict
from decimal import Decimal
from pathlib import Path
import re
import subprocess

ROLES = {
    "prior_annual": ("prior", "annual"), "prior_ytd": ("prior", "ytd_prior"),
    "prior_q3": ("prior", "q3"), "latest_annual": ("latest", "annual"),
    "latest_ytd": ("latest", "ytd_latest"),
}
AMOUNT = re.compile(r"(?<![\w.,])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\d.,])")
UNIT = re.compile(r"\bin (thousands|millions|billions)\b", re.I)
INLINE = re.compile(r"\s*(thousand|million|billion|[KMB]\b)", re.I)
FY = re.compile(r"\b(?:full[ -]?(?:fiscal[ -]?)?year|fiscal year|FY\s*20\d\d|twelve months ended)\b", re.I)
Q3 = re.compile(r"\b(?:third quarter|Q3|three months ended september 30)\b", re.I)
Q4 = re.compile(r"\b(?:fourth quarter|Q4|three months ended december 31)\b", re.I)
YTD6 = re.compile(r"six months ended|(?:twenty[ -]?(?:six|eight)|26|28) weeks ended", re.I)
YTD9 = re.compile(r"nine months ended|(?:thirty[ -]?nine|forty|39|40) weeks ended", re.I)
SINGLE = re.compile(r"three months ended|(?:twelve|thirteen|12|13) weeks ended", re.I)
REVENUE = re.compile(r"(?:total\s+)?(?:GAAP\s+)?(?:net\s+)?(?:revenues?|sales)(?:\s*,?\s+net)?", re.I)
REJECT_SCOPE = re.compile(r"continuing operations|discontinued operations|growth\s*%|comparable sales", re.I)
SCALES = {"k": 1000, "thousand": 1000, "m": 1000000, "million": 1000000, "b": 1000000000, "billion": 1000000000}


@dataclass(frozen=True)
class Line:
    page: int
    row: int
    text: str

    @property
    def id(self):
        return f"{self.page}:{self.row}"


def pages(pdf: Path):
    payload = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], timeout=30).decode("utf-8")
    return [Line(page, row, line.rstrip()) for page, content in enumerate(payload.split("\f"), 1)
            for row, line in enumerate((text for text in content.splitlines() if text.strip()), 1)]


def amount_spans(line):
    return [match for match in AMOUNT.finditer(line)
            if not re.match(r"\s*%", line[match.end():])
            and not (re.search(r"[a-zA-Z]\($", line[:match.start()]) and line[match.end():].startswith(")"))]


def chosen_display(line, tokens):
    spans = amount_spans(line.text)
    if not tokens or min(tokens) < 1 or max(tokens) > len(spans):
        raise ValueError(f"Unknown numeric column on {line.id}")
    selected = [spans[index - 1] for index in tokens]
    return [{"token_index": index, "raw": match[0], "column_start": match.start(),
             "column_end": match.end()} for index, match in zip(tokens, selected)]


def amount_values(line, tokens, scale):
    printed = chosen_display(line, tokens)
    return [Decimal(item["raw"].replace(",", "")) * scale for item in printed]


def read_layout(records):
    return [Line(**row) for row in records]


def show_layout(records):
    return "\n".join(f"[{row.page}:{row.row}] {row.text}" for row in read_layout(records))


def make_proof(line, tokens, scale, anchors):
    return {"at": line.id, "tokens": list(tokens), "scale": scale,
            "amounts": [format(x, "f") for x in amount_values(line, tokens, scale)],
            "evidence_anchors": [asdict(anchor) for anchor in anchors]}


def label_prefix(row, first):
    prefix = row[:first.start()].strip(" •*>$:.-")
    prefix = re.sub(r"(?<=[a-zA-Z])\(\d+\)", "", prefix)
    return re.sub(r"\s+", " ", prefix)


def scale_at(rows, line, tokens, allowed_inline=True):
    spans = amount_spans(line.text)
    inline = [INLINE.match(line.text[spans[n - 1].end():]) for n in tokens] if allowed_inline else []
    if inline and all(inline):
        factors = {SCALES[m[1].lower().rstrip("s")] for m in inline}
        return (factors.pop(), line) if len(factors) == 1 else None
    for candidate in reversed(rows):
        if m := UNIT.search(candidate.text):
            return SCALES[m[1].lower().rstrip("s")], candidate
    return None


def actual_candidates(line, nearby, year, vintage, tokens):
    if len(tokens) != 4 or not REVENUE.fullmatch(label_prefix(line.text, tokens[0])):
        return None
    if any(REJECT_SCOPE.search(row.text) for row in nearby[-9:]):
        return None
    duration = YTD6 if vintage == "prior" else YTD9
    for heading in reversed(nearby[-12:]):
        m, q = duration.search(heading.text), SINGLE.search(heading.text)
        if not m or not q or m.start() <= q.start():
            continue
        years = [row for row in nearby[-12:] if len(re.findall(r"\b20\d\d\b", row.text)) == 4]
        if not years or re.findall(r"\b20\d\d\b", years[-1].text)[2] != str(year):
            return None
        picked = (3,)
        if scoped := scale_at(nearby[-14:], line, picked, allowed_inline=False):
            scale, unit = scoped
            return make_proof(line, picked, scale, [heading, years[-1], unit])
    return None


def forecast_candidates(line, nearby, year, tokens):
    if not 1 <= len(tokens) <= 4 or REJECT_SCOPE.search(line.text):
        return {}
    statement = line.text.casefold()
    bare = REVENUE.fullmatch(label_prefix(line.text, tokens[0]))
    prose = (REVENUE.search(statement) and re.search(r"\$|\bUSD\b", statement)
             and re.search(r"expect|anticipate|will be|range|between", statement))
    if not bare and not prose:
        return {}
    pool = [row for row in [line, *reversed(nearby[-8:])] if re.search(rf"\b{year}\b", row.text)]
    headers = [(kind, row, match) for row in pool for kind, pattern in (("q3", Q3), ("q4", Q4), ("annual", FY))
               if (match := pattern.search(row.text))]
    if not headers or REJECT_SCOPE.search(headers[0][1].text):
        return {}
    claims = {}
    if len(tokens) == 4 and bare:
        annual = next((header for header in headers if header[0] == "annual"), None)
        quarter = next((header for header in headers if header[0] != "annual"), None)
        if not annual or not quarter or annual[2].start() == quarter[2].start():
            return {}
        ordered = sorted([annual, quarter], key=lambda header: header[2].start())
        assignment = [(header, (column, column + 1)) for column, header in zip((1, 3), ordered)]
    elif len(tokens) <= 2 and re.search(r"guidance|outlook|range|expect",
                                      " ".join(row.text for row in nearby[-8:]) + line.text, re.I):
        if any(word in statement for word in ("approx", "at least", "up to", "no more", "as much as")):
            return {}
        assignment = [(headers[0], tuple(range(1, len(tokens) + 1)))]
    else:
        return {}
    for (kind, header, _), selected in assignment:
        if scoped := scale_at(nearby[-10:], line, selected):
            scale, unit = scoped
            claims[kind] = make_proof(line, selected, scale, [header, unit])
    return claims


def candidates(case):
    proofs = {role: {} for role in ROLES}
    for vintage, doc in case["docs"].items():
        lines = read_layout(doc["lines"])
        opening = " ".join(line.text for line in lines[:25])
        restricted = bool(re.search(r"results are presented on a continuing operations basis", opening, re.I))
        for offset, line in enumerate(lines):
            tokens = amount_spans(line.text)
            if not tokens:
                continue
            # Recent lines can carry a header from the preceding physical page.
            nearby = lines[max(0, offset - 20):offset]
            bounds = forecast_candidates(line, nearby, case["fiscal_year"], tokens)
            actual = None if restricted else actual_candidates(line, nearby, case["report_year"], vintage, tokens)
            if actual:
                bounds["ytd_prior" if vintage == "prior" else "ytd_latest"] = actual
            for role, (expected_vintage, kind) in ROLES.items():
                if expected_vintage == vintage and kind in bounds:
                    proof = bounds[kind]
                    proofs[role][(proof["at"], tuple(proof["tokens"]))] = proof
    return proofs
