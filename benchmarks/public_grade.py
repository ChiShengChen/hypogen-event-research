"""Blind local scoring and paired question/answer exports for the public pilot."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import hashlib
import json
import os
from pathlib import Path
from statistics import median
from time import sleep
from typing import Literal

from pydantic import Field

from benchmarks.public_cases import load_cases, read_rows
from benchmarks.public_pilot import web_items, write_json
from research_app.adapters import AdapterError, Codex
from research_app.discovery import source_key
from research_app.research import document_evidence
from research_app.schema import Schema

JUDGE = "gpt-6.2-sol"
SUPPLY_RUBRIC_REVISION = 2
ARMS = ("direct", "harness")
DIMENSIONS = ("task", "evidence", "reasoning")
SUITES = ("FinanceBench", "FinSearchComp T3", "FinanceGym", "Supply chain")
GUIDE = {
    "FinanceBench": (
        "Task: judge the answer against the supplied reference, including sign, period and units. "
        "Evidence: check that cited excerpt IDs support the answer; ignore the experiment ingest dates. "
        "Reasoning: check the requested formula, operands and explanation; for a lookup assess the "
        "financial statement line and interpretation. Where primary evidence makes the gold ambiguous, mention it."
    ),
    "FinSearchComp T3": (
        "Task: check all requested items against the public reference, including any rounding tolerance. "
        "Evidence: judge whether observed citation excerpts support the specific figures and periods. "
        "Reasoning: check intermediate figures, calculation, scope, reconciliation or comparison. "
        "If the primary evidence contradicts the reference, flag it explicitly and assess against the stated question."
    ),
    "FinanceGym": (
        "There is no official rubric or gold in this sample. Task: answer the main question and each part "
        "with a concrete event-specific view. Evidence: use independent visible excerpts and cutoff dates; "
        "a date supplied by a respondent alone is not verification. Penalize demonstrated lookahead, "
        "flag undocumented dates separately and do not assume contamination from an unknown date. "
        "Reasoning: separate facts from conditional forecasts, assess mechanism, key risk and falsification."
    ),
    "Supply chain": (
        "Task: proactive discovery of named non-target companies, with roles and event-specific exposure. "
        "Evidence: assess actual support from source excerpts and flag unsupported supplier, customer, qualification, "
        "or order claims. Reasoning: assess whether the answer supplies a conditional earnings mechanism, an observable "
        "catalyst, an invalidation, and a materiality/valuation limit. For each answer, record distinct audited "
        "companies discussed as linked or peers, each named company's status, whether a full thesis is present, "
        "and 0-based reference indexes it actually establishes. A plausible explicitly labeled peer with no supply "
        "claim is insufficient for a gold supplier/customer hit. Accept other valid companies, but they have no gold index. "
        "Use independently checked reference passages only where the answer cited the matched URL."
        " Ignore bare mentions in evidence lists unless the answer makes a substantive claim about the company. "
        "Allow names or ticker aliases. Never infer that ZEISS SMT is listed or that product approval means an actual order."
    ),
}

SOURCE_ALIASES = {
    "https://nvidianews.nvidia.com/news/nvidia-blackwell-platform-arrives-to-power-a-new-era-of-computing":
        "https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Blackwell-Platform-Arrives-to-Power-a-New-Era-of-Computing/",
    "https://www.sec.gov/Archives/edgar/data/100517/000010051724000016/ual_12312023erex992.htm":
        "https://www.sec.gov/Archives/edgar/data/100517/000010051724000016/ual-20240122.htm",
}


class Company(Schema):
    name: str
    status: Literal["supported", "uncertain", "contradicted"]
    gold_indexes: list[int]
    actionable_research: bool
    rationale: str


class ArmGrade(Schema):
    task: int = Field(ge=0, le=2)
    evidence: int = Field(ge=0, le=2)
    reasoning: int = Field(ge=0, le=2)
    rationale: str
    companies: list[Company]


class Grade(Schema):
    a: ArmGrade
    b: ArmGrade


def excerpts(path, citations):
    keys = {source_key(row["ref"]) for row in citations}
    keys.discard(None)
    observed = {}
    if not keys:
        return observed
    for item in web_items(read_rows(path)):
        for hit in item.get("results", []):
            key = source_key(hit.get("url", ""))
            if key in keys:
                snippet = hit.get("snippet") or ""
                record = observed.setdefault(key, {
                    "url": hit["url"], "title": hit.get("title", ""), "excerpts": [],
                })
                if snippet and snippet not in record["excerpts"] and len(record["excerpts"]) < 3:
                    record["excerpts"].append(snippet[:850])
    return observed


def anonymize(case, result, path):
    answer = "\n".join(line for line in result["answer"].splitlines() if "生成模式為" not in line)
    citations = result["citations"]
    if case["suite"] == "Supply chain" and (report := result.get("report")):
        used_urls = {row["source"] for row in report["evidence"]
                     if f"[`{row['id']}`](#" in answer}
        citations = [citation for citation in citations if citation["ref"] in used_urls]
        answer = answer.split("\n## 證據快照", 1)[0]
    observed = excerpts(path, citations)
    checked = {}
    if case["suite"] == "Supply chain":
        for company, relationship, url in case["reference"]:
            checked.setdefault(source_key(url), []).append(f"{company}: {relationship}")
        for alias, original in SOURCE_ALIASES.items():
            if passages := checked.get(source_key(original)):
                checked[source_key(alias)] = passages
    return {
        "answer": answer,
        "citations": [
            {"ref": row["ref"], "claimed_date": row["published_on"],
             "claim": row["supports"][:350],
             "tool_evidence": observed.get(source_key(row["ref"])),
             "verified_primary_passage": checked.get(source_key(row["ref"]), [])}
            for row in citations
        ],
    }


def grade_case(case, output, results):
    order = ARMS if hashlib.sha256(case["id"].encode()).digest()[0] % 2 else ARMS[::-1]
    adapter = Codex(reasoning_effort="medium")
    result = adapter._generate(Grade, (
        "You are evaluating two anonymized answers independently as a skeptical financial research reviewer. "
        "Give each dimension 2 for complete, 1 for materially partial, 0 for missing or wrong, and explain "
        "the major reason in concise Traditional Chinese. Do not reward length, headings, or citation count. "
        "Citations supplied by respondents are claims: check them against shared input excerpts, actual "
        "web-tool excerpts, or independently verified primary passages. Lack of an excerpt is insufficient "
        "verification, not proof a relationship is false. "
        "Use a blank companies list except for Supply chain. The answer identities and order do not matter. "
        + GUIDE[case["suite"]]
    ), {
        "question": case["question"], "cutoff": case["cutoff"], "target": case["target"],
        "reference": case["reference"],
        "shared_evidence": [row for doc in case["docs"] for row in document_evidence(doc)],
        **{label: anonymize(case, results[arm], output / case["id"] / arm / "events.jsonl")
           for label, arm in zip(("a", "b"), order)},
    })
    grades = {arm: getattr(result, label).model_dump() for label, arm in zip(("a", "b"), order)}
    write_json(output / case["id"] / "grade.json", {
        "judge": JUDGE, "arms": grades, "supply_rubric_revision": SUPPLY_RUBRIC_REVISION,
    })
    return case["id"]


def read_result(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def snapshot(cases, output):
    rows = []
    for case in cases:
        folder = output / case["id"]
        grade = read_result(folder / "grade.json")
        if case["suite"] == "Supply chain" and grade.get("supply_rubric_revision") != SUPPLY_RUBRIC_REVISION:
            grade = {}
        rows.append({
            "case": case,
            "results": {arm: read_result(folder / arm / "result.json") for arm in ARMS},
            "grade": grade.get("arms"),
        })
    return rows


def total(grade):
    return sum(grade[key] for key in DIMENSIONS)


def score_delta(rows):
    differences = [total(row["grade"]["harness"]) - total(row["grade"]["direct"]) for row in rows]
    return {
        "n": len(differences),
        "harness_minus_direct": round(sum(differences) / len(differences), 2) if differences else None,
        "wins_ties_losses": [
            sum(value > 0 for value in differences), differences.count(0),
            sum(value < 0 for value in differences),
        ],
    }


def date_flags(case, result):
    cutoff = case["cutoff"]
    late, unknown = 0, 0
    if cutoff:
        for citation in result["citations"]:
            try:
                late += date.fromisoformat(citation["published_on"]) > date.fromisoformat(cutoff)
            except (TypeError, ValueError):
                unknown += 1
    return late, unknown


def supply_counts(rows, arm):
    gold_total, hits, supported, uncertain, contradicted, hypotheses = 0, 0, 0, 0, 0, 0
    for row in rows:
        gold_total += len(row["case"]["reference"])
        companies = row["grade"][arm]["companies"]
        hits += len({index for company in companies if company["status"] == "supported"
                     for index in company["gold_indexes"] if 0 <= index < len(row["case"]["reference"])})
        supported += sum(company["status"] == "supported" for company in companies)
        uncertain += sum(company["status"] == "uncertain" for company in companies)
        contradicted += sum(company["status"] == "contradicted" for company in companies)
        hypotheses += sum(company["actionable_research"] and company["status"] == "supported"
                          for company in companies)
    return {
        "gold_relationship_hits": hits, "gold_relationship_total": gold_total,
        "supported_companies": supported, "uncertain_companies": uncertain,
        "contradicted_companies": contradicted, "conditional_research_hypotheses": hypotheses,
    }


def export(rows, output):
    summaries = {}
    report = [
        "# 金融研究品質實驗｜Harness 與純 Astra", "",
        "兩組以本機已登入的 Codex CLI 執行同一個 `gpt-6.2-astra`，推理強度皆為 medium。",
        "評審為 `gpt-6.2-sol`。每題隱去系統名稱並交換呈現順序，分別給任務完成、證據支持和推理各 0 至 2 分。",
        "分數只納入兩邊均完成且已評分的題目。這是抽樣本地評分，FinanceGym 完整標準由作者保留。",
        "FrontierFinance 下載回傳 HTTP 401。財報組改用 FinanceBench 公開案例，兩邊共用相同原文節錄。",
        "搜尋組使用相同的每題來源網域、七個查詢及七次開頁的提示上限，另記錄實耗與超限。"
        "FinSearchComp T3 在此使用限定網域的搜尋設定。歷史回放使用現今索引，"
        "來源日期可能只有模型陳述，未使用凍結語料。", "",
        "財報題的證據分看共用節錄。搜尋題的證據分看可追溯的工具摘錄，供應鏈題也納入已核對的原始公告段落。"
        "工具摘錄缺少段落時，需打開原文才能判定引文是否確實支持論點。", "",
        "| 題組 | 兩邊完成／計畫 | 已評分 | 純 Astra／6 | Harness／6 | Harness 勝／和／負 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for suite in SUITES:
        all_rows = [row for row in rows if row["case"]["suite"] == suite]
        pairs = [row for row in all_rows if all("answer" in row["results"][arm] for arm in ARMS)]
        graded = [row for row in pairs if row["grade"]]
        n = len(graded)
        values = {arm: [total(row["grade"][arm]) for row in graded] for arm in ARMS}
        outcomes = score_delta(graded)["wins_ties_losses"]
        in_budget = [row for row in graded if not any(
            row["results"][arm]["audit"]["budget_exceeded"] for arm in ARMS
        )]
        summary = {"planned": len(all_rows), "paired": len(pairs), "graded": n,
                   "harness_win_tie_loss": outcomes, "within_budget": score_delta(in_budget), "arms": {}}
        for arm in ARMS:
            results = [row["results"][arm] for row in pairs]
            flags = [date_flags(row["case"], row["results"][arm]) for row in pairs]
            summary["arms"][arm] = {
                "mean_out_of_6": round(sum(values[arm]) / n, 2) if n else None,
                "dimension_means_out_of_2": {
                    key: round(sum(row["grade"][arm][key] for row in graded) / n, 2) if n else None
                    for key in DIMENSIONS
                },
                "median_seconds": median(row["elapsed_seconds"] for row in results) if results else None,
                "median_search_queries": median(row["audit"]["actions"]["search"] for row in results) if results else None,
                "median_input_tokens": median(row["audit"]["usage"]["input_tokens"] for row in results) if results else None,
                "over_search_budget": sum(row["audit"]["budget_exceeded"] for row in results),
                "claimed_post_cutoff_citations": sum(late for late, _ in flags),
                "citations_missing_usable_dates": sum(unknown for _, unknown in flags),
            }
            if suite == "Supply chain":
                summary["arms"][arm].update(supply_counts(graded, arm))
        summaries[suite] = summary
        means = [summary["arms"][arm]["mean_out_of_6"] for arm in ARMS]
        shown = [f"{mean:.2f}" if mean is not None else "—" for mean in means]
        report.append(f"| {suite} | {len(pairs)}/{len(all_rows)} | {n} | {shown[0]} | {shown[1]} | "
                      f"{'/'.join(map(str, outcomes)) if n else '—'} |")

    report += ["", "## 耗時與搜尋稽核", "",
               "| 題組 | 純 Astra 中位秒數 | Harness 中位秒數 | 超搜尋預算案數（純／系統） | 截止日後引文（純／系統） | 日期不可判引文（純／系統） |",
               "|---|---:|---:|---:|---:|---:|"]
    for suite, summary in summaries.items():
        arms = [summary["arms"][arm] for arm in ARMS]
        seconds = [f"{row['median_seconds']:.1f}" if row["median_seconds"] is not None else "—"
                   for row in arms]
        columns = ["/".join(str(row[key]) for row in arms) for key in (
            "over_search_budget", "claimed_post_cutoff_citations", "citations_missing_usable_dates",
        )]
        report.append(f"| {suite} | {' | '.join(seconds + columns)} |")
    report += ["", "截止日後與日期不可判計數來自回答明列的引用日期。原始搜尋命中內容可見於各案的 JSONL。", "",
               "| 題組 | 兩邊都在搜尋預算內且已評分 | 平均配對分差（Harness 減純 Astra） |",
               "|---|---:|---:|"]
    for suite, summary in summaries.items():
        budget = summary["within_budget"]
        difference = budget["harness_minus_direct"]
        report.append(f"| {suite} | {budget['n']} | "
                      f"{f'{difference:+.2f}' if difference is not None else '—'} |")
    report += ["",
               "## 未提示的供應鏈機會", "",
               "| 項目 | 純 Astra | Harness |", "|---|---:|---:|"]
    supply = summaries["Supply chain"]["arms"]
    report.append("| 標註關係命中率 | " + " | ".join(
        f"{supply[arm]['gold_relationship_hits']}/{supply[arm]['gold_relationship_total']}"
        for arm in ARMS
    ) + " |")
    for key, label in (
        ("supported_companies", "有依據的公司"),
        ("uncertain_companies", "證據不足的公司"),
        ("contradicted_companies", "與證據矛盾的公司"),
        ("conditional_research_hypotheses", "可驗證的條件式假設"),
    ):
        report.append(f"| {label} | {supply['direct'][key]} | {supply['harness'][key]} |")

    report += ["", "## 逐題結果", "",
               "| 編號 | 純 Astra | Harness | 純 Astra 評語 | Harness 評語 |",
               "|---|---:|---:|---|---|"]
    qa = ["# 完整題目與原始回答", ""]
    for row in rows:
        case, results, grade = row["case"], row["results"], row["grade"]
        if grade:
            rationales = [grade[arm]["rationale"].replace("|", "／").replace("\n", " ") for arm in ARMS]
            report.append(f"| {case['id']} | {total(grade['direct'])} | {total(grade['harness'])} | "
                          f"{rationales[0]} | {rationales[1]} |")
        qa += [f"## {case['id']} · {case['suite']}", "", case["question"], ""]
        if case["cutoff"]:
            qa += [f"截止日 {case['cutoff']}", ""]
        for arm, label in zip(ARMS, ("純 Astra", "Harness")):
            result = results[arm]
            qa += [f"### {label}", "", result.get("answer") or result.get("error") or "尚無執行結果。", ""]
            if result.get("citations"):
                qa.extend(f"- {citation['ref']}" for citation in result["citations"])
                qa.append("")
    failures = [(row["case"]["id"], arm, row["results"][arm]["error"])
                for row in rows for arm in ARMS if "error" in row["results"][arm]]
    if failures:
        report += ["", "## 未取得回答的執行", ""]
        report.extend(f"- {case_id} · {arm} · {error}" for case_id, arm, error in failures)
    write_json(output / "summary.json", summaries)
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (output / "questions-and-answers.md").write_text("\n".join(qa), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/public-benchmark"))
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--export-only", action="store_true")
    args = parser.parse_args()
    cases = load_cases(args.output / "inputs")
    os.environ["RESEARCH_CODEX_MODEL"] = JUDGE
    failed = set()
    while True:
        rows = snapshot(cases, args.output)
        if not args.export_only:
            ready = [row for row in rows if not row["grade"] and row["case"]["id"] not in failed
                     and all("answer" in row["results"][arm] for arm in ARMS)]
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                jobs = {pool.submit(grade_case, row["case"], args.output, row["results"]):
                        row["case"]["id"] for row in ready}
                for future in as_completed(jobs):
                    try:
                        print("graded", future.result(), flush=True)
                    except (ValueError, AdapterError) as exc:
                        case_id = jobs[future]
                        failed.add(case_id)
                        print("grade failed", case_id, str(exc), flush=True)
        rows = snapshot(cases, args.output)
        export(rows, args.output)
        if not args.watch or all(all(row["results"].values()) for row in rows):
            break
        sleep(10)


if __name__ == "__main__":
    main()
