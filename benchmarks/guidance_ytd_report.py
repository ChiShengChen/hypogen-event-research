"""Export pilot gates, full replies, citations and reproducible ledgers."""
import json
from pathlib import Path
import shutil

from benchmarks import guidance_ytd_run as run
from benchmarks.guidance_ytd_regression import PREVIOUS
from benchmarks.v9_equal_review import USAGE, write_csv, write_text

NAMES = {"current": "現版 Harness", "revised": "新版 Harness", "astra": "純 Astra"}
PHASES = {"pilot": "先導", "holdout": "保留集"}
ITEMS = {
    "implied_remainder_prior": "前次隱含 Q4 營收",
    "implied_remainder_new": "最新隱含 Q4 營收",
    "implied_remainder_change": "隱含 Q4 差額",
    "implied_remainder": "隱含 Q4 方向",
}


def call_files(root, key, arm):
    job = root / "jobs" / f"{key}-{arm}"
    files = (("answer.json", "模型原始 JSON"), ("events.jsonl", "CLI 事件"),
             ("request.json", "完整請求"), ("stderr.log", "診斷"))
    return " · ".join(f"[{label}](jobs/{job.name}/{file})"
                      for file, label in files if (job / file).is_file() and (job / file).stat().st_size)


def verify_calls(root, cases, requests):
    ledger = []
    for key, row in cases.items():
        for arm in run.GENERATION:
            result = run.b.equal.receipt(root, key, arm)
            job = root / "jobs" / f"{key}-{arm}"
            if result:
                request = run.read(job / "request.json")
                assert request == requests[key][arm]
                assert run.b.equal.digest(request) == result["request_sha256"]
            if result.get("status") == "completed":
                events = [json.loads(line)["event"] for line in (job / "events.jsonl").read_text().splitlines()]
                assert sum(event.get("type") == "turn.completed" for event in events) == 1
                assert not any(event.get("item", {}).get("type") in run.b.equal.journal.PROHIBITED for event in events)
            columns = ("reason", "started_at", "finished_at", "elapsed_seconds", "queue_seconds",
                       "cli_elapsed_seconds", "prompt_bytes", "request_sha256")
            ledger.append({"case": key, "split": row["case"]["split"], "call": arm,
                           "status": result.get("status", "not_started")} |
                          {column: result.get(column) for column in columns} | (result.get("usage") or {}))
    fields = ("case", "split", "call", "status", "reason", "started_at", "finished_at", "queue_seconds",
              "elapsed_seconds", "cli_elapsed_seconds", "prompt_bytes", "request_sha256", *USAGE)
    write_csv(root / "execution.csv", fields, ledger)
    return ledger


def anchors(root, cases, summaries):
    lines = ["# 累計營收期間核對 · 逐案問答", "",
             "以下為封存答案、模型實際回覆與新版驗證器選定的原文欄。金額為美元。", ""]
    scores, proofs = [], []
    for key, row in cases.items():
        case = row["case"]
        split = case["split"]
        documents = {doc["id"]: doc for doc in case["documents"]}
        lines.extend([f"## {case['issuer']} · {PHASES[split]}", "", f"研究截止　{case['as_of']}", ""])
        for prefix, doc in documents.items():
            lines.append(f"- [{prefix} 官方完整公告]({doc['source_url']}) · [本機 PDF](filings/{prefix}.pdf) · "
                         f"[逐頁文字](filings/{prefix}.pages.txt)")
        lines.extend(["", "### 封存裁定", "", f"{case['trap']}", "", "| 項目 | 答案 |", "|---|---|"])
        for item, value in row["gold"].items():
            lines.append(f"| {ITEMS[item]} | {value} |")
        lines.append("")
        for name, refs in case["figures"].items():
            for ref in refs:
                page = int(ref["block"].rsplit(":p", 1)[1])
                lines.append(f"- {name}　{ref['quote']}。[官方第 {page} 頁]({documents[ref['document']]['source_url']}#page={page})")
        lines.append("")
        call = run.b.equal.receipt(root, key, "extract")
        direct = run.b.equal.receipt(root, key, "astra")
        for arm, raw in (("extract", call), ("astra", direct)):
            if links := call_files(root, key, arm):
                lines.append(f"- {arm} · {raw.get('status', 'not_started')}。{links}")
                if reason := raw.get("raw", {}).get("missing_reason"):
                    lines.append(f"  原回覆的證據缺口　{reason}")
        lines.append("")
        outcomes = summaries[split]["scores"].get(key, {})
        if not outcomes:
            lines.extend(["本案未取得可計分回覆。執行狀態另見帳本。", ""])
        for arm, label in NAMES.items():
            outcome = outcomes.get(arm)
            if not outcome:
                continue
            lines.extend([f"### {label}", "", "| 項目 | 回覆 | 答案 | 對錯 |", "|---|---:|---:|---|"])
            for item, rating in outcome["items"].items():
                lines.append(f"| {ITEMS[item]} | {rating['answer']} | {rating['gold']} | {'對' if rating['correct'] else '錯'} |")
                scores.append({"case": key, "split": split, "arm": arm, "item": item, **rating,
                               "case_exact": outcome["exact"], "false_adjustment": outcome["false_adjustment"],
                               "failure": "、".join(outcome["failure_dimensions"])})
            if outcome["failure_dimensions"]:
                lines.extend(["", "**失分**　" + "、".join(outcome["failure_dimensions"])])
            lines.append("")
        for name, operand in call.get("validation", {}).get("proofs", {}).items():
            for cell in operand:
                proof = cell["ref"]
                lines.extend([
                    f"- 新版 {name}　財年 {cell['fiscal_year']}，涵蓋第 "
                    f"{'、'.join(map(str, cell['quarters']))} 季，公告 {cell['published_at']}。",
                    f"  {cell['table']}。{cell['header']}。第 {cell['column']} 欄，原始值 {proof['quote']}，"
                    f"換算 {cell['value']} 美元。[官方原頁]({cell['source_url']})",
                ])
                proofs.append({"case": key, "operand": name, **cell})
        for name, error in call.get("validation", {}).get("errors", {}).items():
            lines.append(f"- 待查 {name}　{error}")
        lines.append("")
    write_csv(root / "scores.csv", ("case", "split", "arm", "item", "kind", "answer", "gold", "correct",
                                      "case_exact", "false_adjustment", "failure"), scores)
    run.b.equal.journal.atomic(root / "provenance.json", proofs)
    write_text(root / "qa-records.md", lines)


def regression_artifacts(root):
    rows = run.read(root / "regressions.json")
    target = root / "regression-original"
    target.mkdir(exist_ok=True)
    for row in rows:
        key, repeat = row["case"], row["repeat"]
        for arm in ("harness", "astra"):
            name = f"{key}~r{repeat}-{arm}"
            shutil.copyfile(PREVIOUS / "calls" / f"{name}.json", target / f"{name}.json")
            shutil.copyfile(PREVIOUS / "jobs" / name / "answer.json", target / f"{name}-answer.json")
    return {arm: sum(row[arm]["exact"] for row in rows) for arm in run.ARMS}, len(rows)


def publish(root):
    cases, requests, protocol = run.inputs_at(root)
    summaries = {split: run.phase_status(root, cases, split) for split in PHASES}
    for split, data in summaries.items():
        run.b.equal.journal.atomic(root / f"summary-{split}.json", data)
    ledger = verify_calls(root, cases, requests)
    anchors(root, cases, summaries)
    regress, repeats = regression_artifacts(root)
    pilot, holdout = summaries["pilot"], summaries["holdout"]
    pword = "通過" if pilot["passed"] else "未通過"
    hword = "通過" if holdout["passed"] else "未通過" if holdout["paired"] else "未開跑"
    lines = [
        "# 累計營收期間核對", "",
        f"**先導 {pilot['paired']}/4 組齊全，{pword}。保留集 {holdout['paired']}/8 組齊全，{hword}。**", "",
        f"離線回歸（四發行人、每案三次）重用封存擷取。現版 {regress['current']}/{repeats}，"
        f"新版 {regress['revised']}/{repeats}，純 Astra {regress['astra']}/{repeats}。回歸與樣本外分開計分。", "",
        "| 階段與組別 | 全對 | 正例全對 | 負例全對 | 數值全對 | 誤調 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for split, data in summaries.items():
        for arm, label in NAMES.items():
            result = data["metrics"][arm]
            complete = any(arm in row for row in data["scores"].values())
            values = [str(result[column]) if complete else "—" for column in
                      ("exact", "positive", "negative", "numeric_exact", "false_adjustments")]
            lines.append(f"| {PHASES[split]} · {label} | " + " | ".join(values) + " |")
    lines.extend(["", "保留集的獨立兩個目標分別按封存規則計算。"
                  f"相對現版的改善{'達標' if holdout['improved'] else '未達標'}。"
                  f"相對純 Astra 的領先{'達標' if holdout['leads'] else '未達標'}。", "",
                  "## 案例差異", "",
                  "| 階段 | 發行人 | 現版 | 新版 | 純 Astra |",
                  "|---|---|---|---|---|"])
    for key, row in cases.items():
        split = row["case"]["split"]
        scored = summaries[split]["scores"].get(key, {})
        outcomes = []
        for arm in NAMES:
            result = scored.get(arm)
            if result is None:
                outcomes.append("—")
            else:
                outcomes.append("全對" if result["exact"] else "、".join(result["failure_dimensions"]))
        lines.append(f"| {PHASES[split]} | {row['case']['issuer']} | " + " | ".join(outcomes) + " |")
    lines.extend(["", "## 呼叫用量", "",
                  "| 呼叫 | 啟動／完成 | 輸入／輸出詞元 | 累計秒數 |",
                  "|---|---:|---:|---:|"])
    for arm in run.GENERATION:
        rows = [row for row in ledger if row["call"] == arm and row["started_at"]]
        inp = sum(row.get("input_tokens", 0) for row in rows)
        otp = sum(row.get("output_tokens", 0) for row in rows)
        seconds = sum(row.get("elapsed_seconds") or 0 for row in rows)
        lines.append(f"| {'共享擷取' if arm == 'extract' else '純 Astra'} | {len(rows)}／"
                     f"{sum(row['status'] == 'completed' for row in rows)} | {inp:,}／{otp:,} | {seconds:.1f} |")
    lines.extend(["", "八案保留集與四案先導一同封存，僅在先導通過時派發。模型採同一 Astra medium、各一次、"
                  "180 秒、停用搜尋。現版與新版共用擷取回覆，新版按表頭和時點選擇累計實績。"
                  "純 Astra 獨立計算並逐欄提交依據。公告時間以日期日末作代理。", "",
                  f"封存時間 {protocol['sealed_at']}。正例需新舊金額、差額、方向與原文欄位同時正確。"
                  "負例需明確保留判斷並指出缺少的證據。現版與新版的算式沿用 v2。", "",
                  "- [逐案問答及來源](qa-records.md) · [逐題評分](scores.csv) · [執行帳本](execution.csv)",
                  "- [欄頭與原文定位](provenance.json) · [封存協議](protocol.json) · [封存案例](cases.json)",
                  "- [回歸評分](regressions.json) · [回歸原始回傳](regression-original/)"])
    write_text(root / "report.md", lines)
