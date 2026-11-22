"""Run the ASML historical replay and the synthetic financial control with Astra."""
import argparse
import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from research_app.adapters import Codex
from research_app.schema import Event, Question
from research_app.store import Store

ROOT = Path(__file__).resolve().parents[1]
ASML_Q3 = "https://www.sec.gov/Archives/edgar/data/937966/000093796624000022/pressreleasequarterlyresul.htm"
ASML_Q4 = "https://investor.asml.com/news-releases/news-release-details/q4-2024-financial-results"
PUBLIC_QUESTION = (
    "請回答 ASML 2024 Q3 營收、Q3 淨新增訂單及其中的 EUV 訂單、"
    "2025 營收指引及它是否為實績。2024 Q4 實際淨新增訂單於截止時點可知嗎？"
)
SYNTHETIC_QUESTION = (
    "以事件原定截止時點為限，客戶 X 已認證乙的先進封裝產品嗎？"
    "如果本季全數交付認列批數從 600 改成 300，分別是多少增量營業利益與稀釋 EPS？"
    "請列出 EPS 差額、損益兩平批數及第一個達到正增量營業利益的整數批數。"
)
MODEL = "gpt-6.2-astra"


def asml():
    # Archive replay uses date-only, conservative end-of-day availability proxies.
    # Paragraphs are Chinese paraphrases of the linked public disclosures.
    return Event.model_validate({
        "event_text": "ASML 公布 2024 Q3 財報。研究 2025 年淨新增訂單與營收。",
        "as_of": "2024-10-15T23:59:59Z",
        "research_target": "ASML",
        "research_horizon": "2025",
        "documents": [
            {
                "id": "asml-q3", "source": ASML_Q3, "kind": "disclosure",
                "published_at": "2024-10-15T23:59:59Z", "obtained_at": "2024-10-15T23:59:59Z",
                "paragraphs": {
                    "q3-actual": "財報表列 2024 Q3 營收 7,467 百萬歐元，淨新增訂單 2,633 百萬歐元。"
                                 "其中 EUV 訂單約 14 億歐元。Q2 淨新增訂單 5,567 百萬歐元。",
                    "guidance": "管理層預估 2024 Q4 營收 88 至 92 億歐元，2025 全年營收 300 至 350 億歐元、毛利率 51% 至 53%。",
                    "management": "管理層表示 AI 市場有上行潛力，其他市場復甦較慢。"
                                  "部分客戶的先進邏輯製程擴產延後，影響 EUV 需求時程。"
                                  "記憶體擴產有限，重點為 HBM 與 DDR5 技術轉換。",
                },
            },
            {
                "id": "asml-q4", "source": ASML_Q4, "kind": "disclosure",
                "published_at": "2025-01-29T23:59:59Z", "obtained_at": "2025-01-29T23:59:59Z",
                "paragraphs": {"q4-actual": "後續公布 2024 Q4 實際淨新增訂單 7,088 百萬歐元。"},
            },
        ],
    })


def direct(output, name, prompt, search=False):
    destination = (output / f"{name}.md").resolve()
    with TemporaryDirectory(prefix="astra-pilot-") as directory:
        command = ["codex", "-a", "never"]
        if search:
            command.append("--search")
        else:
            command += ["-c", 'web_search="disabled"']
        command += [
            "exec", "--cd", directory, "--skip-git-repo-check", "--ephemeral", "--ignore-user-config",
            "--sandbox", "read-only", "--disable", "shell_tool", "--disable", "multi_agent",
            "--model", MODEL, "--color", "never", "--json", "--output-last-message", str(destination), "-",
        ]
        with (output / f"{name}.jsonl").open("w", encoding="utf-8") as log:
            result = subprocess.run(command, input=prompt, encoding="utf-8", stdout=log,
                                    stderr=subprocess.PIPE, timeout=180)
    if result.returncode:
        raise RuntimeError(f"{name} failed with exit code {result.returncode}")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def system(output, name, event):
    adapter = Codex()
    store = Store(output / f"{name}.sqlite3")
    run = store.create(event, adapter)
    report_id = run["report_id"]
    original = store.revision(report_id, 1)
    if name == "asml-system":
        result = store.question(report_id, Question(parent_revision=1, question=PUBLIC_QUESTION), adapter)
        assert "asml-q4:q4-actual" not in {row["id"] for row in original["evidence"]}
    else:
        qa = store.question(report_id, Question(
            parent_revision=1, question="客戶 X 已認證乙的先進封裝產品嗎？",
        ), adapter)
        branch = store.question(report_id, Question(
            parent_revision=1, question="當季交付並認列批量改為 300 批", overrides={"lots": 300},
        ), adapter)
        child = store.revision(report_id, branch["child_revision"])
        assert child["hypotheses"] == original["hypotheses"]
        result = {"qa": qa, "branch": branch, "original": original["model_outputs"], "child": child["model_outputs"]}
    (output / f"{name}.md").write_text(original["markdown"], encoding="utf-8")
    write_json(output / f"{name}.json", {"run": run, "answer": result, "evidence": original["evidence"]})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=["asml-search", "asml-system", "asml-snapshot", "synthetic-system", "synthetic-direct"])
    parser.add_argument("--output", type=Path, default=Path("output/astra-benchmark"))
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    start = perf_counter()
    if args.arm.startswith("asml"):
        event = asml()
        if args.arm == "asml-system":
            system(output, args.arm, event)
        else:
            prompt = (
                f"請用繁體中文對 ASML 做時點研究。截止時間 {event.as_of.isoformat()}。{PUBLIC_QUESTION}"
                "提供來源 URL 及日期，提出 2025 年可區別的多空傳導、查核指標、時點與可推翻條件，"
                "缺乏估值資料時說明限制。約 700 字。"
            )
            if args.arm == "asml-search":
                prompt += "請實際使用原生網路搜尋，優先採公司或監管機關資料。"
            else:
                prompt += ("只使用以下時點可見的公司揭露整理資料。\n"
                           + event.model_copy(update={"documents": event.documents[:1]}).model_dump_json())
            direct(output, args.arm, prompt, search=args.arm == "asml-search")
    else:
        event = Event.model_validate_json((ROOT / "research_app/fixtures/shutdown.json").read_text(encoding="utf-8"))
        if args.arm == "synthetic-system":
            system(output, args.arm, event)
        else:
            direct(output, args.arm, "用繁體中文回答。這是虛構資料，僅使用下列輸入。"
                   + SYNTHETIC_QUESTION + "\n" + event.model_dump_json())
    write_json(output / f"{args.arm}-timing.json", {"model": MODEL, "elapsed_seconds": round(perf_counter() - start, 2)})


if __name__ == "__main__":
    main()
