"""Build vintage-safe semiconductor cases from SEC Company Facts 10-Q instances."""

import json
from datetime import date, timedelta
from decimal import Decimal, localcontext
from pathlib import Path

from research_app.research import build_context
from research_app.schema import Event

TICKERS = {
    "AMD": "0000002488", "INTC": "0000050863", "MU": "0000723125",
    "QCOM": "0000804328", "TXN": "0000097476",
}
TAGS = {
    "revenue": (("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"), "USD"),
    "gross": (("GrossProfit",), "USD"),
    "cogs": (("CostOfRevenue", "CostOfGoodsAndServicesSold"), "USD"),
    "operating_income": (("OperatingIncomeLoss",), "USD"),
    "net": (("NetIncomeLoss", "ProfitLoss"), "USD"),
    "shares": (("WeightedAverageNumberOfDilutedSharesOutstanding",), "shares"),
    "eps": (("EarningsPerShareDiluted",), "USD/shares"),
}


def filing_index(data):
    filings = {}
    for name, (tags, unit) in TAGS.items():
        for tag in tags:
            for row in data["facts"]["us-gaap"].get(tag, {}).get("units", {}).get(unit, []):
                if row["form"] != "10-Q" or row.get("fp") not in {"Q1", "Q2", "Q3"} or "start" not in row:
                    continue
                end = date.fromisoformat(row["end"])
                duration = end - date.fromisoformat(row["start"])
                filed = date.fromisoformat(row["filed"])
                if not 75 <= duration.days <= 110 or not 0 <= (filed - end).days <= 70:
                    continue
                key = (end, filed, row["accn"], row["fp"])
                filings.setdefault(key, {}).setdefault(name, (Decimal(str(row["val"])), tag))
    per_period = {}
    for (end, filed, accn, fp), values in sorted(filings.items()):
        if not {"revenue", "operating_income", "net", "shares", "eps"} <= values.keys():
            continue
        if "gross" not in values and "cogs" not in values:
            continue
        if not values["shares"][0] > 0 or not values["revenue"][0] > 0:
            continue
        if "gross" not in values:
            values["gross"] = (values["revenue"][0] - values["cogs"][0],
                               f"{values['revenue'][1]} − {values['cogs'][1]}")
        if values["gross"][0] > values["revenue"][0] or values["operating_income"][0] > values["gross"][0]:
            continue
        with localcontext() as ctx:
            ctx.prec = 40
            eps_proxy = values["net"][0] / values["shares"][0]
        if abs(eps_proxy - values["eps"][0]) > Decimal("0.03"):
            continue
        per_period.setdefault(end, {"end": end, "filed": filed, "accession": accn, "fp": fp, "values": values})
    return per_period


def disclosure(cik, identifier, filing):
    available = filing["filed"].isoformat() + "T23:59:59Z"
    details = "；".join(f"{name}={value}（{tag}）"
                       for name, (value, tag) in filing["values"].items() if name != "cogs")
    accession = filing["accession"]
    return {
        "id": identifier, "source": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}-index.htm",
        "kind": "disclosure", "text_format": "summary", "availability_basis": "replay_day_end",
        "published_at": available, "obtained_at": available,
        "paragraphs": {"income": f"{filing['end']} 結束的單季，US GAAP。美元原值及稀釋股數。{details}。"},
    }


def baseline(previous, future, doc):
    values = {key: pair[0] for key, pair in previous["values"].items()}
    tax = Decimal("0.21")
    return {
        "period_end": future.isoformat(),
        "available_at": doc["obtained_at"],
        "segment_revenue": {"consolidated": str(values["revenue"])},
        "gross_margin": str((values["gross"] / values["revenue"]).quantize(Decimal("0.00000001"))),
        "opex": str(values["gross"] - values["operating_income"]),
        "tax_rate": str(tax), "other_after_tax": str(values["net"] - values["operating_income"] * (1 - tax)),
        "diluted_shares": str(values["shares"]),
        "evidence_ids": [doc["id"] + ":income"],
        "method": "去年同季公開值作固定季節基準。21% 為模型稅率假設，稅後其他項目為去年同季淨利的對帳餘額。",
    }


def make_case(ticker, cik, event, targets, previous):
    event_doc = disclosure(cik, "issuer-event", event)
    baseline_docs = [disclosure(cik, f"prior-q{index}", row) for index, row in enumerate(previous, 2)]
    quarters = [baseline(old, new["end"], doc) for old, new, doc in zip(previous, targets, baseline_docs)]
    model = Event.model_validate({
        "event_text": f"{ticker} 公布截至 {event['end']} 的財年第一季 10-Q，修正後續第二、第三季盈利預測。",
        "research_target": ticker, "research_horizon": targets[-1]["end"].isoformat(),
        "as_of": event_doc["published_at"], "documents": [*baseline_docs, event_doc], "search_mode": "off",
        "earnings_plan": {"event_at": event_doc["published_at"], "currency": "USD", "basis": "US_GAAP",
                          "quarters": quarters, "generate_drivers": True},
    })
    actual = {}
    for row in targets:
        values = {key: value[0] for key, value in row["values"].items()}
        actual[row["end"].isoformat()] = {
            "values": {key: str(value) for key, value in {
                "revenue": values["revenue"], "gross_margin": values["gross"] / values["revenue"],
                "operating_income": values["operating_income"], "eps": values["eps"],
            }.items()},
            "document": disclosure(cik, f"actual-{row['fp'].lower()}", row),
        }
    return {"id": f"{ticker}-{event['end'].year}", "event": model, "context": build_context(model),
            "actual": actual}


def load_cases(folder: Path, selections=None):
    all_cases = []
    selections = selections or {ticker: range(2019, 2025) for ticker in TICKERS}
    cik_by_ticker = {**TICKERS, "NVDA": "0001045810"}
    for ticker, years in selections.items():
        cik = cik_by_ticker[ticker]
        filings = filing_index(json.loads((folder / f"{ticker}.json").read_text()))
        for year in years:
            events = [row for row in filings.values() if row["end"].year == year and row["fp"] == "Q1"]
            if len(events) != 1:
                raise ValueError(f"{ticker} {year}: expected one Q1 filing, got {len(events)}")
            event = events[0]
            targets = []
            previous = []
            for step, fp in enumerate(("Q2", "Q3"), 1):
                candidates = [row for row in filings.values() if row["fp"] == fp and
                              abs((row["end"] - event["end"]).days - 91 * step) <= 18]
                if len(candidates) != 1:
                    raise ValueError(f"{ticker} {year}: no unique next {fp}")
                target = candidates[0]
                earlier = [row for row in filings.values() if row["fp"] == fp and
                           abs((target["end"] - row["end"]).days - 365) <= 18 and row["filed"] < event["filed"]]
                if len(earlier) != 1:
                    raise ValueError(f"{ticker} {year}: no unique prior {fp}")
                targets.append(target)
                previous.append(earlier[0])
            all_cases.append(make_case(ticker, cik, event, targets, previous))
    return all_cases
