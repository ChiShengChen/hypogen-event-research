"""Export the V9 paired benchmark and import human ratings with a local review key."""

import csv
from pathlib import Path
import re
import secrets
import shutil
from statistics import mean, median

from benchmarks import hypothesis_pilot as hypothesis
from benchmarks import v9_equal as run
from benchmarks.earnings_execution import atomic


REF = Path("docs/v9-four-case-review/raw/reference")
LABELS = {"astra": "純 Astra", "v9": "V9 Harness"}
STATUSES = {"completed": "完成", "timeout": "逾時", "interrupted": "中斷",
            "error": "失敗", "queued": "排隊未開始", "unplanned": "未排入"}
TEXT_FIELDS = {"company": "公司", "mechanism": "傳導", "catalyst": "催化劑",
               "prediction": "可查核預測", "invalidation": "失效條件", "materiality": "影響規模",
               "evidence_ids": "證據"}
RATINGS = ("citations", "mechanism", "testable_prediction", "invalidation")
REVIEW_FIELDS = ("case", "code", "analyst_id", *RATINGS, "major_errors", "ready", "edit_seconds", "notes")
USAGE = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
RETRY_DELAY = re.compile(r"retrying sampling request .*? in ([0-9.]+)s\).*?sampling_error=(.*)")


def write_text(path, lines):
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_calls(root, cases):
    calls = {}
    for key, case in cases.items():
        for arm in (*run.ARMS, *run.JUDGES):
            record = run.receipt(root, key, arm)
            if not record:
                job = root / "jobs" / f"{key}-{arm}"
                record = run.journal.restore(root, job) if (job / "state.json").exists() else {"status": "unplanned"}
            calls[key, arm] = {"case": key, "phase": case["split"], "call": arm} | record
    return calls


def arm_pairs(calls, key):
    return {arm: calls[key, arm].get("hypotheses") for arm in run.ARMS
            if calls[key, arm]["status"] == "completed"}


def model_scores(cases, calls):
    rows = {}
    for key, case in cases.items():
        if any(calls[key, judge]["status"] != "completed" for judge in run.JUDGES):
            continue
        visible = {row["id"] for row in case["input"]["evidence"]}
        future = {row["id"] for row in case["judge_only"]}
        for label, arm in run.judge_mapping(key).items():
            ratings = [calls[key, judge]["ratings"][label] for judge in run.JUDGES]
            scores = {field: mean(rating[field] for rating in ratings) for field in hypothesis.DIMENSIONS}
            rows[key, arm] = {"dimensions": scores, "score": sum(scores.values()),
                              "gate": hypothesis.disqualified(calls[key, arm]["hypotheses"], ratings, visible, future)}
    return rows


def review_set(cases, calls):
    selected = {}
    for key, case in cases.items():
        pairs = arm_pairs(calls, key)
        if len(pairs) == 2:
            selected[key] = (case, pairs)
    if any(case["split"] == "pilot" and key not in selected for key, case in cases.items()):
        # Keep earlier complete examples usable as calibration while the new formal comparison is blocked.
        for key, case in cases.items():
            if case["split"] != "pilot":
                continue
            pairs = {arm: hypothesis.read(REF / key / f"{style}.json")["hypotheses"]
                     for arm, style in (("astra", "astra-direct"), ("v9", "current-harness"))}
            selected[f"C-{key}"] = (case | {"split": "calibration"}, pairs)
    return selected


def anonymous_keys(root, selected):
    # Keep the alias order unchanged if a report is re-exported after more calls or reviews.
    path = root / "review-key.restricted.json"
    mapping = hypothesis.read(path)
    rng = secrets.SystemRandom()
    used = {code for case in mapping.values() for code in case}
    for key, (_, pairs) in selected.items():
        if key in mapping:
            if {entry["arm"]: entry["answer_sha256"] for entry in mapping[key].values()} != {
                arm: run.digest(run.scoreable_pair(pair)) for arm, pair in pairs.items()
            }:
                raise ValueError(f"覆核包的既有回覆已變動 {key}")
            continue
        arms = list(run.ARMS)
        rng.shuffle(arms)
        mapping[key] = {}
        for arm in arms:
            code = f"R{rng.randrange(1000, 10000)}"
            while code in used:
                code = f"R{rng.randrange(1000, 10000)}"
            used.add(code)
            mapping[key][code] = {"arm": arm, "answer_sha256": run.digest(run.scoreable_pair(pairs[arm]))}
    if mapping:
        atomic(path, mapping)
        path.chmod(0o600)
    return mapping


def import_ratings(path, selected, mapping):
    reviews = {}
    if path is None:
        return reviews
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REVIEW_FIELDS:
            raise ValueError("人工覆核 CSV 欄位不符")
        for row in reader:
            key, code, analyst = row["case"], row["code"], row["analyst_id"].strip()
            if key not in selected or code not in mapping.get(key, {}):
                raise ValueError("人工覆核 CSV 含未知的匿名代碼")
            if not any(row[field] for field in REVIEW_FIELDS[2:]):
                continue
            if not analyst or any(row[field] not in {"0", "1"} for field in (*RATINGS, "ready")):
                raise ValueError(f"{key}/{code} 須填覆核者代號及各項 0 或 1")
            try:
                major, seconds = int(row["major_errors"]), int(row["edit_seconds"])
            except ValueError as exc:
                raise ValueError(f"{key}/{code} 錯誤數及秒數須為整數") from exc
            all_checks = all(row[field] == "1" for field in RATINGS)
            if min(major, seconds) < 0 or (row["ready"] == "1") != (all_checks and major == 0):
                raise ValueError(f"{key}/{code} 覆核判定和核對項目不一致")
            arm = mapping[key][code]["arm"]
            if (key, arm) in reviews:
                raise ValueError(f"{key}/{code} 人工評分重複")
            reviews[key, arm] = {"analyst_id": analyst, "major_errors": major, "edit_seconds": seconds,
                                 "ready": int(row["ready"]), **{field: int(row[field]) for field in RATINGS}}
    for key in selected:
        if all((key, arm) in reviews for arm in run.ARMS) and len({
            reviews[key, arm]["analyst_id"] for arm in run.ARMS
        }) != 1:
            raise ValueError(f"{key} 兩組須由同一位分析師獨立評分")
    return reviews


def research_input(case):
    row = case["input"]
    lines = [f"**研究題目**　{row['event_text']}", f"**截止時間**　{row['as_of']}。**研究期間**　{row['horizon']}。", ""]
    for item in row["evidence"]:
        lines += [f"- **{item['id']}**　{item['quote']} [原始來源]({item['source']})"]
        anchor = case["anchors"].get(item["id"])
        if anchor:
            lines += [f"  - 原文短節錄：{anchor}"]
    return lines + [""]


def hypothesis_lines(pair):
    lines = []
    for index, item in enumerate(pair.values(), 1):
        lines += [f"**假說 {index}**", ""]
        for field, value in item.items():
            label = TEXT_FIELDS[field]
            text = "、".join(value) or "—" if field == "evidence_ids" else value
            lines.append(f"- **{label}**　{text}")
        lines += [""]
    return lines


def blind_files(out, selected, mapping):
    lines = [
        "# 研究首稿匿名覆核", "",
        "請獨立評分同案兩份首稿，兩份使用相同的題目和當時可得證據。原始來源可點開查核。每份首稿的假說均按相同欄位呈現。", "",
        "1. 在評分表填寫覆核者代號。每案兩份由同一位分析師評分。",
        "2. 依序核對引文支持、因果機制、可驗證預測、失效條件。每項兩條假說皆具備才填 1，其餘填 0。",
        f"3. 填寫重大錯誤件數。定義是{run.REVIEW_RULES['major_error']}",
        f"4. 準備度填 1 的條件是{run.REVIEW_RULES['ready']} 其餘填 0。",
        "5. 記錄完成必要修稿所需整數秒數。備註可列出錯誤與證據編號。", "",
    ]
    rows = []
    names = {"pilot": "先導", "holdout": "正式保留集", "calibration": "封存校準"}
    for key, (case, pairs) in selected.items():
        lines.extend([f"## {key} · {case['name']}", "", f"**用途**　{names[case['split']]}", ""])
        lines += research_input(case)
        for code, entry in mapping[key].items():
            lines.extend([f"### 首稿 {code}", ""])
            lines += hypothesis_lines(run.scoreable_pair(pairs[entry["arm"]]))
            rows.append({"case": key, "code": code})
    write_text(out / "analyst-review.md", lines)
    write_csv(out / "review-form.csv", REVIEW_FIELDS, rows)


def aggregate(calls, keys, arm):
    records = [calls[key, arm] for key in keys]
    completed = [row for row in records if row["status"] == "completed"]
    usage = [row["usage"] for row in records if row.get("usage") and "turn.completed" in row["event_seconds"]]
    seconds = [row["elapsed_seconds"] for row in completed]
    return {"completed": len(completed), "started": sum(bool(row.get("started_at")) for row in records),
            "timeouts": sum(row["status"] == "timeout" for row in records),
            "failed": sum(row["status"] in {"interrupted", "error"} for row in records),
            "tokens_observed": len(usage), "usage": {field: sum(row[field] for row in usage) for field in USAGE}
            if usage else None, "median_completed_seconds": round(median(seconds), 2) if seconds else None}


def review_metrics(cases, calls, reviews):
    result = {}
    for split in ("pilot", "holdout"):
        ids = [key for key, case in cases.items() if case["split"] == split]
        completed = [key for key in ids if len(arm_pairs(calls, key)) == 2]
        rated = [key for key in completed if all((key, arm) in reviews for arm in run.ARMS)]
        arms = {}
        for arm in run.ARMS:
            values = [reviews[key, arm] for key in rated]
            arms[arm] = {
                "ready": sum(row["ready"] for row in values),
                "major_errors": sum(row["major_errors"] for row in values),
                "median_edit_seconds": median(row["edit_seconds"] for row in values) if values else None,
            }
        result[split] = {"planned": len(ids), "complete_pairs": len(completed), "human_pairs": len(rated),
                         "available_for_review": len(completed) - len(rated),
                         "arms": {arm: aggregate(calls, ids, arm) | arms[arm] for arm in run.ARMS}}
    hold = result["holdout"]
    rules = run.REVIEW_RULES["gate"]
    v9, astra = (hold["arms"][arm] for arm in ("v9", "astra"))
    result["passed"] = (
        v9["ready"] >= rules["v9_ready_min"] and v9["ready"] - astra["ready"] >= rules["v9_ready_lead"]
        and v9["major_errors"] <= astra["major_errors"]
    ) if hold["complete_pairs"] == rules["complete_pairs"] and hold["human_pairs"] == rules["reviewed_pairs"] else None
    return result


def preserve_records(root, out):
    controlled = root / "controlled-stop.json"
    if controlled.exists():
        shutil.copyfile(controlled, out / controlled.name)
    for folder in ("batches", "calls"):
        source = root / folder
        if source.exists():
            shutil.copytree(source, out / "raw" / folder, dirs_exist_ok=True)
    for source in (root / "jobs").glob("*"):
        target = out / "raw" / "jobs" / source.name
        target.mkdir(parents=True, exist_ok=True)
        for name in ("state.json", "answer.json", "events.jsonl", "stderr.log", "request.json"):
            if (source / name).exists():
                shutil.copyfile(source / name, target / name)


def ledger_and_scorecards(out, calls, scores, reviews):
    ledger = []
    for (key, arm), row in calls.items():
        if arm in run.JUDGES and row["status"] == "unplanned":
            continue
        usage = row.get("usage") if "turn.completed" in row.get("event_seconds", {}) else None
        ledger.append({field: row.get(field) for field in (
            "case", "phase", "call", "status", "reason", "queued_at", "started_at", "finished_at",
            "queue_seconds", "preparation_seconds", "elapsed_seconds", "cli_elapsed_seconds", "prompt_bytes",
            "request_sha256",
        )} | (usage or {}))
    write_csv(out / "execution.csv", ("case", "phase", "call", "status", "reason", "queued_at", "started_at",
              "finished_at", "queue_seconds", "preparation_seconds", "elapsed_seconds", "cli_elapsed_seconds",
              "prompt_bytes", "request_sha256", *USAGE), ledger)
    rows = []
    for (key, arm), row in calls.items():
        if arm not in run.ARMS:
            continue
        model, human = scores.get((key, arm), {}), reviews.get((key, arm), {})
        rows.append({"case": key, "phase": row["phase"], "arm": arm, "generation_status": row["status"],
                     "model_score": model.get("score"), "model_disqualified": bool(model["gate"]["candidates"])
                     if model else None, **{field: human.get(field) for field in (*RATINGS, "ready", "major_errors", "edit_seconds")}})
    write_csv(out / "scores.csv", ("case", "phase", "arm", "generation_status", "model_score",
              "model_disqualified", *RATINGS, "ready", "major_errors", "edit_seconds"), rows)


def qa_file(out, cases, calls, scores):
    lines = [
        "# V9 等預算逐案問答", "",
        "此紀錄供結果查核。匿名人評應使用獨立的匿名 PDF 和空白表。下列為生成時點可見的封存摘要，並附原文摘錄與可開啟的原始公告。", "",
    ]
    for key, case in cases.items():
        lines.extend([f"## {key} · {case['name']}", "", f"**分組**　{case['split']}", ""])
        lines += research_input(case)
        for arm in run.ARMS:
            row = calls[key, arm]
            lines.extend([f"### {LABELS[arm]}", "", f"**執行狀態**　{STATUSES[row['status']]}。", ""])
            records = {f"raw/calls/{key}-{arm}.json": "正式回傳",
                       f"raw/jobs/{key}-{arm}/events.jsonl": "CLI 事件",
                       f"raw/jobs/{key}-{arm}/answer.json": "模型原始 JSON",
                       f"raw/jobs/{key}-{arm}/stderr.log": "CLI 診斷"}
            links = [f"[{label}]({path})" for path, label in records.items() if (out / path).exists()
                     and (out / path).stat().st_size]
            if links:
                lines.extend([" · ".join(links), ""])
            if row.get("error"):
                lines.extend([f"**失敗原因**　{row['error']}", ""])
            if row.get("hypotheses"):
                lines += hypothesis_lines(row["hypotheses"])
            if model := scores.get((key, arm)):
                lines.extend([f"**雙順序模型評分**　{model['score']}/10。", ""])
                judge_paths = [f"[順序 {index}](raw/calls/{key}-{judge}.json)"
                               for index, judge in enumerate(run.JUDGES, 1)]
                lines.extend([" · ".join(judge_paths), ""])
    write_text(out / "QA.md", lines)


def diagnostic_lines(root, calls):
    lines = []
    for (key, arm), row in calls.items():
        if row["status"] not in {"timeout", "interrupted", "error"}:
            continue
        path = Path("jobs") / f"{key}-{arm}" / "stderr.log"
        log = root / path
        retries = RETRY_DELAY.findall(log.read_text(encoding="utf-8", errors="replace")) if log.exists() else []
        detail = f"CLI 宣告等待 {float(retries[-1][0]):.1f} 秒後重試" if retries else ""
        if detail and "at capacity" in retries[-1][1]:
            detail += "，訊息指出該模型已達容量"
        label = LABELS.get(arm, arm)
        diagnostics = f" [CLI 紀錄](raw/{path})" if log.exists() and log.stat().st_size else ""
        lines.append(f"- {key} {label}，{STATUSES[row['status']]}。" + (f"{detail}。" if detail else "") + diagnostics)
    return lines


def report_lines(root, summary, model_count, calibration, calls):
    protocol = hypothesis.read(root / "protocol.json")
    pilot, holdout = (summary[split] for split in ("pilot", "holdout"))
    gates = {True: "通過", False: "未通過", None: "待完成"}
    table = ["| 階段 | 完整配對 | 人工盲評配對 | 可交覆核的配對 |",
             "|---|---:|---:|---:|"]
    for label, split in (("先導", pilot), ("保留集", holdout)):
        planned = split["planned"]
        table += [f"| {label} | {split['complete_pairs']}/{planned} | {split['human_pairs']}/{planned} | "
                  f"{split['available_for_review']} |"]
    lines = [
        "# V9 等預算研究首稿評測", "",
        f"**先導門檻{'通過' if pilot['complete_pairs'] == pilot['planned'] else '未通過'}。"
        f"人工驗收{gates[summary['passed']]}。** 兩組維持原生成提示，使用相同的 Astra medium、點時證據和 180 秒 CLI 上限，各一次啟動。"
        "程式停用搜尋，詞元採實耗紀錄，服務端詞元及 CLI 內部重試沒有可強制上限。", "",
        *table, "",
        f"新雙順序模型評分已完成 {model_count} 案。前瞻實績完成 0 案，這批為歷史時點回放。"
        f"匿名包另有 {calibration} 個先前封存的校準案例，供評分者試填。", "",
        "| 階段與組別 | 啟動 | 完成 | 逾時 | 其他失敗 | 完成回覆中位秒數 | 詞元回合 | 輸入／輸出詞元 | 人工可用率 | 重大錯誤 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, split in (("先導", pilot), ("保留集", holdout)):
        for arm, row in split["arms"].items():
            usage = row["usage"] or {}
            values = [row["started"], row["completed"], row["timeouts"], row["failed"], row["median_completed_seconds"],
                      row["tokens_observed"], f"{usage['input_tokens']}／{usage['output_tokens']}" if usage else None,
                      f"{row['ready']}/{split['human_pairs']}" if split["human_pairs"] else None,
                      row["major_errors"] if split["human_pairs"] else None]
            lines.append(f"| {label} {LABELS[arm]} | " + " | ".join("—" if v is None else str(v) for v in values) + " |")
    if diagnostics := diagnostic_lines(root, calls):
        lines += ["", "## 失敗紀錄", "", *diagnostics]
    if intervention := hypothesis.read(root / "controlled-stop.json"):
        lines += ["", f"{intervention['job']} 的 stderr 回報 HTTP 429，但當時的 JSON 事件只記了回合開始。"
                  "實際執行依預註冊以 SIGTERM 停止，原紀錄標為中斷並保留。"
                  "程式後續加入 stderr 自動停派測試。 [停止決策紀錄](controlled-stop.json)"]
    lines += [
        "", "## 方法與採用門檻", "", f"封存時間（UTC）　{protocol['sealed_at']}。輸入與請求分別由預註冊檔記錄 SHA-256。", "",
        "保留集主指標採分析師判定。通過要求八案完整配對且評完，V9 至少六案可用，至少領先兩案，重大錯誤數至多與純 Astra 相同。"
        "逐次帳本保留快取與推理詞元欄位。欄位空白代表 CLI 未回報可用用量。180 秒到期即發送終止訊號，耗時包含輪詢與清理。", "",
        "封存材料包含同日可得的繁體中文摘要、可開啟的發行人或監管機構原文連結及短節錄。模型只使用封存摘要。"
        "回放可檢查引文與時點紀律，模型預訓練所知的後續歷史無法從回放排除。", "",
        "覆核時請只提供匿名 PDF 與評分表，收回表單後再與公開逐案材料核對。", "",
        "- [評測 PDF](report.pdf) · [逐案完整 QA](QA.md) · [QA PDF](qa-records.pdf) · [逐案評分](scores.csv)",
        "- [預註冊](protocol.json) · [封存案例](cases.json) · [送出請求](requests.json) · [執行帳本](execution.csv) · [摘要數據](summary.json)",
        "- [分析師匿名 PDF](analyst-review.pdf) · [空白評分表](review-form.csv)",
    ]
    return lines


def publish(root, cases, out, ratings=None):
    out.mkdir(parents=True, exist_ok=True)
    calls = read_calls(root, cases)
    scores = model_scores(cases, calls)
    selected = review_set(cases, calls)
    mapping = anonymous_keys(root, selected)
    reviews = import_ratings(ratings, selected, mapping)
    summary = review_metrics(cases, calls, reviews)
    model_count = len(scores) // 2
    calibration = sum(case["split"] == "calibration" for case, _ in selected.values())
    summary.update(model_pairs=model_count, prospective_resolved=0, calibration_pairs=calibration,
                   calibration_human_pairs=sum(all((key, arm) in reviews for arm in run.ARMS)
                                               for key in selected if key.startswith("C-")))
    for name in ("protocol.json", "cases.json", "requests.json"):
        shutil.copyfile(root / name, out / name)
    preserve_records(root, out)
    ledger_and_scorecards(out, calls, scores, reviews)
    blind_files(out, selected, mapping)
    qa_file(out, cases, calls, scores)
    atomic(out / "summary.json", summary)
    write_text(out / "README.md", report_lines(root, summary, model_count, calibration, calls))
