"""Replay six archived issuers without generating any new extraction."""
import json
from pathlib import Path

from benchmarks import guidance_arithmetic as b
from benchmarks import guidance_tables as t
from benchmarks.guidance_ytd_regression import ENDS

OUT = Path("output/guidance-table")


def replay(out=OUT):
    rows = []
    for root in (Path("output/guidance-arithmetic-v2"), Path("output/guidance-ytd")):
        frozen = json.loads((root/"cases.json").read_text())
        for key, data in frozen.items():
            if root.name == "guidance-ytd" and key not in ("mndy", "frog"):
                continue
            case = b.Case.model_validate(data["case"])
            blocks = b.case_blocks(case)
            known = data.get("vintages") or {
                doc.id: {"report_end": end, "fiscal_year": 2025, "quarter": q}
                for doc, end, q in zip(case.documents, ENDS[key], (2, 3))}
            calls = [f"{key}~r{repeat}-harness" for repeat in range(1,4)] if root.name != "guidance-ytd" else [f"{key}-extract"]
            for label in calls:
                path = root/"calls"/f"{label}.json"
                call = json.loads(path.read_text())
                source = call.get("raw", call.get("output"))
                response = b.Extraction.model_validate(source)
                assessment = t.revised(case, blocks, response, known)
                marks = b.grade(case, b.gold(case, blocks), assessment["answers"])
                rows.append({"case": key, "source": str(path), "original": source,
                             "numeric_exact": marks["exact"], "validation": assessment, "score": marks})
                print(key, label, marks["exact"], assessment["errors"], flush=True)
    out.mkdir(parents=True,exist_ok=True)
    b.equal.journal.atomic(out/"regressions.json",rows)
    return rows


if __name__ == "__main__":
    replay()
