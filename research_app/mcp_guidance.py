"""Read or replay published guidance comparisons against their archived evidence."""

from mcp.server.fastmcp.exceptions import ToolError
from urllib.parse import urldefrag

from .mcp_benchmarks import ROOT, read


def case_index():
    result = []
    for archive in ("guidance-table", "guidance-ytd"):
        for key, row in read(ROOT / "docs" / archive / "cases.json").items():
            case = row["case"]
            result.append({"archive": archive, "case_id": key, "issuer": case["issuer"],
                           "ticker": case["ticker"], "as_of": case["as_of"], "split": case["split"]})
    return result


def check_archive(archive, case_id, strategy):
    from benchmarks import guidance_arithmetic as arithmetic
    from benchmarks import guidance_tables, guidance_ytd

    directory = ROOT / "docs" / archive
    row = read(directory / "cases.json").get(case_id)
    if row is None:
        raise ToolError("封存案例不存在。先用 guidance_cases 查公司或股票代號。")
    case = arithmetic.Case.model_validate(row["case"])
    try:
        blocks = arithmetic.case_blocks(case)
    except FileNotFoundError as exc:
        raise ToolError("此 case 缺少本機封存公告。請依該 benchmark 的來源帳本還原檔案。") from exc
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    if strategy == "veto":
        replay = read(ROOT / "output/guidance-veto-comparison/dev-replay.json")
        match = next((entry for entry in (replay or {}).get("cases", [])
                      if entry["source"] == archive and entry["case"] == case_id), None)
        if match is None:
            raise ToolError("此案例沒有本機 Veto 封存結果。")
        result = {"answers": match["arms"]["veto"]["answers"], "vetoes": match["vetoes"],
                  "vetoed_items": match["vetoed_items"], "source": "archived_development_result"}
    else:
        result = {}
    arm = "extract" if strategy == "extract" else "astra"
    raw = read(directory / "raw/formal" / f"{case_id}-{arm}.json")
    if raw is None:
        raise ToolError("此案例沒有公開封存的原始回覆。")
    if strategy == "extract":
        extraction = arithmetic.Extraction.model_validate(raw)
        verifier = guidance_tables if archive == "guidance-table" else guidance_ytd
        result = verifier.revised(case, blocks, extraction, row["vintages"])
    if strategy == "astra":
        result = {"answers": {item["item"]: item["value"] for item in raw["answers"]},
                  "figures": raw.get("figures_used", []), "reason": raw.get("reason")}
    locator_ids = set(raw.get("evidence_ids", []))
    for figure in result.get("figures", []) + raw.get("figures", []):
        locator_ids.update((figure.get("block"), figure.get("unit_block")))
    documents = {doc.id: doc for doc in case.documents}
    citations = []
    for block_id, block in blocks.items():
        if block_id not in locator_ids:
            continue
        document = documents[block_id.split(":", 1)[0]]
        locator = block_id.rsplit(":", 1)[-1]
        page = locator[1:] if document.content_type == "text/plain" and locator.startswith("p") else ""
        link = f"{urldefrag(document.source_url)[0]}#page={int(page)}" if page.isdigit() else document.source_url
        citations.append({"id": block_id, "quote": block["text"], "source_url": document.source_url, "link": link,
                          "published_at": document.published_at.isoformat(),
                          "obtained_at": document.obtained_at.isoformat()})
    return {"case_id": case_id, "archive": archive, "strategy": strategy, "as_of": case.as_of.isoformat(),
            "model_calls": 0, "source": "archived_model_replay", **result, "citations": citations,
            "raw_response": str(directory / "raw/formal" / f"{case_id}-{arm}.json")}
