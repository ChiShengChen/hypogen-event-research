"""Generate human-readable evidence, scoring and failure tables from sealed receipts."""

from collections import Counter
from pathlib import Path
from urllib.parse import quote

from study import ARMS, DEPS, MODELS, OUT, number, read

LABELS = {
    "direct": "直接作答", "all_or_nothing": "整組核對", "fieldwise": "逐欄核對",
    "prior_annual": "前次全年指引", "prior_q3": "前次 Q3 指引",
    "prior_ytd": "前次上半年累計", "latest_annual": "最新全年指引",
    "latest_ytd": "最新前九月累計", "prior_q4": "前次隱含 Q4",
    "latest_q4": "最新隱含 Q4", "change": "差額", "direction": "方向",
}
FAMILY_LABELS = {"astra": "Astra", "claude": "Claude"}


def write(name, lines):
    target = Path(__file__).with_name(name)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def percent(value):
    return "—" if value is None else f"{value:.1%}"


def ratio(count, total):
    return f"{count}/{total}" if total else "—"


def value(amount):
    return "暫緩" if amount is None else f"`{amount}`"


def escape(raw):
    return raw.strip().replace("|", r"\|").replace("`", "'")


def show_row(row):
    return f"`{row['page']}:{row['row']}` {escape(row['text'])}"


def evidence_file(cases):
    lines = ["# 逐案原文與金額", "",
             "頁碼採原始 PDF 順序，列數是該頁非空白列序。下列連結開到原始頁。改動案例保留每處改動的原始頁列。",
             "", "完整頁面文字、原 PDF 雜湊及逐列支撐均在 [案例封存](results/cases.json)。"]
    for identifier, case in cases.items():
        row_index = {vintage: {f"{r['page']}:{r['row']}": r for r in doc["lines"]}
                     for vintage, doc in case["docs"].items()}
        lines += ["", f"## {case['issuer']} · {identifier}", "",
                  f"- 分割與種類：{case['split']} / {case['kind']}",
                  f"- [前次公告 {case['dates']['prior']}]({case['docs']['prior']['url']})",
                  f"- [最新公告 {case['dates']['latest']}]({case['docs']['latest']['url']})"]
        for field, expected in case["expected"].items():
            lines.append(f"- {LABELS[field]} {value(expected)}")
        if case.get("edits"):
            for edit in case["edits"]:
                lines.append(f"- 受控改動 `{edit['vintage']} {edit['page']}:{edit['row']}`　`{edit['old']}` → `{edit['new']}`")
        for role, locators in case["gold"].items():
            lines += ["", f"### {LABELS[role]}", ""]
            if not locators:
                lines.append(case["missing"][role])
                continue
            for reference in locators:
                vintage, at = reference["vintage"], reference["at"]
                location = quote(reference["url"], safe=":/%#=?&._-")
                picked = ", ".join(pick["raw"] for pick in reference["printed"])
                normalized = ", ".join(reference["amounts"])
                lines.append(f"- `{at}` 選 `{picked}` × {reference['scale']:,} → `{normalized}` USD。"
                             f" 財期 `{reference['period']}`，財年 {reference['fiscal_year']}。 [原文 PDF]({location})")
                lines.append(f"  - 原始列 {show_row(row_index[vintage][at])}")
                lines.extend(f"  - 支撐 {show_row(anchor)}" for anchor in reference["evidence_anchors"])
    return lines


def arm_table(metrics):
    lines = ["| 處理 | 有證據且正確 / 可答 | 誤發布 / 發布 | 數值錯 | 可答但暫緩 | 差額正確但取證有錯 / 差額正確 |",
             "|---|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        r = metrics[arm]
        lines.append(f"| {LABELS[arm]} | {ratio(r['supported_correct'], r['answerable'])} |"
                     f" {ratio(r['false_published'], r['published'])} | {r['numeric_false']} |"
                     f" {r['abstained_answerable']} | {ratio(r['concealed_errors'], r['delta_correct'])} |")
    return lines


def case_scores(scores, execution):
    by_id = {score["id"]: score for score in scores}
    lines = ["# 模型回傳與逐案評分", "",
             "保留金額、引文、換算、算式與政策的差異。服務失敗也列於原預算。"
             " 下表中的可答但暫緩也計入錯誤欄位。完整狀態與程序訊息見 [執行帳本](results/execution.json)。"]
    for run in execution:
        identifier = run["id"]
        score = by_id.get(identifier)
        lines += ["", f"## {identifier}", ""]
        if run["status"] == "unstarted":
            lines.append("封存，未派發。")
            continue
        lines.append(f"- 狀態 `{run['status']}`，耗時 `{run.get('elapsed_seconds')}` 秒。[逐次回傳](results/calls/{identifier}.json)")
        if not score:
            lines.append(f"- 原因 `{run.get('reason')}`，{escape(str(run.get('error', '逐次紀錄含服務資訊')))}")
            continue
        lines.extend(f"- {LABELS[role]} `{diagnosis}`" for role, diagnosis in score["diagnostics"].items())
        lines += ["", "| 欄位 | 標註 | 直接 | 整組 | 逐欄 |", "|---|---|---|---|---|"]
        for field in DEPS:
            entries = [score["grades"][arm][field] for arm in ARMS]
            displayed = []
            for entry in entries:
                grade = "正確" if entry["grounded_correct"] else "正確暫緩" if entry["numeric_exact"] and entry["actual"] is None else "失分"
                displayed.append(f"{value(entry['actual'])}（{grade}）")
            lines.append(f"| {LABELS[field]} | {value(entries[0]['expected'])} | {' | '.join(displayed)} |")
    return lines


def shifts(original, variant, arm):
    return [
        None if None in (old, new) else new - old
        for field in ("prior_q4", "latest_q4", "change")
        for old, new in [(number(original["grades"][arm][field]["actual"]),
                          number(variant["grades"][arm][field]["actual"]))]
    ]


def results_report(cases, summary, scores, execution):
    lines = ["# 完整公告評測結果", "", "本表使用封存後實際回傳。各分割和模型家族分開計數。",
             "", "## 執行完成率", "",
             "| 分割 | 家族 | 條件 | 開始 | 結構化回覆 | 實測輸入詞元 | 實測輸出詞元 | 呼叫秒數 |",
             "|---|---|---|---:|---:|---:|---:|---:|"]
    for stage in ("pilot", "holdout"):
        for family in MODELS:
            for mode in ("full", "oracle", "controlled"):
                rows = [row for row in execution if row["stage"] == stage and row["family"] == family and
                        mode == (row["mode"] if cases[row["key"]]["kind"] == "original" else "controlled")]
                if not rows:
                    continue
                statuses = Counter(row["status"] for row in rows)
                input_total = sum((row.get("usage") or {}).get("input_tokens", 0) for row in rows)
                output_total = sum((row.get("usage") or {}).get("output_tokens", 0) for row in rows)
                elapsed = sum(row.get("elapsed_seconds") or 0 for row in rows)
                begin = len(rows) - statuses["unstarted"]
                lines.append(f"| {stage} | {FAMILY_LABELS[family]} | {mode} | {ratio(begin, len(rows))} |"
                             f" {ratio(statuses['completed'], len(rows))} | {input_total:,} | {output_total:,} | {elapsed:.2f} |")
    lines += ["", "零詞元表示帳本沒有可加總的詞元。CLI 可能分別回報推理、快取或重試詞元，實際用量以原始帳本為準。",
              "", "## 真實案例"]
    for stage in ("pilot", "holdout"):
        for family in MODELS:
            for mode in ("full", "oracle"):
                lines += ["", f"### {stage} · {FAMILY_LABELS[family]} · {mode}", ""]
                cohort = [r for r in scores if r["stage"] == stage and r["family"] == family and r["mode"] == mode and r["kind"] == "original"]
                if not cohort:
                    lines.append("沒有有效回覆。")
                    continue
                metrics = summary["real"][stage][family][mode]
                lines.extend(arm_table(metrics))
                p = metrics["paired_policy"]
                lines += ["", f"- 逐欄多保留 {p['additional_supported_fields']} 個欄位，"
                          f"新增誤發布 {p['additional_false_publications']} 個，涉及 {p['issuers_with_additional_supported_fields']} 家發行人。"
                          f"同觀測風險的覆蓋率增益 {percent(p['coverage_gain_at_equal_risk'])}。",
                          f"- 直接作答在差額正確的案例有 {metrics['direct']['concealed_operand_values']} 案含錯誤或缺漏金額。"]
                d = metrics["direct"]
                if d["concealed_wilson95_issuer"]:
                    lo, hi = d["concealed_wilson95_issuer"]
                    lines.append(f"- 差額正確且取證有錯的條件比例，其發行人層級 Wilson 95% 區間 {percent(lo)}–{percent(hi)}。")
                for arm in ARMS:
                    r = metrics[arm]
                    upper = r["issuer_risk_exact_upper95_if_zero"]
                    if upper is not None:
                        lines.append(f"- {LABELS[arm]}有 {r['issuers_published']} 家發行人發布且零誤發布。發行人層級單尾 95% 精確上界 {percent(upper)}。")
    lines += ["", "## 受控擾動", "",
              "Rapid7 的改動分別改變兩邊和單側的累計營收。各改動回覆與同家族原始案例比較。"]
    raw = {(r["case"], r["family"]): r for r in scores if r["mode"] == "full"}
    for family in MODELS:
        if not any(r["family"] == family and r["kind"] != "original" for r in scores):
            continue
        lines += ["", f"### {FAMILY_LABELS[family]}", ""]
        lines.extend(arm_table(summary["controlled"][family]))
        lines += ["", "| 改動 | 預期差額 | 直接差額 | 逐欄差額 | 直接作答的前次、最新、差額變動 |",
                  "|---|---:|---:|---:|---|"]
        for identifier in ("common", "latest_shift"):
            r = raw.get((identifier, family))
            if r:
                d, f = (r["grades"][a]["change"] for a in ("direct", "fieldwise"))
                base = raw.get(("rpd", family))
                measured = "；".join(value(n) for n in shifts(base, r, "direct")) if base else "—"
                lines.append(f"| {identifier} | {value(d['expected'])} | {value(d['actual'])} | {value(f['actual'])} | {measured} |")
    lines += ["", "## 檔案", "",
              "- [逐案原文與欄位](evidence.md) · [逐案回傳與評分](case-scores.md) · [失分明細](results/failures.json)",
              "- [逐欄評分 JSON](results/scores.json) · [機器摘要](results/summary.json) · [原始帳本](results/execution.json)",
              "- [封存規則](protocol.md) · [封存案與完整頁面](results/cases.json) · [請求](results/requests.json)"]
    return lines


if __name__ == "__main__":
    cases = read(OUT / "cases.json")
    summary, scores, execution = [read(OUT / f"{name}.json") for name in ("summary", "scores", "execution")]
    write("evidence.md", evidence_file(cases))
    write("case-scores.md", case_scores(scores, execution))
    write("results.md", results_report(cases, summary, scores, execution))
