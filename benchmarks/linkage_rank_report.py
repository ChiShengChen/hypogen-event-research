"""Export ranking results, the execution ledger and independently blinded analyst drafts."""

import os
from pathlib import Path
import secrets
import shutil

from benchmarks import linkage_rank as rank
from benchmarks.linkage_depth_report import DIMENSIONS, aggregate, findings_lines, input_lines
from benchmarks.v9_equal_review import STATUSES, USAGE, call_links, write_csv, write_text

ARMS = ("ranked", "current", "astra")
NAMES = {"ranked": "新版 Harness V11", "current": "現版 Harness V10", "astra": "純 Astra", "judge": "匿名 Sol"}
SPLITS = {"pilot": "先導", "holdout": "保留集", "regression": "回歸"}
DIMENSIONS = DIMENSIONS | {"selection": "漏選主要傳導"}
HYPOTHESIS_FIELDS = {
    "mechanism": "傳導機制", "target": "標的", "horizon": "研究期限", "catalyst": "催化劑",
    "prediction": "預測", "invalidation": "推翻條件",
}
CALL_FIELDS = ("case", "split", "call", "status", "reused", "reason", "availability_source", "queued_at", "started_at",
               "finished_at", "queue_seconds", "preparation_seconds", "cli_elapsed_seconds", "elapsed_seconds",
               "prompt_bytes", "reported_wait_seconds", "cooldown_seconds", "request_sha256", *USAGE)


def read_receipts(root, cases):
    records = {}
    for key, case in cases.items():
        for arm in (*rank.ARMS, "judge"):
            row = rank.receipt(root, key, arm, case)
            job = root / "jobs" / f"{key}-{arm}"
            if not row and (job / "state.json").exists():
                row = rank.equal.journal.restore(root, job)
            records[key, arm] = row or {"status": "unplanned"}
    return records


def blind(out, root, cases, receipts):
    key_path = root / "review-key.restricted.json"
    mapping = rank.equal.hypothesis.read(key_path)
    lines = [
        "# 主要財務傳導 · 匿名分析師覆核", "",
        "每案三份研究稿採相同點時證據。依稿內順序，核對兩端引文、必要因果條件、財務歸因、"
        "以及能區別至少一種其他解釋的公開查核。請指出最值得查核的傳導，以及稿件將它排在第幾位。"
        "若因果尚未建立，請核對稿件是否指出具體缺項並保留歸因。", "",
        "每份稿件記錄能否進入分析師覆核、重大錯誤、必要修稿時間（秒）及理由。"
        "所有二元項填 1 或 0，無適用項目請留白並說明。每案三份全部回收才計為一案完成。"
        "請在填表前獨立閱讀本 PDF。", "",
    ]
    rng = secrets.SystemRandom()
    rows = []
    for key, case in cases.items():
        if case["split"] == "regression" or any(receipts[key, arm]["status"] != "completed" for arm in ARMS):
            continue
        findings = {arm: rank.anonymous(receipts[key, arm]["findings"]) for arm in ARMS}
        digests = {arm: rank.equal.digest(payload) for arm, payload in findings.items()}
        if key not in mapping:
            shuffled = list(ARMS)
            rng.shuffle(shuffled)
            mapping[key] = {f"D-{secrets.token_hex(4).upper()}": {"arm": arm, "sha256": digests[arm]}
                            for arm in shuffled}
        elif {row["arm"]: row["sha256"] for row in mapping[key].values()} != digests:
            raise ValueError("已產生的匿名稿遭變更")
        lines.extend([f"## {key} · {case['issuer']}", "", *input_lines(case)])
        for alias, row in mapping[key].items():
            lines.extend([f"### 研究稿 {alias}", "", *findings_lines(findings[row["arm"]])])
            if not any(findings[row["arm"]].values()):
                lines.extend(["未提交連動或證據缺口。", ""])
            rows.append({"case": key, "draft": alias})
    if mapping:
        rank.equal.journal.atomic(key_path, mapping)
        key_path.chmod(0o600)
    if not rows:
        lines.append("目前沒有三稿齊全的正式案例。")
    write_text(out / "analyst-review.md", lines)
    write_csv(out / "review-form.csv",
              ("case", "draft", "analyst_id", *rank.depth.CHECKS, "gap_correct", "principal_rank", "major_error",
               "ready_for_review", "edit_seconds", "notes"), rows)
    return len(rows) // len(ARMS)


def ledgers(out, root, cases, grades, receipts):
    calls, checks, scores = [], [], []
    for (key, arm), row in receipts.items():
        case = cases[key]
        reused = case["split"] == "regression" and arm in {"astra", "current"}
        old_arm = "harness" if arm == "current" else arm
        job = (rank.PREVIOUS / "raw" / "jobs" / f"{case['previous_case']}-{old_arm}"
               if reused else root / "jobs" / f"{key}-{arm}")
        cooldown = rank.equal.hypothesis.read(root / "cooldowns" / f"{job.name}.json") if not reused else {}
        calls.append({field: row.get(field) for field in CALL_FIELDS} | {
            "case": key, "split": case["split"], "call": arm, "reused": reused,
            "reported_wait_seconds": rank.equal.admission.wait_hint(job),
            "cooldown_seconds": cooldown.get("wait_seconds"),
        } | (row.get("usage") or {}))
        if arm == "judge":
            continue
        if row["status"] == "completed":
            for stage, field in (("raw", "raw_findings"), ("published", "findings")):
                paths = row[field]["business_linkages"]
                for check, path in zip(rank.depth.rule_check(paths, case), paths):
                    checks.append({"case": key, "arm": arm, "stage": stage,
                                   "ranking_reason": path.get("ranking_reason")} | check)
        score = (grades[key] or {}).get(arm, {})
        scores.append({
            "case": key, "split": case["split"], "arm": arm, "positive": case["gold"]["positive"],
            "status": row["status"], "exact": score.get("exact"), "major": score.get("major"),
            "principal_rank": score.get("principal_rank"), "qualified_rank": score.get("qualified_rank"),
            "raw_submitted": score.get("raw_submitted"), "published": score.get("submitted"),
            "failure": "、".join(DIMENSIONS[name] for name in score.get("failure_dimensions", ())),
            "gap_correct": score.get("verdict", {}).get("gap_ok"),
            "model_note": score.get("verdict", {}).get("note"), "human_score": None,
        })
    write_csv(out / "execution.csv", CALL_FIELDS, calls)
    write_csv(out / "rule-checks.csv", ("case", "arm", "stage", "index", "evidence", "time", "ranking_reason"), checks)
    write_csv(out / "scores.csv", ("case", "split", "arm", "positive", "status", "exact", "major", "principal_rank",
              "qualified_rank", "raw_submitted", "published", "failure", "gap_correct", "model_note", "human_score"), scores)
    return calls, checks


def raw_location(out, key, arm, case):
    if case.get("previous_case") and arm in {"astra", "current"}:
        return os.path.relpath(rank.PREVIOUS / "raw", out), f"{case['previous_case']}-{'harness' if arm == 'current' else arm}"
    return "raw", f"{key}-{arm}"


def raw_links(out, key, arm, case):
    base, call = raw_location(out, key, arm, case)
    key, arm = call.rsplit("-", 1)
    links = call_links(out, base, key, arm, "逐次回傳")
    request = f"{base}/jobs/{call}/request.json"
    return " · ".join(filter(None, (links, f"[完整請求]({request})" if (out / request).is_file() else "")))


def hypothesis_lines(out, key, arm, case):
    base, call = raw_location(out, key, arm, case)
    raw = rank.equal.hypothesis.read(out / base / "jobs" / call / "answer.json")
    lines = []
    for draft in raw.get("hypotheses", []):
        stance = {"bull": "多方", "bear": "空方", "wait": "觀望"}[draft["stance"]]
        lines.extend([f"**研究首稿 · {stance}**", ""])
        lines.extend(f"- {label}　{draft[field]}" for field, label in HYPOTHESIS_FIELDS.items())
        lines.extend(["- 模型引文　" + "、".join(draft["claim_ids"]), ""])
    return lines


def qa(out, cases, grades, receipts):
    lines = [
        "# 主要財務傳導排序 · 完整逐案 QA", "",
        "此份紀錄含評分與組別。匿名人工覆核使用獨立 PDF。模型收取的完整輸入與回傳可在各案連結下載。", "",
    ]
    for key, case in cases.items():
        lines.extend([f"## {key} · {case['issuer']} · {SPLITS[case['split']]}", "", *input_lines(case),
                      f"**預註冊標準**　{case['gold']['standard']}", ""])
        for arm in ARMS:
            row = receipts[key, arm]
            lines.extend([f"### {NAMES[arm]} · {STATUSES[row['status']]}", ""])
            if links := raw_links(out, key, arm, case):
                lines.extend([links, ""])
            if error := row.get("error"):
                lines.extend([f"執行紀錄　{error}", ""])
            if row["status"] != "completed":
                continue
            lines.extend(hypothesis_lines(out, key, arm, case))
            findings = row["findings"]
            lines.extend(findings_lines(findings))
            hidden = len(row["raw_findings"]["business_linkages"]) - len(findings["business_linkages"])
            if hidden:
                lines.extend([f"程式過濾 {hidden} 條候選，原稿保留於 JSON。", ""])
            for index, path in enumerate(findings["business_linkages"], 1):
                if reason := path.get("ranking_reason"):
                    lines.extend([f"- 第 {index} 條排序理由　{reason}", ""])
            if grade := grades[key]:
                score = grade[arm]
                exact = "全對" if score["exact"] else "未全對"
                lines.extend([f"**模型判讀**　{exact}。{score['verdict']['note']}", ""])
                if case["gold"]["positive"]:
                    lines.extend([f"主要傳導位置　{score['principal_rank'] or '未選入'}。"
                                  f"全項通過位置　{score['qualified_rank'] or '無'}。", ""])
                for candidate in score["verdict"]["candidates"]:
                    failed = "、".join(DIMENSIONS[field] for field in rank.depth.CHECKS if not candidate[field])
                    lines.append(f"- 候選 {candidate['index']}　{failed or '四項語義均通過'}。{candidate['note']}")
                lines.append("")
        if links := raw_links(out, key, "judge", case):
            lines.extend([links, ""])
    write_text(out / "QA.md", lines)


def report(out, totals, cases, grades, calls, protocol):
    p, h, r = (totals[split] for split in ("pilot", "holdout", "regression"))
    lines = [
        "# 跨業務假說的主要財務傳導排序", "",
        f"**先導{'通過' if p['pass'] else '未通過'}，完整三稿 {p['paired']}/4。"
        f"保留集完整三稿 {h['paired']}/8，排序改善{'達標' if h['ranking_improved'] else '未達標'}，"
        f"相對純 Astra 的領先門檻{'達標' if h['leads_astra'] else '未達標'}。**", "",
        "上一輪保留集 V10 和純 Astra 各 6/8 全對。V10 正例 2/4，負例 4/4。純 Astra 正例 4/4，負例 2/4。"
        "本輪在單次呼叫內先找具名承諾、資源、營運與通路變動，按財務影響和可查核性選最多三條，每條附排序理由。", "",
        "| 階段及組別 | 全對 | 正例全對 | 負例全對 | 正例第 1 | 正例前 3 | 重大錯誤 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for split, row in (("先導", p), ("保留集", h), ("回歸", r)):
        for arm in ARMS:
            m = row["metrics"][arm]
            n = row["positive_planned"]
            values = [f"{m['exact']}/{row['planned']}", f"{m['positive']}/{n}", f"{m['negative']}/{n}",
                      f"{m['rank1']}/{n}", f"{m['top3']}/{n}", str(m["major"])]
            lines.append(f"| {split} · {NAMES[arm]} | " + " | ".join(values if row["graded"] else ["—"] * 6) + " |")
    lines.extend(["", f"先導完成匿名模型判讀 {p['graded']}/4，保留集 {h['graded']}/8，回歸 {r['graded']}/4。"
                  f"獨立分析師實際完成 {totals['human_completed']} 案，可送評 {totals['human_pending']} 案。前瞻實績完成 "
                  f"{totals['prospective_completed']} 案，本輪使用歷史回放。", ""])
    if h["graded"] == 8:
        lines.extend([
            f"新版相對現版的正例差額 {h['positive_delta_vs_current']:+d} 案，"
            f"負例差額 {h['negative_delta_vs_current']:+d} 案。相對純 Astra 全對數差額 {h['exact_delta_vs_astra']:+d} 案。", "",
        ])
    elif not p["pass"]:
        lines.extend(["依封存條件停止保留集派發。未執行案例保留在 QA 與帳本。", ""])
    lines.extend(["## 執行帳本", "",
                  "| 呼叫 | 啟動／完成 | 逾時／容量類失敗 | 有回報用量 | 輸入／輸出詞元 | 累計秒數 |",
                  "|---|---:|---:|---:|---:|---:|"])
    for batch, usage in totals["usage"].items():
        for arm in (*ARMS, "judge"):
            m = usage[arm]
            if batch == "regression" and arm in {"current", "astra"}:
                continue
            tokens = m["usage"]
            count = f"{tokens['input_tokens']:,}／{tokens['output_tokens']:,}" if tokens else "—"
            lines.append(f"| {SPLITS.get(batch, '正式')} · {NAMES[arm]} | {m['started']}／{m['returned']} | "
                         f"{m['timeout']}／{m['availability']} | {m['metered']} | {count} | {m['elapsed_seconds']:.2f} |")
    failures = [row for row in calls if row["status"] not in {"completed", "unplanned", "queued"} and not row["reused"]]
    if failures:
        lines.extend(["", "## 失敗回傳", ""])
        for row in failures:
            lines.append(f"- {row['case']} {NAMES[row['call']]}，{STATUSES[row['status']]}（{row['reason']}）。")
    lines.extend(["", "## 回歸與證據", ""])
    for key, case in cases.items():
        if case["split"] != "regression":
            continue
        grade = grades[key]
        detail = "尚無三稿判讀"
        if grade:
            detail = "，".join(f"{NAMES[arm]}{'全對' if grade[arm]['exact'] else '未全對'}" for arm in ARMS)
        lines.append(f"- {case['issuer']} · {detail}。")
    lines.extend([
        "",
        "回歸對照沿用上一輪來源及請求相符的原始 V10 與 Astra 回覆。新版另生成，三稿重做匿名 Sol 判讀。"
        "回歸與正式評分分開計算。新增耗時及詞元只計本輪啟動的呼叫。", "",
        f"發布候選的引文 ID 與期限程式核對共 {totals['rules_passed']}/{totals['rules_checked']} 條通過。"
        f"新版排序理由共 {totals['rank_reasons']}/{totals['rank_candidates']} 條發布候選有填寫。"
        "逐案全對由同一條候選通過語義與程式核對。主要傳導排名指判讀為命中目標路徑的第一條位置，另記全項通過的位置。", "",
        "正式三組各呼叫同一 Astra medium 一次，單工，停用搜尋，每次 180 秒。資料是封存的原文摘錄及同期披露摘要，"
        "附官方原文位置。新版多一個排序理由欄位，匿名判讀隱藏該欄。詞元是各回合實際回報值。", "",
        "IBM 的公告曾用於 V9 服務探針，保留集生成前已換成 Corning。CVS Health 的封存資料也已核對並限於交割日公告。"
        "原四案先導請求及門檻一致，所有開始的先導呼叫照計。"
        + (" [封存修訂帳本](amendment-transfer.json)" if (out / "amendment-transfer.json").is_file() else ""), "",
        f"封存時間（UTC）　{protocol['sealed_at']}。先導須四案三稿及判讀齊全、新版至少 3/4 且零重大錯誤。"
        "保留集須八案齊全、正負例各至少 3/4 且零重大錯誤。排序改善要求至少多對一個正例且負例維持。"
        "領先門檻要求比純 Astra 至少多兩案全對。", "",
        "- [評測 PDF](report.pdf) · [完整 QA PDF](qa-records.pdf) · [逐案 QA](QA.md)",
        "- [預註冊](protocol.json) · [點時原文和裁定](cases.json) · [完整請求](requests.json) · [原始回傳目錄](raw/)",
        "- [逐案評分](scores.csv) · [候選逐項評分](candidate-grades.json) · [程式核對](rule-checks.csv) · "
        "[執行帳本](execution.csv) · [摘要](summary.json)",
        "- [匿名分析師覆核 PDF](analyst-review.pdf) · [空白評分表](review-form.csv)",
    ])
    write_text(out / "README.md", lines)


def publish(root, cases, protocol, out):
    out.mkdir(parents=True, exist_ok=True)
    for name in ("protocol.json", "cases.json", "requests.json"):
        shutil.copyfile(root / name, out / name)
    if (root / "amendment-transfer.json").is_file():
        shutil.copyfile(root / "amendment-transfer.json", out / "amendment-transfer.json")
    if (root / "excluded-initial").is_dir():
        shutil.copytree(root / "excluded-initial", out / "raw" / "excluded-initial", dirs_exist_ok=True)
    receipts = read_receipts(root, cases)
    for folder in ("jobs", "calls", "cooldowns"):
        if (root / folder).is_dir():
            shutil.copytree(root / folder, out / "raw" / folder, dirs_exist_ok=True)
    grades, totals = rank.summary(root, cases, protocol)
    calls, checks = ledgers(out, root, cases, grades, receipts)
    published = [row for row in checks if row["stage"] == "published"]
    ranked = [row for row in published if row["arm"] == "ranked"]
    pending = blind(out, root, cases, receipts)
    totals |= {
        "human_completed": 0, "human_pending": pending, "prospective_completed": 0,
        "rules_checked": len(published), "rules_passed": sum(row["evidence"] and row["time"] for row in published),
        "rank_candidates": len(ranked), "rank_reasons": sum(bool(row["ranking_reason"]) for row in ranked),
        "usage": {
            group: {arm: aggregate([row for row in calls if row["call"] == arm and not row["reused"]
                                   and ((row["split"] == "regression") == (group == "regression"))])
                    for arm in (*ARMS, "judge")}
            for group in ("formal", "regression")
        },
    }
    rank.equal.journal.atomic(out / "summary.json", totals)
    rank.equal.journal.atomic(out / "candidate-grades.json", grades)
    qa(out, cases, grades, receipts)
    report(out, totals, cases, grades, calls, protocol)
