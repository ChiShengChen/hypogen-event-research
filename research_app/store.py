import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from .adapters import AdapterError, EARNINGS_DRIVER_VERSION
from .consensus import parse_consensus
from .discovery import DISCOVERY_VERSION, collect
from .earnings import EarningsError, available_evidence, calculate_earnings, resolve_forecast
from .research import (
    FORMULA_VERSION, REPORT_VERSION, apply_financial_scenario, build_report, document_evidence,
    render, render_followups,
)
from .schema import EarningsPlan, Event, FinancialInputs, ForecastRegistration


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
        plan = EarningsPlan.model_validate({**old, "drivers": list(drivers.values()), "driver_links": list(links.values()),
                                           "eps_assumptions": list(profiles.values()), "calibrate_guidance": calibrate,
                                           "references": pre_event, "event_values": current})
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
                "WHERE report_id=? AND revision=? ORDER BY recorded_at, rowid",
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
                "forecasts": list(logs["forecast"].values()), "reviews": list(logs["review"].values())}

    @staticmethod
    def checked_answer(adapter, report, question):
        answer = adapter.answer(report, question)
        data = answer.model_dump()
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
        if set(data["evidence_ids"]) - {item["id"] for item in report["evidence"]}:
            raise AdapterError("模型回答使用了不存在或不可見的證據引用")
        if not data["evidence_ids"] and not data["gaps"]:
            raise AdapterError("無引文的模型回答必須列明證據缺口")
        return data

    def answer_question(self, report_id, parent, question, adapter):
        initial = self.checked_answer(adapter, parent, question.question)
        if question.evidence_search == "off" or not initial["gaps"]:
            return initial
        event = self.event(report_id)
        if event.search_mode == "off" or not callable(getattr(adapter, "search", None)):
            return initial
        try:
            found, audit = collect(event, adapter, question=question.question,
                                   unanswered=initial["gaps"], parent_evidence=parent["evidence"])
        except AdapterError:
            return {**initial, "evidence_search": {"status": "failed"}}
        if not found:
            return {**initial, "evidence_search": {"status": "no_new_sources", **audit}}
        added = [item for doc in found for item in document_evidence(doc)]
        report = {**parent, "evidence": parent["evidence"] + added}
        refined = self.checked_answer(adapter, report, question.question)
        new_refs = {item["id"] for item in added}
        if not new_refs.intersection(refined["evidence_ids"]):
            return {**initial, "evidence_search": {"status": "unresolved", **audit}}
        followup = {
            "parent_revision": question.parent_revision, "question": question.question,
            "answer": refined, "added_evidence_ids": sorted(new_refs), "discovery": audit,
        }
        original_followups = parent.get("evidence_followups", [])
        report["evidence_followups"] = [*original_followups, followup]
        report["revision_kind"] = "evidence_follow_up"
        report["markdown"] = parent["markdown"] + render_followups({
            "evidence": report["evidence"], "evidence_followups": [followup],
        })
        child = self.save_child(report_id, question.parent_revision, report)
        return {**refined, "child_revision": child, "evidence_search": {"status": "published", **audit}}

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
        for section in ("model_inputs", "model_outputs", "hypotheses", "assessment", "claims"):
            before, after = parent.get(section), report[section]
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
            **opportunity_fields(report),
        }
