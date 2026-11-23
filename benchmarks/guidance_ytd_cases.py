"""Archive issuer releases and manually locate the independent gold inputs."""
from hashlib import sha256
from pathlib import Path
import re
import subprocess

from benchmarks import guidance_arithmetic as b
from benchmarks.guidance_ytd import REVENUE, TITLE, MONEY_MARK, DURATION

ROOT = Path("output/guidance-ytd")
FILES = ROOT / "filings"
URLS = {
    "path-prior": "https://d1io3yog0oux5.cloudfront.net/_2051b5e4c9064e8776da85f780848e5c/uipath/news/2024-09-05_UiPath_Reports_Second_Quarter_Fiscal_2025_358.pdf",
    "path-latest": "https://d1io3yog0oux5.cloudfront.net/_5131cd3f5bd0cd883829934c5dab15cd/uipath/news/2024-12-05_UiPath_Reports_Third_Quarter_Fiscal_2025_373.pdf",
    "docu-prior": "https://s21.q4cdn.com/706790701/files/doc_financials/2025/q2/7706ac78-b4f6-4e99-818b-c8fc0b5de9a0.pdf",
    "docu-latest": "https://s21.q4cdn.com/706790701/files/doc_news/Docusign-Announces-Third-Quarter-Fiscal-2025-Financial-Results-2024.pdf",
    "crwd-prior": "https://ir.crowdstrike.com/node/13426/pdf",
    "crwd-latest": "https://ir.crowdstrike.com/node/13821/pdf",
    "yeti-prior": "https://s22.q4cdn.com/322452763/files/doc_financials/2024/q2/YETI-Reports-Second-Quarter-2024-Results-2024.pdf",
    "yeti-latest": "https://s22.q4cdn.com/322452763/files/doc_financials/2024/q3/YETI-Reports-Third-Quarter-2024-Results-2024.pdf",
    "box-prior": "https://s21.q4cdn.com/328470014/files/doc_news/Box-Reports-Fiscal-Second-Quarter-2025-Financial-Results-2024.pdf",
    "box-latest": "https://s21.q4cdn.com/328470014/files/doc_news/Box-Reports-Fiscal-Third-Quarter-2025-Financial-Results-2024.pdf",
    "s-latest": "https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q3/earnings-result/Q3-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf",
    "s-prior": "https://s28.q4cdn.com/399982429/files/doc_earnings/2025/q2/earnings-result/Q2-FY25-Earnings-Press-Release-FINAL-SentinelOne.pdf",
    "pd-prior": "https://s23.q4cdn.com/247028398/files/doc_news/PagerDuty-Announces-Second-Quarter-Fiscal-2025-Financial-Results-2024.pdf",
    "pd-latest": "https://s23.q4cdn.com/247028398/files/doc_news/PagerDuty-Announces-Third-Quarter-Fiscal-2025-Financial-Results-2024.pdf",
    "hd-prior": "https://ir.homedepot.com/~/media/Files/H/HomeDepot-IR/press-release/q2-2024-earning-release.pdf",
    "hd-latest": "https://ir.homedepot.com/~/media/Files/H/HomeDepot-IR/press-release/q3-2024-earning-release.pdf",
    "deck-prior": "https://d18rn0p25nwr6d.cloudfront.net/CIK-0000910521/5cecef8a-b608-488a-8a1c-629f0fd54187.pdf",
    "deck-latest": "https://d18rn0p25nwr6d.cloudfront.net/CIK-0000910521/c55b9dbd-d813-47e6-8399-fce0ecee367d.pdf",
    "tgt-prior": "https://corporate.target.com/getmedia/50a20b2e-c394-4ae2-ab73-8afcf99b4e0c/Target-Corporation-Reports-Second-Quarter-Earnings.pdf",
    "tgt-latest": "https://corporate.target.com/getmedia/9bb5f514-fcaf-4097-837d-f08ff31cb089/Target-Corporation-Reports-Third-Quarter-Earnings.pdf",
    "cost-prior": "https://s201.q4cdn.com/287523651/files/doc_news/Costco-Wholesale-Corporation-Reports-Second-Quarter-and-Year-To-Date-Operating-Results-For-Fiscal-2025-and-February-Sales-Results-2025.pdf",
    "cost-latest": "https://s201.q4cdn.com/287523651/files/doc_news/Costco-Wholesale-Corporation-Reports-Third-Quarter-and-Year-To-Date-Operating-Results-for-Fiscal-2025-2025.pdf",
    "wday-prior": "https://s23.q4cdn.com/175719177/files/doc_news/Workday-Announces-Fiscal-2025-Second-Quarter-Financial-Results-2024.pdf",
    "wday-latest": "https://s21.q4cdn.com/950027458/files/doc_news/Workday-Announces-Fiscal-2025-Third-Quarter-Financial-Results-11-26-2024-2024.pdf",
    "sprt-prior": "https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q2/earnings-result/Sprout-Social-2Q24-Earnings-Release.pdf",
    "sprt-latest": "https://s203.q4cdn.com/239200346/files/doc_earnings/2024/q3/earnings-result/Sprout-Social-3Q24-Earnings-Release.pdf",
    "docs-prior": "https://s201.q4cdn.com/617428576/files/doc_financials/2025/q2/Doximity-2Q25-Earnings-Call-Press-Release.pdf",
    "docs-latest": "https://s201.q4cdn.com/617428576/files/doc_financials/2025/q3/Doximity-3Q25-Earnings-Call-Press-Release.pdf",
    "mndy-prior": "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001845338/a0415556-b4a7-4c55-88b4-3794d88dbf9c.pdf",
    "mndy-latest": "https://s29.q4cdn.com/881027206/files/doc_financials/2024/q3/Q3-24-PR.pdf",
    "blze-prior": "https://s204.q4cdn.com/590551802/files/doc_news/2024/08/Backblaze-Announces-Second-Quarter-2024-Financial-Results.pdf",
    "blze-latest": "https://s204.q4cdn.com/590551802/files/doc_news/2024/11/Backblaze-Announces-Record-Adjusted-EBITDA-Margin-as-Part-of-Third-Quarter-2024-Financial-Results.pdf",
    "rng-prior": "https://s24.q4cdn.com/639777509/files/doc_news/RingCentral-Announces-Second-Quarter-2024-Results-2024.pdf",
    "rng-latest": "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001384905/698a3372-5d55-497e-936a-4ac8331d1bb1.pdf"
}
URLS.update({
    "frog-prior": "https://s21.q4cdn.com/528621000/files/doc_news/2024/08/1/JFrog-Q2-2024-Earnings-PR_FINAL.pdf",
    "frog-latest": "https://s21.q4cdn.com/528621000/files/doc_financials/2024/q3/FINAL-JFrog-Q3-2024-Earnings-PR_11-7.pdf",
})
ITEMS = ["implied_remainder_prior", "implied_remainder_new", "implied_remainder_change", "implied_remainder"]
CLOSED = ["implied_remainder_prior", "implied_remainder_change", "implied_remainder"]

# Each gold amount is independently checked against the issuer's actual page.
# Tuple order is prior annual, prior Q3, latest annual, prior YTD, latest YTD, optional guidance units.
STANDARD = {
    "docu": ("pilot", "Docusign", "DOCU", 2025, ("2024-09-05", "2024-12-05"), ("2024-07-31", "2024-10-31"),
             ("$2,940 to $2,952", "$743 to $747", "$2,959 to $2,963", "1,445,667", "2,200,487", "in millions, except percentages")),
    "sprt": ("pilot", "Sprout Social", "SPT", 2024, ("2024-08-01", "2024-11-07"), ("2024-06-30", "2024-09-30"),
             ("between $405.0 million and $406.0 million", "between $101.9 million and $102.1 million",
              "between $405.1 million and $405.9 million", "196,180", "298,818", None)),
    "yeti": ("pilot", "YETI", "YETI", 2024, ("2024-08-08", "2024-11-07"), ("2024-06-29", "2024-09-28"),
             "The prior release does not provide a Q3 consolidated net sales dollar outlook. Annual revenue growth rates do not supply it."),
    "wday": ("pilot", "Workday", "WDAY", 2025, ("2024-08-22", "2024-11-26"), ("2024-07-31", "2024-10-31"),
             "The outlook is subscription revenue; it does not establish comparable consolidated total revenue guidance."),
    "s": ("holdout", "SentinelOne", "S", 2025, ("2024-08-27", "2024-12-04"), ("2024-07-31", "2024-10-31"),
          ("$815 million", "$209.5 million", "$818 million", "385,292", "595,940", None)),
    "docs": ("holdout", "Doximity", "DOCS", 2025, ("2024-11-07", "2025-02-06"), ("2024-09-30", "2024-12-31"),
             ("between $535 million and $540 million", "between $152 million and $153 million",
              "between $564.6 million and $565.6 million", "263,508", "432,111", None)),
    "mndy": ("holdout", "monday.com", "MNDY", 2024, ("2024-08-12", "2024-11-11"), ("2024-06-30", "2024-09-30"),
             ("$956 million to $961 million", "$243 million to $247 million",
              "$964 million to $966 million", "453,019", "704,019", None)),
    "frog": ("holdout", "JFrog", "FROG", 2024, ("2024-08-07", "2024-11-07"), ("2024-06-30", "2024-09-30"),
             ("$422 million to $424 million", "between $105 million and $106 million",
              "$425.9 million to $ 426.9 million", "203,354", "312,410", None)),
    "hd": ("holdout", "Home Depot", "HD", 2024, ("2024-08-13", "2024-11-12"), ("2024-07-28", "2024-10-27"),
           "Fiscal-year sales growth guidance and SRS contribution do not establish a prior Q3 USD revenue guidance at the same consolidated scope."),
    "tgt": ("holdout", "Target", "TGT", 2024, ("2024-08-21", "2024-11-20"), ("2024-08-03", "2024-11-02"),
            "Quarterly comparable sales and diluted EPS outlook are not a Q3 consolidated revenue dollar estimate."),
    "cost": ("holdout", "Costco", "COST", 2025, ("2025-03-06", "2025-05-29"), ("2025-02-16", "2025-05-11"),
             "Both announcements provide actual net sales and comparisons, without the prior Q3 or comparable full-year revenue outlook."),
    "deck": ("holdout", "Deckers", "DECK", 2025, ("2024-10-24", "2025-01-30"), ("2024-09-30", "2024-12-31"),
             "Annual net sales can be disclosed, but the prior release does not publish a comparable Q3 total net sales amount."),
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def words(text):
    return " ".join(text.split())


def archive(key, vintage, day):
    name = f"{key}-{vintage}"
    pdf = FILES / f"{name}.pdf"
    pages = subprocess.check_output(["pdftotext","-layout",str(pdf),"-"],text=True).split("\f")
    if not pages[-1].strip():
        pages.pop()
    if name == "mndy-prior":
        # Keep the filing cover and the complete Exhibit 99.1, with original page numbers.
        finish = next((i for i, page in enumerate(pages) if i > 5 and
            "AS OF JUNE 30, 2024" in page and "FINANCIAL STATEMENTS" in page), len(pages))
        if finish == len(pages):
            raise ValueError("could not locate the following exhibit in monday.com 6-K")
        pages = pages[:finish]
    if any(not page.strip() for page in pages):
        raise ValueError(f"blank input page in {pdf}")
    for i in range(1, len(pages)):
        preceding = [line for line in pages[i - 1].splitlines() if line.strip()][-5:]
        following = [line for line in pages[i].splitlines() if line.strip()][:4]
        title = next((j for j, line in enumerate(preceding) if TITLE.search(line)), None)
        # A PDF can place its table title and units on the preceding physical page.
        if title is not None and any("in thousands" in line for line in preceding[title:]) and any(
                DURATION.search(line) for line in following) and not any(TITLE.search(line) for line in following):
            prefix = "\n".join(line for line in preceding[title:] if not line.strip().isdigit())
            pages[i] = prefix + "\n" + pages[i]
    source = FILES / f"{name}.pages.txt"
    source.write_text("\n\n".join(f"[PDF page {i}]\n" + "\n".join(
        line for line in page.splitlines() if line.strip()) for i, page in enumerate(pages, 1)) + "\n")
    from datetime import date, datetime, time
    from zoneinfo import ZoneInfo
    stamp = datetime.combine(date.fromisoformat(day), time(23, 59, 59), tzinfo=ZoneInfo("America/New_York")).isoformat()
    doc = b.ArchivedDocument(id=name, source_url=URLS[name], path=str(source), sha256=digest(source),
                             published_at=stamp, obtained_at=stamp, content_type="text/plain")
    blocks = b.load_blocks(doc)
    if len(blocks) != len(pages):
        raise ValueError(f"PDF page blocks disagree for {name}")
    return doc, blocks, pages, {"pdf": str(pdf), "sha256": digest(pdf), "text_sha256": digest(source),
                                "source": URLS[name], "pages": len(pages)}


def guidance(doc, blocks, amount, unit):
    possible = [key for key, row in blocks.items() if amount in row["text"]]
    if len(possible) != 1:
        raise ValueError(f"{doc.id} expected one page for {amount}: {possible}")
    key, = possible
    units = None
    if unit:
        if unit not in blocks[key]["text"]:
            raise ValueError(f"{doc.id} expected guidance units on {key}")
        units = {"unit_block": key, "unit_quote": unit, "tabular": True}
    return [{"document": doc.id, "block": key, "quote": amount, **(units or {})}]


def money_table(doc, blocks, pages, amount):
    for page, text in enumerate(pages, 1):
        lines = [line for line in text.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            total = REVENUE.search(line) or (doc.id.startswith("frog-") and
                re.match(r"^\s*Total subscription revenue\s{2,}", line))
            # JFrog's only revenue categories are the subscription and license rows included in this total.
            if amount not in line or not total:
                continue
            key = f"{doc.id}:p{page:04d}"
            if not TITLE.search(text) and not (page > 1 and TITLE.search(pages[page - 2][-500:])):
                continue
            heading = [i for i, row in enumerate(lines[:index]) if re.search(r"in (thousands|millions)", row, re.I)]
            if not heading:
                continue
            start = heading[-1]
            mark = next((i for i in range(start, index + 1) if MONEY_MARK.search(lines[i])), None)
            if mark is None:
                continue
            end = MONEY_MARK.search(lines[mark]).end()
            unit = words(" ".join(lines[start:mark] + [lines[mark][:end]]))
            ref = {"document": doc.id, "block": key, "quote": amount, "tabular": True,
                   "unit_block": key, "unit_quote": unit}
            b.read_figure(b.FigureRef.model_validate(ref), blocks)
            return [ref]
    raise ValueError(f"{doc.id} YTD amount {amount} not found in consolidated statements")


def build(key, row):
    split, issuer, ticker, year, releases, period_ends, standard = row
    prior, older, older_pages, a = archive(key, "prior", releases[0])
    latest, newer, newer_pages, c = archive(key, "latest", releases[1])
    if isinstance(standard, str):
        items, figures, gap = CLOSED, {}, dict.fromkeys(CLOSED, standard)
    else:
        old_fy, q3, new_fy, old_total, new_total, unit = standard
        items, gap = ITEMS, {}
        figures = {"prior": guidance(prior, older, old_fy, unit),
                   "prior_interim": guidance(prior, older, q3, unit),
                   "new": guidance(latest, newer, new_fy, unit),
                   "prior_reported_in_period": money_table(prior, older, older_pages, old_total),
                   "reported_in_period": money_table(latest, newer, newer_pages, new_total)}
    case = b.Case(id=key, split=split, ticker=ticker, issuer=issuer, precision="1000",
                  event_at=latest.published_at, as_of=latest.published_at, documents=[prior, latest],
                  figures=figures, style="implicit", items=items, undetermined=gap,
                  labels={"period": f"fiscal {year}", "interim": f"the third quarter of fiscal {year}",
                          "remainder": f"the fourth quarter of fiscal {year}"},
                  trap=standard if gap else "選對本財年與合併口徑的累計營收，排除單季、去年同期和明示獨立 Q4。")
    amounts = b.gold(case, older | newer)
    print(key, split, amounts, flush=True)
    terms = ["prior_interim", "q3", "third quarter", "第三季", "第三季度", "前季", "上一季", "先前", "前次"]
    if key in {"cost", "wday"}:
        terms.extend(["prior figure", "total revenue", "合併營收", "總營收", "訂閱", "subscription", "prior"])
    return {"case":case.model_dump(mode="json"), "vintages":{
                doc.id: {"report_end":end, "fiscal_year":year,"quarter":quarter}
                for doc,end,quarter in zip((prior,latest),period_ends,(2,3))},
            "gap_terms":terms if gap else []}, {prior.id:a, latest.id:c}


def main():
    rows, sources = [], {}
    for key, spec in STANDARD.items():
        row, ledger=build(key,spec)
        rows.append(row)
        sources.update(ledger)
    b.equal.journal.atomic(ROOT/"case-input.json",rows)
    b.equal.journal.atomic(ROOT/"source-ledger.json",sources)


if __name__ == "__main__":
    main()
