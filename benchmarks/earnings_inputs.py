"""Build dated EPS assumptions and load verified historical issuer guidance."""

import csv
from datetime import datetime, time, timezone
from decimal import Decimal, localcontext
import json
from statistics import median

from research_app.schema import Document, EPSAssumptions, EstimateReference

from .earnings_cases import TICKERS, filing_index

PRETAX_TAGS = ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
               "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments")
TAX_TAGS = ("IncomeTaxExpenseBenefit",)
EPS_ISSUER_FIELDS = {"discrete_tax_expense", "tax_rate"}


def end_of_day(day):
    return datetime.combine(day, time(23, 59, 59), tzinfo=timezone.utc)


def accounting_facts(company_facts):
    index = {}
    gaap = company_facts["facts"]["us-gaap"]
    for tags in (PRETAX_TAGS, TAX_TAGS):
        for tag in tags:
            for row in gaap.get(tag, {}).get("units", {}).get("USD", ()):
                if row["form"] != "10-Q" or "start" not in row:
                    continue
                days = (datetime.fromisoformat(row["end"]) - datetime.fromisoformat(row["start"])).days
                if 75 <= days <= 110:
                    key = row["accn"], row["end"], row["filed"]
                    index.setdefault(key, {}).setdefault(tags[0], (Decimal(str(row["val"])), tag))
    return index


def financial_history(sec_dir, tickers=TICKERS):
    history = {}
    for ticker in tickers:
        data = json.loads((sec_dir / f"{ticker}.json").read_text(encoding="utf-8"))
        history[ticker] = filing_index(data).values(), accounting_facts(data)
    return history


def load_guidance(path):
    guide = {}
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            guide.setdefault(row["case"], []).append(row)
    return guide


def add_guidance(event, rows):
    documents, references, event_values = list(event.documents), list(event.earnings_plan.references), list(event.earnings_plan.event_values)
    periods = [row.period_end for row in event.earnings_plan.quarters]
    for number, row in enumerate(rows, 1):
        horizon = int(row["quarter_ahead"])
        if not 1 <= horizon <= len(periods):
            raise ValueError("指引期距須對應預先登記的預測季度")
        available = end_of_day(datetime.fromisoformat(row["published_on"]).date())
        if available > event.as_of:
            raise ValueError("指引新聞稿晚於研究截止時點")
        document_id = f"issuer-guidance-{number}"
        document = Document(
            id=document_id, source=row["source"], kind="disclosure", text_format="summary",
            availability_basis="replay_day_end", published_at=available, obtained_at=available,
            paragraphs={"outlook": row["summary"]},
        )
        documents.append(document)
        if row["metric"] in EPS_ISSUER_FIELDS:
            continue
        key = {"period_end": periods[horizon - 1], "scope": "consolidated", "basis": row["basis"],
               "currency": row["currency"], "duration": "quarter", "metric": row["metric"]}
        reference = EstimateReference(key=key, kind="issuer_guidance", label="公司當時公開的單季展望",
                                      available_at=available, low=row["low"], high=row["high"],
                                      evidence_ids=[f"{document_id}:outlook"])
        bucket = references if available < event.earnings_plan.event_at else event_values
        bucket.append(reference)
    plan = event.earnings_plan.model_copy(update={"references": references, "event_values": event_values})
    return event.model_copy(update={"documents": documents, "earnings_plan": plan})


def add_eps_assumptions(event, ticker, history, issuer_rows=(), *, cik=None):
    filings, facts = history[ticker]
    recent = sorted((row for row in filings if end_of_day(row["filed"]) <= event.as_of),
                    key=lambda row: row["end"], reverse=True)[:4]
    if not recent:
        raise ValueError(f"{ticker} 缺少可得的歷史申報資料")
    documents, tax_samples, nonop_samples = list(event.documents), [], []
    for filing in recent:
        key = filing["accession"], filing["end"].isoformat(), filing["filed"].isoformat()
        extra = facts.get(key, {})
        pretax = extra.get(PRETAX_TAGS[0])
        expense = extra.get(TAX_TAGS[0])
        recorded_at = end_of_day(filing["filed"])
        doc_id = f"eps-history-{key[1]}"
        accession = filing["accession"]
        operating_income = filing["values"]["operating_income"][0]
        shares = filing["values"]["shares"][0]
        values = [f"營業利益 {operating_income} 美元，稀釋加權平均股數 {shares} 股。"]
        if pretax:
            values.append(f"稅前盈餘 {pretax[0]} 美元（{pretax[1]}）。")
        if expense:
            values.append(f"所得稅費用 {expense[0]} 美元（{expense[1]}）。")
        document = Document(
            id=doc_id,
            source=f"https://www.sec.gov/Archives/edgar/data/{int(cik or TICKERS[ticker])}/{accession.replace('-', '')}/{accession}-index.htm",
            kind="disclosure", text_format="summary", availability_basis="replay_day_end",
            published_at=recorded_at, obtained_at=recorded_at,
            paragraphs={"accounting": f"截至 {key[1]} 的 US GAAP 單季。{''.join(values)}"},
        )
        documents.append(document)
        if pretax:
            nonop_samples.append((pretax[0] - operating_income, document))
        if pretax and expense and pretax[0] > 0:
            with localcontext() as ctx:
                ctx.prec = 40
                rate = expense[0] / pretax[0]
            if 0 <= rate <= Decimal("0.45"):
                tax_samples.append((rate.quantize(Decimal("0.00000001")), document))

    def assumption(samples, fallback, method, missing_method):
        used = [row[1] for row in samples] or [documents[-len(recent)]]
        value = median(row[0] for row in samples) if samples else fallback
        return {"value": value.quantize(Decimal("0.00000001")),
                "available_at": max(doc.obtained_at for doc in used),
                "evidence_ids": [f"{doc.id}:accounting" for doc in used],
                "method": method if samples else missing_method}

    tax = assumption(tax_samples, Decimal("0.21"),
                     "最近四個可得的 10-Q 單季中，以稅前獲利且有效稅率介於 0–45% 的樣本取中位數。",
                     "可得歷史季缺少符合條件的有效稅率，以 21% 作模型假設。")
    diluted = assumption([(recent[0]["values"]["shares"][0], documents[-len(recent)])], 0,
                         "沿用最近已公開季度的加權平均稀釋股數。", "")
    nonoperating = assumption(nonop_samples, Decimal(0),
                              "取近期同口徑稅前盈餘與營業利益差額的中位數作經常性代理。",
                              "資料缺少稅前盈餘對帳，暫以零作經常性營業外損益假設。")
    discrete, issuer_taxes = {}, {}
    for number, row in enumerate(issuer_rows, 1):
        if row["metric"] not in EPS_ISSUER_FIELDS:
            continue
        if (row["basis"], row["currency"]) != (event.earnings_plan.basis, event.earnings_plan.currency):
            continue
        target = event.earnings_plan.quarters[int(row["quarter_ahead"]) - 1].period_end
        item = {"available_at": end_of_day(datetime.fromisoformat(row["published_on"]).date()),
                "evidence_ids": [f"issuer-guidance-{number}:outlook"]}
        if row["metric"] == "tax_rate":
            issuer_taxes[target] = {**item, "value": (Decimal(row["low"]) + Decimal(row["high"])) / 2,
                                    "method": "使用公司公開的同季同會計口徑稅率展望。"}
            continue
        if row["low"] != row["high"]:
            raise ValueError("單列所得稅項目須為明確單點")
        discrete.setdefault(target, []).append({
            "label": "發行人預估的一次性所得稅項目", "treatment": "income_tax_expense", "value": row["low"],
            **item, "method": "按當季公開展望單列，負值表示稅務利益。",
        })
    if discrete.keys() & issuer_taxes.keys():
        raise ValueError("有效稅率指引與一次性所得稅項目同時提供，須先確認是否重複計入")
    profiles = [EPSAssumptions(period_end=quarter.period_end, tax_rate=issuer_taxes.get(quarter.period_end, tax), diluted_shares=diluted,
                               recurring_nonoperating=nonoperating, one_offs=discrete.get(quarter.period_end, []))
                for quarter in event.earnings_plan.quarters]
    return event.model_copy(update={"documents": documents,
                                     "earnings_plan": event.earnings_plan.model_copy(update={"eps_assumptions": profiles})})
