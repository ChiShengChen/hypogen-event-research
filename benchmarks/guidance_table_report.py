"""Publish frozen comparisons with issuer links, column proofs and execution receipts."""
from pathlib import Path
import re

from benchmarks import guidance_table_run as run
from benchmarks.guidance_ytd_report import ITEMS, NAMES, PHASES, call_files, verify_calls
from benchmarks.v9_equal_review import write_csv, write_text

paired, b = run.paired, run.b
METRICS = ("exact", "numeric_exact", "numeric_with_bad_citation", "positive", "negative",
           "false_abstentions", "false_adjustments")


def link(ref, document):
    page = int(ref["block"].rsplit(":p", 1)[1])
    return f"[第 {page} 頁第 {ref['line']} 行]({document['source_url']}#page={page})"


def evidence_lines(anchor, doc):
    entries = [(anchor["table"], "表名"), *((item, "表頭") for item in anchor["heading"]),
               *((item, "倍率") for item in anchor["units"]), (anchor["row"], "營收列")]
    return [f"  - {label}　{ref['quote']}。{link(ref, doc)}" for ref, label in entries]


def qa(root, cases, summaries):
    lines = ["# 跨頁表頭與合併營收列核對 · 逐案問答", ""]
    result_rows, case_rows, proofs = [], [], []
    for key, entry in cases.items():
        data, gold = entry["case"], entry["gold"]
        case = b.Case.model_validate(data)
        documents = {doc["id"]: doc for doc in data["documents"]}
        split = data["split"]
        lines.extend([f"## {data['issuer']} · {PHASES[split]}", "",
                      f"研究截止 {data['as_of']}。{data['trap']}", "", "### 題目", ""])
        lines.extend(f"- {item['question']}" for item in b.questions(case))
        lines.extend(["", "### 點時原文與獨立確認欄位", ""])
        for name, doc in documents.items():
            lines.append(f"- [{name} 來源公告]({doc['source_url']}) · [封存 PDF](filings/{name}.pdf) · "
                         f"[逐頁文字](filings/{name}.pages.txt)")
        if "gap_anchor" in entry:
            gap = entry["gap_anchor"]
            area = gap["blocks"][0]
            doc, page = area.rsplit(":p", 1)
            lines.append(f"- 缺項核對　[{gap['quote']}]({documents[doc]['source_url']}#page={int(page)})")
        for operand, anchor in entry.get("gold_columns", {}).items():
            doc = documents[anchor["row"]["block"].rsplit(":p", 1)[0]]
            lines.append(f"- {operand}　第 {anchor['column']} 欄，{anchor['raw']} × {anchor['multiplier']:,} 美元")
            lines.extend(evidence_lines(anchor, doc))
        for operand, refs in data["figures"].items():
            if operand in run.ACTUALS:
                continue
            for ref in refs:
                doc = documents[ref["document"]]
                page = int(ref["block"].rsplit(":p", 1)[1])
                lines.append(f"- {operand}　[{ref['quote']}]({doc['source_url']}#page={page})")
        lines.append("")
        for generation in paired.GENERATION:
            receipt = b.equal.receipt(root, key, generation)
            lines.append(f"- {generation}　{receipt.get('status', 'not_started')}。{call_files(root, key, generation)}")
            raw = receipt.get("raw", {})
            if raw:
                if reason := raw.get("missing_reason") or raw.get("reason"):
                    lines.append(f"  模型判讀　{reason}")
                figures = raw.get("figures", raw.get("figures_used", []))
                for ref in figures:
                    match = re.fullmatch(r"(.+):p([0-9]+)", ref["block"])
                    doc = documents.get(ref["document"])
                    url = f"{doc['source_url']}#page={int(match[2])}" if doc and match and match[1] == doc["id"] else ""
                    value = f"[{ref['quote']}]({url})" if url else ref["quote"]
                    lines.append(f"  - {ref['name']}　{ref['block']} · {value}")
        lines.append("")
        marks = summaries[split]["scores"].get(key, {})
        for arm, label in NAMES.items():
            mark = marks.get(arm)
            if not mark:
                case_rows.append({"case": key, "split": split, "arm": arm, "status": "unscored"})
                continue
            case_rows.append({"case": key, "split": split, "arm": arm, "status": "scored"} |
                             {k: mark[k] for k in ("exact", "numeric_exact", "false_adjustment", "false_abstention")} |
                             {"citation_failures": "／".join(f"{operand} {kind}" for operand, kind in mark["citation_failures"]),
                              "failure_dimensions": "、".join(mark["failure_dimensions"])})
            lines.extend([f"### {label}", "", "| 指標 | 實際回覆 | 封存答案 | 數值或方向 |", "|---|---:|---:|---|"])
            for name, rating in mark["items"].items():
                lines.append(f"| {ITEMS[name]} | {rating['answer']} | {gold[name]} | {'對' if rating['correct'] else '錯'} |")
                result_rows.append({"case": key, "split": split, "arm": arm, "item": name, **rating})
            if mark["failure_dimensions"]:
                lines.append("")
                lines.append("失分　" + "、".join(mark["failure_dimensions"]) + "。")
            lines.append("")
        if not marks:
            lines.extend(["本案未取得可計分回覆。封存原文與逐次狀態可由來源帳本查閱。", ""])
        call = b.equal.receipt(root, key, "extract")
        for validator, label in (("current_validation", "現版"), ("validation", "新版")):
            for name, reason in call.get(validator, {}).get("errors", {}).items():
                lines.append(f"- {label}待查　{name} · {reason}")
        for operand, cells in call.get("validation", {}).get("proofs", {}).items():
            for cell in cells:
                trails = [("數值列", cell["row"]), ("表名", cell["table"])]
                trails.extend(("表頭", item) for item in cell["heading_sources"])
                trails.extend(("倍率", item) for item in cell["unit_sources"])
                trails.extend(("營收組成", item) for item in cell["component_rows"])
                trails.extend([("幣別", cell["currency_source"])] if cell["currency_source"] else [])
                lines.append(f"- 新版 {operand}　公告 {cell['published_at']} · 財年 {cell['fiscal_year']} · "
                             f"第 {cell['column']} 欄 · 原始值 {cell['raw']} · {cell['value']} 美元")
                for label, ref in trails:
                    lines.append(f"  - {label}　{ref['quote']}。[原文位置]({ref['url']})")
                proofs.append({"case": key, "operand": operand, **cell})
        lines.append("")
    write_csv(root / "scores.csv", ("case", "split", "arm", "item", "kind", "answer", "gold", "correct"), result_rows)
    write_csv(root / "case-scores.csv", ("case", "split", "arm", "status", "exact", "numeric_exact",
              "false_adjustment", "false_abstention", "citation_failures", "failure_dimensions"), case_rows)
    b.equal.journal.atomic(root / "provenance.json", proofs)
    write_text(root / "qa-records.md", lines)


def publish(root):
    cases, requests, protocol = paired.inputs_at(root)
    phases = {split: paired.phase_status(root, cases, split) for split in PHASES}
    for split, summary in phases.items():
        b.equal.journal.atomic(root / f"summary-{split}.json", summary)
    ledger = verify_calls(root, cases, requests)
    qa(root, cases, phases)
    pilot, held = phases["pilot"], phases["holdout"]
    regressions = paired.read(root / "regressions.json")
    lines = [
        "# 跨頁表頭與合併營收列核對", "",
        f"**先導 {pilot['paired']}/4 組齊全，{'通過' if pilot['passed'] else '未通過'}。"
        f"保留集 {held['paired']}/8 組齊全，"
        f"{'通過' if held['passed'] else '未通過' if pilot['passed'] else '依規則未開跑'}。**", "",
        f"封存回歸 {sum(entry['numeric_exact'] for entry in regressions)}/{len(regressions)} 數值及方向一致。"
        "包含 monday.com、JFrog，及 GitLab、Pure Storage、Sprinklr、Best Buy 各三次擷取。"
        "回歸不計入新案。", "",
        "新版將兩頁的表名、期間和倍率依欄位對齊。非標準營收總列須能在同一合併營運表中由完整組成逐欄重算。"
        "碰到換表、倍率衝突或僅能證明訂閱小計時暫緩。", "",
        "| 階段與組別 | 全對 | 數值及方向全對 | 數值對、引文錯 | 正例全對 | 負例全對 | 正例誤暫緩 | 負例誤調 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for split, data in phases.items():
        for arm, label in NAMES.items():
            result = data["metrics"][arm]
            scored = any(arm in row for row in data["scores"].values())
            values = [str(result[key]) if scored else "—" for key in METRICS]
            lines.append(f"| {PHASES[split]} · {label} | " + " | ".join(values) + " |")
    lines.extend(["", f"改善門檻{'達標' if held['improved'] else '未達標'}。"
                  f"相對純 Astra 的領先門檻{'達標' if held['leads'] else '未達標'}。", "",
                  "## 逐案裁定", "", "| 階段 | 發行人 | 現版 | 新版 | 純 Astra |",
                  "|---|---|---|---|---|"])
    for key, row in cases.items():
        split = row["case"]["split"]
        marks = phases[split]["scores"].get(key, {})
        vals = ["—" if arm not in marks else "全對" if marks[arm]["exact"] else
                "、".join(dict.fromkeys("單位" if part == "單位錯" else part
                                     for part in marks[arm]["failure_dimensions"])) for arm in NAMES]
        lines.append(f"| {PHASES[split]} | {row['case']['issuer']} | " + " | ".join(vals) + " |")
    salesforce = phases["pilot"]["scores"].get("crm", {}).get("revised")
    if salesforce and salesforce["false_abstention"]:
        lines.extend(["", "Salesforce 的合併美元營收列可用。同名的百分比表也印了 Total revenues，"
                      "新版把該表缺少美元倍率的結果套到整份公告，因而拒收原本有效的數值。"])
    lines.append("")
    lines.append("封存負例將任何要求保留判斷的欄位填入數值記為誤調。比較差額或方向實際遭誤調的案數另列。")
    for arm, label in NAMES.items():
        count = sum(
            marks.get(arm, {}).get("false_adjustment", False) and any(
                str(rating["answer"]).strip().lower() not in {"", "unknown", "none"}
                for field, rating in marks[arm]["items"].items()
                if field in {"implied_remainder_change", "implied_remainder"}
            )
            for marks in held["scores"].values()
        )
        if any(arm in marks for marks in held["scores"].values()):
            lines.append(f"- {label} · 保留集填入不受支持的差額或方向 {count} 案。")
    path = held["scores"].get("path", {}).get("astra")
    if path and path["false_adjustment"] and not path["citation_failures"]:
        lines.extend(["", "UiPath 純 Astra 正確辨識最新全年指引缺失，也保留差額和方向。"
                      "原回傳仍列出可單獨計算的前次隱含金額，依本輪逐欄欄位規則失分。"])
    okta = held["scores"].get("okta", {}).get("astra")
    if okta and okta["numeric_exact"] and not okta["exact"]:
        lines.extend(["", "Okta 純 Astra 算對前次和最新金額、差額與方向。"
                      "回傳引用完整營收列，依封存的欄位規則還需精確摘出當期累計儲存格。"])
    if path and okta and path["false_adjustment"] and not path["citation_failures"] and (
            okta["numeric_exact"] and not okta["exact"]):
        relaxed = held["metrics"]["astra"]["exact"] + 2
        lines.extend(["", f"事後敏感度核對若將 UiPath 與 Okta 兩案都判給純 Astra，"
                      f"純 Astra 為 {relaxed}/8，新版仍為 {held['metrics']['revised']['exact']}/8。"])
    lines.extend(["", "## 模型預算與設定", "",
                  "| 呼叫 | 開始／回傳 | 實際輸入／輸出詞元 | 累計執行秒數 |", "|---|---:|---:|---:|"])
    for arm in paired.GENERATION:
        attempts = [row for row in ledger if row["call"] == arm and row["started_at"]]
        label = "共用 Astra 擷取" if arm == "extract" else "純 Astra"
        completed = sum(row["status"] == "completed" for row in attempts)
        inp = sum(row.get("input_tokens") or 0 for row in attempts)
        out = sum(row.get("output_tokens") or 0 for row in attempts)
        elapsed = sum(row["elapsed_seconds"] or 0 for row in attempts)
        lines.append(f"| {label} | {len(attempts)}／{completed} | {inp:,}／{out:,} | {elapsed:.1f} |")
    lines.extend(["", f"現版 {protocol['baseline']}。模型 {protocol['model']}，{protocol['effort']}，"
                  f"各一次、單工、停用搜尋、每次最多 {protocol['timeout_seconds']} 秒。"
                  "兩組收到同一批點時公告。版本差異取自共用擷取。詞元為實際用量。"
                  "來源以美東發布日的日末作為代理時點。公告保留原始分頁。"
                  "封存前人工查看原文以建立答案，Okta 的表頭也用來核對股數與美元倍率分開處理。"
                  "八案皆在封存後首次執行模型推論。", "",
                  f"推論前封存 {protocol['sealed_at']}。正例須同時通過新舊金額、差額、方向和欄位證據。"
                  f"既有計分容差沿用。{protocol['stop']}", "",
                  "分析師盲評 0 案。前瞻實績 0 案。ASML 劇本屬功能實測，另存一份原始稿。", "",
                  "- [逐案 QA](qa-records.md) · [案件評分](case-scores.csv) · [逐題評分](scores.csv)",
                  "- [執行帳本](execution.csv) · [封存規則](protocol.json) · [完整案例](cases.json)",
                  "- [公司與來源帳本](source-ledger.json) · [表頭和列欄證據](provenance.json) · [回歸](regressions.json)",
                  "- [ASML 多立場劇本](scenario-draft.md)"])
    write_text(root / "report.md", lines)


if __name__ == "__main__":
    publish(Path("output/guidance-table"))
