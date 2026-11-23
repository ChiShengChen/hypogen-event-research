"""Evidence and public tests for hypotheses about linked business changes."""

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from .schema import DetailedAnswer, Hypotheses, Nonempty, Schema


class LinkedBusinessHypothesis(Schema):
    linked_stance: Literal["bull", "bear"]
    scope: Literal["internal", "counterparty"]
    origin_business: Nonempty
    origin_evidence_ids: list[Nonempty] = Field(min_length=1, max_length=3)
    affected_company: Nonempty
    affected_business: Nonempty
    affected_evidence_ids: list[Nonempty] = Field(min_length=1, max_length=3)
    mechanism: Nonempty
    baseline: Nonempty
    condition: Nonempty
    financial_effect: Nonempty
    alternative_explanation: Nonempty
    metric: Nonempty
    observation_period: Nonempty
    public_source: Nonempty
    deadline: date
    prediction: Nonempty
    invalidation: Nonempty


class LinkageFindings(Schema):
    business_linkages: list[LinkedBusinessHypothesis] = Field(max_length=3)
    business_linkage_gap: Nonempty | None


class LinkedHypotheses(Hypotheses, LinkageFindings):
    pass


class LinkedAnswer(DetailedAnswer, LinkageFindings):
    pass


class RankedBusinessHypothesis(LinkedBusinessHypothesis):
    ranking_reason: Nonempty


class RankedHypotheses(LinkedHypotheses):
    business_linkages: list[RankedBusinessHypothesis] = Field(max_length=3)


class RankedAnswer(LinkedAnswer):
    business_linkages: list[RankedBusinessHypothesis] = Field(max_length=3)


def linkage_refs(path):
    return set(path["origin_evidence_ids"]) | set(path["affected_evidence_ids"])


def linkage_fields(report):
    if "business_linkages" in report:
        return {"business_linkages": report["business_linkages"],
                "business_linkage_gap": report.get("business_linkage_gap")}
    return {}


def merged_linkages(report, paths, gap, key):
    distinct = {}
    for path in [*paths, *report.get("business_linkages", [])]:
        identity = tuple(key(path[field]) for field in ("origin_business", "affected_company", "affected_business", "metric"))
        distinct.setdefault(identity, path)
    return {"business_linkages": list(distinct.values())[:3],
            "business_linkage_gap": gap or report.get("business_linkage_gap")}


class BusinessLinkageGeneration:
    prompt_version = 10
    supports_business_linkages = True
    hypothesis_schema = LinkedHypotheses
    hypothesis_extension = (
        "\nIn the same report generate up to three additional second-order business hypotheses in business_linkages. "
        "Look beyond the event's named operating line into another distinct business, product, channel, project, "
        "or an evidenced counterparty business. Analyze internal trade-offs (shared capex, people, capacity, "
        "distribution, customer mix or pricing) and documented external transmission. Prioritize the most "
        "decision-relevant supported links. An unrelated segment's disclosed guidance is not a transmission. "
        "Budget becoming available does not establish its destination. A shared customer or technology does not "
        "prove order transfer. Use internal for a different part of the research target and counterparty for "
        "a different company. Use the exact published business or product name for origin_business and "
        "affected_business, copied from their respective cited evidence quotes. Cite evidence for both ends. "
        "For a counterparty, its name must also be in the affected evidence. "
        "Keep the anchor facts and your conditional inference distinct: mechanism traces event, changed "
        "operating variable or decision, then the affected business. Name what must happen in condition and "
        "compare with an explicit no-change or disclosed baseline. Identify the revenue, margin, cash-flow, "
        "or invested-capital effect for the affected business and its direction, with a supported sensitivity "
        "or an explicit missing input. Do not assign numbers that are not grounded. Link each path to the "
        "main bull or bear thesis only if it would materially change the researcher's judgment. "
        "Give an alternative explanation that could move the same outcome and the public observation that "
        "would separate it. Supply a metric, measured period, actual public source to watch, analyst "
        "review deadline in ISO date format within the horizon, directional prediction and matching falsifier. "
        "A review deadline is not a promised publication date. A disclosure can support a proxy without "
        "establishing a specific customer's volumes. Do not make silence disconfirm the claim. "
        "Write in concise Traditional Chinese. If no supported named link with a feasible public test "
        "exists, return an empty list and tell the analyst what specific evidence is missing. "
        "Supply business_linkage_gap for important unresolved links even when another path survives."
    )


class RankedBusinessLinkageGeneration(BusinessLinkageGeneration):
    prompt_version = 11
    hypothesis_schema = RankedHypotheses
    answer_schema = RankedAnswer
    ranking_instruction = (
        " Before selecting linkages, identify explicit contract or spending commitments, named operational "
        "arrangements, documented resource transfers, and changes in distribution or customer access. "
        "Trace each from the event into the affected business and compare these candidates before drafting. "
        "Put the primary financially consequential transmission first. Rank by support at both endpoints, "
        "plausible scale at the affected business, likelihood of the needed conditions, and ability of a "
        "public observation to distinguish a competing explanation. A specific disclosed commitment or "
        "operating arrangement with a direct financial consequence normally ranks ahead of a generic "
        "synergy, proxy, or indirect secondary effect. Distinguish the committed amount or capacity from "
        "realized revenue, profit or cash. When scale is unknown, name the missing volume, price, duration, "
        "or deployment and allocation input that would size it. Keep up to three distinct links in descending "
        "order. For each give one concise Traditional Chinese sentence in ranking_reason explaining its "
        "selection and relative priority. Apply the same evidence and abstention criteria to every candidate."
    )
    hypothesis_extension = BusinessLinkageGeneration.hypothesis_extension + ranking_instruction


def validate_linkages(generated, report, evidence, key, *, note_missing=True):
    cutoff = datetime.fromisoformat(report["as_of"])
    try:
        horizon = date.fromisoformat(report["horizon"])
    except ValueError:
        horizon = None
    sources = {ref: row["quote"] for ref, row in evidence.items()
               if row["kind"] == "disclosure" and not row["synthetic"]
               and max(datetime.fromisoformat(row[field]) for field in ("published_at", "obtained_at")) <= cutoff}
    target = key(report["target"])
    accepted, seen = [], set()
    rejected = 0
    for path in generated.business_linkages:
        origin_refs = set(path.origin_evidence_ids)
        affected_refs = set(path.affected_evidence_ids)
        company = key(path.affected_company)
        origin, affected = key(path.origin_business), key(path.affected_business)
        dedupe = (origin, company, affected, key(path.metric))
        if (
            not all((origin, affected, company)) or origin == affected or dedupe in seen
            or (origin_refs | affected_refs) - sources.keys()
            or not any(origin in key(sources[ref]) for ref in origin_refs)
            or not any(affected in key(sources[ref]) for ref in affected_refs)
            or (company == target) != (path.scope == "internal")
            or (path.scope == "counterparty" and not any(company in key(sources[ref]) for ref in affected_refs))
            or path.deadline < cutoff.date() or (horizon is not None and path.deadline > horizon)
            or key(path.prediction) == key(path.invalidation)
        ):
            rejected += 1
            continue
        seen.add(dedupe)
        accepted.append(path.model_dump(mode="json"))
    gap = generated.business_linkage_gap
    if rejected:
        notice = f"{rejected} 條候選未通過業務名稱、時點引文或查核條件核對。"
        gap = f"{notice} {gap}" if gap else notice
    if not accepted and not gap and note_missing:
        gap = "需要同時支持起點與受影響業務的點時披露，以及可區分該機制的公開指標。"
    return accepted, gap
