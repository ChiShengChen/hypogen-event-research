import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from uuid import uuid4

from .adapters import AdapterError, EARNINGS_DRIVER_VERSION
from .scenario_research import scenario_fields
from .business_linkage import LinkedAnswer, linkage_fields, linkage_refs, merged_linkages, validate_linkages
from .consensus import parse_consensus
from .discovery import DISCOVERY_VERSION, collect
from .earnings import EarningsError, available_evidence, calculate_earnings, operating_numbers, resolve_forecast
from .full_revision import (
    FILING_SELECTION_PROMPT, FilingExtraction, check_filing_revision, filing_citation, parse_filing,
    _source_url,
)
from .hypothesis_tree import branch_context, branch_path, result_nodes, seed_nodes
from .hypothesis_inputs import NewsInput, prepare_inputs, resolve_links
from .research import (
    FORMULA_VERSION, REPORT_VERSION, apply_financial_scenario, build_report, company_key, document_evidence,
    render, render_followups,
)
from .revision_bridge import RevisionQuote, RevisionRequest, evaluate_revision
from .schema import EarningsPlan, Event, FinancialInputs, ForecastRegistration, MetricKey


class MissingReport(Exception):
    pass


def encode(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)


def opportunity_fields(report):
    assessment = report["assessment"]
    ideas = assessment.get("trade_opportunities", [])
    return {
        "trade_opportunities": ideas,
        "trade_opportunities_gap": assessment.get(
            "trade_opportunities_gap", None if ideas else "此版本沒有可列入的延伸交易機會。",
        ),
    }


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    report_id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE,
                    request_key TEXT NOT NULL UNIQUE, event TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS revisions (
                    report_id TEXT NOT NULL REFERENCES runs(report_id),
                    revision INTEGER NOT NULL, parent_revision INTEGER, report TEXT NOT NULL,
                    PRIMARY KEY (report_id, revision),
                    FOREIGN KEY (report_id, parent_revision) REFERENCES revisions(report_id, revision)
                );
                CREATE TABLE IF NOT EXISTS earnings_log (
                    report_id TEXT NOT NULL, revision INTEGER NOT NULL, kind TEXT NOT NULL,
                    action_key TEXT NOT NULL, recorded_at TEXT NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY (report_id, revision, kind, action_key),
                    FOREIGN KEY (report_id, revision) REFERENCES revisions(report_id, revision)
                );
                CREATE TABLE IF NOT EXISTS hypothesis_nodes (
                    sequence INTEGER PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    node_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    UNIQUE (report_id, revision, node_id),
                    FOREIGN KEY (report_id, revision) REFERENCES revisions(report_id, revision)
                );
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def result(row):
        return {"run_id": row[0], "report_id": row[1], "revision": 1, "status": "published"}

    def create(self, event, adapter):
        payload = event.model_dump(mode="json")
        if payload.get("earnings_plan") is None:
            payload.pop("earnings_plan", None)
        else:
            plan_payload = payload["earnings_plan"]
            if not plan_payload["driver_links"]:
                plan_payload.pop("driver_links")
            if not plan_payload["eps_assumptions"]:
                plan_payload.pop("eps_assumptions")
            if plan_payload["calibrate_guidance"] is None:
                plan_payload.pop("calibrate_guidance")
            if plan_payload["revenue_bridge"] is None:
                plan_payload.pop("revenue_bridge")
            references = plan_payload["references"] + plan_payload["event_values"]
            if plan_payload["valuation"]:
                references.append(plan_payload["valuation"]["annual_base_eps"])
            for reference in references:
                if reference["provider"] is None:
                    reference.pop("provider")
        request_key = hashlib.sha256(encode({
            "event": payload, "adapter": adapter.identity, "formula_version": FORMULA_VERSION,
            "report_version": REPORT_VERSION,
            "discovery_version": DISCOVERY_VERSION if event.search_mode != "off" else None,
            **({"earnings_driver_version": EARNINGS_DRIVER_VERSION, "earnings_attribution_version": 1}
               if event.earnings_plan and event.earnings_plan.generate_drivers else {}),
        }).encode()).hexdigest()
        lookup = "SELECT run_id, report_id FROM runs WHERE request_key = ?"
        with self.connection() as db:
            existing = db.execute(lookup, (request_key,)).fetchone()
        if existing:
            return self.result(existing)
        discovery = None
        if event.search_mode != "off":
            found, discovery = collect(event, adapter)
            event = event.model_copy(update={"documents": event.documents + found})
            payload = event.model_dump(mode="json")
        report = build_report(event, adapter, discovery=discovery)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(lookup, (request_key,)).fetchone()
            if existing:
                return self.result(existing)
            report_id, run_id = uuid4().hex, uuid4().hex
            db.execute("INSERT INTO runs VALUES (?, ?, ?, ?)",
                       (report_id, run_id, request_key, encode(payload)))
            db.execute("INSERT INTO revisions VALUES (?, 1, NULL, ?)",
                       (report_id, encode(report)))
        return self.result((run_id, report_id))

    def run(self, run_id):
        with self.connection() as db:
            row = db.execute("SELECT run_id, report_id FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if not row:
            raise MissingReport("找不到研究任務")
        return self.result(row)

    def find_reports(self, query, limit):
        with self.connection() as db:
            db.create_function("company_key", 1, lambda value: company_key(value or ""), deterministic=True)
            db.row_factory = sqlite3.Row
            rows = db.execute("""
                SELECT runs.report_id, revisions.revision,
                       json_extract(revisions.report, '$.target') AS target,
                       json_extract(revisions.report, '$.as_of') AS as_of,
                       substr(json_extract(runs.event, '$.event_text'), 1, 240) AS event_text
                FROM runs JOIN revisions ON revisions.report_id = runs.report_id
                  AND revisions.revision = (SELECT MAX(latest.revision) FROM revisions AS latest
                                            WHERE latest.report_id = runs.report_id)
                WHERE :query = '' OR instr(company_key(target), :query) > 0
                   OR instr(company_key(json_extract(runs.event, '$.event_text')), :query) > 0
                ORDER BY CASE WHEN :query != '' AND company_key(target) = :query THEN 0 ELSE 1 END,
                         runs.rowid DESC
                LIMIT :limit
            """, {"query": company_key(query), "limit": limit}).fetchall()
        return [dict(row) for row in rows]

    def revision(self, report_id, revision):
        with self.connection() as db:
            row = db.execute("""
                SELECT report, parent_revision FROM revisions WHERE report_id = ? AND revision = ?
            """, (report_id, str(revision))).fetchone()
        if not row:
            raise MissingReport("找不到報告或版本")
        return {**json.loads(row[0]), "report_id": report_id, "revision": revision,
                "parent_revision": row[1]}

    def event(self, report_id):
        with self.connection() as db:
            payload = db.execute("SELECT event FROM runs WHERE report_id = ?", (report_id,)).fetchone()[0]
        return Event.model_validate_json(payload)

    def _hypothesis_nodes(self, report):
        with self.connection() as db:
            saved = db.execute(
                "SELECT payload FROM hypothesis_nodes WHERE report_id = ? AND revision = ? ORDER BY sequence",
                (report["report_id"], report["revision"]),
            ).fetchall()
        return seed_nodes(report) + [json.loads(row[0]) for row in saved]

    def hypothesis_tree(self, report_id, revision):
        return {"nodes": self._hypothesis_nodes(self.revision(report_id, revision))}

    def extend_hypothesis_tree(self, report_id, revision, query, adapter):
        report = self.revision(report_id, revision)
        try:
            path = branch_path(self._hypothesis_nodes(report), query.parent_id)
        except KeyError as exc:
            raise MissingReport("此版本找不到指定的假說節點") from exc
        generate = getattr(adapter, "branch_hypotheses", None)
        if not callable(generate):
            raise AdapterError("產生假說分支需要 Codex CLI 或模型 API 模式")
        findings = {}
        urls = list(dict.fromkeys(item.url for item in query.inputs if isinstance(item, NewsInput)))
        search = getattr(adapter, "search", None)
        if urls and callable(search):
            try:
                findings = resolve_links(search, urls, query.question, report["as_of"])
            except AdapterError:
                # The user may continue with the parent and other available inputs.
                findings = {}
        inputs = prepare_inputs(query, report["as_of"], findings)
        context = branch_context(report, path, query, inputs)
        draft = generate(context)
        nodes = result_nodes(report, path, query, draft, context, company_key, inputs)
        with self.connection() as db:
            db.executemany(
                "INSERT INTO hypothesis_nodes (report_id, revision, node_id, payload) VALUES (?, ?, ?, ?)",
                [(report_id, revision, item["id"], encode(item)) for item in nodes],
            )
        return {"nodes": nodes, "selected_id": nodes[0]["id"]}

    def save_child(self, report_id, parent_revision, report):
        data = {key: value for key, value in report.items() if key not in {"report_id", "revision", "parent_revision"}}
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            revision = db.execute(
                "SELECT MAX(revision) + 1 FROM revisions WHERE report_id = ?", (report_id,)
            ).fetchone()[0]
            db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?)",
                       (report_id, revision, parent_revision, encode(data)))
        return revision

    def earnings_revision_inputs(self, report_id, revision, period_end):
        report = self.revision(report_id, revision)
        if "earnings" not in report:
            raise EarningsError("此版本缺少盈利預測")
        earnings = report["earnings"]
        period = period_end.isoformat()
        target = next((row for row in earnings["quarters"] if row["period_end"] == period), None)
        base = target["scenarios"].get("base") if target else None
        if base is None:
            raise EarningsError("指定季度缺少基準情境")
        plan = EarningsPlan.model_validate(earnings["inputs"])
        key = MetricKey(metric="revenue", period_end=period_end, duration="quarter",
                        scope="consolidated", basis=plan.basis, currency=plan.currency)
        return report, plan, key, base["revised"]

    def full_revenue_revision_check(self, report_id, revision, request, adapter):
        report, plan, key, point = self.earnings_revision_inputs(report_id, revision, request.period_end)
        cutoff = datetime.fromisoformat(report["as_of"])
        event_at = request.event_at or plan.event_at
        if not _source_url(request.source_url):
            raise EarningsError("請提供公司或 SEC 公告的 HTTPS 來源")
        if not event_at <= request.published_at <= request.obtained_at <= cutoff:
            raise EarningsError("公告公開與取得時間須位於事件和報告截止時間之間")
        if (key.currency, key.basis) != ("USD", "US_GAAP"):
            raise EarningsError("完整公告覆核目前支援美元、美國 GAAP 的單季合併營收")
        if adapter.identity["mode"] == "fixture":
            raise EarningsError("完整公告覆核需要 Codex CLI 或模型 API 模式")
        blocks = parse_filing(request.html, document_id="release")
        if not blocks:
            raise EarningsError("HTML 未含可讀取的公告內文")
        document = {"id": "release", "source_url": request.source_url,
                    "published_at": request.published_at.isoformat(), "obtained_at": request.obtained_at.isoformat(),
                    "blocks": blocks}
        extraction = adapter._generate(FilingExtraction, FILING_SELECTION_PROMPT, {
            "target": key.model_dump(mode="json"), "baseline": {"amount": point["revenue"], "available_at": report["as_of"]},
            "event_at": event_at.isoformat(), "as_of": report["as_of"], "fiscal_label": request.fiscal_label,
            "documents": [document],
        })
        audit = check_filing_revision(key=key, incumbent=point["revenue"], event_at=event_at, as_of=cutoff,
                                      documents=[document], selection=extraction.selection, fiscal_label=request.fiscal_label)
        if extraction.selection is None:
            refs = set(extraction.evidence_ids)
            audit["citations"] = [filing_citation(document, block) for block in blocks if block["id"] in refs]
            audit["evidence_ids"] = [item["id"] for item in audit["citations"]]
        return {"as_of": report["as_of"], "report_revision": revision, "incumbent": point["revenue"], "audit": audit,
                **linkage_fields(report), **scenario_fields(report)}

    def revenue_revision_check(self, report_id, revision, request):
        report, plan, key, point = self.earnings_revision_inputs(report_id, revision, request.period_end)
        quarter = next(row for row in plan.quarters if row.period_end == request.period_end)
        driver = next((row for row in plan.drivers if row.scenario == "base" and row.period_end == request.period_end), None)
        profile = next((row for row in plan.eps_assumptions if row.period_end == request.period_end), None)
        cutoff = datetime.fromisoformat(report["as_of"])
        incumbent_refs = list(dict.fromkeys(driver.evidence_ids if driver else quarter.evidence_ids))
        if len(incumbent_refs) > 12:
            raise EarningsError("現版預估引用超過試算可逐筆核對的 12 項上限。")
        with localcontext() as ctx:
            ctx.prec = 50
            amount = Decimal(point["revenue"]).quantize(Decimal("0.00000001")).normalize()
            incumbent = RevisionQuote(key=key, available_at=cutoff, low=amount, high=amount,
                                      evidence_ids=incumbent_refs)
            audit = evaluate_revision(
                RevisionRequest(key=key, event_at=request.event_at or plan.event_at, incumbent=incumbent,
                                original=request.original, disclosure=request.disclosure),
                report["evidence"], as_of=cutoff, fiscal_label=request.fiscal_label,
            )
            financial_impact = None
            if audit["status"] == "eligible":
                revised = quarter.model_copy(update={
                    "segment_revenue": {"consolidated": Decimal(audit["revised"])},
                    "gross_margin": Decimal(point["gross_margin"]),
                    "opex": Decimal(point["opex"]),
                })
                scenario = operating_numbers(revised, profile=profile)
                financial_impact = {
                    metric: {"before": point[metric], "after": format(scenario[metric], "f")}
                    for metric in ("revenue", "operating_income", "eps")
                }
            elif audit["status"] == "noop":
                financial_impact = {
                    metric: {"before": point[metric], "after": point[metric]}
                    for metric in ("revenue", "operating_income", "eps")
                }
        return {"as_of": report["as_of"], "report_revision": revision, "audit": audit,
                "financial_impact": financial_impact, **linkage_fields(report), **scenario_fields(report)}

    def earnings_branch(self, report_id, branch):
        parent = self.revision(report_id, branch.parent_revision)
        if "earnings" not in parent:
            raise EarningsError("原稿缺少盈利預測基準")
        old = parent["earnings"]["inputs"]
        incoming = {(item.period_end.isoformat(), item.scenario): item.model_dump(mode="json")
                    for item in branch.drivers}
        if len(incoming) != len(branch.drivers):
            raise EarningsError("修改項目重複")
        if {period for period, _ in incoming} - {item["period_end"] for item in old["quarters"]}:
            raise EarningsError("情境須對應既有預測季度")
        drivers = {(item["period_end"], item["scenario"]): item for item in old["drivers"]}
        drivers.update(incoming)
        links = {item["id"]: item for item in old.get("driver_links", [])}
        links.update({item.id: item.model_dump(mode="json") for item in branch.driver_links})
        if len(links) > 20:
            raise EarningsError("同一版本最多保留二十個假說驅動連結")
        profiles = {item["period_end"]: item for item in old.get("eps_assumptions", [])}
        profiles.update({item.period_end.isoformat(): item.model_dump(mode="json") for item in branch.eps_assumptions})
        if set(profiles) - {item["period_end"] for item in old["quarters"]}:
            raise EarningsError("EPS 假設須對應既有預測季度")
        calibrate = branch.calibrate_guidance if branch.calibrate_guidance is not None else old.get("calibrate_guidance")
        plan_event_at = datetime.fromisoformat(old["event_at"])
        pre_event, current = list(old["references"]), list(old["event_values"])
        for reference in branch.issuer_guidance:
            bucket = pre_event if reference.available_at < plan_event_at else current
            data = reference.model_dump(mode="json")
            if data not in bucket:
                bucket.append(data)
        if len(pre_event) > 40 or len(current) > 20:
            raise EarningsError("加入指引後超過此版本的基準或事件數字上限")
        bridge = branch.revenue_bridge.model_dump(mode="json") if branch.revenue_bridge else old.get("revenue_bridge")
        if bridge and (len(old["quarters"]) != 2 or bridge["period_end"] != max(row["period_end"] for row in old["quarters"])):
            raise EarningsError("營收橋接須對應第二個預測季度")
        plan = EarningsPlan.model_validate({**old, "drivers": list(drivers.values()), "driver_links": list(links.values()),
                                           "eps_assumptions": list(profiles.values()), "calibrate_guidance": calibrate,
                                           "references": pre_event, "event_values": current, "revenue_bridge": bridge})
        return self._save_earnings_child(report_id, parent, plan, "earnings_scenario")

    def earnings_consensus(self, report_id, request):
        parent = self.revision(report_id, request.parent_revision)
        if "earnings" not in parent:
            raise EarningsError("原稿缺少盈利預測基準")
        old = EarningsPlan.model_validate(parent["earnings"]["inputs"])
        document, references, log = parse_consensus(request, old, parent["target"], datetime.now(timezone.utc))
        if any(row["document_id"] == document.id for row in parent["evidence"]):
            return parent
        if len(old.references) + len(references) > 40:
            raise EarningsError("共識快照超出此版本的四十筆基準上限")
        evidence = document_evidence(document)
        new = {**parent, "evidence": [*parent["evidence"], *evidence],
               "claims": [*parent["claims"], *[
                   {"id": f"fact:{row['id']}", "kind": "fact", "text": row["quote"], "evidence_id": row["id"]}
                   for row in evidence
               ]], "consensus_imports": [*parent.get("consensus_imports", []), log]}
        plan = old.model_copy(update={"references": [*old.references, *references]})
        return self._save_earnings_child(report_id, new, plan, "earnings_consensus")

    def _save_earnings_child(self, report_id, parent, plan, kind):
        earnings = calculate_earnings(
            plan, datetime.fromisoformat(parent["as_of"]), parent["evidence"],
            hypotheses=parent["hypotheses"], claims=parent["claims"],
            business_linkages=parent.get("business_linkages", ()),
        )
        earnings["driver_origin"] = ("analyst_branch" if kind == "earnings_scenario"
                                     else parent["earnings"].get("driver_origin", "input"))
        report = {**parent, "earnings": earnings, "revision_kind": kind}
        report["earnings_parent_revision"] = parent["revision"]
        report["markdown"] = render(report)
        child = self.save_child(report_id, parent["revision"], report)
        return self.revision(report_id, child)

    def _earnings_action(self, report_id, revision, kind, key, payload, now):
        encoded = encode(payload)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT recorded_at, payload FROM earnings_log "
                "WHERE report_id=? AND revision=? AND kind=? AND action_key=?",
                (report_id, revision, kind, key),
            ).fetchone()
            if existing:
                if existing[1] != encoded:
                    raise EarningsError("已有不同內容的核對紀錄")
                return {"id": key, "recorded_at": existing[0], **payload}
            recorded_at = now.isoformat()
            db.execute("INSERT INTO earnings_log VALUES (?, ?, ?, ?, ?, ?)",
                       (report_id, revision, kind, key, recorded_at, encoded))
        return {"id": key, "recorded_at": recorded_at, **payload}

    def register_forecast(self, report_id, revision, request):
        report = self.revision(report_id, revision)
        snapshot = datetime.fromisoformat(report["as_of"])
        now = datetime.now(timezone.utc)
        if request.deadline <= snapshot or request.key.period_end < snapshot.date():
            raise EarningsError("觀測期末和截止日須在原稿時點之後")
        if request.purpose == "live" and now > snapshot and request.key.period_end < now.date():
            raise EarningsError("已結束的觀測期間只能登記為歷史回放")
        if request.purpose == "live" and request.deadline <= now:
            raise EarningsError("正式登記時截止日尚未到期")
        available_evidence(request.evidence_ids, {row["id"]: row for row in report["evidence"]}, snapshot)
        payload = {**request.model_dump(mode="json"), "snapshot_as_of": report["as_of"], "target": report["target"]}
        key = hashlib.sha256(encode(payload).encode()).hexdigest()[:24]
        return self._earnings_action(report_id, revision, "forecast", key, payload, now)

    def forecast_resolution(self, report_id, revision, forecast_id, request):
        self.revision(report_id, revision)
        with self.connection() as db:
            stored = db.execute(
                "SELECT recorded_at, payload FROM earnings_log "
                "WHERE report_id=? AND revision=? AND kind='forecast' AND action_key=?",
                (report_id, revision, forecast_id),
            ).fetchone()
        if stored is None:
            raise MissingReport("找不到預測登記")
        raw = json.loads(stored[1])
        snapshot, target = raw.pop("snapshot_as_of"), raw.pop("target")
        forecast = ForecastRegistration.model_validate(raw)
        registration = {**forecast.model_dump(), "key": forecast.key}
        registration["snapshot_as_of"] = datetime.fromisoformat(snapshot)
        registration["registered_at"] = datetime.fromisoformat(stored[0])
        now = datetime.now(timezone.utc)
        outcome, score = resolve_forecast(registration, request, now)
        payload = {
            "forecast_id": forecast_id, "outcome": outcome, "brier_score": score, "target": target,
            "observation": request.model_dump(mode="json"),
        }
        return self._earnings_action(report_id, revision, "resolution", forecast_id, payload, now)

    def research_review(self, report_id, revision, request):
        self.revision(report_id, revision)
        payload = request.model_dump(mode="json")
        return self._earnings_action(report_id, revision, "review", uuid4().hex, payload, datetime.now(timezone.utc))

    def earnings_status(self, report_id, revision):
        report = self.revision(report_id, revision)
        with self.connection() as db:
            rows = db.execute(
                "SELECT kind, action_key, recorded_at, payload FROM earnings_log "
                "WHERE report_id=? AND revision=? AND kind IN ('forecast', 'resolution', 'review') "
                "ORDER BY recorded_at, rowid",
                (report_id, revision),
            ).fetchall()
        logs = {"forecast": {}, "resolution": {}, "review": {}}
        for kind, action_key, at, payload in rows:
            logs[kind][action_key] = {"id": action_key, "recorded_at": at, **json.loads(payload)}
        now = datetime.now(timezone.utc)
        for key, forecast in logs["forecast"].items():
            forecast["resolution"] = logs["resolution"].get(key)
            forecast["status"] = (forecast["resolution"]["outcome"] if forecast["resolution"] else
                                  "overdue" if datetime.fromisoformat(forecast["deadline"]) < now else "pending")
        return {"report_id": report_id, "revision": revision, "earnings": report.get("earnings"),
                "forecasts": list(logs["forecast"].values()), "reviews": list(logs["review"].values()),
                **linkage_fields(report), **scenario_fields(report)}

    @staticmethod
    def checked_answer(adapter, report, question):
        answer = adapter.answer(report, question)
        data = answer.model_dump() | scenario_fields(report)
        evidence = {item["id"]: item for item in report["evidence"]}
        if isinstance(answer, LinkedAnswer):
            data["business_linkages"], data["business_linkage_gap"] = validate_linkages(
                answer, report, evidence, company_key, note_missing=bool(answer.business_linkages),
            )
        calculations = {item["id"]: item for item in report.get("disclosed_calculations", [])}
        selected = list(dict.fromkeys(data.pop("calculation_ids", [])))
        if set(selected) - calculations.keys():
            raise AdapterError("模型選取了不存在或不可見的計算資料")
        for key in selected:
            item = calculations[key]
            left, right = item["operands"]
            numbers = "、".join(
                f"{operand['label']} {'約' if operand['approximate'] else ''}{Decimal(operand['value']):,f} {operand['unit']}"
                for operand in (left, right)
            )
            relation = "≈" if item["unit"] == "%" or item["approximate"] else "="
            approx = "（來源金額為約數）" if item["approximate"] else ""
            data["answer"] += (
                f"\n\n{item['label']}：{numbers}；"
                f"{item['formula']} {relation} {item['value']}{item['unit']}{approx}。"
            )
            data["evidence_ids"] = list(dict.fromkeys(data["evidence_ids"] + item["evidence_ids"]))
        if selected:
            data["calculations"] = [calculations[key] for key in selected]
        if set(data["evidence_ids"]) - evidence.keys():
            raise AdapterError("模型回答使用了不存在或不可見的證據引用")
        if not data["evidence_ids"] and not data["gaps"]:
            raise AdapterError("無引文的模型回答必須列明證據缺口")
        return data

    def answer_question(self, report_id, parent, question, adapter):
        initial = self.checked_answer(adapter, parent, question.question)
        if "business_linkages" in initial:
            initial.update(merged_linkages(parent, initial["business_linkages"], initial["business_linkage_gap"], company_key))
        else:
            initial.update(linkage_fields(parent))

        def finish_initial(**extra):
            result = {**initial, **extra}
            if initial.get("business_linkages") and initial["business_linkages"] != parent.get("business_linkages"):
                followup = {"parent_revision": question.parent_revision, "question": question.question,
                            "answer": initial, "added_evidence_ids": []}
                report = {**parent, **linkage_fields(initial), "revision_kind": "linkage_follow_up",
                          "evidence_followups": [*parent.get("evidence_followups", []), followup]}
                report["markdown"] = render(report)
                result["child_revision"] = self.save_child(report_id, question.parent_revision, report)
            return result

        if question.evidence_search == "off" or not initial["gaps"]:
            return finish_initial()
        event = self.event(report_id)
        if event.search_mode == "off" or not callable(getattr(adapter, "search", None)):
            return finish_initial()
        try:
            found, audit = collect(event, adapter, question=question.question,
                                   unanswered=initial["gaps"], parent_evidence=parent["evidence"])
        except AdapterError:
            return finish_initial(evidence_search={"status": "failed"})
        if not found:
            return finish_initial(evidence_search={"status": "no_new_sources", **audit})
        added = [item for doc in found for item in document_evidence(doc)]
        report = {**parent, "evidence": parent["evidence"] + added}
        new_refs = {item["id"] for item in added}
        refined = self.checked_answer(adapter, report | {"linkage_refresh_evidence_ids": sorted(new_refs)}, question.question)
        refreshed = [path for path in refined.get("business_linkages", []) if new_refs.intersection(linkage_refs(path))]
        if not new_refs.intersection(refined["evidence_ids"]) and not refreshed:
            return finish_initial(evidence_search={"status": "unresolved", **audit})
        can_refresh = "business_linkages" in refined
        if can_refresh:
            report.update(merged_linkages(initial, refreshed, refined["business_linkage_gap"], company_key))
            report["claims"] = [*parent["claims"], *(
                {"id": f"fact:{item['id']}", "kind": "fact", "text": item["quote"], "evidence_id": item["id"]}
                for item in added
            )]
            refined.update(linkage_fields(report))
        followup = {
            "parent_revision": question.parent_revision, "question": question.question,
            "answer": refined, "added_evidence_ids": sorted(new_refs), "discovery": audit,
        }
        original_followups = parent.get("evidence_followups", [])
        report["evidence_followups"] = [*original_followups, followup]
        report["revision_kind"] = "evidence_follow_up"
        if can_refresh:
            report["markdown"] = render(report)
        else:
            report["markdown"] = parent["markdown"] + render_followups({
                "evidence": report["evidence"], "evidence_followups": [followup],
            })
        child = self.save_child(report_id, question.parent_revision, report)
        return {**linkage_fields(report), **refined, "child_revision": child, "evidence_search": {"status": "published", **audit}}

    def question(self, report_id, question, adapter):
        parent = self.revision(report_id, question.parent_revision)
        if question.overrides is None:
            return {**self.answer_question(report_id, parent, question, adapter), **opportunity_fields(parent)}

        if parent["model_inputs"] is None:
            raise ValueError("此版本缺少可重算的財務參數")
        previous_inputs = FinancialInputs.model_validate(parent["model_inputs"])
        inputs = previous_inputs.model_copy(update=question.overrides.model_dump())
        if parent.get("report_version") == REPORT_VERSION:
            report = apply_financial_scenario(parent, inputs)
        else:
            report = build_report(self.event(report_id), adapter, inputs, discovery=parent.get("discovery"))
            if parent.get("evidence_followups"):
                report["evidence_followups"] = parent["evidence_followups"]
                included = {item["id"] for item in report["evidence"]}
                report["evidence"].extend(item for item in parent["evidence"] if item["id"] not in included)
        changes = []
        for section in ("model_inputs", "model_outputs", "hypotheses", "assessment", "claims", "business_linkages"):
            before, after = parent.get(section), report.get(section)
            if isinstance(before, dict):
                changes.extend(
                    {"field": f"{section}.{field}", "before": before.get(field), "after": after.get(field)}
                    for field in sorted(before.keys() | after.keys())
                    if before.get(field) != after.get(field)
                )
            elif before != after:
                changes.append({"field": section, "before": before, "after": after})
        eps_delta = Decimal(report["model_outputs"]["incremental_eps"]) - Decimal(
            parent["model_outputs"]["incremental_eps"]
        )
        threshold = report["model_outputs"]["break_even_lots"]
        threshold_text = f"{threshold} 批" if threshold is not None else "無法達成"
        report["question"] = question.question
        report["revision_kind"] = "scenario"
        report["changes"] = changes
        report["incremental_eps_delta"] = str(eps_delta)
        report["branch_summary"] = {
            "parent_revision": question.parent_revision, "prior_lots": previous_inputs.lots,
        }
        report["markdown"] = render(report)
        revision = self.save_child(report_id, question.parent_revision, report)
        return {
            "child_revision": revision, "changes": changes, "incremental_eps_delta": str(eps_delta),
            "answer": (
                f"若 {inputs.lots:,} 批全數在本季交付並認列，增量營業利益為 "
                f"{Decimal(report['model_outputs']['incremental_operating_profit']):+,f} {inputs.currency}，"
                f"稀釋 EPS 增量為 {Decimal(report['model_outputs']['incremental_eps']):+f} {inputs.currency}/股，"
                f"較母版變動 {eps_delta:+f} {inputs.currency}/股。"
                f"每批變動成本為 {inputs.variable_cost_per_lot:,f} {inputs.currency}，"
                f"季內新增固定支出為 {inputs.fixed_cost:,f} {inputs.currency}，"
                f"該條件下最低不虧損量為 {threshold_text}。交易方向仍待營運證據與估值。"
            ),
            "evidence_ids": [inputs.evidence_id],
            "gaps": report["valuation"]["gaps"],
            **linkage_fields(report), **scenario_fields(report),
            **opportunity_fields(report),
        }
