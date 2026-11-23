"""Build the reader-facing audit and comparison figure from immutable receipts."""

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
MODELS = {"astra": "Astra", "claude": "Claude Sonnet"}
ROLES = {"prior_annual": "前次全年", "prior_q3": "前次 Q3", "prior_ytd": "前次上半年",
         "latest_annual": "最新全年", "latest_ytd": "最新前九月"}


def read(name):
    return json.loads((OUT / f"{name}.json").read_text())


def write(name, body):
    (HERE / name).write_text("\n".join(body) + "\n", encoding="utf-8")


def ratio(stats):
    return f"{stats['k']}/{stats['n']}" if stats["n"] else "—（分母 0）"


def estimate(stats):
    if not stats["n"]:
        return ratio(stats)
    low, high = stats["wilson95"]
    return f"{ratio(stats)}（{low:.1%}–{high:.1%}）"


def dollars(value):
    return "—" if value is None else f"`{value}`"


def as_line(r):
    line = r["text"].strip().replace("|", r"\|")
    return f"`{r['page']}:{r['row']}` {line}"


def evidence(cases):
    lines = ["# 原始公告、取值與正解", "",
             "PDF 頁採實體頁碼。HTML 使用固定 45 列的連續區塊。"
             " 下列為封存定位，來源全文與原件雜湊見 [cases.json](results/cases.json)。"]
    for case in cases.values():
        lines += ["", f"## {case['issuer']}", "",
                  f"- [前次原公告（{case['docs']['prior']['date'][:10]}）]({case['docs']['prior']['url']})",
                  f"- [最新原公告（{case['docs']['latest']['date'][:10]}）]({case['docs']['latest']['url']})",
                  "- 前次、最新、差額（USD） " +
                  " / ".join(dollars(case["expected"][f]) for f in ("prior_q4", "latest_q4", "change")),
                  "", "| 取值 | 可接受定位 | 換算後金額（USD） |", "|---|---|---|"]
        for role, proofs in case["gold"].items():
            for proof in proofs:
                lines.append(f"| {ROLES[role]} | [`{proof['at']}`]({proof['url']})"
                             f" `{proof['tokens']}` | {' 至 '.join(proof['amounts'])} |")
        for role, proofs in case["gold"].items():
            for proof in proofs:
                lines += ["", f"### {ROLES[role]} · {proof['at']}", "",
                          f"- 原文 `{proof['row'].strip().replace('`', '')}`",
                          f"- 原值 {', '.join(x['raw'] for x in proof['printed'])}，倍率 {proof['scale']:,}"]
                lines += [f"- 支撐 {as_line(anchor)}" for anchor in proof["evidence_anchors"]]
    return lines


def call_results(cases, scores, ledger):
    by_id = {r["id"]: r for r in scores}
    lines = ["# 逐案原始回傳與評分", "",
             "數字以美元計。以下保留模型原始指標、評分和失敗原因。"
             " [完整原始題目及兩組輸入](results/requests.json) · [失敗紀錄](results/failures.json)"]
    for call in ledger:
        name = call["id"]
        case = cases[call["key"]]
        lines += ["", f"## {case['issuer']} · {MODELS[call['family']]}", "",
                  f"- 執行 `{call['status']}`，耗時 `{call.get('elapsed_seconds')}` 秒。"]
        if call["status"] != "unstarted":
            lines.append(f"- [逐次原始回傳與帳本](results/calls/{name}.json)")
        row = by_id.get(name)
        if not row:
            lines.append(f"- 原因 `{call.get('reason')}`。")
            continue
        lines += ["", "| 欄位 | 模型原回傳 | 金額（解碼後） | 正解 | 有號誤差 |",
                  "|---|---:|---:|---:|---:|"]
        for field, value in row["values_usd"].items():
            lines.append(f"| {field} | {dollars(row['response'][field])} | {dollars(value)} | "
                         f"{dollars(row['expected'][field])} | {dollars(row['signed_errors_usd'][field])} |")
        for role, status in row["operand_status"].items():
            picks = [p for p in row["response"]["evidence"] if p["role"] == role]
            text = ", ".join(f"`{p['page']}:{p['row']} {p['indices']}`" for p in picks)
            lines.append(f"- {ROLES[role]}　`{status}` {text}")
    return lines


def report(summary, cases, ledger, scores):
    paired = summary["matched_issuers"]
    lines = ["# 完整公告差額評分審計", "",
             f"7 家新發行人，{len(paired)}/{len(cases)} 家雙模型配對。已啟動 "
             f"{summary['started']}/{summary['planned']} 次，收到 {len(scores)}/{summary['planned']} 次有效回覆。",
             "", "## 只看差額會高估多少", "",
             "每個分母都是配對發行人。表中括號為 Wilson 95% 區間。"
             " 完整答案要求新舊絕對值、差額、方向和五個原文取值均正確。",
             "", "| 模型 | 差額精確 | 新舊金額精確 | 完整答案 | 差額給了分而完整答案未過 |",
             "|---|---:|---:|---:|---:|"]
    for key, model in MODELS.items():
        stats = summary["model_results"][key]["matched"]
        measures = ("delta_exact", "absolute_pair_correct", "fully_grounded", "delta_only_overcredit")
        lines.append(f"| {model} | " + " | ".join(estimate(stats[k]) for k in measures) + " |")
    names = {m: "、".join(MODELS[key] for key in values) for m, values in summary["leader"].items()}
    lines += ["", (f"按差額排名最高為 {names['delta_exact']}。按完整證據排名最高為 {names['fully_grounded']}。"
                   if len(paired) >= 6 else "配對發行人不足預註冊的六家。"),
              "", "## 差額正確時，哪裡仍然出錯", "",
              "| 模型 | 錯金額掩蓋 | 同額誤差精確抵消 | 證據鏈不完整 | 僅引文出錯 | 容差新增錯絕對值 |",
              "|---|---:|---:|---:|---:|---:|"]
    for key, model in MODELS.items():
        stats = summary["model_results"][key]["matched"]
        metrics = ("numeric_mask_given_exact_delta", "exact_cancellation_given_exact_delta",
                   "unsupported_given_exact_delta", "citation_only_given_exact_delta", "tolerance_only_masks_wrong_level")
        lines.append(f"| {model} | " + " | ".join(estimate(stats[m]) for m in metrics) + " |")
    lines += ["", "前四欄的分母為差額精確的回覆。最後一欄使用 ±100,000 美元的通過數為分母。"
              " 有金額錯誤、缺漏或引文錯誤都能造成證據鏈不完整。"
              " 金額掩蓋只計已提交且可判定為錯的數值，精確抵消另要求兩個絕對值偏移相等、差額自洽。"]
    masked_issuers = {r["case"] for r in scores if r["case"] in paired and r["numeric_mask"]}
    lines += ["", f"本批有 {len(masked_issuers)} 家配對發行人出現精確差額掩蓋錯值。"
              f"兩家發行人的預註冊擴大訊號因此{'達標' if len(masked_issuers) >= 2 else '未達'}。"
              " 歷史 Harness 曾出現六次精確抵消，其中包含重跑。兩次結果的發行人與流程不同。"
              " [歷史帶符號誤差](../artifacts/archive-error-magnitudes.csv)",
              "", "## 執行帳本", "",
              "| 模型 | 有效回覆 / 封存 | 輸入詞元 | 輸出詞元 | 累計呼叫秒數 |",
              "|---|---:|---:|---:|---:|"]
    for key, model in MODELS.items():
        calls = [c for c in ledger if c["family"] == key]
        input_tokens = sum((r.get("usage") or {}).get("input_tokens", 0) for r in calls)
        output_tokens = sum((r.get("usage") or {}).get("output_tokens", 0) for r in calls)
        elapsed = sum(r.get("elapsed_seconds") or 0 for r in calls)
        done = sum(c["status"] == "completed" for c in calls)
        lines.append(f"| {model} | {done}/{len(calls)} | {input_tokens:,} | {output_tokens:,} | {elapsed:.1f} |")
    lines += ["", "供應商對推理、輸出及快取詞元的歸類可能不同。時間為各呼叫累計。",
              "", "按預註冊，兩個模型的金額字串都可解碼一層多餘的 JSON 引號。"]
    for key, model in MODELS.items():
        corrected = [r["id"] for r in scores if r["family"] == key and any(
            isinstance(r["response"][field], str) and r["response"][field].startswith('"')
            for field in ("prior_q4", "latest_q4", "change"))]
        lines.append(f"- {model} 有 {len(corrected)} 次原回傳出現額外引號。 [原始回傳](case-results.md)")
    lines += [
              "", "## 可覆核範圍", "",
              "採公開文件的便利樣本，集中在商用軟體、IT 服務和網路工具，統計單位是發行人。"
              " 每家族每案只推論一次。欄位和等價引文為單人標註並以程式重算，獨立複標 0 案。"
              " 樣本外指本專案此前未使用。模型訓練資料未知。兩組均使用原始公告與同一通用數字索引。"
              " 過去多次重跑的歷史結果保留為開發證據。",
              "", "- [主圖 PDF](scoring-gap.pdf) · [逐案原文](evidence.md) · [回傳與評分](case-results.md)",
              "- [預註冊](protocol.md) · [實際帳本](results/execution.json) · [評分 JSON](results/scores.json) · [失敗 JSON](results/failures.json)"]
    return lines


def figure(summary):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    fig, ax = plt.subplots(figsize=(7.1, 3.15))
    fig.subplots_adjust(left=0.24, top=0.78, bottom=0.24, right=0.94)
    fig.text(0.04, 0.94, "Exact delta vs. fully grounded answer", weight="bold", size=14)
    fig.text(0.04, 0.86, f"{len(summary['matched_issuers'])} paired issuers  |  Wilson 95% intervals", size=9, color="#3b4d61")
    distinct = (("delta_exact", "#547aa5", "Exact delta", 0.12), ("fully_grounded", "#14746f", "Fully grounded", -0.12))
    for i, (name, label) in enumerate(MODELS.items()):
        s = summary["model_results"][name]["matched"]
        for metric, color, legend, shift in distinct:
            datum = s[metric]
            if not datum["n"]:
                continue
            rate = datum["k"] / datum["n"]
            low, high = datum["wilson95"]
            ax.errorbar(rate, 1-i+shift, xerr=[[max(0, rate-low)], [max(0, high-rate)]], marker="o",
                        color=color, label=legend if i == 0 else None, capsize=3, markersize=6)
    ax.set(xlim=(-.03, 1.03), ylim=(-.42, 1.42), yticks=[1, 0], yticklabels=list(MODELS.values()))
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="x", color="#e3eaf0")
    for edge in ("top", "right", "left"):
        ax.spines[edge].set_visible(False)
    ax.tick_params(axis="y", length=0)
    handles, _ = ax.get_legend_handles_labels()
    if handles:
        ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.24), ncols=2, fontsize=9)
    fig.savefig(HERE / "scoring-gap.pdf")
    plt.close(fig)


def csv_export(scores):
    fields = ("id", "case", "family", "delta_exact", "levels_exact", "all_grounded", "numeric_mask", "exact_cancel",
              "delta_with_unsupported_evidence", "delta_with_citation_problem_only", "tolerance_only_masks_wrong_level")
    with (OUT / "scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(scores)


if __name__ == "__main__":
    summary, cases, scores, ledger = (read(name) for name in ("summary", "cases", "scores", "execution"))
    write("evidence.md", evidence(cases))
    write("case-results.md", call_results(cases, scores, ledger))
    write("report.md", report(summary, cases, ledger, scores))
    csv_export(scores)
    figure(summary)
