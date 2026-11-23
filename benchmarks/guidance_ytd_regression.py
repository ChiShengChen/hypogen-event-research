"""Replay the twelve archived v2 extractions without issuing model calls."""
import argparse
import json
from pathlib import Path
import shutil

from benchmarks import guidance_arithmetic as bench
from benchmarks import guidance_ytd as ytd

PREVIOUS = Path.home() / ".local/state/hypogen-benchmarks/guidance-v2-91ea253/output/guidance-arithmetic-v2"
ROOT = Path("output/guidance-ytd")
ENDS = {"gitlab": ("2024-07-31", "2024-10-31"),
        "pure": ("2024-08-04", "2024-11-03"),
        "sprinklr": ("2024-07-31", "2024-10-31"),
        "bestbuy": ("2024-08-03", "2024-11-02")}


def run(previous, out):
    cases = json.loads((previous / "cases.json").read_text())
    records = []
    for key, row in cases.items():
        case = bench.Case.model_validate(row["case"])
        for doc in case.documents:
            path = Path(doc.path)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(previous / "filings" / path.name, path)
        vintages = {doc.id: {"report_end": end, "fiscal_year": 2025, "quarter": quarter}
                    for doc, end, quarter in zip(case.documents, ENDS[key], (2, 3))}
        blocks = bench.case_blocks(case)
        gold = bench.gold(case, blocks)
        for i in range(1, 4):
            source = previous / "calls" / f"{key}~r{i}-harness.json"
            raw = json.loads(source.read_text())
            ext = bench.Extraction.model_validate(raw["output"])
            result = ytd.revised(case, blocks, ext, vintages)
            old, _ = bench.harness_answers(case, blocks, ext)
            astra = json.loads((previous / "calls" / f"{key}~r{i}-astra.json").read_text())
            assert old == raw["answers"]
            records.append({
                "case": key, "repeat": i, "current": bench.grade(case, gold, old),
                "astra": bench.grade(case, gold, astra["answers"]),
                "revised": bench.grade(case, gold, result["answers"]), "validation": result,
                "original_extraction": raw["output"],
            })
    out.mkdir(parents=True, exist_ok=True)
    bench.equal.journal.atomic(out / "regressions.json", records)
    print({arm: sum(r[arm]["exact"] for r in records) for arm in ("astra", "current", "revised")})
    for record in records:
        if not record["revised"]["exact"]:
            print(record["case"], record["repeat"], record["validation"]["errors"])
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", default=PREVIOUS, type=Path)
    parser.add_argument("--out", default=ROOT, type=Path)
    args = parser.parse_args()
    run(args.previous, args.out)
