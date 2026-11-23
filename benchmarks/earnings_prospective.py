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
from benchmarks.earnings_horizon_inputs import add_revenue_history, revenue_history
from benchmarks.earnings_inputs import add_eps_assumptions, add_guidance, financial_history, load_guidance
from benchmarks.public_pilot import EFFORT, MODEL, write_json
from research_app.adapters import Codex, EARNINGS_DRIVER_VERSION
from research_app.earnings import METRICS, SCENARIOS, EarningsError, available_evidence, calculate_earnings, complete_plan, validate_plan
from research_app.research import build_context
from research_app.schema import Amount, EarningsPlan, Event, Nonempty, RevenueBridge, Schema

PROTOCOL = {"version": VERSION, "arms": ARMS, "model": MODEL, "reasoning_effort": EFFORT,
            "earnings_driver_version": EARNINGS_DRIVER_VERSION, "events_per_issuer": 6,
            "issuers": TICKERS, "future_quarters": 2, "scenarios": SCENARIOS}
RESIDUAL_ARMS = ("astra", "harness", "residual_a", "residual_b")
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


def summarize_reviews(rows, key, *, arms=ARMS):
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
    completed = [case_id for case_id in key if all(entries.get((case_id, arm)) is not None for arm in arms)]
    return {
        "paired_cases": len(completed),
        "arms": {
            arm: {
                "major_error_rate": mean(entries[(case_id, arm)][0] for case_id in completed),
                "public_check_rate": mean(entries[(case_id, arm)][1] for case_id in completed),
                "median_seconds": median(entries[(case_id, arm)][2] for case_id in completed),
            }
            for arm in arms if completed
        },
    }


class Cohort:
    def __init__(self, folder, *, horizon=False, residual=False):
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
                protocol = {**PROTOCOL, **({"revenue_bridge_version": 1} if horizon or residual else {})}
                if residual:
                    protocol.update(arms=RESIDUAL_ARMS, revenue_residual_version=1)
                value = {"protocol": protocol, "frozen_at": utc_now().isoformat()}
                db.execute("INSERT OR IGNORE INTO protocol VALUES (1,?)", (canonical(value),))
                manifest = db.execute("SELECT manifest FROM protocol WHERE id=1").fetchone()
            self.manifest = json.loads(manifest[0])
            registered = self.manifest["protocol"]
            self.driver_version = registered["earnings_driver_version"]
            self.horizon = registered.get("revenue_bridge_version") == 1
            self.residual = registered.get("revenue_residual_version") == 1
            self.arms = RESIDUAL_ARMS if self.residual else ARMS
            expected = {**PROTOCOL, "earnings_driver_version": self.driver_version}
            if self.horizon:
                expected["revenue_bridge_version"] = 1
            if self.residual:
                expected.update(arms=self.arms, revenue_residual_version=1)
            if (self.driver_version not in {3, EARNINGS_DRIVER_VERSION}
                    or (horizon and not self.horizon) or (residual and not self.residual)
                    or canonical(registered) != canonical(expected)):
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
        if bool(plan.revenue_bridge) != self.horizon:
            raise EarningsError("營收橋接和隊列封存的方案版本不符")
        if plan.revenue_bridge and plan.revenue_bridge.method == "confirmed_turn":
            raise EarningsError("轉折候選須另行驗收，現有隊列已鎖定季節橋接方案")
        if plan.revenue_bridge and plan.revenue_bridge.method in RESIDUAL_ARMS[2:] and not self.residual:
            raise EarningsError("修正候選須登記到獨立的修正方案隊列")
        if self.residual and plan.revenue_bridge.adjustments:
            raise EarningsError("修正隊列的分部輸入須使用 residual_inputs")
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
        if not self.horizon:
            snapshot["earnings_plan"].pop("revenue_bridge")
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
            if set(result) != set(self.arms) or any(
                len(arm["points"]) != len(expected) or
                {(row["period_end"], row["scenario"]) for row in arm["points"]} != expected
                for arm in result.values()
            ):
                raise EarningsError(f"{'四組' if self.residual else '三組'}須完整交付相同兩季三情境")
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
        events = {row["case_id"]: Event.model_validate_json(row["event"]) for row in rows}
        cases = [{"id": case_id, "context": build_context(event)} for case_id, event in events.items()]
        review, key = blind_records(cases, outputs, arms=self.arms)
        expected = [(ticker, index, f"{ticker}-{index:02}") for ticker in TICKERS for index in range(1, 7)]
        by_id = {row["case_id"]: row for row in snapshots}
        slots = [{"case": case_id, "company": ticker, "slot": index,
                  "status": ("sealed" if by_id[case_id]["sealed_at"] else "enrolled") if case_id in by_id else "awaiting_release"}
                 for ticker, index, case_id in expected]
        observations, by_horizon = [], {1: [], 2: []}
        for case_id, actual in actuals:
            periods = sorted(q.period_end.isoformat() for q in events[case_id].earnings_plan.quarters)
            step = periods.index(actual["period_end"]) + 1
            for arm, result in outputs[case_id].items():
                base = next(point for point in result["points"] if point["scenario"] == "base"
                            and point["period_end"] == actual["period_end"])
                observations.append((arm, base, actual))
                by_horizon[step].append((arm, base, actual))
        metrics = score_rows(observations, arms=self.arms) if observations else {}
        summary = {"planned": len(slots), "enrolled": len(rows), "sealed": len(outputs),
                   "resolved_quarters": len(actuals), "metrics": metrics, "slots": slots}
        if self.residual:
            summary["metrics_by_horizon"] = {str(step): score_rows(values, arms=self.arms) if values else {}
                                             for step, values in by_horizon.items()}
            summary["cases_with_adjustment"] = {
                method: sum(Decimal(((result[method].get("audit") or {}).get("residual") or {}).get("delta") or "0") != 0
                            for result in outputs.values())
                for method in RESIDUAL_ARMS[2:]
            }
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
            summary["human_review"] = summarize_reviews(csv.DictReader(stream), key, arms=self.arms)
        write_json(self.folder / "status.json", summary)
        group_count = "四組" if self.residual else "三組"
        (self.folder / "status.md").write_text("\n".join([
            "# 半導體前瞻盈利對照", "",
            f"方案鎖定 {self.manifest['frozen_at']}。預留 {len(slots)} 案，"
            f"已登記 {len(rows)} 案，已封存{group_count}預測 {len(outputs)} 案，已取得 {len(actuals)} 季實績。",
            f"{group_count}都完成人工覆核的事件有 {summary['human_review']['paired_cases']} 案。",
            f"{group_count}均交兩季三情境，未到期的季數不參與誤差平均。", "",
            *([f"已封存案例中，A 調整 {summary['cases_with_adjustment']['residual_a']} 案，"
               f"B 調整 {summary['cases_with_adjustment']['residual_b']} 案。", ""] if self.residual else []),
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


def residual_forecasts(event, context, astra, incumbent):
    output = {"astra": {"points": astra}, "harness": {"points": project_rows(incumbent)}}
    frozen = EarningsPlan.model_validate(incumbent["inputs"])
    for method in RESIDUAL_ARMS[2:]:
        bridge = RevenueBridge.model_validate({**event.earnings_plan.revenue_bridge.model_dump(), "method": method})
        challenger = frozen.model_copy(update={"revenue_bridge": bridge})
        trial = calculate_earnings(challenger, event.as_of, context["evidence"])
        output[method] = {"points": project_rows(trial), "audit": trial.get("revenue_bridge")}
    return output


def run_case(case_id, event, driver_version=EARNINGS_DRIVER_VERSION, *, residual=False):
    context = build_context(event)
    adapter = Codex(reasoning_effort=EFFORT, earnings_driver_version=driver_version)
    astra = direct_points(event, context, adapter)
    plan = event.earnings_plan.model_copy(update={"revenue_bridge": None})
    if residual:
        incumbent = complete_plan(plan, event.as_of, context, adapter)
        return case_id, residual_forecasts(event, context, astra, incumbent)
    calc = recalculate_direct(event.model_copy(update={"earnings_plan": plan}), context, astra)
    harness = project_rows(complete_plan(event.earnings_plan, event.as_of, context, adapter))
    return case_id, {arm: {"points": points} for arm, points in zip(ARMS, (astra, calc, harness))}


def seed_frozen_inputs(cohort, source):
    if not cohort.residual:
        raise EarningsError("舊快照匯入僅用於獨立的修正方案隊列")
    path = (source / "cohort.sqlite3").resolve()
    if path == cohort.path.resolve():
        raise EarningsError("來源與修正隊列資料庫必須分開")
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        source_protocol = json.loads(db.execute("SELECT manifest FROM protocol WHERE id=1").fetchone()[0])["protocol"]
        if source_protocol.get("revenue_bridge_version") != 1 or source_protocol.get("revenue_residual_version"):
            raise EarningsError("須使用已封存的季節橋接隊列作為快照來源")
        snapshots = db.execute(
            "SELECT c.ticker,c.accession,c.event,c.snapshot_sha256,s.sealed_at "
            "FROM cases c JOIN submissions s USING (case_id) WHERE c.slot=1 ORDER BY c.case_id"
        ).fetchall()
    with cohort.connection() as db:
        known = {row["accession"] for row in db.execute("SELECT accession FROM cases")}
    for ticker, accession, payload, digest, sealed_at in snapshots:
        if accession in known or INITIAL_ACCESSIONS.get(ticker) != accession:
            continue
        if sha256(payload.encode()).hexdigest() != digest:
            raise EarningsError("季節橋接來源快照的雜湊不符")
        event = Event.model_validate_json(payload)
        if datetime.fromisoformat(sealed_at).date() >= min(q.period_end for q in event.earnings_plan.quarters):
            raise EarningsError("季節橋接來源快照未在期末前封存")
        print("enrolled", cohort.enroll(ticker, accession, event, utc_now()), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/earnings-prospective"))
    parser.add_argument("--horizon", action="store_true", help="新建使用第二預測季營收橋接的獨立隊列")
    parser.add_argument("--residual", action="store_true", help="新建含 T+2 修正 A/B 的四組獨立隊列")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    seed = commands.add_parser("seed")
    seed.add_argument("--sec-dir", type=Path, default=Path("output/earnings-benchmark/sec"))
    seed.add_argument("--guidance", type=Path)
    seed.add_argument("--from-cohort", type=Path, help="匯入既有季節橋接隊列已封存的原始事件")
    enroll = commands.add_parser("enroll")
    enroll.add_argument("ticker", choices=tuple(TICKERS))
    enroll.add_argument("accession")
    enroll.add_argument("event", type=Path)
    commands.add_parser("run")
    resolve = commands.add_parser("resolve")
    resolve.add_argument("case")
    resolve.add_argument("actual", type=Path)
    args = parser.parse_args()
    cohort = Cohort(args.output, horizon=args.horizon, residual=args.residual)
    if args.command == "seed" and args.from_cohort:
        seed_frozen_inputs(cohort, args.from_cohort)
        summary = cohort.export()
        print({key: value for key, value in summary.items() if key != "slots"})
        return
    if args.command == "seed":
        existing = {row["company"] for row in cohort.export()["slots"] if row["status"] != "awaiting_release"}
        if args.guidance and cohort.driver_version == 3:
            parser.error("舊方案維持原始輸入，加入公司指引請建立新隊列")
        history = financial_history(args.sec_dir) if cohort.driver_version != 3 and set(INITIAL_PERIODS) - existing else {}
        revenue = revenue_history(args.sec_dir, INITIAL_PERIODS) if cohort.horizon and history else {}
        guide = load_guidance(args.guidance) if args.guidance else {}
        for ticker in INITIAL_PERIODS:
            if ticker not in existing:
                now = utc_now()
                accession, event = initial_case(args.sec_dir, ticker, now)
                if history:
                    rows = guide.get(f"{ticker}-01", [])
                    event = add_eps_assumptions(add_guidance(event, rows), ticker, history, rows)
                if revenue:
                    event = add_revenue_history(event, ticker, revenue[ticker], (4, 1), "guided_absolute")
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
            jobs = {pool.submit(run_case, case_id, event, cohort.driver_version, residual=cohort.residual): case_id
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
