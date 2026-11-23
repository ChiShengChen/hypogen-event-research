"""Freeze, run, and later score the next semiconductor earnings cohort."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
from statistics import mean, median
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AwareDatetime, Field

from benchmarks.earnings_cases import TICKERS, baseline, disclosure, filing_index
from benchmarks.earnings_equal import ARMS, VERSION, blind_records, direct_points, project_rows, recalculate_direct, score_rows
from benchmarks.earnings_inputs import add_eps_assumptions, add_guidance, financial_history, load_guidance
from benchmarks.public_pilot import EFFORT, MODEL, write_json
from research_app.adapters import Codex, EARNINGS_DRIVER_VERSION
from research_app.earnings import METRICS, SCENARIOS, EarningsError, available_evidence, complete_plan, validate_plan
from research_app.research import build_context
from research_app.schema import Amount, Event, Nonempty, Schema

PROTOCOL = {"version": VERSION, "arms": ARMS, "model": MODEL, "reasoning_effort": EFFORT,
            "earnings_driver_version": EARNINGS_DRIVER_VERSION, "events_per_issuer": 6,
            "issuers": TICKERS, "future_quarters": 2, "scenarios": SCENARIOS}
# Fiscal endpoints are fixed in the initial enrollment, ahead of the outcomes.
INITIAL_PERIODS = {
    "AMD": ("2026-12-26", "2027-03-27"),
    "INTC": ("2026-12-26", "2027-03-27"),
    "TXN": ("2026-12-31", "2027-03-31"),
}
INITIAL_ACCESSIONS = {
    "AMD": "0000002488-26-000191",
    "INTC": "0000050863-26-000191",
    "TXN": "0000097476-26-000169",
}


class ActualQuarter(Schema):
    period_end: date
    duration: Literal["quarter"]
    currency: Nonempty
    basis: Nonempty
    scope: Nonempty
    source: Nonempty
    accession: Nonempty
    published_at: AwareDatetime
    revenue: Annotated[Amount, Field(ge=0)]
    gross_margin: Annotated[Amount, Field(le=1)]
    operating_income: Amount
    eps: Amount


def utc_now():
    return datetime.now(timezone.utc)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def summarize_reviews(rows, key):
    entries = {}
    for row in rows:
        if any(row.get(field) is None for field in ("case", "candidate", "major_error", "public_check", "seconds")):
            raise EarningsError("匿名覆核表缺少必填欄位")
        labels = key.get(row["case"], {})
        if row["candidate"] not in labels:
            raise EarningsError("匿名覆核表引用不存在的候選")
        identity = (row["case"], labels[row["candidate"]])
        if identity in entries:
            raise EarningsError("匿名覆核表有重複列")
        entries[identity] = None
        values = [row[field].strip() for field in ("major_error", "public_check", "seconds")]
        if not any(values):
            continue
        try:
            elapsed = Decimal(values[2])
            if not elapsed.is_finite() or elapsed < 0 or values[0] not in {"0", "1"} or values[1] not in {"0", "1"}:
                raise ValueError
        except (ValueError, InvalidOperation) as exc:
            raise EarningsError("覆核須填寫 0/1 的錯誤與可驗證性，以及有效秒數") from exc
        entries[identity] = (int(values[0]), int(values[1]), float(elapsed))
    completed = [case_id for case_id in key if all(entries.get((case_id, arm)) is not None for arm in ARMS)]
    return {
        "paired_cases": len(completed),
        "arms": {
            arm: {
                "major_error_rate": mean(entries[(case_id, arm)][0] for case_id in completed),
                "public_check_rate": mean(entries[(case_id, arm)][1] for case_id in completed),
                "median_seconds": median(entries[(case_id, arm)][2] for case_id in completed),
            }
            for arm in ARMS if completed
        },
    }


class Cohort:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / "cohort.sqlite3"
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS protocol (id INTEGER PRIMARY KEY CHECK (id=1), manifest TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY, ticker TEXT NOT NULL, slot INTEGER NOT NULL CHECK (slot BETWEEN 1 AND 6),
                    accession TEXT NOT NULL UNIQUE, event_at TEXT NOT NULL, enrolled_at TEXT NOT NULL,
                    event TEXT NOT NULL, snapshot_sha256 TEXT NOT NULL, UNIQUE(ticker, slot)
                );
                CREATE TABLE IF NOT EXISTS submissions (
                    case_id TEXT PRIMARY KEY REFERENCES cases(case_id), sealed_at TEXT NOT NULL,
                    forecasts TEXT NOT NULL, submission_sha256 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS actuals (
                    case_id TEXT REFERENCES submissions(case_id), period_end TEXT NOT NULL,
                    outcome TEXT NOT NULL, recorded_at TEXT NOT NULL, PRIMARY KEY(case_id, period_end)
                );
            """)
            manifest = db.execute("SELECT manifest FROM protocol WHERE id=1").fetchone()
            if not manifest:
                value = {"protocol": PROTOCOL, "frozen_at": utc_now().isoformat()}
                db.execute("INSERT OR IGNORE INTO protocol VALUES (1,?)", (canonical(value),))
                manifest = db.execute("SELECT manifest FROM protocol WHERE id=1").fetchone()
            self.manifest = json.loads(manifest[0])
            registered = self.manifest["protocol"]
            self.driver_version = registered["earnings_driver_version"]
            if (self.driver_version not in {3, EARNINGS_DRIVER_VERSION}
                    or canonical(registered) != canonical({**PROTOCOL, "earnings_driver_version": self.driver_version})):
                raise EarningsError("前瞻組方案已鎖定。請使用相同版本或在新目錄建立另一組。")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def enroll(self, ticker, accession, event, now):
        plan = event.earnings_plan
        if ticker not in TICKERS or event.research_target != ticker or plan is None:
            raise EarningsError("目標、隊列公司或盈利計畫不符")
        if event.search_mode != "off" or not plan.generate_drivers or len(plan.quarters) != 2:
            raise EarningsError("隊列須使用兩季凍結基準及模型驅動")
        if self.driver_version == 3 and (plan.eps_assumptions or plan.calibrate_guidance is not None):
            raise EarningsError("此隊列已鎖定舊模型。新 EPS 與指引方案須放入新隊列。")
        if plan.event_at > event.as_of or event.as_of > now:
            raise EarningsError("事件和快照必須已可取得")
        if any(quarter.period_end <= now.date() for quarter in plan.quarters):
            raise EarningsError("兩個預測期間均須尚未結束")
        if any(doc.synthetic or max(doc.published_at, doc.obtained_at) > event.as_of for doc in event.documents):
            raise EarningsError("登記檔含虛構或截止日後才可得的文件")
        if not any(doc.kind == "disclosure" and valid_sec_source(doc.source, ticker, accession)
                   and doc.published_at == plan.event_at for doc in event.documents):
            raise EarningsError("須附隊列公司在事件日的原始 SEC 申報")
        validate_plan(plan, event.as_of, build_context(event)["evidence"])
        snapshot = event.model_dump(mode="json")
        if self.driver_version == 3:
            snapshot["earnings_plan"].pop("eps_assumptions")
            snapshot["earnings_plan"].pop("calibrate_guidance")
        encoded = canonical(snapshot)
        fingerprint = sha256(encoded.encode()).hexdigest()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM cases WHERE accession=?", (accession,)).fetchone()
            if existing:
                if existing["snapshot_sha256"] != fingerprint:
                    raise EarningsError("同一 SEC 申報已登記，快照不可覆寫")
                return existing["case_id"]
            prior = db.execute("SELECT * FROM cases WHERE ticker=? ORDER BY slot DESC LIMIT 1", (ticker,)).fetchone()
            slot = prior["slot"] + 1 if prior else 1
            if slot > PROTOCOL["events_per_issuer"]:
                raise EarningsError("此公司六個名額已用完")
            if prior and plan.event_at <= datetime.fromisoformat(prior["event_at"]):
                raise EarningsError("後續事件必須晚於此公司上次登記")
            if (not prior and ticker in INITIAL_ACCESSIONS and accession != INITIAL_ACCESSIONS[ticker]):
                raise EarningsError("此公司的首輪申報已由方案指定")
            if (prior or ticker not in INITIAL_ACCESSIONS) and plan.event_at <= datetime.fromisoformat(self.manifest["frozen_at"]):
                raise EarningsError("後續事件須在隊列方案鎖定後才公開")
            case_id = f"{ticker}-{slot:02}"
            db.execute("INSERT INTO cases VALUES (?,?,?,?,?,?,?,?)", (
                case_id, ticker, slot, accession, plan.event_at.isoformat(), now.isoformat(), encoded, fingerprint,
            ))
        return case_id

    def seal(self, case_id, result, now):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            case = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if not case:
                raise EarningsError("未找到事件登記")
            old = db.execute("SELECT forecasts FROM submissions WHERE case_id=?", (case_id,)).fetchone()
            encoded = canonical(result)
            if old:
                if old["forecasts"] != encoded:
                    raise EarningsError("已封存的輸出不可覆寫")
                return
            event = Event.model_validate_json(case["event"])
            if now < datetime.fromisoformat(case["enrolled_at"]):
                raise EarningsError("不可在登記前封存預測")
            periods = {q.period_end.isoformat() for q in event.earnings_plan.quarters}
            if any(date.fromisoformat(period) <= now.date() for period in periods):
                raise EarningsError("預測未在觀測期結束前完成")
            expected = {(period, scenario) for period in periods for scenario in SCENARIOS}
            if set(result) != set(ARMS) or any(
                len(arm["points"]) != len(expected) or
                {(row["period_end"], row["scenario"]) for row in arm["points"]} != expected
                for arm in result.values()
            ):
                raise EarningsError("三組須完整交付相同兩季三情境")
            visible = {row["id"]: row for row in build_context(event)["evidence"]}
            for arm in result.values():
                for point in arm["points"]:
                    if not point.get("rationale") or not point.get("evidence_ids") or any(
                        not Decimal(point[metric]).is_finite() for metric in METRICS
                    ):
                        raise EarningsError("封存項目缺少數字、理由或引文")
                    available_evidence(point["evidence_ids"], visible, event.as_of)
            db.execute("INSERT INTO submissions VALUES (?,?,?,?)",
                       (case_id, now.isoformat(), encoded, sha256(encoded.encode()).hexdigest()))

    def resolve(self, case_id, actual, now):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT c.ticker,c.event,s.sealed_at FROM cases c "
                             "JOIN submissions s ON c.case_id=s.case_id WHERE c.case_id=?", (case_id,)).fetchone()
            if not row:
                raise EarningsError("事件須先完成三組封存")
            event = Event.model_validate_json(row["event"])
            plan = event.earnings_plan
            if actual.period_end not in {q.period_end for q in plan.quarters}:
                raise EarningsError("實績期別與登記不符")
            if (actual.currency, actual.basis, actual.scope) != (plan.currency, plan.basis, "consolidated"):
                raise EarningsError("實績幣別、口徑或合併範圍不符")
            if (not datetime.fromisoformat(row["sealed_at"]) < actual.published_at <= now
                    or actual.published_at.date() < actual.period_end
                    or not valid_sec_source(actual.source, row["ticker"], actual.accession)):
                raise EarningsError("實績須由同一公司在封存與期末後公開，且已可取得")
            value = canonical(actual.model_dump(mode="json"))
            date_key = actual.period_end.isoformat()
            previous = db.execute("SELECT outcome FROM actuals WHERE case_id=? AND period_end=?",
                                  (case_id, date_key)).fetchone()
            if previous:
                if previous["outcome"] != value:
                    raise EarningsError("首次實績版本不可覆寫")
                return
            db.execute("INSERT INTO actuals VALUES (?,?,?,?)", (case_id, date_key, value, now.isoformat()))

    def unsealed(self):
        with self.connection() as db:
            return [(row["case_id"], Event.model_validate_json(row["event"]))
                    for row in db.execute("SELECT * FROM cases WHERE case_id NOT IN "
                                          "(SELECT case_id FROM submissions) ORDER BY case_id")]

    def export(self):
        with self.connection() as db:
            rows = db.execute(
                "SELECT c.*,s.sealed_at,s.forecasts,s.submission_sha256 FROM cases c LEFT JOIN submissions s USING(case_id)"
            ).fetchall()
            actuals = [(row["case_id"], json.loads(row["outcome"])) for row in db.execute("SELECT * FROM actuals")]
        for row in rows:
            if sha256(row["event"].encode()).hexdigest() != row["snapshot_sha256"] or (
                row["forecasts"] and sha256(row["forecasts"].encode()).hexdigest() != row["submission_sha256"]
            ):
                raise EarningsError(f"{row['case_id']} 快照或預測的完整性檢查失敗")
        snapshots = [{key: row[key] for key in row.keys() if key not in ("event", "forecasts")} for row in rows]
        outputs = {row["case_id"]: json.loads(row["forecasts"]) for row in rows if row["forecasts"]}
        cases = [{"id": row["case_id"], "context": build_context(Event.model_validate_json(row["event"]))} for row in rows]
        review, key = blind_records(cases, outputs)
        expected = [(ticker, index, f"{ticker}-{index:02}") for ticker in TICKERS for index in range(1, 7)]
        by_id = {row["case_id"]: row for row in snapshots}
        slots = [{"case": case_id, "company": ticker, "slot": index,
                  "status": ("sealed" if by_id[case_id]["sealed_at"] else "enrolled") if case_id in by_id else "awaiting_release"}
                 for ticker, index, case_id in expected]
        observations = []
        for case_id, actual in actuals:
            for arm, result in outputs[case_id].items():
                base = next(point for point in result["points"] if point["scenario"] == "base"
                            and point["period_end"] == actual["period_end"])
                observations.append((arm, base, actual))
        metrics = score_rows(observations) if observations else {}
        summary = {"planned": len(slots), "enrolled": len(rows), "sealed": len(outputs),
                   "resolved_quarters": len(actuals), "metrics": metrics, "slots": slots}
        for name, value in (("protocol", self.manifest), ("snapshots", snapshots),
                            ("blind-review", review), ("review-key", key)):
            write_json(self.folder / f"{name}.json", value)
        review_form = self.folder / "review-form.csv"
        if not review_form.exists():
            with review_form.open("w", newline="", encoding="utf-8-sig") as stream:
                csv.writer(stream).writerow(("case", "candidate", "major_error", "public_check", "seconds", "notes"))
        with review_form.open(newline="", encoding="utf-8-sig") as stream:
            existing = {(row["case"], row["candidate"]) for row in csv.DictReader(stream)}
        with review_form.open("a", newline="", encoding="utf-8") as stream:
            csv.writer(stream).writerows((case_id, label, "", "", "", "")
                                         for case_id, arms in key.items() for label in arms
                                         if (case_id, label) not in existing)
        with review_form.open(newline="", encoding="utf-8-sig") as stream:
            summary["human_review"] = summarize_reviews(csv.DictReader(stream), key)
        write_json(self.folder / "status.json", summary)
        (self.folder / "status.md").write_text("\n".join([
            "# 半導體前瞻盈利對照", "",
            f"方案鎖定 {self.manifest['frozen_at']}。預留 {len(slots)} 案，"
            f"已登記 {len(rows)} 案，已封存三組預測 {len(outputs)} 案，已取得 {len(actuals)} 季實績。",
            f"三組都完成人工覆核的事件有 {summary['human_review']['paired_cases']} 案。",
            "三組均交兩季三情境，未到期的季數不參與誤差平均。", "",
            "| 案例 | 公司 | 狀態 |", "|---|---|---|",
            *(f"| {row['case']} | {row['company']} | {row['status']} |" for row in slots),
        ]) + "\n", encoding="utf-8")
        return summary


def valid_sec_source(source, ticker, accession):
    parts = urlsplit(source)
    prefix = f"/Archives/edgar/data/{int(TICKERS[ticker])}/{accession.replace('-', '')}/"
    return parts.scheme == "https" and parts.netloc in {"sec.gov", "www.sec.gov"} and parts.path.startswith(prefix)


def initial_case(folder, ticker, now):
    source = json.loads((folder / f"{ticker}.json").read_text())
    available = [row for row in filing_index(source).values() if row["filed"] < now.date()]
    latest = next(row for row in available if row["accession"] == INITIAL_ACCESSIONS[ticker])
    periods = [date.fromisoformat(raw) for raw in INITIAL_PERIODS[ticker]]
    earlier = [row for row in available if row["filed"] < latest["filed"]]
    old = [max((row for row in earlier if row["fp"] == quarter), key=lambda row: row["filed"])
           for quarter in ("Q2", "Q1")]
    cited = [disclosure(TICKERS[ticker], label, row)
             for label, row in zip(("baseline-q4", "baseline-q1", "issuer-event"), (*old, latest))]
    baselines = [baseline(previous, period, doc) for previous, period, doc in zip(old, periods, cited)]
    baselines[0]["method"] = "事件前最新 Q2 同口徑規模代理。保留模型稅率及歷史對帳餘額。"
    return latest["accession"], Event.model_validate({
        "research_target": ticker, "research_horizon": periods[-1].isoformat(),
        "event_text": f"{ticker} 公布截至 {latest['end']} 的第三季原始 10-Q。凍結資料後預測下一個 Q4 和 Q1。",
        "as_of": now, "search_mode": "off", "documents": cited,
        "earnings_plan": {"event_at": cited[-1]["published_at"], "currency": "USD", "basis": "US_GAAP",
                          "quarters": baselines, "generate_drivers": True},
    })


def run_case(case_id, event, driver_version=EARNINGS_DRIVER_VERSION):
    context = build_context(event)
    adapter = Codex(reasoning_effort=EFFORT, earnings_driver_version=driver_version)
    astra = direct_points(event, context, adapter)
    calc = recalculate_direct(event, context, astra)
    harness = project_rows(complete_plan(event.earnings_plan, event.as_of, context, adapter))
    return case_id, {arm: {"points": points} for arm, points in zip(ARMS, (astra, calc, harness))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/earnings-prospective"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    seed = commands.add_parser("seed")
    seed.add_argument("--sec-dir", type=Path, default=Path("output/earnings-benchmark/sec"))
    seed.add_argument("--guidance", type=Path)
    enroll = commands.add_parser("enroll")
    enroll.add_argument("ticker", choices=tuple(TICKERS))
    enroll.add_argument("accession")
    enroll.add_argument("event", type=Path)
    commands.add_parser("run")
    resolve = commands.add_parser("resolve")
    resolve.add_argument("case")
    resolve.add_argument("actual", type=Path)
    args = parser.parse_args()
    cohort = Cohort(args.output)
    if args.command == "seed":
        existing = {row["company"] for row in cohort.export()["slots"] if row["status"] != "awaiting_release"}
        if args.guidance and cohort.driver_version == 3:
            parser.error("舊方案維持原始輸入，加入公司指引請建立新隊列")
        history = financial_history(args.sec_dir) if cohort.driver_version != 3 and set(INITIAL_PERIODS) - existing else {}
        guide = load_guidance(args.guidance) if args.guidance else {}
        for ticker in INITIAL_PERIODS:
            if ticker not in existing:
                now = utc_now()
                accession, event = initial_case(args.sec_dir, ticker, now)
                if history:
                    rows = guide.get(f"{ticker}-01", [])
                    event = add_eps_assumptions(add_guidance(event, rows), ticker, history, rows)
                print("enrolled", cohort.enroll(ticker, accession, event, now), flush=True)
    elif args.command == "enroll":
        print("enrolled", cohort.enroll(args.ticker, args.accession,
                                        Event.model_validate_json(args.event.read_text()), utc_now()))
    elif args.command == "resolve":
        cohort.resolve(args.case, ActualQuarter.model_validate_json(args.actual.read_text()), utc_now())
    elif args.command == "run":
        os.environ["RESEARCH_CODEX_MODEL"] = MODEL
        failures = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            jobs = {pool.submit(run_case, case_id, event, cohort.driver_version): case_id
                    for case_id, event in cohort.unsealed()}
            for job in as_completed(jobs):
                try:
                    case_id, result = job.result()
                    cohort.seal(case_id, result, utc_now())
                    print("sealed", case_id, flush=True)
                except Exception as exc:
                    failures.append({"case": jobs[job], "error": str(exc)})
                    print("failed", jobs[job], str(exc), flush=True)
        write_json(cohort.folder / "run-failures.json", failures)
        if failures:
            cohort.export()
            raise SystemExit(1)
    summary = cohort.export()
    print({key: value for key, value in summary.items() if key != "slots"})


if __name__ == "__main__":
    main()
