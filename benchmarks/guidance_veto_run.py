"""Compare Harness modes on guidance-revision arithmetic.

`--phase replay` rescores archived replies with zero model calls. Each case keeps the grader its benchmark
sealed. The direct arm is the archived pure-Astra reply; the veto arm is that same reply after the
deterministic veto; the extract arm is the archived extraction reply through the newest table verifier.
Every replayed case was seen while the veto rules were written, so this is a development result only.
"""

import argparse
from decimal import Decimal
import json
from pathlib import Path

from benchmarks import guidance_arithmetic as b
from benchmarks import guidance_harness as harness
from benchmarks import guidance_table_run as table
from benchmarks import guidance_ytd_run as ytd

OUT = Path("docs/guidance-veto")
SOURCES = {"guidance-ytd": Path("docs/guidance-ytd"), "guidance-table": Path("docs/guidance-table")}
ARMS = ("astra", "veto", "extract")


def grade_direct(source, row, case, blocks, answers, figures, rationale, evidence_ids):
    if source == "guidance-ytd":
        cited = any(ref in blocks and ref.startswith(case.documents[0].id + ":") for ref in evidence_ids)
        return ytd.grade(row, case, blocks, answers, figures, {}, rationale, missing_source=not cited)
    missing = not set(row.get("gap_anchor", {}).get("blocks", [])).intersection(evidence_ids)
    return table.grade(row, case, blocks, answers, figures, rationale=rationale, evidence_ids=evidence_ids,
                       missing_source=missing)


def grade_extract(source, row, case, blocks, result):
    rationale = result["reason"] or ""
    categories = result["categories"].values()
    if source == "guidance-ytd":
        return ytd.grade(row, case, blocks, result["answers"], result["figures"], result["errors"], rationale,
                         categories=categories)
    return table.grade(row, case, blocks, result["answers"], result["figures"], errors=result["errors"],
                       categories=categories, rationale=rationale, proofs=result["proofs"])


def outcome(case, marks, answers):
    negative = bool(case.undetermined)
    said = [str(answers.get(item, "")).strip().casefold() for item in case.items]
    return {"exact": marks["exact"], "numeric_exact": marks["numeric_exact"],
            "false_adjustment": negative and any(value not in {"", "unknown"} for value in said),
            "false_abstention": not negative and any(value == "unknown" for value in said),
            "failures": marks.get("failure_dimensions", [])}


def replay_case(source, row, astra, extraction):
    case = b.Case.model_validate(row["case"])
    blocks = b.case_blocks(case)
    direct = ytd.Direct.model_validate(astra).model_dump(mode="json")
    answers = {entry["item"]: entry["value"] for entry in direct["answers"]}
    rationale = direct["missing_reason"] or direct["reason"]
    arms = {"astra": (answers, grade_direct(source, row, case, blocks, answers, direct["figures_used"], rationale,
                                            direct["evidence_ids"]))}
    veto = harness.answer("veto", case, blocks, direct)
    arms["veto"] = (veto["answers"], grade_direct(source, row, case, blocks, veto["answers"], veto["figures"],
                                                  veto["reason"] or rationale, veto["evidence_ids"]))
    extract = harness.answer("extract", case, blocks, extraction, row["vintages"])
    arms["extract"] = (extract["answers"], grade_extract(source, row, case, blocks, extract))
    return {"source": source, "case": case.id, "ticker": case.ticker, "split": case.split,
            "negative": bool(case.undetermined), "gold": row["gold"],
            "arms": {arm: outcome(case, marks, said) | {"answers": said} for arm, (said, marks) in arms.items()},
            "vetoes": veto["vetoes"], "vetoed_items": veto["vetoed_items"]}


def exact_sign_test(wins, losses):
    """Two-sided exact McNemar p-value from discordant counts."""
    n = wins + losses
    if n == 0:
        return 1.0
    from math import comb
    tail = sum(comb(n, k) for k in range(0, min(wins, losses) + 1)) / Decimal(2) ** n
    return float(min(Decimal(1), 2 * tail))


def tally(rows):
    metrics = {}
    for arm in ARMS:
        marks = [row["arms"][arm] for row in rows]
        metrics[arm] = {
            "cases": len(marks),
            "exact": sum(m["exact"] for m in marks),
            "numeric_exact": sum(m["numeric_exact"] for m in marks),
            "positive_exact": sum(m["exact"] for m, row in zip(marks, rows) if not row["negative"]),
            "negative_exact": sum(m["exact"] for m, row in zip(marks, rows) if row["negative"]),
            "false_adjustments": sum(m["false_adjustment"] for m in marks),
            "false_abstentions": sum(m["false_abstention"] for m in marks),
        }
    paired = {}
    for key in ("numeric_exact", "exact"):
        wins = sum(row["arms"]["veto"][key] and not row["arms"]["astra"][key] for row in rows)
        losses = sum(row["arms"]["astra"][key] and not row["arms"]["veto"][key] for row in rows)
        paired[key] = {"veto_only": wins, "astra_only": losses, "p_two_sided": exact_sign_test(wins, losses)}
    return {"metrics": metrics, "veto_vs_astra": paired,
            "vetoed_cases": [row["case"] for row in rows if row["vetoed_items"]],
            "false_vetoes": [row["case"] for row in rows if row["vetoed_items"] and not row["negative"]]}


def replay(out=OUT):
    rows = []
    for source, root in SOURCES.items():
        cases = json.loads((root / "cases.json").read_text())
        for key, row in cases.items():
            raw = root / "raw" / "formal"
            rows.append(replay_case(source, row, json.loads((raw / f"{key}-astra.json").read_text()),
                                    json.loads((raw / f"{key}-extract.json").read_text())))
    summary = {
        "note": "Development replay: every case was seen while the veto rules were written. Zero model calls.",
        "by_source": {source: {split: tally([row for row in rows if row["source"] == source and row["split"] == split])
                               for split in ("pilot", "holdout")} for source in SOURCES},
        "all": tally(rows), "cases": rows,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "dev-replay.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("replay",), required=True)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    summary = replay(args.out)
    for source, splits in summary["by_source"].items():
        for split, result in splits.items():
            print(source, split, {arm: (m["exact"], m["numeric_exact"], m["false_adjustments"], m["false_abstentions"])
                                  for arm, m in result["metrics"].items()})
    print("all", json.dumps({key: summary["all"][key] for key in ("veto_vs_astra", "vetoed_cases", "false_vetoes")}))


if __name__ == "__main__":
    main()
