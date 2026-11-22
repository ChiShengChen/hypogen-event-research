import hashlib
import json
import sqlite3
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from .adapters import AdapterError
from .research import FORMULA_VERSION, REPORT_VERSION, apply_financial_scenario, build_report, render
from .schema import Event, FinancialInputs


class MissingReport(Exception):
    pass


def encode(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)


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
        request_key = hashlib.sha256(encode({
            "event": payload, "adapter": adapter.identity, "formula_version": FORMULA_VERSION,
            "report_version": REPORT_VERSION,
        }).encode()).hexdigest()
        lookup = "SELECT run_id, report_id FROM runs WHERE request_key = ?"
        with self.connection() as db:
            existing = db.execute(lookup, (request_key,)).fetchone()
        if existing:
            return self.result(existing)
        report = build_report(event, adapter)
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

    def question(self, report_id, question, adapter):
        parent = self.revision(report_id, question.parent_revision)
        if question.overrides is None:
            answer = adapter.answer(parent, question.question)
            if set(answer.evidence_ids) - {item["id"] for item in parent["evidence"]}:
                raise AdapterError("模型回答使用了不存在或不可見的證據引用")
            if not answer.evidence_ids and not answer.gaps:
                raise AdapterError("無引文的模型回答必須列明證據缺口")
            return answer.model_dump()

        if parent["model_inputs"] is None:
            raise ValueError("此版本缺少可重算的財務參數")
        previous_inputs = FinancialInputs.model_validate(parent["model_inputs"])
        inputs = previous_inputs.model_copy(update=question.overrides.model_dump())
        if parent.get("report_version") == REPORT_VERSION:
            report = apply_financial_scenario(parent, inputs)
            for field in ("report_id", "revision", "parent_revision"):
                report.pop(field, None)
        else:
            with self.connection() as db:
                payload = db.execute("SELECT event FROM runs WHERE report_id = ?", (report_id,)).fetchone()[0]
            report = build_report(Event.model_validate_json(payload), adapter, inputs)
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
        report["changes"] = changes
        report["incremental_eps_delta"] = str(eps_delta)
        report["branch_summary"] = {
            "parent_revision": question.parent_revision, "prior_lots": previous_inputs.lots,
        }
        report["markdown"] = render(report)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            revision = db.execute(
                "SELECT MAX(revision) + 1 FROM revisions WHERE report_id = ?", (report_id,)
            ).fetchone()[0]
            db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?)",
                       (report_id, revision, question.parent_revision, encode(report)))
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
        }
