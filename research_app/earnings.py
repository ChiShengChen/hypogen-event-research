"""Point-in-time earnings revisions, scenario valuation, and forecast resolution."""
from calendar import monthrange
from collections import Counter
from decimal import Decimal, localcontext
from datetime import datetime
import re

from .discovery import source_key
from .revenue import RESIDUAL_METHODS, bridge_forecast, residual_persistence

from .schema import DriverDraft, DriverImpact, EarningsPlan, EstimateDriver, HypothesisDriverLink

SCENARIOS = ("bear", "base", "bull")
METRICS = {"revenue": "營收", "gross_margin": "毛利率", "operating_income": "營業利益", "eps": "稀釋 EPS"}
EPS_INPUTS = {"tax_rate": "常態有效稅率", "diluted_shares": "稀釋股數", "recurring_nonoperating": "經常性營業外損益"}
REVENUE_METHODS = {"latest_run_rate": "最近單季營收", "seasonal_prior": "去年同季營收",
                   "guided_seasonal": "指引中點乘歷史季節比率", "guided_absolute": "指引中點加歷史季節差額",
                   "year_on_year": "以最新年增率調整去年同季", "confirmed_turn": "雙訊號轉折調整",
                   "residual_a": "季節偏離延續修正", "residual_b": "季節與分部收入增量修正"}


class EarningsError(ValueError):
    pass


def available_evidence(refs, visible, cutoff, *, after=None):
    for ref in refs:
        row = visible.get(ref)
        if not row or row["synthetic"] or row["kind"] != "disclosure":
            raise EarningsError(f"預測輸入缺少真實可見來源：{ref}")
        published = datetime.fromisoformat(row["published_at"])
        observed = datetime.fromisoformat(row["obtained_at"])
        if observed > cutoff or (after is not None and published < after):
            raise EarningsError(f"來源與基準或事件時點不符：{ref}")


def validate_plan(plan, as_of, evidence):
    if plan.event_at > as_of:
        raise EarningsError("事件時點不可晚於研究截止時點")
    visible = {row["id"]: row for row in evidence}
    for record in [*plan.references, *plan.quarters]:
        if record.available_at >= plan.event_at:
            raise EarningsError("事件前基準必須早於事件")
        available_evidence(record.evidence_ids, visible, record.available_at)
    for record in plan.event_values:
        if not plan.event_at <= record.available_at <= as_of:
            raise EarningsError("事件數字必須於事件至研究截止時點之間可得")
        available_evidence(record.evidence_ids, visible, record.available_at, after=plan.event_at)
    for quarter in plan.quarters:
        if quarter.period_end < plan.event_at.date():
            raise EarningsError("預測季度不得在事件前已結束")
    for profile in plan.eps_assumptions:
        items = [*(getattr(profile, key) for key in EPS_INPUTS), *profile.one_offs]
        for item in items:
            if item.available_at > as_of:
                raise EarningsError("EPS 假設可得時間晚於研究截止時點")
            available_evidence(item.evidence_ids, visible, item.available_at)
    if bridge := plan.revenue_bridge:
        near, far = sorted(plan.quarters, key=lambda row: row.period_end)
        if (bridge.currency, bridge.basis) != (plan.currency, plan.basis):
            raise EarningsError("第二預測季營收橋接的幣別或會計口徑不符")
        if any(item.period_end >= near.period_end or item.period_end > item.available_at.date() for item in bridge.history):
            raise EarningsError("營收歷史必須早於首個預測季")
        for item in [*bridge.history, *bridge.adjustments, *bridge.operating_signals, *bridge.residual_inputs]:
            if item.available_at > as_of:
                raise EarningsError("營收橋接來源晚於研究截止時點")
            available_evidence(item.evidence_ids, visible, item.available_at)
        if any(item.segment not in far.segment_revenue for item in [*bridge.adjustments, *bridge.residual_inputs]):
            raise EarningsError("營收橋接調整對應不到財務分部")
        recognition = {item.segment for item in [*bridge.adjustments, *bridge.residual_inputs] if item.driver == "recognition"}
        if any(shift and shift.segment in recognition and far.period_end in {shift.from_period, shift.to_period}
               for shift in (link.recognition_shift for link in plan.driver_links)):
            raise EarningsError("營收橋接與跨季認列連結可能重複計入")
        if bridge.method == "residual_b" and any(
            driver.period_end == far.period_end and driver.shipment_changes.keys() & recognition
            for driver in plan.drivers
        ):
            raise EarningsError("T+2 分部認列增量和既有台數調整可能重複計入")
    if valuation := plan.valuation:
        ref = valuation.annual_base_eps
        key = ref.key
        if (
            key.metric != "eps" or key.duration != "year" or key.scope != "consolidated"
            or key.basis != plan.basis or key.currency != plan.currency
            or key.period_end != valuation.fiscal_year_end or ref.low != ref.high
            or ref.low <= 0 or ref.available_at >= plan.event_at or ref.kind == "reported_actual"
        ):
            raise EarningsError("本益比估值須使用事件前同口徑、正值且為單點的年度 EPS 預估")
        available_evidence(ref.evidence_ids, visible, ref.available_at)
        if valuation.price_at:
            if valuation.price_at > as_of:
                raise EarningsError("估值使用的股價晚於研究截止時點")
            available_evidence([valuation.price_evidence_id], visible, valuation.price_at)
    for driver in plan.drivers:
        available_evidence(driver.evidence_ids, visible, as_of)
    quarters = {row.period_end: row for row in plan.quarters}
    shipment_slots = {(row.period_end, row.scenario, segment) for row in plan.drivers
                      for segment, shipment in row.shipment_changes.items() if shipment.incremental_recognized_units}
    for link in plan.driver_links:
        available_evidence(link.evidence_ids, visible, as_of)
        for period, _, segment, _ in link_impacts(link):
            if period not in quarters or (segment and segment not in quarters[period].segment_revenue):
                raise EarningsError(f"假說連結使用了不存在的季度或分部：{link.id}")
            if link.recognition_shift:
                slot = (period, link.scenario, segment)
                if slot in shipment_slots:
                    raise EarningsError(f"跨季認列與其他台數調整重疊：{link.id}")
                shipment_slots.add(slot)
    return visible


def operating_numbers(quarter, driver=None, profile=None):
    segments = quarter.segment_revenue.copy()
    margin, opex = quarter.gross_margin, quarter.opex
    if driver:
        if (set(driver.segment_revenue_delta) | set(driver.shipment_changes)) - segments.keys():
            raise EarningsError("預測調整使用了不存在的營收分部")
        for segment, amount in driver.segment_revenue_delta.items():
            segments[segment] += amount
        for segment, change in driver.shipment_changes.items():
            segments[segment] += change.incremental_recognized_units * change.revenue_per_unit
        margin += driver.gross_margin_delta
        opex += driver.opex_delta
    revenue = sum(segments.values(), Decimal(0))
    if any(value < 0 for value in segments.values()) or margin > 1 or opex < 0:
        raise EarningsError("重算後的分部營收、毛利率或營業費用超出可用範圍")
    gross_profit = revenue * margin
    operating_income = gross_profit - opex
    if profile is None:
        net_income = operating_income * (1 - quarter.tax_rate) + quarter.other_after_tax
        shares = quarter.diluted_shares
    else:
        pretax = operating_income + profile.recurring_nonoperating.value
        discrete_tax = Decimal(0)
        for item in profile.one_offs:
            if item.treatment == "pretax_nonoperating":
                pretax += item.value
            else:
                discrete_tax += item.value
        tax_base = pretax if profile.recognize_loss_tax_benefit else max(pretax, Decimal(0))
        net_income = pretax - tax_base * profile.tax_rate.value - discrete_tax
        shares = profile.diluted_shares.value
    return {
        "segment_revenue": segments, "revenue": revenue, "gross_margin": margin,
        "gross_profit": gross_profit, "opex": opex, "operating_income": operating_income,
        "net_income": net_income, "eps": net_income / shares,
    }


def issuer_guidance(plan):
    """Select comparable quarter-level issuer points or ranges, with an unambiguous latest vintage."""
    eligible = {}
    periods = {quarter.period_end for quarter in plan.quarters}
    for row in [*plan.references, *plan.event_values]:
        key = row.key
        if (
            row.kind != "issuer_guidance" or key.period_end not in periods
            or key.metric not in {"revenue", "gross_margin"} or key.duration != "quarter"
            or key.scope != "consolidated" or (key.currency, key.basis) != (plan.currency, plan.basis)
            or (key.metric == "revenue" and row.low < 0) or (key.metric == "gross_margin" and row.high > 1)
        ):
            continue
        eligible.setdefault((key.period_end, key.metric), []).append(row)
    result = {}
    for key, rows in eligible.items():
        latest = max(row.available_at for row in rows)
        current = [row for row in rows if row.available_at == latest]
        if len({(row.low, row.high) for row in current}) == 1:
            result[key] = current[0]
    return result


def calibrate_drivers(quarter, drivers, guidance):
    base = drivers.get("base")
    if base is None:
        return drivers, []
    forecasts = {scenario: operating_numbers(quarter, driver) for scenario, driver in drivers.items()}
    changes, audit = {}, []
    for metric in ("revenue", "gross_margin"):
        reference = guidance.get((quarter.period_end, metric))
        if reference is None:
            continue
        prior = forecasts["base"][metric]
        midpoint = (reference.low + reference.high) / 2
        if metric == "revenue" and not prior and midpoint:
            continue
        if metric == "gross_margin" and max(row[metric] for row in forecasts.values()) + midpoint - prior > 1:
            continue
        changes[metric] = midpoint / prior if metric == "revenue" and prior else midpoint - prior
        audit.append({"period_end": quarter.period_end.isoformat(), "metric": metric, "draft_base": format(prior, "f"),
                      "calibrated_base": format(midpoint, "f"), "reference": reference.model_dump(mode="json")})
    calibrated = {}
    for scenario, driver in drivers.items():
        update = {}
        if "revenue" in changes and forecasts["base"]["revenue"]:
            deltas = driver.segment_revenue_delta.copy()
            for segment, amount in forecasts[scenario]["segment_revenue"].items():
                deltas[segment] = deltas.get(segment, Decimal(0)) + amount * (changes["revenue"] - 1)
            update["segment_revenue_delta"] = deltas
        if "gross_margin" in changes:
            update["gross_margin_delta"] = driver.gross_margin_delta + changes["gross_margin"]
        calibrated[scenario] = driver.model_copy(update=update) if update else driver
    return calibrated, audit


def bridge_drivers(quarter, drivers, bridge, guide):
    base = drivers.get("base")
    if base is None:
        return drivers, None
    base_revenue = operating_numbers(quarter, base)["revenue"]
    if base_revenue <= 0:
        raise EarningsError("第二預測季草擬營收須為正值")
    try:
        anchor_total, audit = bridge_forecast(bridge, guide, base_revenue)
    except ValueError as exc:
        raise EarningsError(str(exc)) from exc
    factor = Decimal(audit["anchor"]) / base_revenue
    if factor == 1 and not audit["adjustments"]:
        audit["original_draft"] = format(base_revenue, "f")
        return drivers, audit
    calibrated = {}
    for scenario, driver in drivers.items():
        raw = operating_numbers(quarter, driver)
        deltas = {name: driver.segment_revenue_delta.get(name, Decimal(0)) + value * (factor - 1)
                  for name, value in raw["segment_revenue"].items()}
        for item in audit["adjustments"]:
            deltas[item["segment"]] += Decimal(item["value"])
        calibrated[scenario] = driver.model_copy(update={"segment_revenue_delta": deltas})
    audit["original_draft"] = format(base_revenue, "f")
    audit["before_hypothesis_links"] = format(anchor_total, "f")
    return calibrated, audit


def residual_source_keys(refs, visible):
    keys = set()
    for ref in refs:
        doc = visible[ref]
        keys.add(("document", doc.get("document_id") or ref.split(":", 1)[0]))
        if parsed := source_key(doc.get("source", "")):
            host, path, _ = parsed
            accession = re.match(r"/archives/edgar/data/\d+/(\d{18})(?:/|$)", path, re.IGNORECASE)
            if host == "sec.gov" and accession:
                keys.add(("accession", accession[1]))
            else:
                keys.add(("url", host, path))
    return keys


def residual_components(bridge, visible):
    """Disqualify overlapping increments rather than choosing between their rows."""
    candidates = [row for row in bridge.residual_inputs if row.basis_incremental_to_incumbent]
    keys = {}
    for row in candidates:
        scope = (row.segment.casefold(), row.driver)
        family = " ".join(row.source_family.casefold().split())
        mechanism = " ".join(row.mechanism.casefold().split())
        keys[row.id] = {("mechanism", mechanism), ("family", *scope, family),
                        *(("source", *scope, *source) for source in residual_source_keys(row.evidence_ids, visible))}
    counts = Counter(key for entries in keys.values() for key in entries)
    applied, skipped = [], []
    for row in bridge.residual_inputs:
        if not row.basis_incremental_to_incumbent:
            reason = "未確認為既有預測尚未納入的分部收入。"
        elif any(counts[key] > 1 for key in keys[row.id]):
            reason = "同一機制、來源文件或來源家族的分部驅動重複。"
        else:
            applied.append(row)
            continue
        skipped.append((row, reason))
    return applied, skipped


def apply_earnings_residual(quarter, drivers, factor, items):
    adjusted = {}
    for scenario, driver in drivers.items():
        if factor == 1 and not items:
            adjusted[scenario] = driver
            continue
        raw = operating_numbers(quarter, driver)
        segments = driver.segment_revenue_delta.copy()
        for name, amount in raw["segment_revenue"].items():
            segments[name] = segments.get(name, Decimal(0)) + amount * (factor - 1)
        revenue = raw["revenue"] * factor
        profit = raw["gross_profit"] * factor
        opex_delta = driver.opex_delta
        for item in items:
            segments[item.segment] += item.incremental_revenue
            revenue += item.incremental_revenue
            margin = item.incremental_gross_margin
            profit += item.incremental_revenue * (raw["gross_margin"] if margin is None else margin)
            opex_delta += item.incremental_opex
        if revenue <= 0:
            raise EarningsError("修正後有情境營收不為正值")
        revised = driver.model_copy(update={
            "segment_revenue_delta": segments, "gross_margin_delta": profit / revenue - quarter.gross_margin,
            "opex_delta": opex_delta,
        })
        operating_numbers(quarter, revised)
        adjusted[scenario] = revised
    return adjusted


def residual_drivers(quarter, drivers, bridge, guide, direct_guide, visible, profile):
    base = drivers.get("base")
    if base is None:
        return drivers, None
    baseline = operating_numbers(quarter, base, profile)
    revenue = baseline["revenue"]
    persistence, audit = residual_persistence(bridge, guide, revenue, direct_guide=direct_guide)
    factor = (revenue + persistence) / revenue if persistence else Decimal(1)
    items, skipped = [], []
    blocked = audit["status"] in {"missing_baseline", "issuer_guidance"}
    if bridge.method == "residual_b":
        if blocked:
            skipped = [(row, audit["reason"]) for row in bridge.residual_inputs]
        else:
            items, skipped = residual_components(bridge, visible)
    adjusted = drivers
    try:
        adjusted = apply_earnings_residual(quarter, drivers, factor, items)
    except EarningsError:
        skipped.extend((row, "各情境重算後的分部營收、毛利率或費用超出有效範圍。") for row in items)
        items = []
        try:
            adjusted = apply_earnings_residual(quarter, drivers, factor, items)
        except EarningsError:
            factor, persistence = Decimal(1), Decimal(0)
        audit.update(status="infeasible", reason="至少一個情境的財務數值超出有效範圍，保留有效的原估或延續修正。")
    result = operating_numbers(quarter, adjusted["base"], profile)
    audit["baseline_financials"] = numbers_json(baseline)
    audit["revised_financials"] = numbers_json(result)
    audit["estimate"] = format(result["revenue"], "f")
    audit["delta"] = format(result["revenue"] - revenue, "f")
    if bridge.method == "residual_b":
        audit["segment_input_count"] = len(bridge.residual_inputs)
        audit["segment_applied_count"] = len(items)
        audit["segment_status"] = "applied" if items else "withheld" if bridge.residual_inputs else "missing_evidence"
    if items:
        audit.update(status="applied", reason="採用可核對且未重複的 T+2 分部收入增量。")
    audit["components"] = [{
        "id": "persistence", "kind": "persistence", "status": "applied" if persistence else "skipped",
        "delta": format(persistence, "f"), "evidence_ids": audit["evidence_ids"],
    }]
    for item in items:
        audit["components"].append({**item.model_dump(mode="json"), "period_end": bridge.period_end.isoformat(),
                                    "kind": "segment", "status": "applied", "delta": format(item.incremental_revenue, "f")})
    for item, reason in skipped:
        audit["components"].append({**item.model_dump(mode="json"), "period_end": bridge.period_end.isoformat(),
                                    "kind": "segment", "status": "skipped", "delta": "0", "reason": reason})
    audit["ablation"] = []
    removable = ([("persistence", Decimal(1), items)] if persistence else []) + [
        (item.id, factor, [other for other in items if other.id != item.id]) for item in items
    ]
    for name, kept_factor, kept_items in removable:
        try:
            remaining = apply_earnings_residual(quarter, drivers, kept_factor, kept_items)
            metrics = operating_numbers(quarter, remaining["base"], profile)
        except EarningsError:
            audit["ablation"].append({"id": name, "status": "infeasible", "reason": "單項移除後的財務數值無法重算。"})
        else:
            keys = (*METRICS, "gross_profit", "opex")
            audit["ablation"].append({"id": name, "status": "ok",
                                      "without": numbers_json({key: metrics[key] for key in keys})})
    refs = list(dict.fromkeys([*audit["evidence_ids"], *(ref for row in items for ref in row.evidence_ids)]))
    audit["evidence_ids"] = refs
    return adjusted, {
        "period_end": bridge.period_end.isoformat(), "method": bridge.method,
        "requested_method": bridge.method, "original_draft": audit["baseline"],
        "anchor": format(revenue + persistence, "f"), "anchor_evidence_ids": refs, "alternatives": {},
        "adjustments": [{**row.model_dump(mode="json"), "value": format(row.incremental_revenue, "f"),
                         "method": row.rationale} for row in items],
        "before_hypothesis_links": audit["estimate"], "residual": audit,
    }


def revenue_expectations(plan, quarter, base):
    """Keep the historical forecast distinct from the pre-event market snapshot."""
    if base is None:
        return {}
    period = quarter.period_end
    matches = [item for item in plan.references if item.kind in {"consensus", "internal"} and item.key.metric == "revenue"
               and item.key.period_end == period and item.key.duration == "quarter" and item.key.scope == "consolidated"
               and (item.key.currency, item.key.basis) == (plan.currency, plan.basis)]
    latest, internal = {}, None
    for item in sorted(matches, key=lambda row: row.available_at):
        if item.kind == "internal":
            internal = item
        else:
            latest[item.provider or item.label] = item
    prior = (internal.low + internal.high) / 2 if internal else sum(quarter.segment_revenue.values())
    return {
        "before": format(prior, "f"), "after": format(base, "f"),
        "before_label": "事件前內部預估" if internal else "原財務基準",
        "before_evidence_ids": internal.evidence_ids if internal else quarter.evidence_ids,
        "consensus": [{"reference": row.model_dump(mode="json"),
                       "delta": format(base - (row.low + row.high) / 2, "f")} for row in latest.values()],
    }


def numbers_json(numbers):
    return {key: numbers_json(value) if isinstance(value, dict) else format(value, "f")
            for key, value in numbers.items()}


def comparison_rows(plan):
    results = []
    for event in plan.event_values:
        latest = {}
        for base in sorted(plan.references, key=lambda row: row.available_at):
            if base.key == event.key:
                latest[(base.kind, base.provider)] = base
        for base in latest.values():
            relation = "above" if event.low > base.high else "below" if event.high < base.low else "overlaps"
            results.append({
                "baseline": base.model_dump(mode="json"), "event": event.model_dump(mode="json"),
                "relation": relation,
                "midpoint_delta": format((event.low + event.high - base.low - base.high) / 2, "f"),
            })
    return results


def valuation_rows(plan, quarterly):
    valuation = plan.valuation
    if valuation is None:
        return None
    end = valuation.fiscal_year_end
    previous_year = end.year - 1
    start_boundary = end.replace(year=previous_year, day=min(end.day, monthrange(previous_year, end.month)[1]))
    rows = [row for row in quarterly if start_boundary < row["period_end"] <= end]
    if not rows:
        raise EarningsError("估值年度內缺少預測季度")
    values = {}
    old_eps = valuation.annual_base_eps.low
    old_value = old_eps * valuation.old_multiple
    for scenario, multiple in valuation.scenario_multiples.items():
        if any(scenario not in row["scenarios"] for row in rows):
            continue
        annual_income_change = sum((row["scenarios"][scenario]["delta"]["net_income"] for row in rows), Decimal(0))
        eps_change = annual_income_change / valuation.annual_diluted_shares
        revised = old_eps + eps_change
        entry = {"annual_eps": revised, "eps_delta": eps_change, "multiple": multiple,
                 "annual_net_income_delta": annual_income_change}
        if revised <= 0:
            values[scenario] = {**numbers_json(entry), "status": "nonpositive_eps"}
            continue
        fair = revised * multiple
        entry |= {
            "value": fair, "earnings_effect": eps_change * valuation.old_multiple,
            "multiple_effect": revised * (multiple - valuation.old_multiple), "total_delta": fair - old_value,
        }
        if valuation.market_price is not None:
            entry["upside_fraction"] = fair / valuation.market_price - 1
        values[scenario] = {**numbers_json(entry), "status": "scenario"}
    return {
        "method": "forward_pe", "inputs": valuation.model_dump(mode="json"),
        "prior_value": format(old_value, "f"), "scenarios": values,
    }


def link_impacts(link):
    if shift := link.recognition_shift:
        amount = shift.units * shift.revenue_per_unit
        return [(shift.from_period, "segment_revenue", shift.segment, -amount),
                (shift.to_period, "segment_revenue", shift.segment, amount)]
    return [(row.period_end, row.metric, row.segment, row.delta) for row in link.impacts]


def compile_driver(plan, period, scenario, audit, quarter, driver, profile):
    linked = [(link, [row for row in link_impacts(link) if row[0] == period])
              for link in plan.driver_links if link.scenario == scenario]
    for link, impacts in linked:
        if not impacts:
            continue
        before = operating_numbers(quarter, driver, profile)
        if driver is None:
            driver = EstimateDriver(period_end=period, scenario=scenario, segment_revenue_delta={},
                                    shipment_changes={}, gross_margin_delta=0, opex_delta=0,
                                    rationale=link.assumption, evidence_ids=link.evidence_ids)
        revenue = driver.segment_revenue_delta.copy()
        changes = {"gross_margin": driver.gross_margin_delta, "opex": driver.opex_delta}
        for _, metric, segment, delta in impacts:
            if segment:
                revenue[segment] = revenue.get(segment, Decimal(0)) + delta
            else:
                changes[metric] += delta
        driver = driver.model_copy(update={"segment_revenue_delta": revenue,
                                          "gross_margin_delta": changes["gross_margin"],
                                          "opex_delta": changes["opex"]})
        after = operating_numbers(quarter, driver, profile)
        audit[link.id]["effects"].append({"period_end": period.isoformat(), **numbers_json({
            key: after[key] - before[key] for key in (*METRICS, "net_income")
        })})
    return driver


def link_model_drivers(drivers, hypotheses):
    """Attribute generated bear/bull numeric changes without counting them twice."""
    by_stance = {row["stance"]: row for row in hypotheses}
    links, retained = [], []
    for driver in drivers:
        hypothesis = by_stance.get(driver.scenario)
        if not hypothesis:
            retained.append(driver)
            continue
        impacts = [
            DriverImpact(period_end=driver.period_end, metric="segment_revenue", segment=segment, delta=delta)
            for segment, delta in driver.segment_revenue_delta.items() if delta
        ]
        impacts += [DriverImpact(period_end=driver.period_end, metric=metric, delta=delta)
                    for metric, delta in (("gross_margin", driver.gross_margin_delta), ("opex", driver.opex_delta))
                    if delta]
        if not impacts or len(impacts) > 6:
            retained.append(driver)
            continue
        links.append(HypothesisDriverLink(
            id=f"draft-{driver.period_end}-{driver.scenario}", hypothesis_stance=driver.scenario,
            scenario=driver.scenario, hypothesis_summary=hypothesis["mechanism"], evidence_ids=driver.evidence_ids,
            assumption=driver.rationale, public_check=hypothesis["prediction"], falsifier=hypothesis["invalidation"],
            impacts=impacts, origin="model_draft",
        ))
        retained.append(driver.model_copy(update={"segment_revenue_delta": {}, "gross_margin_delta": Decimal(0),
                                                  "opex_delta": Decimal(0)}))
    return retained, links


def calculate_earnings(plan, as_of, evidence, *, hypotheses=(), claims=()):
    visible = validate_plan(plan, as_of, evidence)
    by_stance = {row["stance"]: row for row in hypotheses}
    refs = {row["id"]: row.get("evidence_id") for row in claims}
    audit = {}
    for link in plan.driver_links:
        if link.hypothesis_stance not in by_stance:
            raise EarningsError(f"找不到連結的假說：{link.id}")
        hypothesis = by_stance[link.hypothesis_stance]
        hypothesis_refs = {refs.get(ref) for ref in hypothesis["claim_ids"]}
        audit[link.id] = {
            **link.model_dump(mode="json"), "source_overlap": sorted(hypothesis_refs.intersection(link.evidence_ids)),
            "hypothesis_prediction": hypothesis["prediction"], "effects": [],
        }
    quarterly, guidance_audit = [], []
    bridge_audit = None
    profiles = {profile.period_end: profile for profile in plan.eps_assumptions}
    eligible_guidance = issuer_guidance(plan) if plan.calibrate_guidance or plan.revenue_bridge else {}
    guidance = eligible_guidance if plan.calibrate_guidance else {}
    near_period = min((quarter.period_end for quarter in plan.quarters), default=None)
    with localcontext() as ctx:
        ctx.prec = 50
        for quarter in sorted(plan.quarters, key=lambda value: value.period_end):
            baseline = operating_numbers(quarter)
            profile = profiles.get(quarter.period_end)
            drivers = {driver.scenario: driver for driver in plan.drivers if driver.period_end == quarter.period_end}
            if guidance:
                drivers, entries = calibrate_drivers(quarter, drivers, guidance)
                guidance_audit.extend(entries)
            bridge = plan.revenue_bridge
            is_bridge_quarter = bridge and quarter.period_end == bridge.period_end
            uses_residual = is_bridge_quarter and bridge.method in RESIDUAL_METHODS
            if is_bridge_quarter and not uses_residual:
                direct_guide = eligible_guidance.get((quarter.period_end, "revenue"))
                if direct_guide is None:
                    drivers, bridge_audit = bridge_drivers(
                        quarter, drivers, bridge, eligible_guidance.get((near_period, "revenue"))
                    )
            compiled = {}
            for scenario in SCENARIOS:
                driver = compile_driver(plan, quarter.period_end, scenario, audit, quarter, drivers.get(scenario), profile)
                if driver is not None:
                    compiled[scenario] = driver
            if uses_residual:
                compiled, bridge_audit = residual_drivers(
                    quarter, compiled, bridge, eligible_guidance.get((near_period, "revenue")),
                    eligible_guidance.get((quarter.period_end, "revenue")), visible, profile,
                )
            scenarios = {}
            for scenario, driver in compiled.items():
                revised = operating_numbers(quarter, driver, profile)
                delta = {key: revised[key] - baseline[key] for key in revised if key != "segment_revenue"}
                delta["segment_revenue"] = {
                    name: revised["segment_revenue"][name] - prior
                    for name, prior in baseline["segment_revenue"].items()
                }
                scenarios[scenario] = {"revised": revised, "delta": delta}
            expectation = revenue_expectations(plan, quarter, scenarios.get("base", {}).get("revised", {}).get("revenue"))
            quarterly.append({"period_end": quarter.period_end, "baseline": baseline, "scenarios": scenarios,
                              "revenue_expectations": expectation})
            if bridge_audit and quarter.period_end.isoformat() == bridge_audit["period_end"]:
                bridge_audit["segment_revenue"] = numbers_json(scenarios["base"]["revised"]["segment_revenue"])
                bridge_audit["after_hypothesis_links"] = format(scenarios["base"]["revised"]["revenue"], "f")
        return {
            "inputs": plan.model_dump(mode="json"),
            "comparisons": comparison_rows(plan),
            "quarters": [
                {"period_end": row["period_end"].isoformat(), "baseline": numbers_json(row["baseline"]),
                 "scenarios": numbers_json(row["scenarios"]),
                 **({"revenue_expectations": row["revenue_expectations"]} if plan.revenue_bridge else {})} for row in quarterly
            ],
            "valuation": valuation_rows(plan, quarterly),
            "driver_audit": list(audit.values()),
            **({"guidance_calibration": guidance_audit} if guidance_audit else {}),
            **({"revenue_bridge": bridge_audit} if bridge_audit else {}),
            "unlinked_driver_inputs": [
                {"period_end": driver.period_end.isoformat(), "scenario": driver.scenario}
                for driver in plan.drivers if any(driver.segment_revenue_delta.values())
                or driver.gross_margin_delta or driver.opex_delta
                or any(change.incremental_recognized_units for change in driver.shipment_changes.values())
            ],
            "gaps": [
                f"缺少 {row['period_end']} {key} 的修正驅動。"
                for row in quarterly for key in SCENARIOS if key not in row["scenarios"]
            ],
        }


def complete_plan(plan, as_of, context, adapter):
    review = {"hypotheses": context.get("hypotheses", ()), "claims": context.get("claims", ())}
    if not plan.generate_drivers:
        return calculate_earnings(plan, as_of, context["evidence"], **review)
    validate_plan(plan, as_of, context["evidence"])
    draft = getattr(adapter, "earnings_drivers", None)
    if draft is None:
        raise EarningsError("此模型模式不支援草擬預測驅動")
    legacy = getattr(adapter, "earnings_driver_version", None) == 3
    excluded = {"revenue_bridge"}
    if legacy:
        excluded.update({"eps_assumptions", "calibrate_guidance"})
    result: DriverDraft = draft({
        "target": context["target"], "event": context["event_text"], "as_of": context["as_of"],
        "evidence": [row for row in context["evidence"] if row["kind"] == "disclosure" and not row["synthetic"]],
        "baseline": plan.model_dump(mode="json", exclude=excluded),
        **({"hypotheses": list(review["hypotheses"])} if review["hypotheses"] else {}),
    })
    expected = {(quarter.period_end, name) for quarter in plan.quarters for name in SCENARIOS}
    if {(driver.period_end, driver.scenario) for driver in result.drivers} != expected:
        raise EarningsError("模型草擬需涵蓋每個季度的空、基準、多情境")
    candidates = [driver.to_driver() for driver in result.drivers]
    candidates, links = link_model_drivers(candidates, review["hypotheses"]) if not plan.driver_links else (candidates, [])
    filled = EarningsPlan.model_validate({
        **plan.model_dump(), "generate_drivers": False,
        "drivers": candidates, "driver_links": [*plan.driver_links, *links],
        "calibrate_guidance": plan.calibrate_guidance if plan.calibrate_guidance is not None else (
            not legacy and bool(issuer_guidance(plan))
        ),
    })
    result = calculate_earnings(filled, as_of, context["evidence"], **review)
    result["driver_origin"] = "model_draft"
    return result


def resolve_forecast(registration, resolution, now):
    disclosure = resolution.document
    if disclosure.published_at <= registration["snapshot_as_of"] or disclosure.obtained_at > now:
        raise EarningsError("核對文件須於原稿截止後公開，且現在已可取得")
    if registration["purpose"] == "live" and disclosure.published_at <= registration["registered_at"]:
        raise EarningsError("實績資料須於正式登記後公開")
    if resolution.status != "reported":
        if now < registration["deadline"] or disclosure.published_at.date() < registration["key"].period_end:
            raise EarningsError("未到截止日或來源早於觀測期末")
        return resolution.status, None
    if resolution.key != registration["key"]:
        raise EarningsError("實績的指標、期別、分部、幣別或會計口徑不一致")
    if disclosure.published_at > registration["deadline"]:
        return "late", None
    hit = registration["low"] <= resolution.value <= registration["high"]
    probability = registration["probability"]
    score = format((probability - int(hit)) ** 2, "f") if probability is not None else None
    return "hit" if hit else "miss", score


def render_earnings(earnings, cite):
    inputs = earnings["inputs"]
    labels = {"bear": "空方", "base": "基準", "bull": "多方"}
    kinds = {"issuer_guidance": "公司指引", "issuer_outlook": "公司長期情境", "consensus": "市場共識",
             "internal": "內部預估", "reported_actual": "實際披露"}
    origin = "模型草擬，待研究員覆核" if earnings.get("driver_origin") == "model_draft" else "研究輸入情境"

    def fmt(raw, kind):
        value = Decimal(raw)
        if kind == "eps":
            return f"{value:,.2f}"
        if kind == "gross_margin":
            return f"{value:.2%}"
        return f"{value / 1_000_000:,.1f}"

    def source_line(row):
        return "、".join(cite(ref) for ref in row["evidence_ids"])

    lines = ["## 事件前比較基準", ""]
    lines.append(f"- 事件時點 {inputs['event_at']}。會計口徑 {inputs['basis']}。金額以各幣別百萬計，EPS 是每股。")
    for reference in inputs["references"]:
        key = reference["key"]
        metric = key["metric"]
        values = f"{fmt(reference['low'], metric)}–{fmt(reference['high'], metric)}"
        lines.append(
            f"- {kinds[reference['kind']]}｜{reference['label']}｜{key['period_end']} "
            f"{key['duration']} {key['scope']} {METRICS[metric]} {values}（{key['basis']} {key['currency']}）"
            f"｜可得日 {reference['available_at']} {source_line(reference)}"
        )
    if not any(row["kind"] == "consensus" for row in inputs["references"]):
        lines.append("- 快照缺少可比較的市場共識。")
    for result in earnings["comparisons"]:
        old, new = result["baseline"], result["event"]
        key = new["key"]
        metric = key["metric"]
        delta = Decimal(result["midpoint_delta"])
        change = f"{delta * 100:+.2f} 個百分點" if metric == "gross_margin" else fmt(delta, metric)
        direction = {"above": "高於", "below": "低於", "overlaps": "區間重疊"}[result["relation"]]
        lines.append(
            f"- {kinds[new['kind']]} {new['label']}｜{sym_metrics(key)}｜"
            f"{fmt(new['low'], metric)}–{fmt(new['high'], metric)} 相較 {kinds[old['kind']]} {direction}，"
            f"中點差 {change}。{source_line(new)}"
        )

    lines += ["", "## 盈利預測修正", "", f"{origin}。金額為百萬 {inputs['currency']}，EPS 為 {inputs['currency']}/股。", ""]
    if not earnings["quarters"]:
        lines += ["缺少可用的事件前季度預估。", ""]
    drivers = {(entry["period_end"], entry["scenario"]): entry for entry in inputs["drivers"]}
    baselines = {quarter["period_end"]: quarter for quarter in inputs["quarters"]}
    profiles = {row["period_end"]: row for row in inputs.get("eps_assumptions", [])}
    for row in earnings["quarters"]:
        period = row["period_end"]
        baseline = baselines[period]
        lines += [
            f"### 截至 {period} 的季度", "",
            f"基準方法 {baseline['method']}。{source_line(baseline)}", "",
            "| 指標 | 舊預估 | 空方新值（差額） | 基準新值（差額） | 多方新值（差額） |",
            "|---|---:|---:|---:|---:|",
        ]
        rows = [(key, label, row["baseline"], None) for key, label in METRICS.items()]
        rows += [(name, name, row["baseline"]["segment_revenue"], "segment_revenue")
                 for name in row["baseline"]["segment_revenue"]]
        for key, label, old, section in rows:
            unit = "revenue" if section else key
            cells = [fmt(old[key], unit)]
            for scenario in SCENARIOS:
                values = row["scenarios"].get(scenario)
                if not values:
                    cells.append("—")
                    continue
                revised = values["revised"][section] if section else values["revised"]
                delta = values["delta"][section] if section else values["delta"]
                difference = fmt(delta[key], unit)
                if unit == "gross_margin":
                    difference = f"{Decimal(delta[key]) * 100:+.2f}pp"
                cells.append(f"{fmt(revised[key], unit)}（{difference}）")
            lines.append(f"| {label} | {' | '.join(cells)} |")
        lines.append("")
        if expectation := row.get("revenue_expectations"):
            prior = fmt(expectation["before"], "revenue")
            revised = fmt(expectation["after"], "revenue")
            prior_refs = "、".join(cite(ref) for ref in expectation["before_evidence_ids"])
            lines.append(f"- {expectation['before_label']} {prior} → 事件後營收基準 {revised}。{prior_refs}")
            for item in expectation["consensus"]:
                reference = item["reference"]
                lines.append(f"  - {reference['label']}，原區間 {fmt(reference['low'], 'revenue')} 至 "
                             f"{fmt(reference['high'], 'revenue')}，事件後預估與共識中點差 {fmt(item['delta'], 'revenue')}。"
                             f"{source_line(reference)}")
            if not expectation["consensus"]:
                lines.append("  - 這一季未取得同口徑點時市場共識。")
        bridge = earnings.get("revenue_bridge")
        if bridge and bridge["period_end"] == period:
            refs = "、".join(cite(ref) for ref in bridge["anchor_evidence_ids"])
            lines.append(f"- 第二預測季營收從草擬 {fmt(bridge['original_draft'], 'revenue')}，以 "
                         f"{REVENUE_METHODS[bridge['method']]} {fmt(bridge['anchor'], 'revenue')} 為基礎，"
                         f"套用調整後為 {fmt(bridge['after_hypothesis_links'], 'revenue')}。{refs}")
            if turn := bridge.get("turn"):
                state = {"up": "上行", "down": "下行", "unconfirmed": "訊號未達門檻", "missing_signal": "缺少可比訊號"}
                lines.append(f"  - 轉折判定為{state[turn['status']]}，相對原草擬營收自動調整 "
                             f"{fmt(turn['delta'], 'revenue')}。{turn.get('reason', '')} {turn['public_check']} {turn['falsifier']}")
                if turn["guidance_surprise"] is not None:
                    lines.append(f"  - 指引相對季節基準偏離 {fmt(turn['guidance_surprise'], 'gross_margin')}，"
                                 f"最新實績相對季節基準偏離 {fmt(turn['reported_surprise'], 'gross_margin')}。")
                for item in turn.get("operating_signals", []):
                    lines.append(f"  - 營運訊號 {item['observation']}。{source_line(item)}")
            if residual := bridge.get("residual"):
                before = residual["baseline_financials"]
                after = residual["revised_financials"]
                lines.append(
                    f"  - {residual['reason']} 營收變動 {fmt(residual['delta'], 'revenue')}，稀釋 EPS "
                    f"由 {fmt(before['eps'], 'eps')} 至 {fmt(after['eps'], 'eps')}。"
                )
                if residual["normal_far"] is not None:
                    lines.append(f"  - 歷史季節路徑 {fmt(residual['normal_far'], 'revenue')}，近期營收路徑 "
                                 f"{fmt(residual['recent_far'], 'revenue')}，估計延續比例 "
                                 f"{fmt(residual['persistence'], 'gross_margin')}。")
                if residual.get("segment_status") == "missing_evidence":
                    lines.append("  - 本案未取得可證明尚未納入原估的量化 T+2 分部收入增量。")
                for component in residual["components"]:
                    if component["status"] == "skipped" and component.get("reason"):
                        lines.append(f"  - {component['id']} 未採用。{component['reason']}")
                for ablation in residual["ablation"]:
                    if ablation["status"] == "ok":
                        without = ablation["without"]
                        lines.append(f"  - 移除 {ablation['id']} 時，營收 {fmt(without['revenue'], 'revenue')}，"
                                     f"稀釋 EPS {fmt(without['eps'], 'eps')}。")
                lines.append(f"  - {residual['public_check']} {residual['falsifier']}")
            for item in bridge["adjustments"]:
                lines.append(f"  - {item['segment']} {fmt(item['value'], 'revenue')}。{item['method']} {source_line(item)}")
                lines.append(f"    - 查核 {item['public_check']}。反證 {item['falsifier']}。")
            if not bridge["adjustments"]:
                lines.append("  - 本季沒有可單列且可量化的分部增減項。")
        for entry in earnings.get("guidance_calibration", []):
            if entry["period_end"] == period:
                key, reference = entry["metric"], entry["reference"]
                lines.append(
                    f"- 公司指引校準 {METRICS[key]}，草擬 {fmt(entry['draft_base'], key)}，"
                    f"採指引中點 {fmt(entry['calibrated_base'], key)}。{source_line(reference)}"
                )
        if profile := profiles.get(period):
            lines.append("- EPS 以稅前損益、常態稅率與單列項目重算。")
            for key, label in EPS_INPUTS.items():
                item = profile[key]
                value = fmt(item["value"], "gross_margin" if key == "tax_rate" else "revenue")
                unit = {"recurring_nonoperating": f" 百萬 {inputs['currency']}", "diluted_shares": " 百萬股"}.get(key, "")
                lines.append(f"  - {label} {value}{unit}。{item['method']} {source_line(item)}")
            for item in profile["one_offs"]:
                treatment = {"pretax_nonoperating": "稅前營業外損益", "income_tax_expense": "一次性所得稅費用"}
                lines.append(f"  - {item['label']}，{treatment[item['treatment']]} {fmt(item['value'], 'revenue')}。"
                             f"{item['method']} {source_line(item)}")
            if not profile["one_offs"]:
                lines.append("  - 預估未單列一次性項目。")
            if not profile["recognize_loss_tax_benefit"]:
                lines.append("  - 稅前虧損情境未假設可認列稅務利益。")
        for scenario in SCENARIOS:
            driver = drivers.get((period, scenario))
            if driver:
                lines.append(f"- {labels[scenario]}　{driver['rationale']} {source_line(driver)}")
                for segment, shipment in driver["shipment_changes"].items():
                    lines.append(f"  - {segment} 認列台數調整 {shipment['incremental_recognized_units']}，"
                                 f"單台收入 {shipment['revenue_per_unit']} {inputs['currency']}。"
                                 f"{shipment['recognition_basis']}")
        lines.append("")
    lines.extend(f"- {gap}" for gap in earnings["gaps"])
    if earnings.get("driver_audit") or earnings.get("unlinked_driver_inputs"):
        lines += ["", "## 假說與財務驅動追溯", ""]
        for link in earnings.get("driver_audit", []):
            owner = "模型草擬，待覆核" if link.get("origin") == "model_draft" else "研究輸入"
            lines += [
                f"- **{link['id']}｜{labels[link['scenario']]}**　{link['hypothesis_summary']}（{owner}） {source_line(link)}",
                f"  - 對應假說的原始預測　{link['hypothesis_prediction']}",
                f"  - 模型條件　{link['assumption']}",
                f"  - 核對與反證　{link['public_check']}　{link['falsifier']}",
            ]
            if not link["source_overlap"]:
                lines.append("  - 連結來源與假說原引文無交集，待研究員確認關聯。")
            if shift := link["recognition_shift"]:
                lines.append(f"  - 移轉 {shift['units']} 台，自 {shift['from_period']} 至 "
                             f"{shift['to_period']}。{shift['recognition_basis']}")
            for effect in link["effects"]:
                lines.append(f"  - {effect['period_end']} 營收差 {fmt(effect['revenue'], 'revenue')}，"
                             f"營業利益差 {fmt(effect['operating_income'], 'operating_income')}，"
                             f"EPS 差 {fmt(effect['eps'], 'eps')}。")
        if earnings.get("unlinked_driver_inputs"):
            lines.append("- 部分原始調整未掛接具名假說。連結影響按列示順序計算，交互作用歸於後套用項目。")
    lines += ["", "## 本益比情境估值", ""]
    if valuation := earnings["valuation"]:
        baseline = valuation["inputs"]["annual_base_eps"]
        lines.append(f"- 年度 EPS 基準 {baseline['low']}，原本益比 {valuation['inputs']['old_multiple']} 倍。"
                     f"將同財年季度淨利差額除以 {valuation['inputs']['annual_diluted_shares']} 年度稀釋股數。"
                     f"{valuation['inputs']['multiple_basis']} {source_line(baseline)}")
        for scenario, row in valuation["scenarios"].items():
            if row["status"] == "nonpositive_eps":
                lines.append(f"- {labels[scenario]}情境的年度 EPS 非正，無本益比估值。")
                continue
            label = labels[scenario]
            lines.append(f"- {label}情境每股情境價值 {fmt(row['value'], 'eps')} {inputs['currency']}，"
                         f"盈利變動影響 {fmt(row['earnings_effect'], 'eps')}，"
                         f"倍數變動影響 {fmt(row['multiple_effect'], 'eps')}。")
            if "upside_fraction" in row:
                ref = valuation["inputs"]["price_evidence_id"]
                lines.append(f"  - 相對 {valuation['inputs']['price_at']} 的現價變化 "
                             f"{Decimal(row['upside_fraction']):+.2%}。{cite(ref)}")
        if valuation["inputs"]["market_price"] is None:
            lines.append("- 快照缺少可引用的現價，未計算漲跌幅。")
    else:
        lines.append("- 缺少同口徑年度盈利基準或估值倍數。")
    return lines


def sym_metrics(key):
    return f"{key['period_end']} {key['scope']} {METRICS[key['metric']]}"
