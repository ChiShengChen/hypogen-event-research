import argparse
import json
from datetime import datetime
from difflib import unified_diff
from pathlib import Path

from .adapters import AdapterError, LinkedFixture, RankedCodex, RankedLive
from .schema import Event, Question
from .store import Store


def main():
    parser = argparse.ArgumentParser(description="執行虛構停工事件研究")
    parser.add_argument("--output", type=Path, default=Path("output/demo"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--codex", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fixtures = Path(__file__).parent / "fixtures"
    event = Event.model_validate_json((fixtures / "shutdown.json").read_text(encoding="utf-8"))
    db = Store(args.output / "research.sqlite3")
    engine = RankedCodex() if args.codex else RankedLive() if args.live else LinkedFixture()
    evidence_check = None
    extra_reports = {}
    try:
        result = db.create(event, engine)
        report_id = result["report_id"]
        parent = db.revision(report_id, 1)
        question = Question(parent_revision=1, question="若合格產能只能接到 300 批，乙還受益嗎？",
                            overrides={"lots": 300})
        branch = db.question(report_id, question, engine)
        child = db.revision(report_id, branch["child_revision"])
        if args.live or args.codex:
            evidence_question = Question(parent_revision=1, question="客戶已認證乙嗎？")
            before = db.question(report_id, evidence_question, engine)
            print("原稿認證追問", before, flush=True)
        if args.codex:
            later_event = event.model_copy(
                update={"as_of": datetime.fromisoformat("2025-01-21T09:00:00+08:00")}
            )
            later = db.create(later_event, engine)
            late_report = db.revision(later["report_id"], 1)
            after = db.question(later["report_id"], evidence_question, engine)
            print("新截止時點認證追問", after, flush=True)
            if not before["gaps"] or "qualification:1" not in after["evidence_ids"]:
                raise AdapterError("GPT 的認證追問未通過時點驗證")
            evidence_check = {
                "model": engine.identity["model"],
                "question": evidence_question.question,
                "before": {"as_of": parent["as_of"], "report_id": report_id, **before},
                "after": {"as_of": late_report["as_of"], "report_id": later["report_id"], **after},
            }
            demand = Event.model_validate_json((fixtures / "demand.json").read_text(encoding="utf-8"))
            demand_run = db.create(demand, engine)
            extra_reports = {
                "with-qualification.md": late_report["markdown"],
                "demand.md": db.revision(demand_run["report_id"], 1)["markdown"],
            }
    except AdapterError as exc:
        parser.exit(1, f"{exc}\n")
    original, revised = parent["markdown"], child["markdown"]
    diff = "".join(unified_diff(original.splitlines(keepends=True), revised.splitlines(keepends=True),
                                fromfile="original.md", tofile="revised.md"))
    artifacts = {"original.md": original, "revised.md": revised, "revision.diff": diff, **extra_reports}
    if evidence_check is not None:
        artifacts["evidence-check.json"] = json.dumps(evidence_check, ensure_ascii=False, indent=2) + "\n"
    for filename, body in artifacts.items():
        path = args.output / filename
        path.write_text(body, encoding="utf-8")
        print(path.resolve())
    print(f"EPS {parent['model_outputs']['incremental_eps']} → {child['model_outputs']['incremental_eps']} "
          f"（差額 {branch['incremental_eps_delta']}）")
    print(branch["answer"])


if __name__ == "__main__":
    main()
