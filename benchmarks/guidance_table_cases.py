"""Prepare independent gold operands and archive complete releases in print order."""
from datetime import date, datetime, time
from hashlib import sha256
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

from benchmarks import guidance_arithmetic as b
from benchmarks.guidance_ytd_cases import CLOSED, ITEMS, URLS as EARLIER_URLS, guidance

OUT = Path("output/guidance-table")
URLS = {
    "blze-prior": "https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf",
    "blze-latest": "https://s204.q4cdn.com/590551802/files/doc_financials/2025/q1/BLZE-Q3-2024-Earnings-Press-Release-1.pdf",
    "mdt-prior": "https://news.medtronic.com/2024-11-19-Medtronic-reports-second-quarter-fiscal-2025-financial-results?asPDF=1",
    "mdt-latest": "https://news.medtronic.com/2025-02-18-Medtronic-reports-third-quarter-fiscal-2025-financial-results?asPDF=1",
    "frsh-prior": "https://s21.q4cdn.com/987526491/files/doc_events/2024/07/Q2-24-Quarterly-Earnings-Release.pdf",
    "frsh-latest": "https://s21.q4cdn.com/987526491/files/doc_events/2024/11/freshworks_third_quarter_2024_earnings_release.pdf",
    "cdw-prior": "https://s205.q4cdn.com/557255526/files/doc_news/2024/07/1/CDW-2024-6-30-Earnings-Release.pdf",
    "cdw-latest": "https://s205.q4cdn.com/557255526/files/doc_financials/2024/q3/CDW-2024-9-30-Earnings-Release.pdf",
    "crm-prior": "https://investor.salesforce.com/files/doc_financials/2025/q2/CRM-Q2-FY25-Earnings-Press-Release-w-financials.pdf",
    "crm-latest": "https://investor.salesforce.com/files/doc_financials/2025/q3/CRM-Q3-FY25-Earnings-Press-Release-w-financials.pdf",
    "low-prior": "https://corporate.lowes.com/sites/lowes-corp/files/2024-08/q2-2024-earnings-release.pdf",
    "low-latest": "https://corporate.lowes.com/sites/lowes-corp/files/2024-11/q3-2024-earnings-release.pdf",
    "wmt-prior": "https://stock.walmart.com/_assets/_5813cf69129ed45d080396680f549a44/walmart/db/938/9486/earnings_release/Earnings-Release-2025-Q2.pdf",
    "wmt-latest": "https://corporate.walmart.com/content/dam/corporate/documents/newsroom/2024/11/19/walmart-releases-q3-fy25-earnings/q3-fy25-earnings-release.pdf",
    "docn-prior": "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001582961/082a1066-1be0-49b0-a692-e13e9e106cac.pdf",
    "docn-latest": "https://cdn.prod.nntech.io/company-events/reports/69e45bc4-e04d-32a0-a1b7-ee48f33dc56b/report.pdf",
    "net-prior": "https://www.cloudflare.net/files/doc_financials/2024/q2/Q2-24-Exhibit-99-1_final.pdf",
    "net-latest": "https://cloudflare.net/files/doc_financials/2024/q3/Q3-24-Exhibit-99-1.pdf",
    "okta-prior": "https://cdn.prod.nntech.io/company-events/reports/14d748af-eba3-3fa0-b662-8786dd9a178d/report.pdf",
    "okta-latest": "https://cdn.prod.nntech.io/company-events/reports/a206ef16-5b5b-33e8-b4ba-a1b1aab065e0/report.pdf",
    "snow-prior": "https://cdn.prod.nntech.io/company-events/reports/4ed104a9-7f76-3aac-9c04-5604fb7c734e/report.pdf",
    "snow-latest": "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/ca80b036-253b-49b4-a6ce-69de8d98b8eb.pdf"
}
URLS.update({key: EARLIER_URLS[key] for key in ("path-prior", "path-latest")})
ORIGINS = {
    "docn-latest": "https://www.sec.gov/Archives/edgar/data/1582961/000158296124000153/a2024-q3dopressrelease.htm",
    "okta-prior": "https://investor.okta.com/news-releases/news-release-details/okta-announces-second-quarter-fiscal-year-2025-financial-results",
    "okta-latest": "https://investor.okta.com/news-releases/news-release-details/okta-announces-third-quarter-fiscal-year-2025-financial-results",
    "snow-prior": "https://investors.snowflake.com/news/news-details/2024/Snowflake-Reports-Financial-Results-for-the-Second-Quarter-of-Fiscal-2025/default.aspx",
}
JUN_SEP = ("2024-06-30", "2024-09-30")
JUL_OCT = ("2024-07-31", "2024-10-31")

# Manually reviewed outlook quotes (prior annual, prior Q3, latest annual) and YTD cells (prior, latest).
POSITIVES = {
    "frsh": ("pilot", "Freshworks", "FRSH", 2024, ("2024-07-30", "2024-11-06"), JUN_SEP,
             ("$707.0 - $713.0", "$180.0 - $183.0", "$713.6 - $716.6", "339,274", "525,849",
              "($ in millions, except per share data)"),
             "期間、期末與年份分行，營收列和數字用點線分隔。"),
    "crm": ("pilot", "Salesforce", "CRM", 2025, ("2024-08-28", "2024-12-03"), JUL_OCT,
            ("$37.7 Billion to $38.0 Billion", "$9.31 Billion to $9.36 Billion", "$37.8 Billion to $38.0 Billion",
             "18,458", "27,902", None),
            "跨欄期間與年份分行。合併金額涵蓋訂閱支援與專業服務。"),
    "blze": ("holdout", "Backblaze", "BLZE", 2024, ("2024-08-08", "2024-11-07"), JUN_SEP,
             ("$126.5 million to $128.5 million", "$32.4 million to $32.8 million", "$127.0 million to $128.0 million",
              "61,253", "93,842", None),
             "最新公告的營運表標題與千元倍率在前一實體頁，累計期間和金額在次頁。"),
    "docn": ("holdout", "DigitalOcean", "DOCN", 2024, ("2024-08-08", "2024-11-04"), JUN_SEP,
             ("$770 to $775 million", "$196 to $197 million", "$775 to $777 million", "377,206", "575,690", None),
             "單季與累計在同表，期間、期末和年份分三行。"),
    "net": ("holdout", "Cloudflare", "NET", 2024, ("2024-08-01", "2024-11-07"), JUN_SEP,
            ("$1,657.0 to $1,659.0 million", "$423.0 to $424.0 million", "$1,661.0 to $1,662.0 million",
             "779,598", "1,209,680", None),
            "兩個跨欄期間各有第二行截止日和第三行年份。"),
    "okta": ("holdout", "Okta", "OKTA", 2025, ("2024-08-28", "2024-12-03"), JUL_OCT,
             ("$2.555 billion to $2.565 billion", "$648 million to $650 million", "$2.595 billion to $2.597 billion",
              "1,263", "1,928", None),
             "期間分行，同一表頭把美元百萬與股數千分開聲明。"),
}
NEGATIVES = {
    "low": ("pilot", "Lowe’s", "LOW", 2024, ("2024-08-20", "2024-11-19"), ("2024-08-02", "2024-11-01"),
            "前次有全年銷售指引，缺第三季合併銷售美元指引。",
            "prior", "Total sales of $82.7 to $83.2 billion",
            ("prior_interim", "comparable sales", "prior q3", "third quarter", "第三季", "Q3")),
    "mdt": ("pilot", "Medtronic", "MDT", 2025, ("2024-11-19", "2025-02-18"), ("2024-10-25", "2025-01-24"),
            "排除匯率等因素的有機成長率，無法證明同口徑合併營收美元。",
            "prior", "raised its FY25 organic revenue growth guidance",
            ("prior_interim", "organic", "有機", "成長率", "dollar revenue", "第三季", "Q3")),
    "path": ("holdout", "UiPath", "PATH", 2025, ("2024-09-05", "2024-12-05"), JUL_OCT,
             "最新公告只列 Q4 獨立指引，沒有可用累計倒推的新全年營收。",
             "latest", "For the fourth quarter fiscal 2025, UiPath expects",
             ("new figure", "new annual", "full year", "full-year", "annual", "全年", "第四季", "Q4")),
    "wmt": ("holdout", "Walmart", "WMT", 2025, ("2024-08-15", "2024-11-19"), JUL_OCT,
            "季度及全年指引為固定匯率的淨銷售增率，無法定位當期合併營收美元。",
            "prior", "for Q3 and raises its outlook for FY25",
            ("prior_interim", "constant currency", "固定匯率", "constant-currency", "sales growth", "net sales")),
    "cdw": ("holdout", "CDW", "CDW", 2024, ("2024-07-31", "2024-10-30"), JUN_SEP,
            "公告列合併實績與調整後業績，缺第三季及全年可比美元營收指引。",
            "prior", "announced second quarter 2024 results",
            ("prior_interim", "prior q3", "third quarter", "guidance", "指引", "展望", "第三季", "Q3")),
    "snow": ("holdout", "Snowflake", "SNOW", 2025, ("2024-08-21", "2024-11-20"), JUL_OCT,
             "指引限產品收入，排除合併營收內的專業服務與其他。",
             "prior", "The following table summarizes our guidance for the full-year fiscal 2025",
             ("prior_interim", "product revenue", "產品營收", "產品收入", "professional services", "專業服務")),
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def archive(root, key, vintage, day):
    name = f"{key}-{vintage}"
    pdf = root / "filings" / f"{name}.pdf"
    pages = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True).split("\f")
    indexed = [(page, [line for line in content.splitlines() if line.strip()])
               for page, content in enumerate(pages, 1) if content.strip()]
    path = pdf.with_suffix(".pages.txt")
    path.write_text("\n\n".join(f"[PDF page {page}]\n" + "\n".join(lines) for page, lines in indexed) + "\n")
    stamp = datetime.combine(date.fromisoformat(day), time(23, 59, 59), ZoneInfo("America/New_York"))
    doc = b.ArchivedDocument(id=name, source_url=URLS[name], path=str(path), sha256=digest(path),
                             published_at=stamp, obtained_at=stamp, content_type="text/plain")
    blocks = b.load_blocks(doc)
    if len(blocks) != len(indexed):
        raise ValueError(f"missing parsed page in {name}")
    return doc, blocks, indexed, {"source": URLS[name], "issuer_or_sec_origin": ORIGINS.get(name, URLS[name]),
           "pdf": str(pdf), "pdf_sha256": digest(pdf), "text_sha256": digest(path), "pages": len(indexed)}


def actual_anchor(doc, indexed, raw, year, quarter, end):
    # Check already selected gold amounts against the printed rows independently of the two validators.
    title, scope, candidates = None, [], []
    for page, lines in indexed:
        for number, line in enumerate(lines, 1):
            item = {"block": f"{doc.id}:p{page:04d}", "line": number, "quote": line.strip()}
            if re.search(r"consolidated statements of operations", line, re.I):
                title, scope = item, []
            elif re.search(r"consolidated statements of (?:cash flows|stockholders)|gaap to non-gaap|consolidated balance sheets",
                           line, re.I):
                title = None
            elif title:
                label = re.match(r"^\s*(?:total\s+)?revenues?\b", line, re.I)
                if label and raw in line and re.search(r"(?:^|\D)" + re.escape(raw) + r"(?:\D|$)", line):
                    units = [ref for ref in scope if re.search(r"in (?:thousands|millions)", ref["quote"], re.I)]
                    period = "six" if quarter == 2 else "nine"
                    heading = [ref for ref in scope if (re.search(fr"\b{period} months ended", ref["quote"], re.I) or
                               end.strftime("%B %d").replace(" 0", " ") in ref["quote"] or str(end.year) in ref["quote"])]
                    if units and heading and len(scope) < 14:
                        factor = 1_000 if "in thousands" in units[0]["quote"].lower().split(",")[0] else 1_000_000
                        candidates.append({"row": item, "units": units, "heading": heading, "table": title,
                                           "raw": raw, "column": 3, "multiplier": factor, "fiscal_year": year,
                                           "equivalent_amounts": [raw, "$" + raw, "$ " + raw]})
                scope.append(item)
    if len(candidates) != 1:
        raise ValueError(f"{doc.id}: expected one reviewed consolidated row for {raw}, got {len(candidates)}")
    return candidates[0]


def build(root, key, spec, positive):
    split, issuer, ticker, year, releases, ends, *details = spec
    prior, older, older_pages, a = archive(root, key, "prior", releases[0])
    latest, newer, newer_pages, c = archive(root, key, "latest", releases[1])
    if positive:
        (old_fy, old_q3, new_fy, old_ytd, new_ytd, unit), classification = details
        figures = {"prior": guidance(prior, older, old_fy, unit), "prior_interim": guidance(prior, older, old_q3, unit),
                   "new": guidance(latest, newer, new_fy, unit)}
        anchors = {}
        for name, doc, pages, amount, quarter, end in zip(("prior_reported_in_period", "reported_in_period"),
                (prior, latest), (older_pages, newer_pages), (old_ytd, new_ytd), (2, 3), ends):
            anchor = actual_anchor(doc, pages, amount, year, quarter, date.fromisoformat(end))
            anchors[name] = anchor
            units = anchor["units"][0]
            figures[name] = [{"document": doc.id, "block": anchor["row"]["block"], "quote": amount, "tabular": True,
                              "unit_block": units["block"], "unit_quote": units["quote"]}]
        items, gap, fields = ITEMS, {}, {"gold_columns": anchors}
    else:
        classification, vintage, wording, terms = details
        items, figures, gap = CLOSED, {}, dict.fromkeys(CLOSED, classification)
        blocks = older if vintage == "prior" else newer
        anchors = [block for block, data in blocks.items() if b.normalize(wording) in b.normalize(data["text"])]
        if len(anchors) != 1:
            raise ValueError(f"{key}: negative locator not unique: {anchors}")
        fields = {"gap_terms": list(terms), "gap_anchor": {"blocks": anchors, "quote": wording}}
    case = b.Case(id=key, split=split, ticker=ticker, issuer=issuer, precision="1000",
                  event_at=latest.published_at, as_of=latest.published_at, documents=[prior, latest],
                  figures=figures, style="implicit", items=items, undetermined=gap, trap=classification,
                  labels={"period": f"fiscal {year}", "interim": f"the third quarter of fiscal {year}",
                          "remainder": f"the fourth quarter of fiscal {year}"})
    return {"case": case.model_dump(mode="json"), "vintages": {doc.id: {
            "report_end": end, "fiscal_year": year, "quarter": quarter}
            for doc, end, quarter in zip((prior, latest), ends, (2, 3))}, **fields}, {prior.id: a, latest.id: c}


def main(root=OUT):
    rows, sources = [], {}
    for phase in ("pilot", "holdout"):
        for positive, specs in ((True, POSITIVES), (False, NEGATIVES)):
            for key, spec in specs.items():
                if spec[0] == phase:
                    row, ledger = build(root, key, spec, positive)
                    rows.append(row)
                    sources.update(ledger)
    b.equal.journal.atomic(root / "case-input.json", rows)
    b.equal.journal.atomic(root / "source-ledger.json", sources)


if __name__ == "__main__":
    main()
