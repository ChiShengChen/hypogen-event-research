from datetime import timezone
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext

from .adapters import AdapterError

FORMULA_VERSION = 2
REPORT_VERSION = 3


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


def build_context(event, inputs=None):
    evidence = [
        {
            "id": f"{doc.id}:{paragraph}", "document_id": doc.id, "paragraph": paragraph,
            "source": doc.source, "quote": quote, "synthetic": doc.synthetic, "kind": doc.kind,
            "published_at": doc.published_at.isoformat(), "obtained_at": doc.obtained_at.isoformat(),
        }
        for doc in event.documents
        if max(doc.published_at, doc.obtained_at) <= event.as_of
        for paragraph, quote in sorted(doc.paragraphs.items())
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


def build_report(event, adapter, inputs=None):
    report = build_context(event, inputs)
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
    report["assessment"] = generated.assessment.model_dump()
    report["adapter"] = adapter.identity
    report["report_version"] = REPORT_VERSION
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
    lines.extend(["", "## 事件與證據判讀", "", f"收件敘述（待核）　{report['event_text']}", ""])
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
    ), "", "## 市場預期與估值", ""])
    lines.extend(f"- {gap}" for gap in report["valuation"]["gaps"])
    lines.extend(["", "## 主張索引", ""])
    for claim in report["claims"]:
        identifier = claim["id"]
        label = {"fact": "來源原句", "assumption": "待查假設", "model_result": "情境計算"}[claim["kind"]]
        if identifier == "lots" or identifier.startswith("scenario:"):
            label = "情境假設"
        source = f"（{cite(claim['evidence_id'])}）" if claim.get("evidence_id") else ""
        lines.append(f'- <a id="{claim_anchors[identifier]}"></a> `{identifier}` {label}　{claim["text"]}{source}')
    lines.extend(["", "## 原文與時點", ""])
    for item in report["evidence"]:
        identifier = item["id"]
        label = "虛構，" if item["synthetic"] else ""
        label += {"scenario": "情境假設", "disclosure": "來源揭露", "unspecified": "提供的資料"}[item["kind"]]
        lines.extend([
            f'- <a id="{anchor_ids[identifier]}"></a> `{identifier}` {item["source"]} '
            f'第 {item["paragraph"]} 段（{label}）',
            f'  - 公開 {item["published_at"]}，取得 {item["obtained_at"]}。',
            f'  - 原文　{item["quote"]}',
        ])
    return "\n".join(lines) + "\n"
