import re
from datetime import timezone
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, localcontext

from .adapters import AdapterError
from .earnings import complete_plan, render_earnings, validate_plan
from .schema import CompanyExposure, TradeOpportunity

FORMULA_VERSION = 2
REPORT_VERSION = 8
MAX_TRADE_OPPORTUNITIES = 4

SUPPLY_ROLES = {
    "upstream": "上游關鍵供應商",
    "downstream": "下游客戶與需求",
    "alternative": "替代供應商與同業",
}
RELATION_STATUSES = {
    "disclosed_relationship": "已揭露產品關係",
    "candidate": "待確認的曝險對象",
    "comparable_only": "同業對照",
}
TRADE_DIRECTIONS = {"long_if": "條件式偏多", "short_if": "條件式偏空", "watch": "觀察"}


def company_key(name):
    return "".join(character for character in name.casefold() if character.isalnum())


def trade_opportunities(assessment, report, evidence):
    mentioned = company_key(report["event_text"])
    target = company_key(report["target"])
    eligible = {
        company_key(item.company): item for item in assessment.supply_chain
        if company_key(item.company) not in mentioned and company_key(item.company) != target
        and "匿名" not in item.company and "anonymous" not in item.company.casefold()
    }
    results = {}
    for idea in assessment.trade_opportunities:
        name = company_key(idea.company)
        if name not in eligible:
            continue
        exposure = eligible[name]
        claimed = set(idea.evidence_ids)
        if claimed - evidence.keys() or not claimed.intersection(exposure.evidence_ids):
            raise AdapterError("延伸交易機會須引用已驗證的供應鏈關係")
        if idea.direction != "watch" and exposure.status != "disclosed_relationship":
            raise AdapterError("待確認曝險或同業對照只能列為觀察")
        symbol, ref = idea.ticker, idea.listing_evidence_id
        if symbol or ref:
            source = evidence.get(ref)
            quoted = source and re.search(
                rf"(?<![A-Za-z0-9]){re.escape(symbol or '')}(?![A-Za-z0-9])", source["quote"]
            )
            if not symbol or not quoted or name not in company_key(source["quote"]):
                raise AdapterError("交易代號缺少同時列出公司與代號的可見證據")
        results.setdefault(name, idea)

    for name, exposure in eligible.items():
        if len(results) == MAX_TRADE_OPPORTUNITIES:
            break
        if name in results:
            continue
        results[name] = TradeOpportunity(
            company=exposure.company, direction="watch", earnings_path=exposure.transmission,
            catalyst=exposure.public_check, trigger="待公開資料確認受影響產品與規模後，再評估方向。",
            invalidation="若公開資料確認事件未影響該公司的對應產品，移出事件觀察清單。",
            evidence_gap=f"{exposure.materiality} {exposure.gap}",
            ticker=None, listing_evidence_id=None, evidence_ids=exposure.evidence_ids,
        )
    gap = None
    if not results:
        gap = (
            "目前的公司證據只涵蓋已點名或未具名的對象。需要其他具名供應鏈公司的公開來源。"
            if assessment.supply_chain else "缺少截止時點可用、可連結研究標的與其他具名公司的產品關係證據。"
        )
    return {
        "trade_opportunities": [idea.model_dump() for idea in results.values()],
        "trade_opportunities_gap": gap,
    }


def complete_supply_chain(assessment, report, cited_text):
    known = {company_key(item.company) for item in assessment.supply_chain}
    target = company_key(report["target"])
    for edge in report["supply_edges"]:
        if len(assessment.supply_chain) == 6:
            break
        parties = (company_key(edge["supplier"]), company_key(edge["customer"]))
        ref = edge["evidence_id"]
        if target not in parties or edge["status"] != "evidenced" or ref not in cited_text:
            continue
        downstream = parties[0] == target
        side = edge["customer"] if downstream else edge["supplier"]
        company = side.removeprefix("虛構")
        key = company_key(company)
        if not key or key in known or key not in cited_text[ref]:
            continue
        assessment.supply_chain.append(CompanyExposure(
            company=company, role="downstream" if downstream else "upstream", status="candidate",
            product_scope=edge["product"],
            relationship=f"輸入資料的供應路徑為 {edge['supplier']} → {edge['customer']}，來源可核對公司名稱。",
            transmission="若事件影響這項產品的訂單或交付，可能沿買賣關係影響收入或成本。",
            materiality="待確認訂單規模與公司營收占比。",
            public_check="查雙方財報或公告是否揭露對應產品的訂單及交付。",
            gap="供應方向、涉案料號與實際交付仍待確認。", evidence_ids=[ref],
        ))
        known.add(key)


def calculate(inputs):
    with localcontext() as ctx:
        ctx.prec = 50
        contribution = inputs.price_per_lot - inputs.variable_cost_per_lot
        revenue = inputs.price_per_lot * inputs.lots
        total_contribution = contribution * inputs.lots
        operating_profit = total_contribution - inputs.fixed_cost
        taxable = operating_profit if inputs.full_tax_shield else max(operating_profit, 0)
        net_income = operating_profit - taxable * inputs.tax_rate
        eps = net_income / inputs.diluted_shares
        break_even = 0 if inputs.fixed_cost == 0 else None
        min_profitable = None
        if contribution > 0:
            ratio = inputs.fixed_cost / contribution
            break_even = int(ratio.to_integral_value(rounding=ROUND_CEILING))
            min_profitable = int(ratio.to_integral_value(rounding=ROUND_FLOOR)) + 1
        return {
            "formula_version": FORMULA_VERSION,
            "incremental_revenue": str(revenue),
            "incremental_gross_profit": str(total_contribution),
            "incremental_contribution": str(total_contribution),
            "incremental_tax": str(taxable * inputs.tax_rate),
            "incremental_operating_profit": str(operating_profit),
            "incremental_net_income": str(net_income),
            "incremental_eps": format(eps.normalize(), "f"),
            "break_even_lots": break_even,
            "min_profitable_lots": min_profitable,
            "operating_impact": (
                "增加" if operating_profit > 0 else "減少" if operating_profit < 0 else "持平"
            ),
        }


def document_evidence(doc):
    return [
        {
            "id": f"{doc.id}:{paragraph}", "document_id": doc.id, "paragraph": paragraph,
            "source": doc.source, "quote": quote, "synthetic": doc.synthetic, "kind": doc.kind,
            "text_format": doc.text_format, "availability_basis": doc.availability_basis,
            "published_at": doc.published_at.isoformat(), "obtained_at": doc.obtained_at.isoformat(),
        }
        for paragraph, quote in sorted(doc.paragraphs.items())
    ]


def disclosed_calculations(event, visible):
    results = []
    for calculation in event.reported_calculations:
        value, baseline = calculation.value, calculation.baseline
        refs = list(dict.fromkeys((value.evidence_id, baseline.evidence_id)))
        if set(refs) - visible or value.unit != baseline.unit:
            continue
        if calculation.operation != "difference" and not baseline.value:
            continue
        first, second = f"{value.value:,f}", f"{baseline.value:,f}"
        difference = f"({first} − {second})"
        with localcontext() as ctx:
            ctx.prec = 50
            if calculation.operation == "difference":
                amount = value.value - baseline.value
                formula, unit = difference, value.unit
            else:
                numerator = value.value if calculation.operation == "share" else value.value - baseline.value
                amount = (numerator / baseline.value * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                left = first if calculation.operation == "share" else difference
                formula, unit = f"{left} ÷ {second} × 100%", "%"
        approximate = value.approximate or baseline.approximate
        results.append({
            "id": calculation.id, "label": calculation.label, "value": format(amount, "f"),
            "unit": unit, "formula": formula, "approximate": approximate,
            "operands": [value.model_dump(mode="json"), baseline.model_dump(mode="json")],
            "evidence_ids": refs,
        })
    return results


def build_context(event, inputs=None):
    evidence = [
        item for doc in event.documents
        if max(doc.published_at, doc.obtained_at) <= event.as_of
        for item in document_evidence(doc)
    ]
    visible = {item["id"] for item in evidence}
    edges = []
    for edge in event.supply_edges:
        if edge.valid_from and event.as_of < edge.valid_from:
            continue
        if edge.valid_until and event.as_of >= edge.valid_until:
            continue
        if edge.evidence_id in visible:
            edges.append({**edge.model_dump(mode="json"), "status": "evidenced"})
        else:
            edges.append({
                "supplier": edge.supplier, "customer": edge.customer, "product": edge.product,
                "status": "unknown", "evidence_id": None,
            })

    inputs = inputs if inputs is not None else event.financial_inputs
    if inputs and (
        inputs.evidence_id not in visible
        or (event.research_target and inputs.target != event.research_target)
        or (event.research_horizon and inputs.quarter != event.research_horizon)
    ):
        inputs = None
    claims = []
    for item in evidence:
        is_scenario = item["kind"] == "scenario"
        claim_id = f"{'scenario' if is_scenario else 'fact'}:{item['id']}"
        claim = {
            "id": claim_id, "kind": "assumption" if is_scenario else "fact",
            "text": item["quote"], "evidence_id": item["id"],
        }
        if is_scenario:
            claim["assumption_id"] = claim_id
        claims.append(claim)
    claims.append({
        "id": "unverified_impact", "kind": "assumption", "assumption_id": "impact_mechanism",
        "text": "事件的傳導機制與獲利影響待查。",
    })
    for index, edge in enumerate(edges, 1):
        if edge["status"] == "unknown":
            claims.append({
                "id": f"supply:{index}", "kind": "assumption", "assumption_id": f"supply:{index}",
                "text": f"{edge['supplier']} → {edge['customer']}（{edge['product']}）的供應關係待查。",
            })

    report = {
        "event_text": event.event_text, "as_of": event.as_of.astimezone(timezone.utc).isoformat(),
        "target": inputs.target if inputs else event.research_target or "由事件與可見證據識別",
        "horizon": inputs.quarter if inputs else event.research_horizon or "依事件與可見證據識別",
        "evidence": evidence, "supply_edges": edges, "claims": claims,
        "disclosed_calculations": disclosed_calculations(
            event, {item["id"] for item in evidence if item["kind"] == "disclosure"},
        ),
        "valuation": {"gaps": [
            "缺少截止時點的股價、可比基準及市場共識，無法判斷市場已反映多少。",
            "估值仍需基準獲利與可辯護的估值倍數。",
        ]},
    }
    return apply_financial_scenario(report, inputs)


def apply_financial_scenario(report, inputs):
    outputs = calculate(inputs) if inputs else None
    claims = [claim for claim in report["claims"] if claim["id"] not in {"lots", "eps"}]
    if inputs:
        claims.extend([
            {"id": "lots", "kind": "assumption", "assumption_id": "lots",
             "text": f"假設 {inputs.lots:,} 批在本季交付並全數認列。"},
            {"id": "eps", "kind": "model_result", "calculation_id": "incremental_eps",
             "text": f"單季稀釋 EPS 增量 {Decimal(outputs['incremental_eps']):+f} {inputs.currency}。"},
        ])
    return {
        **report, "claims": claims, "model_inputs": inputs.model_dump(mode="json") if inputs else None,
        "model_outputs": outputs,
    }


def build_report(event, adapter, inputs=None, *, discovery=None):
    report = build_context(event, inputs)
    if event.earnings_plan is not None:
        validate_plan(event.earnings_plan, event.as_of, report["evidence"])
    context = {key: report[key] for key in ("event_text", "as_of", "target", "horizon", "supply_edges")}
    context["evidence"] = [item for item in report["evidence"] if item["kind"] != "scenario"]
    visible = {item["id"] for item in context["evidence"]}
    context["claims"] = [
        claim for claim in report["claims"]
        if claim["id"] not in {"lots", "eps"} and claim.get("evidence_id", "") in visible | {""}
    ]
    generated = adapter.hypotheses(context)
    hypotheses = generated.hypotheses
    ids = {claim["id"] for claim in context["claims"]}
    for hypothesis in hypotheses:
        if set(hypothesis.claim_ids) - ids:
            raise AdapterError("模型假說使用了不存在或不可見的主張引用")
        if (
            (event.research_target or report["model_inputs"]) and hypothesis.target != report["target"]
        ) or (
            (event.research_horizon or report["model_inputs"]) and hypothesis.horizon != report["horizon"]
        ):
            raise AdapterError("模型假說的標的或期間與研究範圍不符")
    limits = [entry.evidence_id for entry in generated.assessment.evidence_limits]
    if set(limits) - visible or len(set(limits)) != len(limits):
        raise AdapterError("模型摘要使用了不存在、不可見或重複的證據引用")
    if visible and not limits:
        raise AdapterError("模型摘要須說明對核心證據的判讀")
    if any(set(check.evidence_ids) - visible for check in generated.assessment.public_checks):
        raise AdapterError("公開查核點使用了不存在或不可見的證據引用")
    cited_text = {item["id"]: company_key(item["quote"]) for item in context["evidence"]}
    for exposure in generated.assessment.supply_chain:
        if set(exposure.evidence_ids) - visible:
            raise AdapterError("供應鏈公司使用了不存在或不可見的證據引用")
        name = company_key(exposure.company)
        if not name or not any(name in cited_text[ref] for ref in exposure.evidence_ids):
            raise AdapterError(f"供應鏈公司未見於所引來源：{exposure.company}")
    by_stance = {hypothesis.stance: hypothesis for hypothesis in hypotheses}
    if len(by_stance) != len(hypotheses) or not {"bull", "bear"} <= by_stance.keys():
        raise AdapterError("模型必須分別提供一項多方及空方假說")
    for field in ("target", "horizon"):
        values = {getattr(hypothesis, field) for hypothesis in hypotheses}
        if len(values) != 1:
            raise AdapterError("多空假說須使用相同的研究標的與期間")
        report[field] = values.pop()
    for field in ("mechanism", "prediction"):
        if getattr(by_stance["bull"], field) == getattr(by_stance["bear"], field):
            raise AdapterError("多方與空方必須提出可區分的機制及預測")
    report["hypotheses"] = [hypothesis.model_dump() for hypothesis in hypotheses]
    complete_supply_chain(generated.assessment, report, cited_text)
    report["assessment"] = generated.assessment.model_dump()
    report["assessment"].update(trade_opportunities(
        generated.assessment, report, {item["id"]: item for item in context["evidence"]},
    ))
    report["adapter"] = adapter.identity
    report["report_version"] = REPORT_VERSION
    if discovery is not None:
        report["discovery"] = discovery
    if event.earnings_plan is not None:
        report["earnings"] = complete_plan(event.earnings_plan, event.as_of, report, adapter)
    report["markdown"] = render(report)
    return report


def financial_lines(inputs, outputs, source):
    if not inputs:
        return ["缺少相符且有時點可見來源的財務輸入，維持定性判斷。"]
    currency = inputs["currency"]
    rows = [
        ("增量營收", "交付認列批數 × 每批售價", "incremental_revenue"),
        ("變動成本", "交付認列批數 × 每批變動成本", None),
        ("增量貢獻利益", "增量營收 − 變動成本", "incremental_contribution"),
        ("增量營業利益", "增量貢獻利益 − 新增固定支出", "incremental_operating_profit"),
        ("增量所得稅", "依增量營業利益及上述稅盾假設計算", "incremental_tax"),
        ("增量稅後盈餘", "增量營業利益 − 增量所得稅", "incremental_net_income"),
        ("稀釋 EPS 增量", "增量稅後盈餘 ÷ 稀釋流通股數", "incremental_eps"),
    ]
    tax_rate = Decimal(inputs["tax_rate"]) * 100
    tax_shield = "虧損稅盾可全額使用" if inputs["full_tax_shield"] else "虧損情境不認列稅盾"
    variable_cost = Decimal(inputs["variable_cost_per_lot"]) * inputs["lots"]
    lines = [
        f"- 數量假設為 {inputs['lots']:,} 批，本季全數交付並認列。參數來源為 {source}。",
        f"- 每批售價 {Decimal(inputs['price_per_lot']):,f}、每批變動成本 "
        f"{Decimal(inputs['variable_cost_per_lot']):,f}、"
        f"季內新增固定支出 {Decimal(inputs['fixed_cost']):,f}，均以 {currency} 計。",
        f"- 稅率 {tax_rate.normalize():f}%，稀釋流通股數 {inputs['diluted_shares']:,} 股，{tax_shield}。",
        "- 此模型只橋接事件的增量影響。公司全季基準 EPS、產品組合、營運資金及資本支出未納入。",
        "", "| 項目 | 計算口徑 | 情境結果 |", "|---|---|---:|",
    ]
    for label, formula, key in rows:
        value = Decimal(outputs[key]) if key else variable_cost
        unit = f"{currency}/股" if key == "incremental_eps" else currency
        lines.append(f"| {label} | {formula} | {value:+,f} {unit} |")
    return lines


def render(report):
    inputs, outputs = report["model_inputs"], report["model_outputs"]
    assessment = report["assessment"]
    model = report["adapter"]
    generator = f"`{model['mode']}`"
    if model.get("model"):
        generator += f"（`{model['model']}`）"
    anchor_ids = {
        item["id"]: f"evidence-{index}" for index, item in enumerate(report["evidence"], 1)
    }
    claim_anchors = {
        claim["id"]: f"claim-{index}" for index, claim in enumerate(report["claims"], 1)
    }

    def cite(ref):
        return f"[`{ref}`](#{anchor_ids[ref]})"

    lines = [
        "# 事件研究報告", "",
        f"- 標的／研究期間為 **{report['target']}／{report['horizon']}**。",
        f"- 截止時點為 {report['as_of']}，生成模式為 {generator}。",
        "- **研究結論為觀望**。待確認事件對公司營運的傳導與現價隱含預期。",
        f"- **核心判斷**　{assessment['thesis']}",
        f"- **首要待證**　{assessment['key_gap']}",
        f"- **下一個查核點**　{assessment['next_check']}",
    ]
    if bridge := report.get("earnings", {}).get("revenue_bridge"):
        quarter = next(row for row in report["earnings"]["quarters"] if row["period_end"] == bridge["period_end"])
        value = quarter["scenarios"]["base"]["revised"]
        currency = report["earnings"]["inputs"]["currency"]
        lines.append(f"- **第二預測季財務影響**　截至 {bridge['period_end']} 的基準營收 "
                     f"{Decimal(value['revenue']) / 1_000_000:,.1f} 百萬 {currency}，"
                     f"稀釋 EPS 為 {Decimal(value['eps']):,.2f} {currency}／股。")
        material = sorted(bridge["adjustments"], key=lambda item: abs(Decimal(item["value"])), reverse=True)[:2]
        for item in material:
            refs = "、".join(cite(ref) for ref in item["evidence_ids"])
            lines.append(f"  - {item['segment']}　查核 {item['public_check']}。反證 {item['falsifier']}。{refs}")
    if inputs:
        eps = Decimal(outputs["incremental_eps"])
        positive = outputs["min_profitable_lots"]
        threshold = (
            f"認列至少 {positive:,} 批才會產生正的增量營業利益"
            if positive is not None else "此成本結構無法產生正的增量營業利益"
        )
        lines.append(
            f"- **情境結果**　假設本季交付並認列 {inputs['lots']:,} 批，"
            f"稀釋 EPS 增量 **{eps:+f} {inputs['currency']}/股**。其他假設固定時，{threshold}。"
        )
        no_loss = outputs["break_even_lots"]
        if no_loss is not None:
            lines.append(f"- 最低不虧損量為 **{no_loss:,} 批**。")
    if branch := report.get("branch_summary"):
        lines.append(
            f"- 相對母版 {branch['parent_revision']}，認列量 {branch['prior_lots']:,} → "
            f"{inputs['lots']:,} 批，稀釋 EPS 增量差 **"
            f"{Decimal(report['incremental_eps_delta']):+f} {inputs['currency']}/股**。"
        )
    if checks := assessment["public_checks"]:
        lines.extend(["", "## 公開查核點", ""])
        for check in checks:
            refs = "、".join(cite(ref) for ref in check["evidence_ids"])
            lines.append(
                f"- **{check['metric']}**　從{check['source_to_watch']}查核（{check['window']}）。"
                f"{check['impact_on_thesis']} {refs}"
            )
    lines.extend(["", "## 供應鏈公司分析", ""])
    for role, label in SUPPLY_ROLES.items():
        exposures = [item for item in assessment["supply_chain"] if item["role"] == role]
        lines.extend([f"### {label}", ""])
        if not exposures:
            lines.extend(["目前可見來源未提供足以列名的公司。", ""])
        for item in exposures:
            refs = "、".join(cite(ref) for ref in item["evidence_ids"])
            lines.extend([
                f"- **{item['company']}**（{RELATION_STATUSES[item['status']]}，{item['product_scope']}）",
                f"  - 來源支持的關係　{item['relationship']} {refs}",
                f"  - 事件傳導　{item['transmission']}",
                f"  - 財務重要性　{item['materiality']}",
                f"  - 公開查核與缺口　{item['public_check']} {item['gap']}",
                "",
            ])
    lines.extend(["## 延伸交易機會", ""])
    lines.append("以下為未在收件敘述中點名的供應鏈公司。方向取決於觸發條件，估值、行情與可執行性仍需查核。")
    if assessment.get("trade_opportunities_gap"):
        lines.extend(["", assessment["trade_opportunities_gap"], ""])
    for idea in assessment["trade_opportunities"]:
        security = f"{idea['ticker']} {cite(idea['listing_evidence_id'])}" if idea["ticker"] else "上市工具待確認"
        refs = "、".join(cite(ref) for ref in idea["evidence_ids"])
        lines.extend([
            "", f"### {idea['company']}｜{TRADE_DIRECTIONS[idea['direction']]}", "",
            f"- 交易標的　{security}",
            f"- 財務傳導　{idea['earnings_path']} {refs}",
            f"- 公開催化劑　{idea['catalyst']}",
            f"- 觸發條件　{idea['trigger']}",
            f"- 失效條件　{idea['invalidation']}",
            f"- 交易前待查　{idea['evidence_gap']}",
        ])
    lines.extend(["", "## 事件與證據判讀", "", f"收件敘述（待核）　{report['event_text']}", ""])
    if discovery := report.get("discovery"):
        actions = sum(stage["web_actions"] for stage in discovery["rounds"])
        accepted = sum(stage["accepted"] for stage in discovery["rounds"])
        if discovery["mode"] == "historical_replay":
            lines.extend(["搜尋為事後歷史回放。日期級來源以 UTC 日末作為可得時點代理。", ""])
        lines.extend([
            f"完成 {len(discovery['rounds'])} 輪來源搜尋，記錄 {actions} 項工具操作，納入 {accepted} 份來源。",
            "",
        ])
    limits = assessment["evidence_limits"]
    if not limits:
        lines.append("截止時點缺乏可判讀的來源。")
    for item in limits:
        lines.append(f"- {cite(item['evidence_id'])} {item['limit']}")
    if report["supply_edges"]:
        lines.extend(["", "### 供應關係", ""])
        for edge in report["supply_edges"]:
            source = cite(edge["evidence_id"]) if edge["evidence_id"] else "待查"
            lines.append(f"- {edge['supplier']} → {edge['customer']}（{edge['product']}）　{source}")
    lines.extend([
        "", "## 多空假說與查核", "",
        "推翻假說需要相反證據。必要紀錄未取得時，假說仍待驗證。", "",
    ])
    for h in report["hypotheses"]:
        refs = "、".join(f"[`{ref}`](#{claim_anchors[ref]})" for ref in h["claim_ids"])
        lines.extend([
            "### " + {"bull": "多方", "bear": "空方", "wait": "觀望"}[h["stance"]], "",
            f"- 傳導機制　{h['mechanism']}", f"- 查核時機　{h['catalyst']}",
            f"- 可驗證預測　{h['prediction']}", f"- 推翻條件　{h['invalidation']}",
            f"- 依據　{refs}", "",
        ])
    lines.extend(["## 財務橋接", "", *financial_lines(
        inputs, outputs, cite(inputs["evidence_id"]) if inputs else None,
    ), ""])
    if "earnings" in report:
        lines.extend(render_earnings(report["earnings"], cite))
    else:
        lines.extend(["## 市場預期與估值", ""])
        lines.extend(f"- {gap}" for gap in report["valuation"]["gaps"])
    lines.extend(["", "## 主張索引", ""])
    summaries = {item["id"] for item in report["evidence"] if item["text_format"] == "summary"}
    for claim in report["claims"]:
        identifier = claim["id"]
        label = {"fact": "來源原句", "assumption": "待查假設", "model_result": "情境計算"}[claim["kind"]]
        if identifier == "lots" or identifier.startswith("scenario:"):
            label = "情境假設"
        elif claim.get("evidence_id") in summaries:
            label = "來源摘要"
        source = f"（{cite(claim['evidence_id'])}）" if claim.get("evidence_id") else ""
        lines.append(f'- <a id="{claim_anchors[identifier]}"></a> `{identifier}` {label}　{claim["text"]}{source}')
    lines.extend(["", "## 來源與時點", ""])
    for item in report["evidence"]:
        identifier = item["id"]
        label = "虛構，" if item["synthetic"] else ""
        label += {"scenario": "情境假設", "disclosure": "來源揭露", "unspecified": "提供的資料"}[item["kind"]]
        text_label = "來源摘要" if item["text_format"] == "summary" else "原文"
        basis = item["availability_basis"]
        if basis == "replay_day_end":
            timing = f'歷史可得時點代理 {item["obtained_at"]}。'
        elif basis == "vendor_point_in_time":
            timing = f'提供者共識快照時點 {item["published_at"]}。實際匯入時點另存於報告版本。'
        elif basis == "search_observed":
            timing = f'公開日期（依搜尋摘要）{item["published_at"][:10]}，搜尋取得 {item["obtained_at"]}。'
        else:
            timing = f'公開 {item["published_at"]}，取得 {item["obtained_at"]}。'
        lines.extend([
            f'- <a id="{anchor_ids[identifier]}"></a> `{identifier}` {item["source"]} '
            f'第 {item["paragraph"]} 段（{label}）',
            f'  - {timing}',
            f'  - {text_label}　{item["quote"]}',
        ])
    return "\n".join(lines) + "\n" + render_followups(report)


def render_followups(report):
    lines = []
    evidence = {item["id"]: item for item in report["evidence"]}
    for followup in report.get("evidence_followups", []):
        answer = followup["answer"]
        lines.extend(["", "## 追問補搜", "", followup["question"], "", answer["answer"], ""])
        for ref in answer["evidence_ids"]:
            item = evidence[ref]
            label = f"[{ref}]({item['source']})" if item["source"].startswith("https://") else f"`{ref}`"
            lines.append(f"- {label}　{item['quote']}")
        if answer["gaps"]:
            lines.extend(f"- 待查　{gap}" for gap in answer["gaps"])
    return "\n".join(lines) + "\n" if lines else ""
