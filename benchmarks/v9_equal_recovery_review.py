"""Publish every V9 recovery attempt and anonymize completed same-round pairs."""

from datetime import datetime
import shutil

from benchmarks import v9_equal_recovery as run, v9_equal_review as review


ROUND_LABELS = {"first": "首次", "recovery": "復原"}
WAIT_LABELS = {"completed": "已完成", "waiting": "等待中", "blocked": "超限停止"}
CAUSES = {"rate_limit": "限流／用量上限", "model_capacity": "模型容量不足",
          "per_call_deadline": "單次逾時", "batch_interruption": "程序中斷",
          "recovered_running": "中斷後恢復", "execution_or_validation": "執行或驗證失敗", "cli_exit": "CLI 結束錯誤"}
LEDGER = ("case", "round", "call", "status", "reason", "availability_source", "launched",
          "queued_at", "started_at", "finished_at", "queue_seconds", "preparation_seconds",
          "elapsed_seconds", "cli_elapsed_seconds", "prompt_bytes", "request_sha256",
          "reported_retry_wait_seconds", *review.USAGE)
WAITS = ("case", "round", "arm", "cause", "status", "reported_wait_seconds", "scheduled_seconds",
         "started_at", "resume_at", "finished_at", "elapsed_seconds")


def select_pairs(cases, calls):
    selected, origin = {}, {}
    for key, case in cases.items():
        for name in run.ROUNDS:
            if run.complete_round(calls, key, name):
                selected[key] = (case, {arm: calls[key, name, arm]["hypotheses"] for arm in run.equal.ARMS})
                origin[key] = name
                break
    return selected, origin


def call_ledger(root, calls):
    rows = []
    for (key, name, arm), row in calls.items():
        job = root / name / "jobs" / f"{key}-{arm}"
        usage = row.get("usage") if "turn.completed" in row.get("event_seconds", {}) else None
        rows.append({field: row.get(field) for field in LEDGER}
                    | {"launched": int(bool(row.get("started_at"))),
                       "reported_retry_wait_seconds": run.wait_hint(job)}
                    | (usage or {}))
    return rows


def time_span(rows, waits):
    starts = [datetime.fromisoformat(row["started_at"]) for row in rows if row["started_at"]]
    ends = [datetime.fromisoformat(row["finished_at"]) for row in (*rows, *waits) if row.get("finished_at")]
    return round((max(ends) - min(starts)).total_seconds(), 3) if starts and ends else None


def effort(rows):
    launched = [row for row in rows if row["launched"]]
    elapsed = [row["elapsed_seconds"] for row in launched if row["elapsed_seconds"] is not None]
    metered = [row for row in launched if row["input_tokens"] is not None]
    return {
        "launched": len(launched), "completed": sum(row["status"] == "completed" for row in launched),
        "timeouts": sum(row["status"] == "timeout" for row in launched),
        "availability_failures": sum(row["reason"] in run.equal.AVAILABILITY_ERRORS for row in launched),
        "metered_calls": len(metered), "observed_call_seconds": round(sum(elapsed), 3),
        "observed_time_calls": len(elapsed),
        "tokens": {field: sum(row[field] for row in metered) for field in review.USAGE} if metered else None,
    }


def summary_data(cases, origin, rows, waits, reviews):
    first = sum(name == "first" for name in origin.values())
    reviewed = sum(all((key, arm) in reviews for arm in run.equal.ARMS) for key in origin)
    return {
        "planned_cases": len(cases), "first_complete_pairs": first, "complete_pairs_with_recovery": len(origin),
        "recovered_pairs": len(origin) - first, "recovery_passed": len(origin) == len(cases),
        "per_case_selected_round": {key: origin.get(key) for key in cases},
        "total": effort(rows),
        "by_round": {name: effort([row for row in rows if row["round"] == name]) for name in run.ROUNDS},
        "by_arm": {arm: effort([row for row in rows if row["call"] == arm]) for arm in run.equal.ARMS},
        "batch_wall_seconds": time_span(rows, waits),
        "cooldowns_completed": sum(row["status"] == "completed" for row in waits),
        "cooldowns_blocked": sum(row["status"] == "blocked" for row in waits),
        "cooldown_seconds": round(sum(row.get("elapsed_seconds", 0) for row in waits), 3),
        "human_review_ready_pairs": len(origin), "human_reviewed_pairs": reviewed,
        "human_review_pending_pairs": len(origin) - reviewed, "new_model_reviewed_pairs": 0,
        "holdout_started_cases": 0, "prospective_resolved_cases": 0,
    }


def table_token_text(row):
    return f"{row['tokens']['input_tokens']:,}／{row['tokens']['output_tokens']:,}" if row["tokens"] else "—"


def write_report(out, cases, calls, waits, summary, protocol):
    count = summary["planned_cases"]
    lines = [
        "# V9 限流後成對復原",
        "",
        f"**首次完整配對 {summary['first_complete_pairs']}/{count}。"
        f"固定復原預算內 {summary['complete_pairs_with_recovery']}/{count}。"
        f"復原流程{'通過' if summary['recovery_passed'] else '未通過'}。**",
        "",
        "四案沿用相同的 V9 生成提示與點時證據，兩組使用相同 Astra medium、單工、不搜尋，單次上限 180 秒。"
        "每案復原至多一次，兩組重生成且交換呼叫順序。同一輪兩組完成才納入覆核。",
        "",
        "| 案例 | 首次 Astra／V9 | 復原 Astra／V9 | 可送評輪次 |",
        "|---|---|---|---|",
    ]
    for key, case in cases.items():
        states = ["／".join(review.STATUSES[calls[key, name, arm]["status"]] for arm in run.equal.ARMS)
                  for name in run.ROUNDS]
        selected = ROUND_LABELS.get(summary["per_case_selected_round"][key], "—")
        lines.append(f"| {key} {case['input']['target']} | {states[0]} | {states[1]} | {selected} |")
    lines += [
        "", "## 呼叫與冷卻", "",
        "| 範圍 | 啟動／完成 | 逾時／容量類失敗 | 已回報詞元的呼叫 | 輸入／輸出詞元 | 已知呼叫秒數 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, row in [(ROUND_LABELS[key], summary["by_round"][key]) for key in run.ROUNDS] + [
        (review.LABELS[key], summary["by_arm"][key]) for key in run.equal.ARMS
    ] + [("總計", summary["total"])]:
        lines.append(f"| {label} | {row['launched']}／{row['completed']} | {row['timeouts']}／{row['availability_failures']} | "
                     f"{row['metered_calls']} | {table_token_text(row)} | {row['observed_call_seconds']:.2f} |")
    if waits:
        lines += ["", "| 案例與輪次 | 觸發 | 公告等待秒數 | 冷卻決策 | 實際冷卻秒數 |",
                  "|---|---|---:|---|---:|"]
        for row in waits:
            seconds = row.get("elapsed_seconds", "—")
            hint = row["reported_wait_seconds"] if row["reported_wait_seconds"] is not None else "—"
            status = WAIT_LABELS[row["status"]]
            lines.append(f"| {row['case']} {ROUND_LABELS[row['round']]} | {CAUSES[row['cause']]} | "
                         f"{hint} | {status} | {seconds} |")
    else:
        lines += ["", "本輪沒有觸發冷卻。"]
    if summary["batch_wall_seconds"] is not None:
        lines += ["", f"批次從第一次啟動至最後一筆記錄共 {summary['batch_wall_seconds']:.2f} 秒，"
                  f"其中已完成冷卻共 {summary['cooldown_seconds']:.2f} 秒。冷卻牆鐘包含程序停機時間。"]
    lines += [
        "", "帳本保留首次與復原的全部啟動紀錄。CLI 未回報用量或耗時的欄位留白。"
        "公告冷卻超過 900 秒即停止派發。缺少公告等待時採 30 秒。", "",
        "## 分析師覆核", "",
        f"可送評 {summary['human_review_ready_pairs']} 案。已收到完整兩組人工評分 {summary['human_reviewed_pairs']} 案，"
        f"待評 {summary['human_review_pending_pairs']} 案。本輪新模型評分 0 案，保留集啟動 0 案，前瞻實績 0 案。",
        "", "評分者使用匿名 PDF 和空白覆核表。完整 QA 供評分後查核。", "",
        f"封存時間（UTC）　{protocol['sealed_at']}。", "",
        "- [評測 PDF](report.pdf) · [完整 QA](QA.md) · [QA PDF](qa-records.pdf)",
        "- [預註冊](protocol.json) · [封存案例](cases.json) · [兩組原始請求](requests.json) · [數字摘要](summary.json)",
        "- [呼叫帳本](execution.csv) · [冷卻帳本](cooldowns.csv) · [逐案評分](scores.csv)",
        "- [分析師匿名 PDF](analyst-review.pdf) · [空白評分表](review-form.csv)",
    ]
    review.write_text(out / "README.md", lines)


def write_qa(out, cases, calls, origin):
    lines = ["# V9 限流後成對復原逐案 QA", "",
             "逐次保存所有已啟動呼叫。分析師覆核使用獨立的匿名資料。", ""]
    for key, case in cases.items():
        lines += [f"## {key} · {case['name']}", "", f"**採用輪次**　{ROUND_LABELS.get(origin.get(key), '缺少完整配對')}。", ""]
        lines += review.research_input(case)
        for name in run.ROUNDS:
            for arm in run.equal.ARMS:
                row = calls[key, name, arm]
                status = review.STATUSES[row["status"]]
                lines += [f"### {ROUND_LABELS[name]} · {review.LABELS[arm]}", "", f"**狀態**　{status}。", ""]
                if reason := row.get("reason"):
                    lines += [f"**執行原因**　{CAUSES.get(reason, reason)}。", ""]
                if links := review.call_links(out, f"raw/{name}", key, arm, "逐次回傳"):
                    lines += [links, ""]
                if row.get("hypotheses"):
                    lines += review.hypothesis_lines(row["hypotheses"])
    review.write_text(out / "QA.md", lines)


def publish(root, cases, out, ratings):
    out.mkdir(parents=True, exist_ok=True)
    protocol = run.read(root / "protocol.json")
    calls = run.records(root, cases)
    selected, origin = select_pairs(cases, calls)
    mapping = review.anonymous_keys(root, selected)
    reviews = review.import_ratings(ratings, selected, mapping)
    rows = call_ledger(root, calls)
    waits = [run.read(path) for path in sorted((root / "cooldowns").glob("*.json"))]
    summary = summary_data(cases, origin, rows, waits, reviews)
    for folder in (*run.ROUNDS, "cooldowns"):
        if (root / folder).exists():
            shutil.copytree(root / folder, out / "raw" / folder, dirs_exist_ok=True)
    for name in ("protocol.json", "cases.json", "requests.json"):
        shutil.copyfile(root / name, out / name)
    review.write_csv(out / "execution.csv", LEDGER, rows)
    review.write_csv(out / "cooldowns.csv", WAITS, waits)
    score_fields = (*review.RATINGS, "ready", "major_errors", "edit_seconds")
    review.write_csv(out / "scores.csv", ("case", "round", "arm", "generation_status", "selected_for_review", *score_fields), [
        {"case": key, "round": name, "arm": arm, "generation_status": row["status"],
         "selected_for_review": int(name == origin.get(key))}
        | {field: reviews.get((key, arm), {}).get(field) for field in score_fields if name == origin.get(key)}
        for (key, name, arm), row in calls.items()
    ])
    review.blind_files(out, selected, mapping)
    write_qa(out, cases, calls, origin)
    run.atomic(out / "summary.json", summary)
    write_report(out, cases, calls, waits, summary, protocol)
