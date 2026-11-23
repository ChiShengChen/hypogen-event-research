"""Archive issuer earnings releases (8-K Item 2.02, exhibit 99.1) from SEC EDGAR for guidance cases.

The SEC asks automated clients to identify themselves. Pass that identity through the SEC_USER_AGENT
environment variable; it is only sent as a request header and never written to disk.
"""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

OUT = Path("output/guidance-arithmetic-v2/filings")
TICKERS = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{folder}/"
EASTERN = ZoneInfo("America/New_York")
INTERVAL = 0.25
_last = [0.0]


def fetch(url):
    agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if not agent:
        raise SystemExit("Set SEC_USER_AGENT to the identity the SEC asks automated clients to send.")
    wait = INTERVAL - (monotonic() - _last[0])
    if wait > 0:
        sleep(wait)
    _last[0] = monotonic()
    request = Request(url, headers={"User-Agent": agent, "Accept-Encoding": "identity"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def ciks(tickers):
    table = json.loads(fetch(TICKERS))
    known = {row["ticker"].upper(): int(row["cik_str"]) for row in table.values()}
    missing = [ticker for ticker in tickers if ticker.upper() not in known]
    if missing:
        raise SystemExit(f"unknown tickers: {missing}")
    return {ticker.upper(): known[ticker.upper()] for ticker in tickers}


def earnings_filings(cik, since):
    recent = json.loads(fetch(SUBMISSIONS.format(cik=cik)))["filings"]["recent"]
    rows = zip(recent["form"], recent["items"], recent["accessionNumber"], recent["acceptanceDateTime"],
               recent["filingDate"])
    return [{"accession": accession, "accepted": accepted, "filed": filed}
            for form, items, accession, accepted, filed in rows
            if form == "8-K" and "2.02" in items.split(",") and filed >= since]


def exhibit(cik, accession):
    folder = accession.replace("-", "")
    index = json.loads(fetch(ARCHIVE.format(cik=cik, folder=folder) + "index.json"))["directory"]["item"]
    names = [row["name"] for row in index if row["name"].lower().endswith((".htm", ".html"))]
    preferred = [name for name in names if re.search(r"ex-?99[._-]?0?1|ex991|exhibit991", name, re.I)]
    choice = (preferred or [name for name in names if re.search(r"ex-?99", name, re.I)] or [None])[0]
    return (ARCHIVE.format(cik=cik, folder=folder) + choice) if choice else None


def accepted_at(value):
    # EDGAR acceptance times are UTC (NETGEAR's 16:11:43 EST release is reported as 21:11:43Z).
    utc = datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    return utc.astimezone(EASTERN).isoformat()


def archive(tickers, since, per_ticker, out=OUT):
    out.mkdir(parents=True, exist_ok=True)
    ledger_path = out / "ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    for ticker, cik in ciks(tickers).items():
        for filing in earnings_filings(cik, since)[:per_ticker]:
            key = f"{ticker.lower()}-{filing['accession']}"
            if key in ledger:
                continue
            try:
                url = exhibit(cik, filing["accession"])
            except HTTPError as exc:
                print(f"{key} index failed: HTTP {exc.code}", flush=True)
                continue
            if url is None:
                print(f"{key} has no exhibit 99", flush=True)
                continue
            body = fetch(url)
            path = out / ticker.lower() / f"{filing['accession']}-{url.rsplit('/', 1)[1]}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            published = accepted_at(filing["accepted"])
            ledger[key] = {
                "ticker": ticker, "cik": cik, "accession": filing["accession"], "source_url": url,
                "path": str(path), "sha256": sha256(body).hexdigest(), "published_at": published,
                "obtained_at": published, "timestamp_basis": "edgar_acceptance",
                "archived_at": datetime.now(EASTERN).isoformat(),
            }
            ledger_path.write_text(json.dumps(ledger, indent=1, ensure_ascii=False))
            print(f"{key} {published} {len(body)} bytes", flush=True)
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--since", default="2023-01-01")
    parser.add_argument("--per-ticker", type=int, default=8)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    archive(args.tickers, args.since, args.per_ticker, args.out)


if __name__ == "__main__":
    main()
