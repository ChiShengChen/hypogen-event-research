"""Conversation tools backed by the same application and SQLite as the workbench."""

from datetime import date
import os
from pathlib import Path
from typing import Annotated, Any, Literal

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import AwareDatetime, Field, ValidationError

from . import mcp_benchmarks as benchmarks, mcp_guidance as guidance
from .api import ArchivedMemoGuidance, FullRevenueRevisionCheck, RevenueRevisionCheck, create_app, default_store
from .hypothesis_inputs import NewsInput, OpinionInput
from .mcp_state import ConversationState
from .memo_export import printable, workbook
from .schema import (
    ConsensusImport, EarningsBranch, Event, ForecastRegistration, ForecastResolution, Question, ResearchReview, Schema,
)

ROOT = Path(__file__).resolve().parents[1]
READ_ONLY = ToolAnnotations(readOnlyHint=True)
ReportID = Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")]
ForecastID = Annotated[str, Field(pattern=r"^[a-f0-9]{24}$")]
MemoID = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Revision = Annotated[int, Field(ge=1, strict=True)]
GuidanceArchive = Literal["guidance-table", "guidance-ytd"]
ArchivePreset = Literal["v9_equal_recovery", "guidance_tables", "guidance_ytd"]


class AttachmentInput(Schema):
    kind: Literal["file"]
    attachment_id: str
    available_on: date | None = None


class FilingInput(Schema):
    period_end: date
    event_at: AwareDatetime | None = None
    fiscal_label: str | None = None
    source_url: str
    published_at: AwareDatetime
    obtained_at: AwareDatetime
    attachment_id: str


BranchSource = Annotated[NewsInput | OpinionInput | AttachmentInput, Field(discriminator="kind")]


def serial(data):
    return data.model_dump(mode="json", exclude_unset=True)


def revision_path(report_id, revision):
    return f"/reports/{report_id}/revisions/{revision}"


def create_server(store=None, adapter=None, *, inbox=None, jobs=None):
    store = store if store is not None else default_store()
    inbox = Path(inbox or os.getenv("HYPOGEN_INBOX", ROOT / "output/mcp-inbox")).resolve()
    jobs = Path(jobs or os.getenv("HYPOGEN_JOBS", ROOT / "output/mcp-jobs")).resolve()
    state = ConversationState(store, inbox)
    app = create_app(store, adapter)
    mcp = FastMCP("hypogen", instructions=(
        "Hypogen uses saved evidence snapshots. Resolve natural-language references with report_find and tree_get. "
        "Keep report_id, revision and the selected node for followups. Cite saved sources and respect the cutoff. "
        "Do not invent evidence or dates. Inspect capabilities before switching modes or requesting a fresh benchmark."
    ))

    async def request(method, path, *, body=None, params=None, headers=None):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://hypogen.local") as client:
            response = await client.request(method, path, json=body, params=params, headers=headers)
        result = response.json()
        if response.is_error:
            detail = result.get("detail", "研究後端未完成請求。")
            if isinstance(detail, list):
                detail = "；".join(".".join(str(piece) for piece in item["loc"][1:]) + " " + item["msg"]
                                  for item in detail)
            raise ToolError(f"HTTP {response.status_code} {detail}")
        return result

    async def post(tool, request_id, path, body, *, headers=None):
        async def action():
            return await request("POST", path, body=body, headers=headers)

        return await state.once(tool, request_id, {"path": path, "body": body}, action)

    @mcp.tool(annotations=READ_ONLY)
    async def capabilities() -> dict[str, Any]:
        """Read the effective model, supported workflows, source inbox, and benchmark presets."""
        engine = await request("GET", "/workbench/config")
        return {"engine": engine, "database": str(store.path.resolve()), "inbox": str(inbox),
                "attachments_max_bytes": 2_097_152,
                "search_modes": ["off", "historical_replay", "live"] if engine["mode"] == "codex" else ["off"],
                "branch_modes": ["followup", "fanout", "custom"] if engine["mode"] != "fixture" else [],
                "guidance_modes": {"report": ["quotes"] + (["filing"] if engine["mode"] != "fixture" else []),
                                   "archived": ["extract", "astra"] + (["veto"] if (ROOT / "output/guidance-veto-comparison/dev-replay.json").is_file() else [])},
                "benchmark_archives": list(benchmarks.ARCHIVES), "benchmark_fresh": ["v9_equal_recovery"]}

    @mcp.tool()
    def attachment_add(filename: str) -> dict[str, Any]:
        """Register one user-supplied file staged in the local inbox, without putting its bytes in the conversation."""
        return state.attach(filename)

    @mcp.tool(annotations=READ_ONLY)
    async def report_find(query: str = "", limit: int = 10) -> dict[str, Any]:
        """Find the latest revision of each saved report by issuer, ticker, or event keywords."""
        return await request("GET", "/reports", params={"query": query, "limit": limit})

    @mcp.tool(annotations=READ_ONLY)
    async def report_get(report_id: ReportID, revision: Revision,
                         view: Literal["research", "full"] = "research") -> dict[str, Any]:
        """Open a specific report. Research view includes its hypotheses, linkages, and original evidence."""
        result = await request("GET", revision_path(report_id, revision))
        if view == "full":
            return result
        fields = ("report_id", "revision", "parent_revision", "target", "event_text", "as_of", "horizon", "claims",
                  "hypotheses", "stance_cases", "assessment", "business_linkages", "business_linkage_gap", "evidence")
        return {name: result[name] for name in fields if name in result}

    @mcp.tool()
    async def report_create(event: Event, request_id: str) -> dict[str, Any]:
        """Generate and save point-in-time research. Keep request_id stable if delivery is retried."""
        result = await post("report_create", request_id, "/events", serial(event))
        return result | {"report": await report_get(result["report_id"], result["revision"])}

    @mcp.tool()
    async def report_ask(report_id: ReportID, question: Question, request_id: str) -> dict[str, Any]:
        """Ask an existing report or recalculate its lots; use evidence_search=off to freeze its evidence."""
        result = await post("report_ask", request_id, f"/reports/{report_id}/questions", serial(question))
        revision = result.get("child_revision") or question.parent_revision
        report = await request("GET", revision_path(report_id, revision))
        references = set(result.get("evidence_ids", []))
        return {"report_id": report_id, "revision": revision, **result,
                "citations": [row for row in report["evidence"] if row["id"] in references]}

    @mcp.tool(annotations=READ_ONLY)
    async def tree_get(report_id: ReportID, revision: Revision) -> dict[str, Any]:
        """List saved hypotheses and branch nodes for this exact report revision."""
        result = await request("GET", revision_path(report_id, revision) + "/hypothesis-tree")
        return {"report_id": report_id, "revision": revision, **result}

    @mcp.tool()
    async def tree_branch(report_id: ReportID, revision: Revision, parent_id: str,
                          mode: Literal["followup", "fanout", "custom"], request_id: str,
                          question: str = "", stance: str | None = None,
                          inputs: Annotated[list[BranchSource], Field(max_length=6)] | None = None) -> dict[str, Any]:
        """Expand one node; optionally use news, attachment IDs, or analyst opinions as branch inputs."""
        body = {"parent_id": parent_id, "mode": mode, "question": question, "stance": stance,
                "inputs": [state.branch_file(item.attachment_id, item.available_on)
                           if isinstance(item, AttachmentInput) else serial(item) for item in (inputs or [])]}
        path = revision_path(report_id, revision)

        result = await post("tree_branch", request_id, path + "/hypothesis-tree", body)
        report = await request("GET", path)
        references = {ref for node in result["nodes"] for ref in (node.get("case") or {}).get("evidence_ids", [])}
        citations = [row for row in report["evidence"] if row["id"] in references]
        if any(ref.startswith("input:") for ref in references):
            tree = await tree_get(report_id, revision)
            citations.extend(row for node in tree["nodes"] for row in node.get("inputs", [])
                             if row["id"] in references and row["status"] == "usable")
        children = [node["id"] for node in result["nodes"] if node.get("kind") == "hypothesis"]
        return {"report_id": report_id, "revision": revision, "parent_id": parent_id, "as_of": report["as_of"],
                **result, "hypothesis_node_ids": children, "citations": citations}

    @mcp.tool()
    async def guidance_check(report_id: ReportID, revision: Revision, request_id: str,
                             quotes: RevenueRevisionCheck | None = None, filing: FilingInput | None = None) -> dict[str, Any]:
        """Check remaining revenue versus the saved estimate, using source quotations or a complete archived HTML file."""
        if (quotes is None) == (filing is None):
            raise ToolError("請提供 quotes 或 filing 其中一種。")
        path = revision_path(report_id, revision) + "/earnings/"
        try:
            if filing:
                path += "full-revision-check"
                data = serial(filing)
                attachment_id = data.pop("attachment_id")
                model = FullRevenueRevisionCheck.model_validate(data | {"html": state.attachment_text(attachment_id)})
            else:
                path += "revision-check"
                model = quotes
        except ValidationError as exc:
            raise ToolError("公告日期、網址或 HTML 不符合完整公告的輸入格式。") from exc
        return await post("guidance_check", request_id, path, serial(model))

    @mcp.tool(annotations=READ_ONLY)
    def guidance_cases(query: str = "") -> dict[str, Any]:
        """List the sealed cross-announcement guidance cases by ticker, company, or case ID."""
        needle = query.strip().casefold()
        return {"cases": [row for row in guidance.case_index()
                          if any(needle in row[key].casefold() for key in ("issuer", "ticker", "case_id"))]}

    @mcp.tool(annotations=READ_ONLY)
    def guidance_replay(archive: GuidanceArchive, case_id: str,
                        strategy: Literal["extract", "astra", "veto"] = "extract") -> dict[str, Any]:
        """Recheck a sealed cross-announcement case using archived replies, with no fresh model calls."""
        return guidance.check_archive(archive, case_id, strategy)

    @mcp.tool(annotations=READ_ONLY)
    async def earnings_get(report_id: ReportID, revision: Revision) -> dict[str, Any]:
        """Read the saved forecasts, financial branches, resolutions and reviews for this report revision."""
        return await request("GET", revision_path(report_id, revision) + "/earnings")

    @mcp.tool()
    async def revision_memo_create(report_id: ReportID, revision: Revision, request_id: str,
                                   period_end: date | None = None, baseline_revision: Revision | None = None,
                                   quotes: RevenueRevisionCheck | None = None, filing: FilingInput | None = None,
                                   cross_page: ArchivedMemoGuidance | None = None) -> dict[str, Any]:
        """Freeze an analyst earnings revision memo with optional validated guidance from a quote or attached HTML."""
        payload = {"period_end": period_end.isoformat() if period_end else None, "baseline_revision": baseline_revision,
                   "quotes": serial(quotes) if quotes else None, "filing": None,
                   "cross_page": serial(cross_page) if cross_page else None}
        if filing:
            data = serial(filing)
            attachment_id = data.pop("attachment_id")
            payload["filing"] = data | {"html": state.attachment_text(attachment_id)}
        path = revision_path(report_id, revision) + "/revision-memos"
        token = os.getenv("RESEARCH_MEMO_AUTHOR_TOKEN")
        return await post("revision_memo_create", request_id, path, payload,
                          headers={"Authorization": "Bearer " + token} if token else None)

    @mcp.tool(annotations=READ_ONLY)
    async def revision_memo_get(report_id: ReportID, revision: Revision, memo_id: MemoID) -> dict[str, Any]:
        """Read a frozen memo, its verified review status, and real versus replay forecast outcomes."""
        path = revision_path(report_id, revision) + f"/revision-memos/{memo_id}"
        return await request("GET", path)

    @mcp.tool()
    async def revision_memo_export(report_id: ReportID, revision: Revision, memo_id: MemoID) -> dict[str, Any]:
        """Save the frozen memo's one-page HTML and editable Excel workbook to the local export folder."""
        memo = (await revision_memo_get(report_id, revision, memo_id))["memo"]
        directory = ROOT / "output/revision-memos" / memo_id
        directory.mkdir(parents=True, exist_ok=True)
        html = directory / "revision-memo.html"
        xlsx = directory / "revision-memo.xlsx"
        html.write_text(printable(memo), encoding="utf-8")
        xlsx.write_bytes(workbook(memo))
        return {"memo_id": memo_id, "html": str(html), "xlsx": str(xlsx)}

    @mcp.tool()
    async def earnings_branch(report_id: ReportID, scenario: EarningsBranch, request_id: str) -> dict[str, Any]:
        """Recalculate defined financial assumptions and save a forecast scenario."""
        return await post("earnings_branch", request_id, f"/reports/{report_id}/earnings/branches", serial(scenario))

    @mcp.tool()
    async def consensus_import(report_id: ReportID, parent_revision: Revision, target: str, provider: str,
                               source_url: str, captured_at: AwareDatetime, purpose: Literal["live", "historical_replay"],
                               attachment_id: str, request_id: str) -> dict[str, Any]:
        """Import a user-provided point-in-time consensus CSV and keep its attribution."""
        try:
            data = ConsensusImport(parent_revision=parent_revision, target=target, provider=provider, source_url=source_url,
                                   captured_at=captured_at, purpose=purpose, csv_text=state.attachment_text(attachment_id))
        except ValidationError as exc:
            raise ToolError("共識的來源、截點或 CSV 不符合匯入格式。") from exc
        return await post("consensus_import", request_id, f"/reports/{report_id}/earnings/consensus", serial(data))

    @mcp.tool()
    async def forecast_register(report_id: ReportID, revision: Revision, forecast: ForecastRegistration) -> dict[str, Any]:
        """Register a forecast against the saved evidence for a future resolution."""
        return await request("POST", revision_path(report_id, revision) + "/forecasts", body=serial(forecast))

    @mcp.tool()
    async def forecast_resolve(report_id: ReportID, revision: Revision, forecast_id: ForecastID,
                               outcome: ForecastResolution) -> dict[str, Any]:
        """Record the disclosed outcome or the reason a saved forecast cannot be evaluated."""
        path = revision_path(report_id, revision) + f"/forecasts/{forecast_id}/resolve"
        return await request("POST", path, body=serial(outcome))

    @mcp.tool()
    async def review_record(report_id: ReportID, revision: Revision, review: ResearchReview, request_id: str) -> dict[str, Any]:
        """Record an actual analyst's review decision and notes for a specific revision."""
        return await post("review_record", request_id, revision_path(report_id, revision) + "/reviews", serial(review))

    @mcp.tool(annotations=READ_ONLY)
    def benchmark_status(preset: ArchivePreset = "v9_equal_recovery", job_id: str | None = None) -> dict[str, Any]:
        """Read a published comparison, or inspect a live job's ledger progress and result by job ID."""
        return benchmarks.job_status(jobs, job_id) if job_id else benchmarks.archive_status(preset)

    @mcp.tool(annotations=READ_ONLY)
    def benchmark_replay(archive: GuidanceArchive, case_id: str) -> dict[str, Any]:
        """Compare archived Astra answers against a local verifier replay of the exact same sealed case."""
        extract = guidance.check_archive(archive, case_id, "extract")
        astra = guidance.check_archive(archive, case_id, "astra")
        return {"case_id": case_id, "model_calls": 0, "extract": extract, "astra": astra}

    @mcp.tool()
    def benchmark_start(request_id: str, preset: Literal["v9_equal_recovery"] = "v9_equal_recovery",
                        resume: bool = False) -> dict[str, Any]:
        """Start or explicitly resume the sealed four-case V9 recovery preset; request_id is the job ID."""
        return benchmarks.start(jobs, request_id, resume)

    return mcp


def main():
    os.chdir(ROOT)
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
