"""Prepare an evidence-linked revision memo from a saved financial model."""

from datetime import date, datetime
from decimal import Decimal, localcontext
from hashlib import sha256

from .earnings import EarningsError, numbers_json, operating_numbers
from .schema import EarningsPlan
from .store import encode


def decimal(value):
    return Decimal(str(value))


def quarter_at(earnings, period):
    return next((row for row in earnings["quarters"] if row["period_end"] == period), None)


def base(row):
    return row.get("scenarios", {}).get("base", {}).get("revised") if row else None


def assumptions(earnings, period, *, baseline=False):
    plan = EarningsPlan.model_validate(earnings["inputs"])
    quarter = next(row for row in plan.quarters if row.period_end.isoformat() == period)
    profile = None if baseline else next((row for row in plan.eps_assumptions
                                          if row.period_end.isoformat() == period), None)
    if not profile:
        return {"tax_rate": str(quarter.tax_rate), "pre_tax_other": "0", "after_tax_other": str(quarter.other_after_tax),
                "shares": str(quarter.diluted_shares), "loss_tax_benefit": True}
    pretax = profile.recurring_nonoperating.value
    after_tax = Decimal(0)
    for item in profile.one_offs:
        if item.treatment == "pretax_nonoperating":
            pretax += item.value
        else:
            after_tax -= item.value
    return {"tax_rate": str(profile.tax_rate.value), "pre_tax_other": str(pretax), "after_tax_other": str(after_tax),
            "shares": str(profile.diluted_shares.value), "loss_tax_benefit": profile.recognize_loss_tax_benefit}


def model_projection(earnings, period, current, total):
    plan = EarningsPlan.model_validate(earnings["inputs"])
    quarter = next(row for row in plan.quarters if row.period_end.isoformat() == period)
    profile = next((row for row in plan.eps_assumptions if row.period_end == quarter.period_end), None)
    # Guidance verifies a consolidated total. A segment allocation requires a separate analyst assumption.
    hypothetical = quarter.model_copy(update={"segment_revenue": {"consolidated": decimal(total)},
                                               "gross_margin": decimal(current["gross_margin"]),
                                               "opex": decimal(current["opex"])})
    with localcontext() as ctx:
        ctx.prec = 50
        return numbers_json(operating_numbers(hypothetical, profile=profile))


def comparisons(report, period):
    plan = report["earnings"]["inputs"]
    event = datetime.fromisoformat(plan["event_at"])
    cutoff = datetime.fromisoformat(report["as_of"])
    rows = {}
    refs = [*(('before', row) for row in plan["references"]), *(('event', row) for row in plan["event_values"])]
    for phase, row in sorted(refs, key=lambda item: datetime.fromisoformat(item[1]["available_at"])):
        key = row["key"]
        if (key["period_end"], key["duration"], key["scope"], key["basis"], key["currency"]) != (
            period, "quarter", "consolidated", plan["basis"], plan["currency"]
        ):
            continue
        instant = datetime.fromisoformat(row["available_at"])
        if (phase == "before" and instant < event) or (phase == "event" and event <= instant <= cutoff):
            group = (phase, row["kind"], row.get("provider"), key["metric"])
            previous = rows.get(group)
            if previous and datetime.fromisoformat(previous["available_at"]) == instant:
                if (previous["low"], previous["high"]) != (row["low"], row["high"]):
                    rows[group] = {**row, "phase": phase, "conflict": True}
                continue
            rows[group] = {**row, "phase": phase, "conflict": False}
    return list(rows.values())


def main_transmission(report, period, evidence):
    eligible = {entry["id"] for entry in evidence if entry["kind"] == "disclosure" and not entry["synthetic"]
                and entry.get("availability_basis") != "vendor_point_in_time"}
    guidance = (report.get("earnings") or {}).get("driver_audit", [])
    ranked = []
    for order, path in enumerate(report.get("business_linkages", [])):
        refs = set(path["origin_evidence_ids"] + path["affected_evidence_ids"])
        if (not refs or not refs <= eligible or not path.get("alternative_explanation") or not path.get("invalidation")
                or not path.get("public_source")):
            continue
        effects = []
        for link in guidance:
            if link["scenario"] != "base" or not link.get("source_overlap") or not any(
                item["affected_company"] == path["affected_company"] and item["affected_business"] == path["affected_business"]
                for item in link.get("related_business_linkages", [])
            ):
                continue
            effects.extend({**effect, "driver_id": link["id"], "origin": link["origin"]}
                           for effect in link["effects"] if effect["period_end"] == period)
        magnitude = abs(sum((decimal(effect["operating_income"]) for effect in effects), Decimal(0)))
        ranked.append((bool(effects), magnitude, -order, {
            **path, "evidence_ids": sorted(refs), "base_effects": effects, "classification": "research_inference",
            "selection": "同季基準情境的已連結營業利益影響" if effects else "原稿排序與兩端證據",
        }))
    return max(ranked, key=lambda item: item[:3])[-1] if ranked else None


def archived_context(report, period, request):
    from mcp.server.fastmcp.exceptions import ToolError

    from .mcp_guidance import ROOT, check_archive, read
    from .research import company_key

    archive, case_id = request["archive"], request["case_id"]
    archived = read(ROOT / "docs" / archive / "cases.json").get(case_id)
    if not archived:
        raise EarningsError("找不到封存的跨頁案例。")
    case = archived["case"]
    cutoff = datetime.fromisoformat(report["as_of"])
    event_at = datetime.fromisoformat(report["earnings"]["inputs"]["event_at"])
    archive_at = datetime.fromisoformat(case["event_at"])
    ytd = [row for row in archived["vintages"].values() if row["quarter"] == 3]
    if (company_key(report["target"]) not in {company_key(case[key]) for key in ("ticker", "issuer")}
            or datetime.fromisoformat(case["as_of"]) > cutoff
            or archive_at.date() != event_at.astimezone(archive_at.tzinfo).date()
            or report["earnings"]["inputs"]["currency"] != case["currency"]
            or report["earnings"]["inputs"]["basis"] != "US_GAAP" or len(ytd) != 1
            or not 77 <= (date.fromisoformat(period) - date.fromisoformat(ytd[0]["report_end"])).days <= 107):
        raise EarningsError("跨頁封存案須與報告的發行人、事件、點時可得性及下一財季相符。")
    try:
        result = check_archive(archive, case_id, "extract")
    except ToolError as exc:
        raise EarningsError(str(exc)) from exc
    return {**result, "period_label": case["labels"]["remainder"], "scope": "derived_midpoints_only"}


def build_memo(report, older, period_end, preview=None, cross_page=None):
    earnings = report.get("earnings") or {}
    if not earnings.get("quarters"):
        raise EarningsError("此報告版本缺少盈利計畫，請用帶有現估與財務基準的報告版本。")
    period = period_end or earnings["quarters"][0]["period_end"]
    current_row = quarter_at(earnings, period)
    current = base(current_row)
    if current is None:
        raise EarningsError("指定季度缺少已保存的基準情境。")
    older_earnings = older.get("earnings") if older else earnings
    if older and (not older_earnings or any(older_earnings["inputs"][key] != earnings["inputs"][key]
                                            for key in ("basis", "currency"))):
        raise EarningsError("母版和現版的會計口徑、幣別或模型不相容。")
    before = base(quarter_at(older_earnings, period)) if older else current_row["baseline"]
    if before is None:
        raise EarningsError("母版缺少同季基準情境。")
    cross_page = archived_context(report, period, cross_page) if cross_page else None
    audit = preview["audit"] if preview else None
    proposed = None
    if audit and audit["status"] in {"eligible", "noop"}:
        proposed = model_projection(earnings, period, current, audit["revised"]) if audit["status"] == "eligible" else current
    seen = comparisons(report, period)
    source_evidence = [row for row in report["evidence"] if not row.get("synthetic", False)]
    main = main_transmission(report, period, source_evidence)
    quotes = {row["id"]: row for row in source_evidence}
    if older:
        quotes.update({row["id"]: row for row in older["evidence"] if row["id"] not in quotes and not row["synthetic"]})
    if audit:
        quotes.update({row["id"]: row for row in audit.get("citations", [])})
    gaps = []
    for kind, name in (("internal", "事件前內部營收預估"), ("consensus", "事件前點時市場營收共識"),
                       ("issuer_guidance", "舊營收指引")):
        if not any(row["phase"] == "before" and row["kind"] == kind and row["key"]["metric"] == "revenue"
                   and not row["conflict"] for row in seen):
            gaps.append(f"缺少{name}。")
    if not main:
        gaps.append(report.get("business_linkage_gap") or "缺少具備兩端引文、替代解釋與公開反證的主要財務傳導。")
    if not audit:
        gaps.append("尚未以原文驗證新指引是否有剩餘調整。")
    elif audit["status"] not in {"eligible", "noop"}:
        gaps.append(audit["reason"])
    vals = earnings.get("valuation")
    return {
        "schema_version": 1, "report_id": report["report_id"], "report_revision": report["revision"],
        "prior_revision": older["revision"] if older else None, "issuer": report["target"],
        "event": report["event_text"], "event_at": earnings["inputs"]["event_at"], "as_of": report["as_of"],
        "period_end": period, "currency": earnings["inputs"]["currency"], "basis": earnings["inputs"]["basis"],
        "prior_label": "母版基準情境" if older else "原財務模型基準", "observed": seen,
        "primary_transmission": main, "guidance_audit": audit, "gaps": gaps,
        "archived_cross_page": cross_page,
        "model": {"prior": before, "current": current, "proposed": proposed,
                  "prior_assumptions": assumptions(older_earnings, period, baseline=older is None),
                  "current_assumptions": assumptions(earnings, period),
                  "calibration": [row for row in earnings.get("guidance_calibration", []) if row["period_end"] == period],
                  "unlinked_inputs": [row for row in earnings.get("unlinked_driver_inputs", []) if row["period_end"] == period],
                  "inputs": [row for row in earnings["inputs"]["drivers"] if row["period_end"] == period],
                  "driver_audit": [{**row, "effects": effects} for row in earnings.get("driver_audit", [])
                                   if (effects := [effect for effect in row["effects"] if effect["period_end"] == period])]},
        "valuation": vals, "prior_valuation": older_earnings.get("valuation") if older else None,
        "trade_opportunities": report["assessment"].get("trade_opportunities", []),
        "trade_opportunities_gap": report["assessment"].get("trade_opportunities_gap"),
        "evidence": list(quotes.values()),
    }


def fingerprint(value):
    return sha256(encode(value).encode()).hexdigest()
