"""Point-in-time comparison of a frozen revenue forecast and disclosed guidance."""

from datetime import datetime
from decimal import Decimal
import re
from urllib.parse import urlsplit

from pydantic import AwareDatetime, Field, model_validator

from .schema import Amount, MetricKey, Nonempty, Schema


class NativeRevisionProof(Schema):
    amount_ref: Nonempty
    context_ref: Nonempty
    header_ref: Nonempty | None = None
    column: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_table(self):
        if self.header_ref is None and self.column is None:
            return self
        if self.header_ref != self.amount_ref or self.column is None:
            raise ValueError("表頭和數值須保存在同一引文，並指定數值欄位")
        return self


class RevisionQuote(Schema):
    """A point or interval in unscaled currency units."""

    key: MetricKey
    available_at: AwareDatetime
    low: Amount
    high: Amount
    evidence_ids: list[Nonempty] = Field(min_length=1, max_length=12)
    native_proof: NativeRevisionProof | None = None

    @model_validator(mode="after")
    def check_range(self):
        if not 0 <= self.low <= self.high:
            raise ValueError("營收區間須為非負且下限不得高於上限")
        if self.native_proof and not {
            self.native_proof.amount_ref, self.native_proof.context_ref,
        }.issubset(self.evidence_ids):
            raise ValueError("原文核對需列出金額及口徑引文")
        return self


class RevisionRequest(Schema):
    key: MetricKey
    event_at: AwareDatetime
    original: RevisionQuote | None = None
    incumbent: RevisionQuote
    disclosure: RevisionQuote | None = None

    @model_validator(mode="after")
    def check_incumbent(self):
        if self.incumbent.low != self.incumbent.high:
            raise ValueError("現版營收預估須為單點")
        return self


_CURRENCY_MARKS = {
    "US$": "USD", "CA$": "CAD", "C$": "CAD", "AU$": "AUD", "A$": "AUD", "HK$": "HKD",
    "NT$": "TWD", "NZ$": "NZD", "CN¥": "CNY", "JP¥": "JPY", "€": "EUR", "£": "GBP", "₩": "KRW",
}
_SCALES = {
    "trillion": 10**12, "tn": 10**12,
    "billion": 10**9, "bn": 10**9, "b": 10**9,
    "million": 10**6, "mn": 10**6, "m": 10**6,
    "thousand": 10**3, "k": 10**3,
    "億": 10**8, "百萬": 10**6, "萬": 10**4,
}
_MONEY = re.compile(
    r"(?<![\w.,])"
    r"(?:(?P<prefix>US\$|CA\$|AU\$|HK\$|NT\$|NZ\$|CN¥|JP¥|C\$|A\$|[$€£₩¥]|(?-i:[A-Z]{3})(?![A-Z]))\s*)?"
    r"(?P<number>(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?)"
    r"(?:\s*(?P<scale>trillion|billion|million|thousand|bn|mn|tn|[bmk]|億|百萬|萬)(?![A-Za-z]))?"
    r"(?:\s*(?P<suffix>(?-i:[A-Z]{3})(?![A-Z])))?(?!\w|[.,][0-9])",
    re.IGNORECASE,
)
_RANGE_CONNECTOR = re.compile(r"\s*(?:to|through|至|到|[-–—])\s*", re.IGNORECASE)
_SPREAD_CONNECTOR = re.compile(r"\s*(?:±|\+\s*/\s*-|plus or minus|上下(?:浮動)?)\s*", re.IGNORECASE)
_ISO_DAY = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")
_SENTENCE_BREAK = re.compile(r"[!?。；;\n]+|(?<![A-Za-z]\.[A-Za-z])\.(?=\s+[A-Z])")
_REVENUE = r"\b(?:revenue|net sales)\b"
_FORWARD_REVENUE = re.compile(
    rf"{_REVENUE}\s+(?:guidance|outlook|forecast|expectation|will be|to be|is expected)\b"
    rf"|\b(?:expects?|forecasts?|outlook for|guidance for)\b[^,.;:]{{0,55}}{_REVENUE}"
    rf"|\bpreliminary (?:net )?{_REVENUE}\s+estimates?\b"
    r"|(?:營收|營業收入)\s*(?:指引|展望|預估|預期)|(?:指引|展望|預估|預期)[^，。]{0,15}(?:營收|營業收入)",
    re.IGNORECASE,
)


def _amounts(statement, currency, *, native_usd=False):
    matches = list(_MONEY.finditer(statement))
    context_currency = native_usd or bool(re.search(rf"\b{re.escape(currency)}\b", statement, re.IGNORECASE))

    def parts(match):
        raw = match["number"]
        marks = [x.upper() for x in (match["prefix"], match["suffix"]) if x]
        ambiguous = {"$", "¥"}
        currencies = {_CURRENCY_MARKS.get(mark, mark) for mark in marks if mark not in ambiguous}
        if currencies - {currency} or ("$" in marks and currency not in {"USD", "CAD", "AUD", "NZD", "HKD", "TWD"}):
            return None
        if "¥" in marks and currency not in {"CNY", "JPY"}:
            return None
        number = Decimal(raw.replace(",", ""))
        scale = _SCALES.get((match["scale"] or "").lower())
        return number, scale, bool(currencies), bool(marks or scale or number >= 100_000)

    intervals = set()
    range_found = False
    for left, right in zip(matches, matches[1:]):
        separator = statement[left.end():right.start()]
        spread = _SPREAD_CONNECTOR.fullmatch(separator.lstrip().lstrip(",") if native_usd else separator)
        between = separator.strip().lower() == "and" and re.search(
            rf"\bbetween\s*(?:{re.escape(currency)}\s*)?$", statement[:left.start()], re.IGNORECASE
        )
        if not spread and not between and not _RANGE_CONNECTOR.fullmatch(separator):
            continue
        first, second = parts(left), parts(right)
        if first is None or second is None:
            continue
        number_a, scale_a, identified_a, money_a = first
        number_b, scale_b, identified_b, money_b = second
        if not ((context_currency or identified_a or identified_b) and (money_a or money_b)):
            continue
        range_found = True
        factor_a = scale_a or (scale_b if number_a < 100_000 else None) or 1
        factor_b = scale_b or (scale_a if number_b < 100_000 else None) or 1
        a, b = number_a * factor_a, number_b * factor_b
        if native_usd and re.match(r"\s*(?:%|percent\b)", statement[right.end():], re.I):
            if not spread:
                continue
            b = a * number_b / 100
        low, high = (a - b, a + b) if spread else (a, b)
        if 0 <= low <= high:
            intervals.add((low, high))
    if range_found:
        return intervals
    points = {
        number * (scale or 1)
        for match in matches
        if (value := parts(match)) is not None
        for number, scale, identified, money in [value]
        if (context_currency or identified) and money
    }
    return {(point, point) for point in points} if len(points) == 1 else set()


def _matches_statement(statement, quote):
    key = quote.key
    folded = statement.casefold()
    end = key.period_end
    iso_days = set(_ISO_DAY.findall(statement))
    date_names = (end.isoformat(), f"{end:%B} {end.day}, {end.year}", f"{end:%b} {end.day}, {end.year}")
    if (iso_days and iso_days != {end.isoformat()}) or not any(x.casefold() in folded for x in date_names):
        return False
    adjusted = bool(re.search(r"\b(?:non[\s_-]*gaap|adjusted)\b|非美國公認會計|調整後", folded))
    if key.basis == "US_GAAP":
        basis = not adjusted and not re.search(r"\bIFRS\b", statement, re.IGNORECASE) and bool(
            re.search(r"\b(?:u\.?s\.?[\s_-]+gaap|gaap)\b|美國公認會計", folded)
        )
    elif key.basis == "IFRS":
        basis = not adjusted and bool(re.search(r"\bifrs\b|國際財務報導", folded))
    else:
        basis = adjusted
    if not basis:
        return False
    if key.scope.casefold() == "consolidated":
        scope = bool(re.search(r"\bconsolidated\b|合併", folded))
    else:
        scope = key.scope.casefold() in folded
    return (
        scope
        and bool(_FORWARD_REVENUE.search(statement))
        and bool(re.search(r"\b(?:fiscal )?quarter\b|\bq[1-4]\b|第?[一二三四1-4]季|季度", folded))
        and not bool(re.search(r"\b(?:full[ -]year|annual)\b|全年|年度", folded))
        and _amounts(statement, key.currency) == {(quote.low, quote.high)}
    )


def _public_time(row):
    if not row or row.get("kind") != "disclosure" or row.get("synthetic"):
        return None
    try:
        url = urlsplit(row.get("source") or "")
        published, obtained = (datetime.fromisoformat(row[field]) for field in ("published_at", "obtained_at"))
    except (KeyError, TypeError, ValueError):
        return None
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        return None
    if published.utcoffset() is None or obtained.utcoffset() is None or published > obtained:
        return None
    return published, obtained


_FISCAL_QUARTER = re.compile(
    r"\bq[1-4]\b|\b(?:first|second|third|fourth|fiscal)\s+quarter\b"
    r"|\bquarters?\s+(?:and fiscal year\s+)?end(?:ed|ing)\b",
    re.IGNORECASE,
)
_GUIDANCE_CONTEXT = re.compile(r"\b(?:guidance|outlook|preliminary|expected|expects|estimates|anticipates)\b", re.I)
_OFF_SCOPE = re.compile(r"\b(?:non[ -]*gaap|adjusted|IFRS|segment(?:s)?|per share)\b", re.I)
_NOT_NEW = re.compile(r"\b(?:prior|previous|original|historical|actual|year[- ]to[- ]date|full[- ]year|annual)\b", re.I)
_USD_NUMBER = re.compile(r"(?<![\w$])\$\s*\d|\bUSD\b", re.I)
_ONE_SIDED = re.compile(
    r"\b(?:at least|at most|up to|less than|more than|above|below|or higher|or lower|lower end|upper end)\b",
    re.I,
)


def _matches_period(text, end, fiscal_label):
    dates = (end.isoformat(), f"{end:%B} {end.day}, {end.year}", f"{end:%b} {end.day}, {end.year}",
             f"{end:%b}. {end.day}, {end.year}")
    folded = text.casefold()
    return any(day.casefold() in folded for day in dates) or (
        fiscal_label and _FISCAL_QUARTER.search(fiscal_label) and str(end.year) in fiscal_label
        and re.search(rf"(?<!\w){re.escape(fiscal_label.casefold())}(?!\w)", folded)
    )


def _native_cells(text, column):
    rows = [line.strip() for line in text.splitlines() if line.strip()]
    if len(rows) != 2:
        return None
    headers, cells = ([piece.strip() for piece in line.strip("|").split("|")] for line in rows)
    if len(cells) != len(headers) + 1 or column >= len(headers):
        return None
    header = headers[column]
    if not re.fullmatch(r"(?:total\s+|net\s+)?(?:revenue|net sales|sales)", cells[0], re.I):
        return None
    if _NOT_NEW.search(header) or _OFF_SCOPE.search(header):
        return None
    if not (_GUIDANCE_CONTEXT.search(header) or re.fullmatch(r"GAAP|U\.S\. GAAP", header, re.I)):
        return None
    return header, cells[column + 1]


def _native_match(quote, visible, fiscal_label):
    key, proof = quote.key, quote.native_proof
    if (key.currency, key.basis, key.scope) != ("USD", "US_GAAP", "consolidated"):
        return False
    amount, context = (visible.get(ref) for ref in (proof.amount_ref, proof.context_ref))
    if not amount or not context or any(row.get("text_format") != "excerpt" for row in (amount, context)):
        return False
    for field in ("source", "published_at", "document_id"):
        if amount.get(field) != context.get(field):
            return False
    scope = context["quote"]
    if not (_FISCAL_QUARTER.search(scope) and _matches_period(scope, key.period_end, fiscal_label)):
        return False
    if proof.column is not None:
        cells = _native_cells(amount["quote"], proof.column)
        if cells is None:
            return False
        header, value = cells
        if not (_GUIDANCE_CONTEXT.search(header) or _GUIDANCE_CONTEXT.search(scope)):
            return False
        if _FISCAL_QUARTER.search(header) and not _matches_period(header, key.period_end, fiscal_label):
            return False
    else:
        statements = _SENTENCE_BREAK.split(amount["quote"])
        if len(statements) != 1:
            return False
        value = statements[0]
        if not _FORWARD_REVENUE.search(value) or _OFF_SCOPE.search(value) or _NOT_NEW.search(value):
            return False
        if _FISCAL_QUARTER.search(value) and proof.amount_ref != proof.context_ref and (
            re.search(r"\b20\d{2}\b", value) and not _matches_period(value, key.period_end, fiscal_label)
        ):
            return False
    return bool(not _ONE_SIDED.search(value) and _USD_NUMBER.search(value)
                and _amounts(value, "USD", native_usd=True) == {(quote.low, quote.high)})


def _source_error(quote, visible, *, published_after=None, prove_statement=False, fiscal_label=None):
    rows = [visible.get(ref) for ref in quote.evidence_ids]
    for row in rows:
        times = _public_time(row)
        if times is None:
            return "引用缺少可見的公開來源。"
        published, obtained = times
        if obtained > quote.available_at or (published_after is not None and published < published_after):
            return "引文公開或取得時點與本次披露不符。"
    if prove_statement and quote.native_proof:
        return None if _native_match(quote, visible, fiscal_label) else "原文的財季、表頭或營收金額無法合併核對。"
    if prove_statement and not any(
        _matches_statement(line, quote)
        for row in rows if row.get("text_format", "excerpt") == "excerpt"
        for line in _SENTENCE_BREAK.split(row.get("quote") or "")
    ):
        return "引文須在同一段明列財季、範圍、會計基礎、幣別與相符的營收指引數值。"
    return None


def evaluate_revision(request: RevisionRequest, evidence, *, as_of: datetime, fiscal_label=None):
    """Constrain an incumbent to the nearest verified interval bound when appropriate."""
    key = request.key
    original, incumbent, disclosure = request.original, request.incumbent, request.disclosure
    audit = {
        "status": "blocked",
        "policy": "nearest_bound_when_outside",
        "reason": "",
        "key": key.model_dump(mode="json"),
        "event_at": request.event_at.isoformat(),
        "original": original.model_dump(mode="json", exclude_none=True) if original else None,
        "incumbent": incumbent.model_dump(mode="json", exclude_none=True),
        "disclosure": disclosure.model_dump(mode="json", exclude_none=True) if disclosure else None,
        "remaining_delta": None,
        "revised": format(incumbent.low, "f"),
        "event_change": None,
        "evidence_ids": [],
    }

    def blocked(reason):
        return {**audit, "reason": reason}

    if key.metric != "revenue" or key.duration != "quarter":
        return blocked("此試算只接受單季營收。")
    if as_of.utcoffset() is None or request.event_at > as_of:
        return blocked("須使用含時區且涵蓋事件的研究截止時點。")
    if disclosure is None:
        return blocked("缺少可核對的同季營收指引。")
    quotes = [incumbent, disclosure, *([original] if original else [])]
    if any(row.key != key for row in quotes):
        return blocked("指標、期別、範圍、幣別或會計基礎不一致。")
    if any(row.available_at > as_of for row in quotes):
        return blocked("資料超過研究截止時點。")
    if disclosure.available_at < request.event_at or (original and original.available_at >= request.event_at):
        return blocked("原預估須早於事件，新指引須在事件時或之後可得。")
    refs = {ref for row in quotes for ref in row.evidence_ids}
    visible = {}
    for row in evidence:
        ref = row.get("id")
        if ref not in refs:
            continue
        if ref in visible and visible[ref] != row:
            return blocked("同一引用識別碼出現相互衝突的資料。")
        visible[ref] = row
    for role, row in (("原預估", original), ("現版預估", incumbent), ("新指引", disclosure)):
        if row is None:
            continue
        error = _source_error(
            row, visible, published_after=request.event_at if row is disclosure else None,
            prove_statement=row is not incumbent, fiscal_label=fiscal_label,
        )
        if error:
            return blocked(f"{role}，{error}")
        audit["evidence_ids"] = list(dict.fromkeys([*audit["evidence_ids"], *row.evidence_ids]))
    if original:
        audit["event_change"] = {
            "low": format(disclosure.low - original.high, "f"),
            "high": format(disclosure.high - original.low, "f"),
            "midpoint_delta": format((disclosure.low + disclosure.high - original.low - original.high) / 2, "f"),
        }
    revised = min(max(incumbent.low, disclosure.low), disclosure.high)
    delta = revised - incumbent.low
    audit.update(
        status="eligible" if delta else "noop",
        reason=("現版預估落在揭露區間外，以最接近的界限試算。" if delta
                else "現版預估已落在揭露區間內，保留既有數值。"),
        remaining_delta=format(delta, "f"),
        revised=format(revised, "f"),
    )
    if disclosure.native_proof and fiscal_label:
        audit["fiscal_label"] = fiscal_label
    return audit
