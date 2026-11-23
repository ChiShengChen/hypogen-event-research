"""Analyst-editable workbook and compact, printable HTML for a frozen memo."""

from html import escape
from io import BytesIO
import json
from urllib.parse import urlsplit

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .revision_memo import decimal

MONEY = '#,##0.00;[Red](#,##0.00);0.00'
METRICS = (("revenue", "營收"), ("gross_margin", "毛利率"), ("operating_income", "營業利益"), ("eps", "稀釋 EPS"))


def source_url(row):
    url = row.get("link") or row.get("source_url") or row.get("source") or ""
    try:
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.hostname and not (parsed.username or parsed.password):
            return url
    except ValueError:
        pass
    return None


def text_cells(sheet, values):
    """Treat source passages and analyst text as spreadsheet literals."""
    sheet.append(values)
    for cell in sheet[sheet.max_row]:
        if isinstance(cell.value, str):
            cell.data_type = "s"


def finish(sheet, widths):
    for column, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor="17324D")
        cell.font = Font(bold=True, color="FFFFFF")
    sheet.freeze_panes = "B2"


def workbook(memo):
    book = Workbook()
    model_sheet = book.active
    model_sheet.title = "預估變動"
    model_sheet.append(["項目", memo["prior_label"], "封存現估", "指引核對後試算", "現估－舊估", "剩餘變動"])
    model = memo["model"]
    labels = ("營收", "毛利率", "營業費用", "稅率", "稅前業外", "稅後項目", "稀釋股數",
              "認列虧損稅益", "毛利", "營業利益", "稅前利益", "所得稅", "稅後淨利", "稀釋 EPS")
    for label in labels:
        model_sheet.append([label])
    for col, point, inputs in (("B", model["prior"], model["prior_assumptions"]),
                               ("C", model["current"], model["current_assumptions"]),
                               ("D", model["proposed"], model["current_assumptions"])):
        if not point:
            continue
        values = [point[key] for key in ("revenue", "gross_margin", "opex")] + [
            inputs[key] for key in ("tax_rate", "pre_tax_other", "after_tax_other", "shares", "loss_tax_benefit")]
        for row, value in enumerate(values, 2):
            cell = model_sheet[f"{col}{row}"]
            cell.value = value if isinstance(value, bool) else decimal(value)
            cell.font = Font(color="174A75")
        formulas = ("{c}2*{c}3", "{c}10-{c}4", "{c}11+{c}6", "IF({c}9,{c}12,MAX({c}12,0))*{c}5",
                    "{c}12-{c}13+{c}7", "{c}14/{c}8")
        for row, formula in enumerate(formulas, 10):
            model_sheet[f"{col}{row}"] = "=" + formula.format(c=col)
    for row in (2, 3, 4, 10, 11, 14, 15):
        model_sheet[f"E{row}"] = f"=C{row}-B{row}"
        if model["proposed"]:
            model_sheet[f"F{row}"] = f"=D{row}-C{row}"
    for row in range(2, 16):
        for cell in model_sheet[row][1:]:
            cell.number_format = "0.00%" if row in (3, 5) else MONEY if row != 9 else "General"
    for label, value in (("標的", memo["issuer"]), ("財季／幣別／基礎", f"{memo['period_end']} ／ {memo['currency']} ／ {memo['basis']}"),
                         ("資訊截止", memo["as_of"]), ("版次", str(memo["report_revision"])),
                         ("剩餘試算口徑", "合併營收按最近指引界限調整，毛利率、費用、稅率與股數沿用現估。")):
        text_cells(model_sheet, [label, value])
    finish(model_sheet, [22, 25, 25, 25, 21, 21])

    expectations = book.create_sheet("事件前後預期")
    expectations.append(["時點", "種類", "提供者", "指標", "可得時間", "下限", "上限", "引文 ID", "狀態"])
    for row in memo["observed"]:
        text_cells(expectations, [row["phase"], row["kind"], row.get("provider"), row["key"]["metric"],
                                  row["available_at"], decimal(row["low"]), decimal(row["high"]),
                                  ", ".join(row["evidence_ids"]), "衝突" if row["conflict"] else "可比"])
    finish(expectations, [13, 21, 26, 19, 31, 19, 19, 42, 13])

    if audit := memo["guidance_audit"]:
        verified = audit["status"] in {"eligible", "noop"}
        check = book.create_sheet("指引核對")
        check.append(["項目", "結果", "來源或說明"])
        text_cells(check, ["處置", audit["status"], audit["reason"]])
        if verified:
            new = audit.get("disclosure") or {"low": audit["new_low"], "high": audit["new_high"]}
            text_cells(check, ["新指引下限", decimal(new["low"])])
            text_cells(check, ["新指引上限", decimal(new["high"])])
            text_cells(check, ["剩餘差額", decimal(audit["remaining_delta"])])
            if (original := audit.get("original")) is not None:
                text_cells(check, ["原引用區間", f"{original['low']} 至 {original['high']}", ", ".join(original["evidence_ids"])])
        if (location := audit.get("location")) is not None:
            text_cells(check, ["原文欄位", json.dumps(location, ensure_ascii=False)])
        if proof := audit.get("unit_proof"):
            text_cells(check, ["單位與倍率", proof["raw_text"], f"{proof['currency']}／{proof['multipliers']}"])
            for row in proof["sources"]:
                text_cells(check, [row["scope"], row["quote"], row["link"]])
                if source_url(row):
                    check[f"C{check.max_row}"].hyperlink = row["link"]
        finish(check, [26, 44, 82])

    drivers = book.create_sheet("傳導與假設")
    drivers.append(["類別", "內容", "來源／條件"])
    if primary := memo["primary_transmission"]:
        for key, label in (("mechanism", "主要傳導"), ("financial_effect", "財務影響"), ("condition", "成立條件"),
                           ("alternative_explanation", "替代解釋"), ("prediction", "預測"), ("invalidation", "失效條件")):
            text_cells(drivers, [label, primary[key], ", ".join(primary["evidence_ids"])])
        text_cells(drivers, ["公開查核", primary["metric"], f"{primary['public_source']}／{primary['deadline']}"])
    for line in memo["gaps"]:
        text_cells(drivers, ["證據缺口", line])
    for row in model["driver_audit"]:
        for effect in row["effects"]:
            text_cells(drivers, [f"{row['scenario']} 假設", row["assumption"], ", ".join(row["evidence_ids"])])
            text_cells(drivers, ["影響", f"營收 {effect['revenue']} ／ 營業利益 {effect['operating_income']} ／ EPS {effect['eps']}", row["id"]])
    for row in model["inputs"]:
        text_cells(drivers, [f"{row['scenario']} 模型輸入", row["rationale"], ", ".join(row["evidence_ids"])])
        for segment, change in row["shipment_changes"].items():
            text_cells(drivers, [f"{segment} 認列", f"{change['incremental_recognized_units']} 台 × {change['revenue_per_unit']}",
                                 change["recognition_basis"]])
    for section, tag in ((model["prior"], "原估"), (model["current"], "現估")):
        for segment, amount in section.get("segment_revenue", {}).items():
            text_cells(drivers, [tag, segment, decimal(amount)])
    finish(drivers, [20, 78, 66])

    valuation = book.create_sheet("估值")
    valuation.append(["情境", "原年度 EPS", "新年度 EPS", "原倍數", "新倍數", "盈利影響", "倍數影響", "估值變化", "情境價值"])
    if values := memo["valuation"]:
        inputs = values["inputs"]
        for scenario, row in values["scenarios"].items():
            if row["status"] != "scenario":
                text_cells(valuation, [scenario, "EPS 非正，P/E 不適用"])
                continue
            n = valuation.max_row + 1
            valuation.append([scenario, decimal(inputs["annual_base_eps"]["low"]), decimal(row["annual_eps"]),
                              decimal(inputs["old_multiple"]), decimal(row["multiple"]), f"=(C{n}-B{n})*D{n}",
                              f"=C{n}*(E{n}-D{n})", f"=F{n}+G{n}", f"=C{n}*E{n}"])
        text_cells(valuation, ["倍數依據", inputs["multiple_basis"]])
        text_cells(valuation, ["範圍", "原報告估值。新指引試算未分配至全年，因此保留原報告估值。"])
    finish(valuation, [19, 23, 23, 15, 15, 19, 19, 19, 19])

    evidence = book.create_sheet("引文")
    evidence.append(["引文 ID", "原文或來源摘要", "公開時間", "取得時間", "來源", "來源類型"])
    for row in memo["evidence"]:
        url = source_url(row)
        text_cells(evidence, [row["id"], row.get("quote"), row.get("published_at"), row.get("obtained_at"),
                              url or row.get("source"), row.get("availability_basis") or row.get("text_format")])
        if url:
            cell = evidence[f"E{evidence.max_row}"]
            cell.hyperlink = url
            cell.style = "Hyperlink"
        evidence[f"B{evidence.max_row}"].alignment = Alignment(wrap_text=True, vertical="top")
    finish(evidence, [34, 95, 29, 29, 55, 25])

    if cross := memo.get("archived_cross_page"):
        archive = book.create_sheet("跨頁證據")
        archive.append(["項目", "數值或原文", "原文定位"])
        text_cells(archive, ["口徑", "依封存公告倒推的中點，供分析師比較。公司正式區間及剩餘試算另列。"])
        text_cells(archive, ["財季標籤", cross["period_label"], cross["case_id"]])
        for name, value in cross["answers"].items():
            text_cells(archive, [name, value])
        for group, proofs in cross["proofs"].items():
            for proof in proofs:
                row = proof.get("row", {})
                text_cells(archive, [group, row.get("quote") or proof.get("raw"), row.get("url")])
                if row.get("url") and source_url({"link": row["url"]}):
                    archive[f"C{archive.max_row}"].hyperlink = row["url"]
        for citation in cross["citations"]:
            text_cells(archive, [citation["id"], str(citation["quote"])[:30000], citation["link"]])
            if source_url(citation):
                archive[f"C{archive.max_row}"].hyperlink = citation["link"]
        finish(archive, [42, 90, 56])

    buffer = BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def money(value, metric):
    if value is None:
        return "—"
    amount = decimal(value)
    if metric == "gross_margin":
        return f"{amount:.2%}"
    return f"{amount:,.3f}" if metric == "eps" else f"{amount / 1_000_000:,.2f}"


def printable(memo):
    def clip(value, limit):
        value = str(value or "")
        return escape(value if len(value) <= limit else value[:limit - 1] + "…")

    model = memo["model"]
    rows = []
    for key, label in METRICS:
        columns = [money(model[name][key], key) if model[name] else "—" for name in ("prior", "current", "proposed")]
        columns.append(money(decimal(model["proposed"][key]) - decimal(model["current"][key]), key)
                       if model["proposed"] else "—")
        rows.append(f"<tr><th>{label}</th>" + "".join(f"<td>{value}</td>" for value in columns) + "</tr>")
    audit = memo["guidance_audit"]
    status = clip(audit["reason"], 118) if audit else "本次未執行原文指引核對。"
    comparison_lines = []
    references = set()
    for kind, phase, label in (("internal", "before", "事件前內估"), ("consensus", "before", "事件前共識"),
                               ("issuer_guidance", "before", "舊指引"), ("issuer_guidance", "event", "新指引")):
        records = [row for row in memo["observed"] if row["kind"] == kind and row["phase"] == phase
                   and row["key"]["metric"] == "revenue" and not row["conflict"]]
        values = []
        for item in records[:2]:
            low, high = (money(item[key], "revenue") for key in ("low", "high"))
            values.append(clip(item.get("provider"), 22) + " " + low + (" 至 " + high if low != high else ""))
            references.update(item["evidence_ids"])
        if label == "新指引" and audit and audit["status"] in {"eligible", "noop"}:
            new = audit.get("disclosure") or {"low": audit["new_low"], "high": audit["new_high"]}
            low, high = (money(new[key], "revenue") for key in ("low", "high"))
            values = [low + (" 至 " + high if low != high else "")]
        comparison_lines.append(f"{label}　{'、'.join(values) or '待核對'}")
    narrative = '<p>目前缺少可定位的主要財務傳導。</p>'
    if main := memo["primary_transmission"]:
        references.update(main["evidence_ids"])
        narrative = (f'<p><b>主假說（推論）</b>　{clip(main["mechanism"], 145)}<br>{clip(main["financial_effect"], 110)}</p>'
                     f'<p><b>替代解釋</b>　{clip(main["alternative_explanation"], 120)}<br>'
                     f'<b>反證</b>　{clip(main["invalidation"], 116)}　{clip(main["deadline"], 12)}<br>'
                     f'<b>查核來源</b>　{clip(main["public_source"], 104)}</p>')
    if audit:
        references.update(audit["evidence_ids"])
    by_id = {row["id"]: row for row in memo["evidence"]}
    ordered = sorted(references, key=lambda k: (k not in (audit or {}).get("evidence_ids", []), k))
    source_links = []
    for key in ordered[:6]:
        url = source_url(by_id.get(key, {}))
        source_links.append(f'<a href="{escape(url, quote=True)}">{clip(key, 42)}</a>' if url else clip(key, 42))
    opportunities = [clip(row.get("company"), 22) for row in memo["trade_opportunities"][:3]]
    cross_text = ""
    if cross := memo.get("archived_cross_page"):
        newer = cross["answers"].get("implied_remainder_new")
        amount = money(newer, "revenue") if newer and newer != "unknown" else "待查"
        cross_text = f"<p>跨頁封存倒推中點　{amount}。原表欄位及比較限制見 Excel。</p>"
    return f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8">
<title>{clip(memo['issuer'], 40)} 財報預估修正稿</title><style>
@page {{ size: A4; margin: 16mm; }} body {{ color:#122b42; font: 11pt "Noto Sans CJK TC", sans-serif;
max-width: 760px; margin: 24px auto; line-height: 1.42; }} h1 {{ font-size: 22pt; margin:0; }}
h2 {{ font-size: 13pt; border-bottom: 1px solid #c5d3e0; margin: 1em 0 .25em; }} p {{ margin: .38em 0; }}
table {{ width:100%; border-collapse:collapse; }} th,td {{ padding: .28em .6em; border-bottom:1px solid #d6e0e8; }}
td {{ text-align:right; }} th {{ text-align:left; }} footer {{ font-size: 8pt; color:#34516b; margin-top:12pt; }}
@media print {{ body {{ margin:0; }} a {{ color:#174a75; }} }} </style>
<h1>{clip(memo['issuer'], 40)}｜財報預估修正稿</h1>
<p>研究版次 {memo['report_revision']}　財季 {clip(memo['period_end'], 12)}　{clip(memo['currency'], 3)}／{clip(memo['basis'], 20)}<br>
截點 {clip(memo['as_of'], 32)}　{clip(memo['event'], 115)}</p>
<h2>預期差與模型變動</h2><p>{'　｜　'.join(comparison_lines)}<br>{status}</p>
<p>金額以百萬原幣列示，EPS 以每股原幣列示。</p>
<table><tr><th>指標</th><th>{clip(memo['prior_label'], 15)}</th><th>封存現估</th><th>指引核對後試算</th><th>剩餘</th></tr>{''.join(rows)}</table>{cross_text}
<h2>主要傳導與查核</h2>{narrative}
<p>延伸供應鏈觀察　{'、'.join(opportunities) or clip(memo['trade_opportunities_gap'] or '待查', 94)}</p>
<h2>覆核重點</h2><p>{'　'.join(clip(gap, 88) for gap in memo['gaps'][:5]) or '逐項核對財務假設與原文。'}</p>
<footer>點時原文　{'　'.join(source_links) or '請查工作簿引文頁'}<br>數值試算、公式、來源與完整缺口見 Excel。</footer>
</html>'''
