"""Evidence-backed conditional research cases for an event."""

from datetime import date, datetime
import re
from typing import Literal

from pydantic import Field

from .business_linkage import RankedBusinessLinkageGeneration, RankedHypotheses
from .schema import Nonempty, Schema

Stance = Literal["bull", "base", "bear", "wait"]
STANCE_LABELS = {"bull": "多方", "base": "基準", "bear": "空方", "wait": "觀望"}
DIRECTIONS = {"up": "增加", "down": "減少", "flat": "持平", "unknown": "待查"}


class ScenarioCase(Schema):
    title: Nonempty
    driver: Nonempty
    conditions: list[Nonempty] = Field(min_length=1, max_length=3)
    mechanism: Nonempty
    financial_metric: Nonempty
    direction: Literal["up", "down", "flat", "unknown"]
    scale_basis_or_gap: Nonempty
    baseline: Nonempty
    public_metric: Nonempty
    public_source: Nonempty
    observation_period: Nonempty
    review_by: date
    prediction: Nonempty
    falsifier: Nonempty
    evidence_ids: list[Nonempty] = Field(min_length=1, max_length=4)


class StanceCases(Schema):
    stance: Stance
    cases: list[ScenarioCase] = Field(max_length=2)
    evidence_gap: Nonempty | None


class ScenarioHypotheses(RankedHypotheses):
    stance_cases: list[StanceCases] = Field(max_length=4)


class ScenarioResearchGeneration(RankedBusinessLinkageGeneration):
    prompt_version = 12
    hypothesis_schema = ScenarioHypotheses
    supports_stance_cases = True
    hypothesis_extension = RankedBusinessLinkageGeneration.hypothesis_extension + (
        "\nAlso generate the stance_cases research section in the same response. Use four stances: bull, "
        "base, bear and wait. Each stance may have up to two conditional cases with different operating "
        "drivers or activation conditions. Across the section prioritize independent mechanisms, distinguish "
        "how the actual evidence changes the no-event or disclosed baseline, and write in Traditional Chinese. "
        "For the base stance use continuity or a disclosed baseline. For wait, identify the missing public "
        "release and explain how its outcomes would resolve an uncertainty. Give each viable case a specific "
        "financial measure and direction, a cited scale basis or missing input, and a same-scope public metric, "
        "source, period, analyst review date, prediction, and contrary observed outcome. Missing disclosure "
        "is not a falsifier. Keep all cases conditional, without invented estimates or probabilities. "
        "Use supplied point-in-time disclosure evidence IDs. If evidence for a stance is insufficient, "
        "leave its cases empty and state the most relevant gap. Do not invent an extra case to fill a quota."
    )


def scenario_fields(report):
    return {"stance_cases": report["stance_cases"]} if "stance_cases" in report else {}


def _horizon_end(value):
    try:
        return date.fromisoformat(value)
    except ValueError:
        years = re.findall(r"(?<![0-9])[12][0-9]{3}(?![0-9])", value)
        return date(int(years[0]), 12, 31) if len(years) == 1 else None


def case_supported(case, report, eligible, key):
    cutoff = datetime.fromisoformat(report["as_of"]).date()
    end = _horizon_end(report["horizon"])
    return (set(case.evidence_ids) <= eligible and bool(key(case.mechanism))
            and case.review_by >= cutoff and (end is None or case.review_by <= end)
            and key(case.prediction) != key(case.falsifier))


def verify_stance_cases(draft, report, evidence, key):
    eligible = {row["id"] for row in evidence if row["kind"] == "disclosure" and not row["synthetic"]}
    by_stance = {stance: {"stance": stance, "cases": [], "evidence_gap": None} for stance in STANCE_LABELS}
    mechanisms, rejected = set(), set()
    for bucket in draft.stance_cases:
        target = by_stance[bucket.stance]
        target["evidence_gap"] = target["evidence_gap"] or bucket.evidence_gap
        for case in bucket.cases:
            mechanism = key(case.mechanism)
            if (not case_supported(case, report, eligible, key) or mechanism in mechanisms
                    or len(target["cases"]) >= 2):
                rejected.add(bucket.stance)
                continue
            mechanisms.add(mechanism)
            target["cases"].append(case.model_dump(mode="json"))
    for stance, target in by_stance.items():
        if not target["cases"] and not target["evidence_gap"]:
            target["evidence_gap"] = (
                "需核對該立場的點時引文、因果機制與同口徑查核條件。" if stance in rejected else
                "待補可公開查核的營運條件或財務依據。"
            )
    return list(by_stance.values())


def scenario_lines(report, cite):
    if "stance_cases" not in report:
        return []
    lines = ["## 多立場情境與劇本", ""]
    for group in report["stance_cases"]:
        lines.extend([f"### {STANCE_LABELS[group['stance']]}", ""])
        for case in group["cases"]:
            refs = "、".join(cite(ref) for ref in case["evidence_ids"])
            lines.extend([
                f"**{case['title']}**", "",
                f"- 驅動因素與條件　{case['driver']}。{'、'.join(case['conditions'])}",
                f"- 傳導機制　{case['mechanism']}",
                f"- 財務影響　{case['financial_metric']}{DIRECTIONS[case['direction']]}。{case['scale_basis_or_gap']}",
                f"- 比較基準　{case['baseline']}",
                f"- 查核　{case['public_source']}，{case['observation_period']}的{case['public_metric']}。覆核日 {case['review_by']}。",
                f"- 可驗證預測　{case['prediction']}",
                f"- 推翻條件　{case['falsifier']}",
                f"- 點時引文　{refs}", "",
            ])
        if group["evidence_gap"]:
            lines.extend([f"**待查**　{group['evidence_gap']}", ""])
    return lines
