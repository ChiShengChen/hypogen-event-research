"""Publish original linkage replies, automated scoring and a private-key review pack."""

from pathlib import Path
import secrets
import shutil

from benchmarks import linkage_depth as depth
from benchmarks.v9_equal_review import STATUSES, USAGE, call_links, write_csv, write_text

LABELS = {"astra": "純 Astra", "harness": "Harness V10"}
DIMENSIONS = {"evidence": "證據定位與引用", "mechanism": "因果傳導", "financial_effect": "財務歸因",
              "falsifier": "反證設計"}
FIELDS = {
    "mechanism": "傳導機制", "baseline": "比較基準", "condition": "必要條件", "financial_effect": "財務影響",
    "alternative_explanation": "其他解釋", "metric": "查核指標", "observation_period": "觀察期間",
    "public_source": "公開查核來源", "deadline": "截止日", "prediction": "預測", "invalidation": "推翻條件",
}


def input_lines(case):
    event = case["input"]
    lines = [f"**研究題目**　{event['event_text']}", "", f"**截止**　{event['as_of']}　**研究期限**　{event['horizon']}", ""]
    for row in event["evidence"]:
        if row["paragraph"] == "original":
            anchor = case["anchors"][row["document_id"]]
            lines.append(f"- `{row['id']}`　{anchor['location']}原文：{row['quote']} [官方來源]({row['source']})")
        else:
            lines.append(f"- `{row['id']}`　{row['quote']} [官方來源]({row['source']})")
    return lines + [""]


def findings_lines(findings):
    lines = []
    for index, path in enumerate(findings["business_linkages"], 1):
        lines += [f"**{index}. {path['origin_business']} → {path['affected_company']} · {path['affected_business']}**", "",
                  "- 起點引文　" + "、".join(path["origin_evidence_ids"]),
                  "- 受影響業務引文　" + "、".join(path["affected_evidence_ids"])]
        lines += [f"- {label}　{path[field]}" for field, label in FIELDS.items()] + [""]
    if gap := findings["business_linkage_gap"]:
        lines += [f"**待查**　{gap}", ""]
    return lines


def receipt(root, key, arm):
    job = root / "jobs" / f"{key}-{arm}"
    if not (job / "state.json").exists():
        return {"status": "unplanned"}
    return depth.equal.journal.restore(root, job)


def blind(out, root, cases, receipts):
    key_path = root / "review-key.restricted.json"
    mapping = depth.equal.hypothesis.read(key_path)
    lines = ["# 跨業務假說匿名覆核", "",
             "兩份研究稿採相同時點證據。獨立核對兩端引文、因果必要條件、財務方向與可區分其他解釋的公開反證。"
             "如資料只顯示共同供應商、並列數字或可能釋出的資源，請核對稿件有沒有說明尚缺的證據。"
             "重大錯誤及是否可送分析師覆核採 0 或 1。每案評完兩組才算完成。", ""]
    rows, used = [], {label for case in mapping.values() for label in case}
    rng = secrets.SystemRandom()
    for key, case in cases.items():
        if any(receipts[key, arm]["status"] != "completed" for arm in depth.ARMS):
            continue
        findings = {arm: receipts[key, arm]["findings"] for arm in depth.ARMS}
        digests = {arm: depth.equal.digest(value) for arm, value in findings.items()}
        if key not in mapping:
            order = list(depth.ARMS)
            rng.shuffle(order)
            mapping[key] = {}
            for arm in order:
                alias = f"R{rng.randrange(1000, 10000)}"
                while alias in used:
                    alias = f"R{rng.randrange(1000, 10000)}"
                used.add(alias)
                mapping[key][alias] = {"arm": arm, "sha256": digests[arm]}
        elif {row["arm"]: row["sha256"] for row in mapping[key].values()} != digests:
            raise ValueError("已產生的匿名稿遭變更")
        lines += [f"## {key} · {case['issuer']}", "", *input_lines(case)]
        for alias, row in mapping[key].items():
            lines += [f"### 首稿 {alias}", "", *findings_lines(findings[row["arm"]])]
            rows.append({"case": key, "alias": alias})
    if not rows:
        lines += ["目前尚無完整配對可送評。"]
    if mapping:
        depth.equal.journal.atomic(key_path, mapping)
        key_path.chmod(0o600)
    write_text(out / "analyst-review.md", lines)
    write_csv(out / "review-form.csv", ("case", "alias", "analyst_id", *depth.CHECKS,
              "gap_correct", "major_error", "ready", "notes"), rows)
    return len(rows) // 2


def ledgers(out, root, cases, grades, receipts):
    call_fields = ("case", "split", "call", "status", "reason", "availability_source", "started_at", "finished_at",
                   "elapsed_seconds", "cli_elapsed_seconds", "prompt_bytes", "reported_wait_seconds", *USAGE)
    calls, rules, scores = [], [], []
    for (key, arm), row in receipts.items():
        case = cases[key]
        job = root / "jobs" / f"{key}-{arm}"
        usage = row.get("usage") if "turn.completed" in row.get("event_seconds", {}) else None
        calls.append({field: row.get(field) for field in call_fields} | {
            "case": key, "split": case["split"], "call": arm,
            "reported_wait_seconds": depth.equal.admission.wait_hint(job),
        } | (usage or {}))
        if arm == "judge":
            continue
        if row["status"] == "completed":
            for stage, field in (("raw", "raw_findings"), ("published", "findings")):
                for item in depth.rule_check(row[field]["business_linkages"], case):
                    rules.append({"case": key, "arm": arm, "stage": stage} | item)
        grade = grades.get(key)
        decision = grade[arm] if grade else {}
        failure = "、".join(DIMENSIONS[name] for name in decision.get("failure_dimensions", []))
        if decision and not decision["exact"] and case["gold"]["positive"] and any(
            all(item[field] for field in depth.CHECKS) and not item["target_path"]
            for item in decision["verdict"]["candidates"]
        ):
            failure = "證據定位與引用（另一路徑通過，但漏掉裁定所指的主要傳導）"
        if not grade:
            failure = "模型評分缺失" if row["status"] == "completed" else f"執行狀態：{STATUSES[row['status']]}"
        scores.append({"case": key, "split": case["split"], "arm": arm, "positive": int(case["gold"]["positive"]),
                       "status": row["status"], "exact": decision.get("exact"), "major": decision.get("major"),
                       "gap_correct": decision.get("verdict", {}).get("gap_ok"),
                       "qualifying": ",".join(map(str, decision.get("qualifying", []))), "failure": failure,
                       "model_note": decision.get("verdict", {}).get("note"), "human_score": None})
    write_csv(out / "execution.csv", call_fields, calls)
    write_csv(out / "rule-checks.csv", ("case", "arm", "stage", "index", "evidence", "time"), rules)
    write_csv(out / "scores.csv", ("case", "split", "arm", "positive", "status", "exact", "major", "gap_correct",
              "qualifying", "failure", "model_note", "human_score"), scores)
    return calls, rules


def aggregate(calls):
    selected = [row for row in calls if row["started_at"]]
    metered = [row for row in selected if row["input_tokens"] is not None]
    return {"started": len(selected), "returned": sum(row["status"] == "completed" for row in selected),
            "timeout": sum(row["status"] == "timeout" for row in selected),
            "availability": sum(row["reason"] in depth.equal.AVAILABILITY_ERRORS for row in selected),
            "elapsed_seconds": round(sum(row["elapsed_seconds"] or 0 for row in selected), 3),
            "metered": len(metered), "usage": {key: sum(row[key] for row in metered) for key in USAGE} if metered else None}


def qa(out, cases, grades, receipts):
    lines = ["# 跨業務假說深度逐案 QA", "",
             "每個案例保留下列點時資料、兩組交付的連動、評分及原始 JSON 連結。原始模型 JSON 含完整首稿。", ""]
    for key, case in cases.items():
        lines += [f"## {key} · {case['issuer']}", "", *input_lines(case),
                  f"**封存裁定**　{case['gold']['standard']}", ""]
        for arm in depth.ARMS:
            row = receipts[key, arm]
            lines += [f"### {LABELS[arm]} · {STATUSES[row['status']]}", ""]
            if links := call_links(out, "raw", key, arm, "逐次回傳"):
                lines += [links, ""]
            if row.get("error"):
                lines += [row["error"], ""]
            if row["status"] == "completed":
                lines += findings_lines(row["findings"])
                hidden = len(row["raw_findings"]["business_linkages"]) - len(row["findings"]["business_linkages"])
                if hidden:
                    lines += [f"程式另過濾 {hidden} 條候選，可在原始 JSON 查核。", ""]
            if grade := grades.get(key):
                score = grade[arm]
                lines += [f"**模型評分**　{'全對' if score['exact'] else '未全對'}。{score['verdict']['note']}", ""]
                for candidate in score["verdict"]["candidates"]:
                    reasons = "、".join(label for field, label in DIMENSIONS.items() if not candidate[field])
                    if case["gold"]["positive"] and not candidate["target_path"]:
                        reasons = f"{reasons}；未命中主要傳導" if reasons else "未命中主要傳導"
                    lines += [f"- 候選 {candidate['index']}　{reasons or '四項語義均通過'}。{candidate['note']}"]
                lines += [""]
        if links := call_links(out, "raw", key, "judge", "判讀原始 JSON"):
            lines += [links, ""]
    write_text(out / "QA.md", lines)


def report(out, summary, cases, receipts, protocol):
    p, h = (summary[split] for split in ("pilot", "holdout"))
    lines = [
        "# 跨業務假說深度 benchmark", "",
        f"**先導{'通過' if p['pass'] else '未通過'}，配對 {p['paired']}/4。"
        f"保留集配對 {h['paired']}/8。Harness {'達成本輪領先門檻' if h['pass'] else '未達本輪領先門檻'}。**", "",
        "| 階段 | 完整配對 | 完成模型判讀 | Harness 全對／重大錯誤 | 純 Astra 全對／重大錯誤 |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, row in (("先導", p), ("保留集", h)):
        marks = [f"{row['metrics'][arm]['exact']}／{row['metrics'][arm]['major']}"
                 if row["graded"] else "—" for arm in ("harness", "astra")]
        lines.append(f"| {label} | {row['paired']}/{row['planned']} | {row['graded']} | {marks[0]} | {marks[1]} |")
    lines += ["", "| 保留集 | 正例全對 | 負例全對 |", "|---|---:|---:|"]
    for arm in ("harness", "astra"):
        metrics = h["metrics"][arm]
        lines.append(f"| {LABELS[arm]} | {metrics['positive']}/4 | {metrics['negative']}/4 |")
    lines += ["", f"以上只計已完成模型判讀的案例。人工盲評完成 0 案，目前可送評 {summary['blind_pairs']} 案。", "",
              "| 呼叫 | 啟動／完成 | 逾時／容量類失敗 | 模型有回報用量 | 輸入／輸出詞元 | 累計耗時秒數 |",
              "|---|---:|---:|---:|---:|---:|"]
    for arm in (*depth.ARMS, "judge"):
        row = summary["usage"][arm]
        tokens = row["usage"]
        use = f"{tokens['input_tokens']:,}／{tokens['output_tokens']:,}" if tokens else "—"
        lines.append(f"| {LABELS.get(arm, 'Sol 評審')} | {row['started']}／{row['returned']} | "
                     f"{row['timeout']}／{row['availability']} | {row['metered']} | {use} | {row['elapsed_seconds']:.2f} |")
    missing = [(key, arm, row) for (key, arm), row in receipts.items()
               if row["status"] not in {"unplanned", "queued", "completed"}]
    if missing:
        lines += ["", "## 執行失敗", ""]
        for key, arm, row in missing:
            lines.append(f"- {key} {LABELS.get(arm, 'Sol 評審')}，{STATUSES[row['status']]}（{row.get('reason', '—')}）。")
    lines += [
        "", "## 評分與控制", "",
        "兩組使用相同 Astra medium、點時證據及 180 秒上限，各一次模型呼叫。搜尋停用，證據來自封存的原文短節錄與同期摘要。"
        "證據缺失指未能用好所提供的證據。完整研究稿共用輸出結構，Harness 經產品提示與驗證流程。詞元為實際回報值。",
        "",
        f"程式逐條核對引文 ID 與期限，{summary['published_rule_passed']}/{summary['published_rule_candidates']} 個發布候選通過。"
        "匿名 Sol 單次判讀負責評估實際語義、財務歸因和反證。案例中點時資料為歷史回放。"
        "Ford 與 ASML 的既有報告僅作離線回歸，均未納入計分。", "",
        f"封存時間（UTC）　{protocol['sealed_at']}。保留集要求八案配對與判讀皆齊全、Harness 正負各至少三案全對、"
        "零重大錯誤且全對數領先至少兩案。負例要求指明證據缺口並保留判斷。", "",
        "- [評測 PDF](report.pdf) · [完整 QA PDF](qa-records.pdf) · [逐案 QA](QA.md)",
        "- [預註冊](protocol.json) · [封存原文和裁定](cases.json) · [完整請求](requests.json)",
        "- [逐案評分](scores.csv) · [程式核對](rule-checks.csv) · [執行帳本](execution.csv) · [數字摘要](summary.json)",
        "- [匿名分析師 PDF](analyst-review.pdf) · [空白評分表](review-form.csv)",
    ]
    if (out / "regressions.json").exists():
        lines += ["- [Ford、ASML 離線回歸紀錄](regressions.json)"]
    write_text(out / "README.md", lines)


def publish(root, cases, out):
    out.mkdir(parents=True, exist_ok=True)
    for name in ("protocol.json", "cases.json", "requests.json"):
        shutil.copyfile(root / name, out / name)
    if (root / "regressions.json").exists():
        shutil.copyfile(root / "regressions.json", out / "regressions.json")
    receipts = {(key, arm): receipt(root, key, arm) for key in cases for arm in (*depth.ARMS, "judge")}
    for folder in ("jobs", "calls", "cooldowns"):
        if (root / folder).exists():
            shutil.copytree(root / folder, out / "raw" / folder, dirs_exist_ok=True)
    grades, summary = depth.summary(root, cases)
    calls, rules = ledgers(out, root, cases, grades, receipts)
    summary.update({"human_completed": 0, "blind_pairs": blind(out, root, cases, receipts),
                    "published_rule_candidates": sum(row["stage"] == "published" for row in rules),
                    "published_rule_passed": sum(row["stage"] == "published" and row["evidence"] and row["time"] for row in rules),
                    "usage": {arm: aggregate([row for row in calls if row["call"] == arm])
                              for arm in (*depth.ARMS, "judge")}})
    depth.equal.journal.atomic(out / "summary.json", summary)
    qa(out, cases, grades, receipts)
    report(out, summary, cases, receipts, depth.equal.hypothesis.read(root / "protocol.json"))
