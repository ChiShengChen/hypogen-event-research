"""Point-in-time earnings revisions, scenario valuation, and forecast resolution."""
from calendar import monthrange
from decimal import Decimal, localcontext
from datetime import datetime

from .schema import DriverDraft, EarningsPlan

SCENARIOS = ("bear", "base", "bull")
METRICS = {"revenue": "營收", "gross_margin": "毛利率", "operating_income": "營業利益", "eps": "稀釋 EPS"}


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
    return visible


def operating_numbers(quarter, driver=None):
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
    net_income = operating_income * (1 - quarter.tax_rate) + quarter.other_after_tax
    return {
        "segment_revenue": segments, "revenue": revenue, "gross_margin": margin,
        "gross_profit": gross_profit, "opex": opex, "operating_income": operating_income,
        "net_income": net_income, "eps": net_income / quarter.diluted_shares,
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
                latest[base.kind] = base
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


def calculate_earnings(plan, as_of, evidence):
    validate_plan(plan, as_of, evidence)
    quarterly = []
    with localcontext() as ctx:
        ctx.prec = 50
        for quarter in sorted(plan.quarters, key=lambda value: value.period_end):
            baseline = operating_numbers(quarter)
            scenarios = {}
            for driver in plan.drivers:
                if driver.period_end == quarter.period_end:
                    revised = operating_numbers(quarter, driver)
                    delta = {key: revised[key] - baseline[key] for key in revised if key != "segment_revenue"}
                    delta["segment_revenue"] = {
                        name: revised["segment_revenue"][name] - prior
                        for name, prior in baseline["segment_revenue"].items()
                    }
                    scenarios[driver.scenario] = {"revised": revised, "delta": delta}
            quarterly.append({"period_end": quarter.period_end, "baseline": baseline, "scenarios": scenarios})
        return {
            "inputs": plan.model_dump(mode="json"),
            "comparisons": comparison_rows(plan),
            "quarters": [
                {"period_end": row["period_end"].isoformat(), "baseline": numbers_json(row["baseline"]),
                 "scenarios": numbers_json(row["scenarios"])} for row in quarterly
            ],
            "valuation": valuation_rows(plan, quarterly),
            "gaps": [
                f"缺少 {quarter.period_end} {key} 的修正驅動。"
                for quarter in plan.quarters for key in SCENARIOS
                if not any((d.period_end, d.scenario) == (quarter.period_end, key) for d in plan.drivers)
            ],
        }


def complete_plan(plan, as_of, context, adapter):
    if not plan.generate_drivers:
        return calculate_earnings(plan, as_of, context["evidence"])
    validate_plan(plan, as_of, context["evidence"])
    draft = getattr(adapter, "earnings_drivers", None)
    if draft is None:
        raise EarningsError("此模型模式不支援草擬預測驅動")
    result: DriverDraft = draft({
        "target": context["target"], "event": context["event_text"], "as_of": context["as_of"],
        "evidence": [row for row in context["evidence"] if row["kind"] == "disclosure" and not row["synthetic"]],
        "baseline": plan.model_dump(mode="json"),
    })
    expected = {(quarter.period_end, name) for quarter in plan.quarters for name in SCENARIOS}
    if {(driver.period_end, driver.scenario) for driver in result.drivers} != expected:
        raise EarningsError("模型草擬需涵蓋每個季度的空、基準、多情境")
    filled = EarningsPlan.model_validate({
        **plan.model_dump(), "generate_drivers": False,
        "drivers": [driver.to_driver().model_dump() for driver in result.drivers],
    })
    result = calculate_earnings(filled, as_of, context["evidence"])
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
