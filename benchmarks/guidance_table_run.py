"""Preregister and run the cross-page and revenue-scope comparison."""

import argparse
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import signal
from threading import Event

from benchmarks import guidance_tables as verifier
from benchmarks import guidance_ytd_run as paired

b = paired.b
OUT = Path("output/guidance-table")
BASELINE = "98e9139"
ACTUALS = ("prior_reported_in_period", "reported_in_period")


def gold_for(row, case, blocks):
    if case.undetermined:
        return b.gold(case, blocks)
    values = {role: b.figure_value(role, refs, blocks) for role, refs in case.figures.items() if role not in ACTUALS}
    for role, approved in row["gold_columns"].items():
        if not all(b.normalize(ref["quote"]) in b.normalize(blocks[ref["block"]]["text"])
                   for ref in (approved["row"], *approved["units"], *approved["heading"])):
            raise ValueError(f"unverified archived anchor: {case.id}/{role}")
        cells = verifier.previous.AMOUNT.findall(approved["row"]["quote"])
        raw = cells[approved["column"] - 1]
        if raw != approved["raw"]:
            raise ValueError(f"archived column does not match approved amount: {case.id}/{role}")
        values[role] = Decimal(raw.replace(",", "")) * approved["multiplier"]
    computed = b.compute(b.GuidanceInputs.model_validate(values))
    return {key: computed[key] for key in case.items}


def exact_columns(row, case, blocks, figures, proofs, evidence_ids):
    remaining = {name: refs for name, refs in paired.refs_for(figures).items()}
    failures = []
    for name, refs in case.figures.items():
        if name in ACTUALS:
            continue
        candidates = remaining.get(name, [])
        accepted = {ref.block for ref in refs}
        accepted.update(row.get("equivalent_guidance", {}).get(name, []))
        try:
            if len(candidates) != 1 or candidates[0].block not in accepted or b.figure_value(
                    name, candidates, blocks) != b.figure_value(name, refs, blocks):
                failures.append((name, "引文不足"))
        except ValueError as exc:
            failures.append((name, "單位錯" if "單位" in str(exc) or "幣別" in str(exc) else "引文不足"))
    for name in ACTUALS:
        anchor = row["gold_columns"][name]
        block = anchor["row"]["block"]
        if proofs is not None:
            entries = proofs.get(name, [])
            sources = {ref["block"] for cell in entries for ref in cell["unit_sources"]}
            required = {ref["block"] for ref in anchor["units"]}
            if (len(entries) != 1 or entries[0]["row"]["block"] != block or
                    entries[0]["raw"] != anchor["raw"] or entries[0]["column"] != anchor["column"]
                    or entries[0]["multiplier"] != anchor["multiplier"] or not required <= sources):
                failures.append((name, "引文不足"))
            continue
        refs = remaining.get(name, [])
        units = {ref["block"] for ref in anchor["units"]}
        heading = {ref["block"] for ref in anchor["heading"]}
        if len(refs) != 1 or refs[0].block != block or b.normalize(refs[0].quote) not in anchor["equivalent_amounts"]:
            failures.append((name, "引文不足"))
            continue
        ref, = refs
        if not (units | heading) <= {block, ref.unit_block, *evidence_ids}:
            failures.append((name, "引文不足"))
            continue
        if ref.unit_quote and (ref.unit_block not in units | {block} or
                b.normalize(ref.unit_quote) not in b.normalize(blocks[ref.unit_block]["text"]) or
                verifier.declaration_factors(verifier.monetary_unit(ref.unit_quote)) != {anchor["multiplier"]}):
            failures.append((name, "單位錯"))
            continue
        if ref.unit_quote is None and not units <= set(evidence_ids):
            failures.append((name, "引文不足"))
    return failures


def grade(row, case, blocks, answers, figures, *, errors=None, categories=(), rationale="", proofs=None,
          evidence_ids=(), missing_source=False):
    expected = {key: val if b.ITEM_KINDS[key] == "direction" or val == "unknown" else Decimal(val)
                for key, val in row["gold"].items()}
    marks = b.grade(case, expected, answers)
    negative = bool(case.undetermined)
    if negative:
        failed = missing_source or not any(term.casefold() in rationale.casefold() for term in row["gap_terms"])
        citations = [("missing_reason", "引文不足")] if failed else []
    else:
        citations = exact_columns(row, case, blocks, figures, proofs, evidence_ids)
    false_adjustment = negative and any(str(answers.get(item, "")).strip().casefold() not in {"", "unknown"}
                                        for item in case.items)
    false_abstention = not negative and any(str(answers.get(item, "")).strip().casefold() == "unknown"
                                           for item in case.items)
    dimensions = set(categories) | {kind for _, kind in citations}
    errors = errors or {}
    if any(token in msg for msg in errors.values() for token in ("倍率", "幣別", "單位", "scale", "currency")):
        dimensions.add("單位")
    if not marks["exact"] and (false_adjustment or not dimensions):
        dimensions.add("營收口徑" if false_adjustment else "算式")
    if not marks["exact"] and not errors and not false_adjustment and not false_abstention:
        dimensions.add("算式")
    exact = marks["exact"] and not citations
    return marks | {"numeric_exact": marks["exact"], "exact": exact, "citation_failures": citations,
                    "false_adjustment": false_adjustment, "false_abstention": false_abstention,
                    "failure_dimensions": [] if exact else sorted(dimensions)}


def normalize(arm, payload, response):
    row, case, blocks = payload
    if arm == "astra":
        direct = paired.Direct.model_validate(response).model_dump(mode="json")
        answers = {entry["item"]: entry["value"] for entry in direct["answers"]}
        refs = direct["evidence_ids"]
        missing = not set(row.get("gap_anchor", {}).get("blocks", [])).intersection(refs)
        return {"raw": direct, "arms": {"astra": grade(row, case, blocks, answers, direct["figures_used"],
                rationale=direct["missing_reason"] or direct["reason"], evidence_ids=refs, missing_source=missing)}}
    extraction = b.Extraction.model_validate(response)
    current = paired.y.revised(case, blocks, extraction, row["vintages"])
    revised = verifier.revised(case, blocks, extraction, row["vintages"])
    scores = {}
    for label, result in (("current", current), ("revised", revised)):
        rationale = " ".join(f"{key} {val}" for key, val in result["errors"].items())
        scores[label] = grade(row, case, blocks, result["answers"], result["figures"],
                              errors=result["errors"], categories=result["categories"].values(),
                              rationale=rationale, proofs=result["proofs"] if label == "revised" else None)
    return {"raw": extraction.model_dump(mode="json"), "current_validation": current,
            "validation": revised, "arms": scores}


def seal(root, rows):
    if any(row["case"]["ticker"] in {"GTLB", "PSTG", "CXM", "BBY", "MNDY", "FROG", "DOCU", "SPT", "YETI",
                                     "WDAY", "S", "DOCS", "HD", "TGT", "COST", "DECK"} for row in rows):
        raise ValueError("issuer used in an earlier experiment")
    for row in rows:
        if bool(row["case"]["undetermined"]) == bool(row.get("gold_columns")):
            raise ValueError(f"gold columns must cover each scorable positive: {row['case']['id']}")
    paths = [Path(__file__), Path(verifier.__file__), Path(paired.__file__), Path("benchmarks/guidance_table_cases.py")]
    protocol = {
        "source_ledger_sha256": sha256((root / "source-ledger.json").read_bytes()).hexdigest(),
        "baseline": BASELINE,
        "hypothesis": "跨頁欄位對齊與合併營收組成核對可多答對正例並維持零誤調。",
        "implementation_sha256": {str(path.resolve().relative_to(Path.cwd())): sha256(path.read_bytes()).hexdigest()
                                  for path in paths},
        "citation_equivalence": "同來源相同時點的原文頁、核可金額與對應欄。跨頁同時列出表頭、倍率及數值頁。"
                                "金額的可接受字面形式逐欄封存。負例須附公告與具體缺項。",
        "separate_metrics": ["numeric_exact", "numeric_with_bad_citation", "false_abstentions", "false_adjustments"],
    }
    return paired.seal(root, rows, extra_protocol=protocol, gold_for=gold_for, both_directions=False,
                       direct_instruction=" For a table continued across pages, cite the currency and scale heading "
                       "using unit_block and also list all separate duration, scale and amount block IDs in evidence_ids.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("seal", "run", "report"))
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with b.equal.journal.exclusive(args.out):
        if args.phase == "seal":
            print(seal(args.out, paired.read(args.out / "case-input.json"))["sealed_at"], flush=True)
        elif args.phase == "run":
            for split in ("pilot", "holdout"):
                if not stop.is_set():
                    paired.run(args.out, split, stop, transform=normalize)
        else:
            from benchmarks.guidance_table_report import publish
            publish(args.out)


if __name__ == "__main__":
    main()
