"""Point-in-time quarterly revenue inputs, including Q4 reconciled from annual filings."""

from datetime import date
from decimal import Decimal
import json

from research_app.schema import Document, RevenueBridge

from .earnings_cases import TAGS, TICKERS, filing_index
from .earnings_inputs import end_of_day

CIKS = {**TICKERS, "NVDA": "0001045810"}


def revenue_history(sec_dir, tickers):
    result = {}
    for ticker in tickers:
        data = json.loads((sec_dir / f"{ticker}.json").read_text())
        quarters = filing_index(data)
        annual = {}
        for tag in TAGS["revenue"][0]:
            for fact in data["facts"]["us-gaap"].get(tag, {}).get("units", {}).get("USD", ()):
                if fact["form"] != "10-K" or "start" not in fact or fact.get("fp") != "FY":
                    continue
                start, stop, filed = (date.fromisoformat(fact[field]) for field in ("start", "end", "filed"))
                if 350 <= (stop - start).days <= 380 and 0 <= (filed - stop).days <= 100:
                    annual.setdefault((stop, filed), (start, fact, tag))
        for (stop, filed), (start, fact, tag) in sorted(annual.items()):
            parts = sorted((row for day, row in quarters.items() if start < day < stop and row["filed"] <= filed
                            and row["fp"] != "Q4"), key=lambda row: row["end"])
            if [row["fp"] for row in parts] != ["Q1", "Q2", "Q3"]:
                continue
            gross = Decimal(str(fact["val"]))
            amounts = [row["values"]["revenue"][0] for row in parts]
            if gross > sum(amounts):
                quarters.setdefault(stop, {"end": stop, "filed": filed, "accession": fact["accn"], "fp": "Q4",
                                           "values": {"revenue": (gross - sum(amounts), tag)},
                                           "annual": gross, "components": parts})
        result[ticker] = list(quarters.values())
    return result


def add_revenue_history(event, ticker, rows, fiscal_quarters, method):
    periods = sorted(quarter.period_end for quarter in event.earnings_plan.quarters)
    visible = sorted((row for row in rows if end_of_day(row["filed"]) <= event.as_of and row["end"] < periods[0]),
                     key=lambda row: row["end"])[-18:]
    documents = list(event.documents)
    history = []

    def add_source(row):
        day = row["end"].isoformat()
        identifier = f"revenue-history-{day}"
        if identifier in {doc.id for doc in documents}:
            return f"{identifier}:revenue"
        accession = row["accession"]
        revenue, tag = row["values"]["revenue"]
        when = end_of_day(row["filed"])
        description = f"{day} 結束的單季 US GAAP 合併營收 {revenue} 美元（{tag}）。"
        if "annual" in row:
            amounts = "、".join(str(part["values"]["revenue"][0]) for part in row["components"])
            description += f"第四季以全年 {row['annual']} 美元減前三季 {amounts} 美元計算。"
        documents.append(Document(id=identifier, kind="disclosure", text_format="summary",
                                  availability_basis="replay_day_end", published_at=when, obtained_at=when,
                                  source=f"https://www.sec.gov/Archives/edgar/data/{int(CIKS[ticker])}/{accession.replace('-', '')}/{accession}-index.htm",
                                  paragraphs={"revenue": description}))
        return f"{identifier}:revenue"

    for row in visible:
        refs = [add_source(row), *(add_source(part) for part in row.get("components", []))]
        history.append({"period_end": row["end"], "fiscal_quarter": int(row["fp"][-1]),
                        "value": row["values"]["revenue"][0], "available_at": end_of_day(row["filed"]),
                        "evidence_ids": refs, "method": "全年減前三季" if "annual" in row else "原始單季申報"})
    bridge = RevenueBridge(period_end=periods[1], currency=event.earnings_plan.currency,
                           basis=event.earnings_plan.basis, near_fiscal_quarter=fiscal_quarters[0],
                           far_fiscal_quarter=fiscal_quarters[1], method=method, history=history)
    return event.model_copy(update={"documents": documents,
                                     "earnings_plan": event.earnings_plan.model_copy(update={"revenue_bridge": bridge})})
