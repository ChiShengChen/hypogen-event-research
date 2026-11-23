"""Point-in-time earnings revisions, scenario valuation, and forecast resolution."""
from calendar import monthrange
from decimal import Decimal, localcontext
from datetime import datetime

from .schema import DriverDraft, DriverImpact, EarningsPlan, EstimateDriver, HypothesisDriverLink

SCENARIOS = ("bear", "base", "bull")
METRICS = {"revenue": "營收", "gross_margin": "毛利率", "operating_income": "營業利益", "eps": "稀釋 EPS"}
EPS_INPUTS = {"tax_rate": "常態有效稅率", "diluted_shares": "稀釋股數", "recurring_nonoperating": "經常性營業外損益"}


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
    validate_plan(plan, as_of, evidence)
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
    profiles = {profile.period_end: profile for profile in plan.eps_assumptions}
    guidance = issuer_guidance(plan) if plan.calibrate_guidance else {}
    with localcontext() as ctx:
        ctx.prec = 50
        for quarter in sorted(plan.quarters, key=lambda value: value.period_end):
            baseline = operating_numbers(quarter)
            profile = profiles.get(quarter.period_end)
            drivers = {driver.scenario: driver for driver in plan.drivers if driver.period_end == quarter.period_end}
            if guidance:
                drivers, entries = calibrate_drivers(quarter, drivers, guidance)
                guidance_audit.extend(entries)
            scenarios = {}
            for scenario in SCENARIOS:
                driver = compile_driver(plan, quarter.period_end, scenario, audit, quarter, drivers.get(scenario), profile)
                if driver is None:
                    continue
                revised = operating_numbers(quarter, driver, profile)
                delta = {key: revised[key] - baseline[key] for key in revised if key != "segment_revenue"}
                delta["segment_revenue"] = {
                    name: revised["segment_revenue"][name] - prior
                    for name, prior in baseline["segment_revenue"].items()
                }
                scenarios[scenario] = {"revised": revised, "delta": delta}
            quarterly.append({"period_end": quarter.period_end, "baseline": baseline, "scenarios": scenarios})
        return {
            "inputs": plan.model_dump(mode="json"),
            "comparisons": comparison_rows(plan),
            "quarters": [
                {"period_end": row["period_end"].isoformat(), "baseline": numbers_json(row["baseline"]),
                 "scenarios": numbers_json(row["scenarios"])} for row in quarterly
            ],
            "valuation": valuation_rows(plan, quarterly),
            "driver_audit": list(audit.values()),
            **({"guidance_calibration": guidance_audit} if guidance_audit else {}),
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
    excluded = {"eps_assumptions", "calibrate_guidance"} if legacy else set()
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
