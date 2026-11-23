"""Deterministic veto over a direct model answer to guidance-revision arithmetic.

The veto keeps the model's own answer. It turns an item into "unknown" only when an operand the model itself
cited carries positive evidence that the item is not built from comparable consolidated USD revenue outlooks:

- metric:     the outlook names a revenue component (subscription, product, services, ...) or a measure that
              is not revenue (ARR, billings, bookings, RPO, GMV, comparable sales);
- rate:       the outlook is a growth rate without a currency amount;
- currency:   the outlook is stated in constant currency or in a currency other than USD;
- visibility: the cited document is not one of the case's point-in-time documents;
- operands:   an answered item does not cite every operand it depends on.

A quote that cannot be found and an amount that cannot be read never veto: absence of proof leaves the model's
answer in place. That is what separates this mode from the extract mode, where an unproven operand becomes
unknown and the Harness can only match the model or fall below it.
"""

from dataclasses import asdict, dataclass
import re

from benchmarks import guidance_arithmetic as bench

GUIDANCE = ("prior", "prior_interim", "new")
DEPENDS = dict(bench.NEEDS) | {
    "implied_remainder_prior": ("prior", "prior_interim", "prior_reported_in_period"),
    "implied_remainder_new": ("new", "reported_in_period"),
}
UNKNOWN = "unknown"
WINDOW = 160
SLOT_WORDS = 3

NOUN = re.compile(r"\b(?:revenues?|sales|ARR|billings|bookings|RPO|GMV)\b", re.I)
NOT_REVENUE = re.compile(r"^(?:ARR|billings|bookings|RPO|GMV)$", re.I)
COMPONENT = re.compile(
    r"\b(?:subscriptions?|products?|services?|licen[cs]es?|professional|maintenance|support|recurring|"
    r"platform|cloud|transactions?|advertising|hardware|core|organic|comparable|comp|same[- ]store)\b", re.I)
BOUNDARY = re.compile(r"[.:;•●○◦▪·()!?]")
AMOUNT = re.compile(r"[$€£¥]\s*\d|\d[\d,.]*\s*(?:thousand|million|billion|trillion)\b|\d{1,3}(?:,\d{3})+", re.I)
RATE = re.compile(r"\d\s*%|\bper\s*cent\b|\bpercent\b", re.I)
CONSTANT_CURRENCY = re.compile(
    r"\(cc\)|\bconstant[\s-]+currency\b|\bcurrency[\s-]+neutral\b|\bex[\s-]?FX\b|\bfixed\s+exchange\b", re.I)
FOREIGN = re.compile(r"[€£¥₹]|\b(?:EUR|GBP|JPY|CNY|RMB|CAD|AUD|CHF|SEK|INR|KRW|BRL)\b|\b(?:C|A|NZ|HK|S)\$")


@dataclass(frozen=True)
class Veto:
    operand: str
    rule: str
    block: str | None
    quote: str
    detail: str


def flat(text):
    return " ".join(str(text).split())


def is_unknown(value):
    return flat(value).casefold() in {"", UNKNOWN}


def metric_clause(text, noun):
    """Return the qualifier words before the metric noun and the clause from them to the end of `text`."""
    start = max(0, noun.start() - 60)
    cut = [match.end() for match in BOUNDARY.finditer(text, start, noun.start())]
    start = cut[-1] if cut else start
    words = text[start:noun.start()].split()
    return " ".join(words[-SLOT_WORDS:]), text[start:]


def metric_of(quote, block_text):
    """Find the metric the cited amount belongs to: in the quote before its first amount, else just before it."""
    first = AMOUNT.search(quote)
    head = quote[:first.start()] if first else quote
    if nouns := list(NOUN.finditer(head)):
        return (nouns[-1][0], *metric_clause(head, nouns[-1]))
    position = flat(block_text).find(quote) if block_text else -1
    if position < 0:
        return None
    window = flat(block_text)[max(0, position - WINDOW):position]
    if nouns := list(NOUN.finditer(window)):
        return (nouns[-1][0], *metric_clause(window, nouns[-1]))
    return None


def guidance_defects(name, ref, blocks):
    quote = flat(ref["quote"])
    block = blocks.get(ref["block"], {}).get("text", "")
    found = metric_of(quote, block)
    clause = quote if found is None else f"{found[2]} {quote}"
    defects = []
    if found is not None:
        noun, slot, _ = found
        if NOT_REVENUE.match(noun):
            defects.append(("metric", f"{name} is a {noun} outlook, not a revenue outlook"))
        elif component := COMPONENT.search(slot):
            defects.append(("metric", f"{name} is a {component[0].lower()} {noun.lower()} outlook, not comparable "
                                      "consolidated total revenue"))
    if RATE.search(quote) and not AMOUNT.search(quote):
        defects.append(("rate", f"{name} is a growth rate without a USD revenue amount"))
    if CONSTANT_CURRENCY.search(clause):
        defects.append(("currency", f"{name} is stated in constant currency, not reported USD"))
    elif FOREIGN.search(quote):
        defects.append(("currency", f"{name} is stated in a currency other than USD"))
    return defects


def operand_vetoes(case, figures, blocks):
    documents = {document.id for document in case.documents}
    vetoes = []
    for figure in figures:
        name, ref = figure["name"], figure
        if ref["document"] not in documents or not str(ref["block"]).startswith(f"{ref['document']}:"):
            vetoes.append(Veto(name, "visibility", ref["block"], flat(ref["quote"]),
                               f"{name} cites {ref['document']}, which is not a point-in-time document of this case"))
            continue
        if name in GUIDANCE:
            vetoes.extend(Veto(name, rule, ref["block"], flat(ref["quote"]), detail)
                          for rule, detail in guidance_defects(name, ref, blocks))
    return vetoes


def apply(case, blocks, reply):
    """Return the model's answers with vetoed items replaced by unknown, plus the evidence for each veto."""
    answers = {row["item"]: row["value"] for row in reply["answers"]}
    figures = reply.get("figures_used") or []
    cited = {figure["name"] for figure in figures}
    vetoes = operand_vetoes(case, figures, blocks)
    flawed = {veto.operand for veto in vetoes}
    vetoed = {}
    for item in case.items:
        if is_unknown(answers.get(item, "")):
            continue
        needs = DEPENDS[item]
        if missing := [name for name in needs if name not in cited]:
            vetoed[item] = f"{item} was answered without citing {', '.join(missing)}"
        elif bad := [name for name in needs if name in flawed]:
            vetoed[item] = f"{item} depends on {', '.join(bad)}"
    result = {item: (UNKNOWN if item in vetoed else answers.get(item, "")) for item in case.items}
    used = [veto for veto in vetoes if any(veto.operand in DEPENDS[item] for item in vetoed)]
    details = list(dict.fromkeys([veto.detail for veto in used] + [reason for reason in vetoed.values()
                                                                   if "without citing" in reason]))
    reason = ("Deterministic veto: " + "; ".join(details) + "." if details else None)
    evidence = list(dict.fromkeys(list(reply.get("evidence_ids") or []) +
                                  [veto.block for veto in used if veto.block in blocks]))
    return {"answers": result, "vetoed_items": vetoed, "vetoes": [asdict(veto) for veto in used],
            "operand_flags": [asdict(veto) for veto in vetoes], "reason": reason, "evidence_ids": evidence,
            "figures": figures}
