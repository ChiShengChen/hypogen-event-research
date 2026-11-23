"""Prove the currency and scale of a selected revenue amount before normalizing it."""

from dataclasses import dataclass
from decimal import Decimal, localcontext
import re

from .revision_bridge import _CURRENCY_MARKS, _MONEY, _RANGE_CONNECTOR, _SCALES, _SPREAD_CONNECTOR


_MAGNITUDES = r"units|whole\s+dollars?|dollars?|thousands?|millions?|billions?|trillions?"
_CURRENCY_NAMES = r"(?:U\.?S\.?|Canadian|Australian|New Zealand|Singapore|Hong Kong|Taiwan)\s+dollars?|euros?|yen|pounds?\s+sterling"
_DECLARATION = re.compile(
    rf"\bin\s+(?:(?:USD|CAD|AUD|EUR|GBP|JPY|CNY|\$)\s+)?(?P<scale>{_MAGNITUDES})\b"
    rf"|\b(?P<scaled_currency>thousands?|millions?|billions?|trillions?)\s+of\s+(?:U\.?S\.?\s+)?dollars?\b"
    rf"|\b(?:USD|U\.?S\.?\s+dollars?)\s+(?P<currency_scale>{_MAGNITUDES})\b"
    rf"|\bin\s+(?P<currency_name>{_CURRENCY_NAMES})\b",
    re.I,
)
_COMMON_DECLARATION = re.compile(
    rf"^\s*\(?\s*(?:(?:US|CA|AU|NZ|HK|NT|C|A)?\$\s*|(?:all\s+)?(?:dollar amounts|amounts|figures|financial data|dollars?|{_CURRENCY_NAMES})"
    r"\s+(?:are\s+)?)?(?:stated\s+|expressed\s+)?(?:in\s+|USD\s+)", re.I,
)
_DOLLAR_SUFFIX = re.compile(r"\s*(?:U\.?S\.?\s+)?dollars?\b", re.I)
_PERCENT_SUFFIX = re.compile(r"\s*(?:%|percent\b)", re.I)
_EXPLICIT_CURRENCY = re.compile(
    r"(?<!\w)(?:(?P<code>USD|CAD|AUD|NZD|GBP|EUR|JPY|CNY|RMB|SGD|HKD|TWD|MXN|BRL|INR|CHF|SEK|NOK|DKK)\b"
    r"|(?P<foreign_dollar>Canadian|Australian|New Zealand|Singapore|Hong Kong|Taiwan)\s+dollars?\b"
    r"|(?P<foreign_name>euros?|yen|pounds?\s+sterling)\b"
    r"|(?P<dollar>(?:U\.?S\.?\s+)?dollars?)\b|(?P<marked>US\$|CA\$|AU\$|HK\$|NT\$|NZ\$|C\$|A\$|CN¥|JP¥|\$|€|£|₩|¥))",
    re.I,
)


@dataclass(frozen=True)
class UnitSource:
    id: str
    quote: str
    scope: str


@dataclass(frozen=True)
class Reading:
    low: Decimal | None
    high: Decimal | None
    raw_text: str
    multipliers: tuple[int, ...]
    sources: tuple[UnitSource, ...]
    reason: str | None = None


@dataclass(frozen=True)
class _Token:
    number: Decimal
    multiplier: int | None
    currencies: frozenset[str]
    start: int
    end: int
    percent: bool


def _currencies(text):
    values = set()
    for match in _EXPLICIT_CURRENCY.finditer(text):
        if match["code"]:
            values.add(match["code"].upper())
        elif match["foreign_dollar"] or match["foreign_name"]:
            values.add((match["foreign_dollar"] or match["foreign_name"]).casefold())
        elif match["dollar"]:
            values.add("USD")
        else:
            mark = match["marked"].upper()
            values.add("USD" if mark == "$" else _CURRENCY_MARKS.get(mark, mark))
    return frozenset(values)


def _factor(value):
    name = " ".join(value.lower().split()).rstrip("s")
    return 1 if name in {"unit", "whole dollar", "dollar"} else _SCALES[name]


def declaration_factors(text):
    fields = ("scale", "scaled_currency", "currency_scale")
    return {1 if match["currency_name"] else _factor(next(match[name] for name in fields if match[name]))
            for match in _DECLARATION.finditer(text)}


def common_unit_label(text):
    """A left label/title declares table units only when its wording is table-wide."""
    return bool(_COMMON_DECLARATION.match(text) and declaration_factors(text))


def _tokens(text):
    for match in _MONEY.finditer(text):
        trailing = text[match.end():]
        dollars = _DOLLAR_SUFFIX.match(trailing)
        end = match.end() + (dollars.end() if dollars else 0)
        marker = " ".join(part for part in (match["prefix"], match["suffix"]) if part)
        currencies = _currencies(marker + (dollars.group(0) if dollars else ""))
        scale = _SCALES.get((match["scale"] or "").lower())
        yield _Token(Decimal(match["number"].replace(",", "")), scale or (1 if dollars else None),
                     currencies, match.start(), end, bool(_PERCENT_SUFFIX.match(trailing)))


def _expression(text, *, tabular):
    tokens = list(_tokens(text))
    pairs = []
    for left, right in zip(tokens, tokens[1:]):
        connector = text[left.end:right.start].lstrip().lstrip(",").strip()
        spread = bool(_SPREAD_CONNECTOR.fullmatch(connector))
        between = connector.casefold() == "and" and bool(re.search(r"\bbetween\s*$", text[:left.start], re.I))
        if not (spread or between or _RANGE_CONNECTOR.fullmatch(connector)):
            continue
        if left.percent or (right.percent and not spread):
            if tabular or left.currencies or right.currencies or left.multiplier or right.multiplier:
                return None
            continue
        if tabular or left.currencies or right.currencies or left.multiplier or right.multiplier:
            pairs.append(((left, right), spread))
    if pairs:
        return pairs[0] if len(pairs) == 1 else None
    points = [token for token in tokens if not token.percent and (tabular or token.currencies or token.multiplier)]
    return ((points[0],), False) if len(points) == 1 else None


def read_units(text, *, amount_ref, currency, sources=(), tabular=False, ambiguous=False):
    """Return the exact monetary expression and its proof, or an explicit blocking reason."""
    expression = _expression(text, tabular=tabular)
    scoped = tuple(source for source in sources if declaration_factors(source.quote))
    if expression is None:
        return Reading(None, None, text, (), scoped, "無法唯一辨識原文金額或完整區間。")
    tokens, spread = expression
    raw = text[tokens[0].start:tokens[-1].end]
    if tokens[-1].percent:
        raw += _PERCENT_SUFFIX.match(text[tokens[-1].end:]).group(0)
    inline = UnitSource(amount_ref, raw, "inline")
    proof_sources = (inline, *scoped)
    inherited = set().union(*(declaration_factors(source.quote) for source in scoped))
    absolute = [token for token in tokens if not token.percent]
    explicit = {token.multiplier for token in absolute if token.multiplier is not None}
    currencies = set().union(*(token.currencies for token in absolute), *(_currencies(source.quote) for source in scoped))
    if re.search(r"[-−]\s*$", text[:tokens[0].start]) or (tabular and text.strip().startswith("(")):
        return Reading(None, None, raw, (), proof_sources, "原文以負數表示，無法套用於營收區間。")
    if ambiguous:
        return Reading(None, None, raw, (), proof_sources, "原文單位和所選欄位的適用範圍不明。")
    if currencies != {currency}:
        return Reading(None, None, raw, (), proof_sources, "原文幣別缺失或與所選報告口徑衝突。")
    if len(inherited) > 1 or (inherited and explicit - inherited):
        return Reading(None, None, raw, (), proof_sources, "原文的欄位、標題或金額倍率互相衝突。")
    shared = inherited or explicit
    if not shared or (len(shared) > 1 and any(token.multiplier is None for token in absolute)):
        return Reading(None, None, raw, (), proof_sources, "原文未證明所選數值的金額倍率。")
    multipliers = tuple(token.multiplier or next(iter(shared)) for token in absolute)
    with localcontext() as ctx:
        ctx.prec = 50
        values = [token.number * multiplier for token, multiplier in zip(absolute, multipliers)]
        if spread:
            margin = values[0] * tokens[-1].number / 100 if tokens[-1].percent else values[1]
            low, high = values[0] - margin, values[0] + margin
        else:
            low, high = values[0], values[-1]
    if not 0 <= low <= high:
        return Reading(None, None, raw, multipliers, proof_sources, "換算後營收區間順序或正負不符。")
    return Reading(low, high, raw, multipliers, proof_sources)
