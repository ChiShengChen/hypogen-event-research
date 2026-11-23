"""Choose how the guidance-arithmetic Harness turns model output into answers.

Set GUIDANCE_HARNESS (or pass --harness to a runner that supports it):

- extract (default): the original Harness. The model only quotes operands; code verifies each quote and
  computes with Decimal, and an unproven operand makes its items unknown. With vintages it uses the
  cumulative-period and cross-page table verifier, otherwise the v1 verifier.
- veto: the model answers directly; code keeps that answer and vetoes only items whose own cited operands
  show a revenue-scope, growth-rate, currency, visibility or missing-operand defect (benchmarks.guidance_veto).

Existing runners keep their fixed extract behaviour; this switch selects the mode for runners built on it.
"""

import os

from benchmarks import guidance_arithmetic as bench
from benchmarks import guidance_veto

ENV = "GUIDANCE_HARNESS"
DEFAULT = "extract"
# Which model call each mode consumes: the extraction request or the direct-answer request.
CALLS = {"extract": "extract", "veto": "astra"}
MODES = tuple(CALLS)


def configured_mode(value=None):
    mode = (value or os.getenv(ENV) or DEFAULT).strip().lower()
    if mode not in CALLS:
        raise ValueError(f"{ENV} must be one of: {', '.join(MODES)}")
    return mode


def answer(mode, case, blocks, reply, vintages=None):
    """Return {"answers", "figures", "errors", "reason", ...} for one model reply under `mode`."""
    mode = configured_mode(mode)
    if mode == "veto":
        result = guidance_veto.apply(case, blocks, reply)
        return result | {"errors": dict(result["vetoed_items"])}
    extraction = bench.Extraction.model_validate(reply)
    if vintages is None:
        answers, errors = bench.harness_answers(case, blocks, extraction)
        return {"answers": answers, "errors": errors, "figures": extraction.model_dump(mode="json")["figures"],
                "reason": " ".join(f"{key} {value}" for key, value in errors.items()) or None}
    from benchmarks import guidance_tables
    result = guidance_tables.revised(case, blocks, extraction, vintages)
    return result | {"reason": " ".join(f"{key} {value}" for key, value in result["errors"].items()) or None}
