import os
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import AwareDatetime, Field, ValidationError, model_validator

from .adapters import AdapterError, configured_adapter
from .earnings import EarningsError
from .hypothesis_tree import TreeQuestion
from .memo_export import printable, workbook
from .memo_workflow import MemoSignoff, freeze, identity, load, sign
from .revision_memo import build_memo
from .revision_bridge import RevisionQuote
from .schema import ConsensusImport, EarningsBranch, Event, ForecastRegistration, ForecastResolution, Question, ResearchReview, Schema
from .store import MissingReport, Store

PACKAGE = Path(__file__).resolve().parent


class RevenueRevisionCheck(Schema):
    period_end: date
    event_at: AwareDatetime | None = None
    fiscal_label: str | None = Field(default=None, min_length=1, max_length=90)
    original: RevisionQuote | None = None
    disclosure: RevisionQuote | None = None


class FullRevenueRevisionCheck(Schema):
    period_end: date
    event_at: AwareDatetime | None = None
    fiscal_label: str | None = Field(default=None, min_length=1, max_length=90)
    source_url: str = Field(min_length=8, max_length=2048)
    published_at: AwareDatetime
    obtained_at: AwareDatetime
    html: str = Field(min_length=1, max_length=2_000_000)


class ArchivedMemoGuidance(Schema):
    archive: Literal["guidance-table", "guidance-ytd"]
    case_id: str = Field(min_length=1, max_length=80)


class MemoRequest(Schema):
    period_end: date | None = None
    baseline_revision: int | None = Field(default=None, ge=1)
    quotes: RevenueRevisionCheck | None = None
    filing: FullRevenueRevisionCheck | None = None
    cross_page: ArchivedMemoGuidance | None = None

    @model_validator(mode="after")
    def one_preview(self):
        if self.quotes and self.filing:
            raise ValueError("引文和完整公告只可選一種輸入。")
        preview = self.quotes or self.filing
        if preview and self.period_end and preview.period_end != self.period_end:
            raise ValueError("指引財季須與修正稿一致。")
        return self


@lru_cache
def default_store():
    return Store(os.getenv("RESEARCH_DB", "output/research.sqlite3"))


def apply_search_defaults(event):
    mode = os.getenv("RESEARCH_SEARCH_MODE", "off")
    if mode == "off" or "search_mode" in event.model_fields_set:
        return event
    domains = event.search_domains or [
        domain.strip()
        for domain in os.getenv("RESEARCH_SEARCH_DOMAINS", "sec.gov").split(",")
        if domain.strip()
    ]
    return Event.model_validate({
        **event.model_dump(), "search_mode": mode, "search_domains": domains,
    })


def create_app(store=None, adapter=None):
    app = FastAPI(title="事件驅動交易假說研究系統")
    app.mount("/workbench-assets", StaticFiles(directory=PACKAGE / "web"), name="workbench-assets")

    def storage():
        return store if store is not None else default_store()

    def generator():
        try:
            return adapter if adapter is not None else configured_adapter()
        except ValueError as exc:
            raise AdapterError(str(exc)) from exc

    @app.exception_handler(MissingReport)
    async def missing(request: Request, exc: MissingReport):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(AdapterError)
    async def adapter_failure(request: Request, exc: AdapterError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(EarningsError)
    async def earnings_validation(request: Request, exc: EarningsError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/", include_in_schema=False)
    def workbench():
        return FileResponse(PACKAGE / "web" / "index.html")

    @app.get("/workbench/config", include_in_schema=False)
    def workbench_config(engine=Depends(generator)):
        return {
            "mode": engine.identity["mode"], "model": engine.identity.get("model"),
            "search_default": os.getenv("RESEARCH_SEARCH_MODE", "off"),
        }

    @app.get("/workbench/examples/{name}", include_in_schema=False)
    def workbench_example(name: str):
        if name not in {"asml-q3", "asml-earnings", "nvidia-h20", "intel-high-na"}:
            raise HTTPException(status_code=404, detail="找不到示範事件")
        return FileResponse(PACKAGE / "examples" / f"{name}.json", media_type="application/json")

    @app.post("/events")
    def create(event: Event, db=Depends(storage), engine=Depends(generator)):
        try:
            event = apply_search_defaults(event)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail="搜尋預設值無效，請檢查模式與來源網域") from exc
        return db.create(event, engine)

    @app.get("/runs/{id}")
    def run(id: str, db=Depends(storage)):
        return db.run(id)

    @app.get("/reports")
    def find_reports(query: str = Query(default="", max_length=120),
                     limit: int = Query(default=10, ge=1, le=30), db=Depends(storage)):
        return {"reports": db.find_reports(query, limit)}

    @app.get("/reports/{id}/revisions/{v}")
    def revision(id: str, v: int, db=Depends(storage)):
        return db.revision(id, v)

    @app.get("/reports/{id}/revisions/{v}/hypothesis-tree")
    def hypothesis_tree(id: str, v: int, db=Depends(storage)):
        return db.hypothesis_tree(id, v)

    @app.post("/reports/{id}/revisions/{v}/hypothesis-tree")
    def extend_hypothesis_tree(id: str, v: int, question: TreeQuestion,
                               db=Depends(storage), engine=Depends(generator)):
        return db.extend_hypothesis_tree(id, v, question, engine)

    @app.get("/reports/{id}/revisions/{v}/earnings")
    def earnings_status(id: str, v: int, db=Depends(storage)):
        return db.earnings_status(id, v)

    @app.post("/reports/{id}/revisions/{v}/earnings/revision-check")
    def revenue_revision_check(id: str, v: int, body: RevenueRevisionCheck, db=Depends(storage)):
        return db.revenue_revision_check(id, v, body)

    @app.post("/reports/{id}/revisions/{v}/earnings/full-revision-check")
    def full_revenue_revision_check(id: str, v: int, body: FullRevenueRevisionCheck,
                                    db=Depends(storage), engine=Depends(generator)):
        return db.full_revenue_revision_check(id, v, body, engine)

    @app.post("/reports/{id}/earnings/branches")
    def earnings_branch(id: str, body: EarningsBranch, db=Depends(storage)):
        return db.earnings_branch(id, body)

    @app.post("/reports/{id}/earnings/consensus")
    def earnings_consensus(id: str, body: ConsensusImport, db=Depends(storage)):
        return db.earnings_consensus(id, body)

    @app.post("/reports/{id}/revisions/{v}/forecasts")
    def register_forecast(id: str, v: int, body: ForecastRegistration, db=Depends(storage)):
        return db.register_forecast(id, v, body)

    @app.post("/reports/{id}/revisions/{v}/forecasts/{forecast_id}/resolve")
    def resolve_forecast(id: str, v: int, forecast_id: str, body: ForecastResolution, db=Depends(storage)):
        return db.forecast_resolution(id, v, forecast_id, body)

    @app.post("/reports/{id}/revisions/{v}/reviews")
    def research_review(id: str, v: int, body: ResearchReview, db=Depends(storage)):
        return db.research_review(id, v, body)

    @app.post("/reports/{id}/revisions/{v}/revision-memos")
    def memo_create(id: str, v: int, body: MemoRequest, request: Request, db=Depends(storage)):
        actor = identity(request.headers.get("authorization"))
        if actor and actor["role"] != "author":
            raise HTTPException(403, "修正稿須由作者身分建立。")
        report = db.revision(id, v)
        baseline = body.baseline_revision if body.baseline_revision is not None else report["parent_revision"]
        if baseline and baseline > v:
            raise EarningsError("舊估版次不得晚於現估。")
        prior = db.revision(id, baseline) if baseline and baseline != v else None
        if prior and prior["as_of"] != report["as_of"]:
            raise EarningsError("新舊版須使用相同點時快照。")
        preview_request = body.quotes or body.filing
        period = body.period_end or (preview_request.period_end if preview_request else None)
        if preview_request and preview_request.event_at:
            plan = (report.get("earnings") or {}).get("inputs", {})
            if not plan or preview_request.event_at != datetime.fromisoformat(plan["event_at"]):
                raise EarningsError("指引核對須沿用封存事件時間。")
        preview = None
        if body.filing:
            preview = db.full_revenue_revision_check(id, v, body.filing, generator())
        elif body.quotes:
            preview = db.revenue_revision_check(id, v, body.quotes)
        cross_page = body.cross_page.model_dump() if body.cross_page else None
        return freeze(db, build_memo(report, prior, period.isoformat() if period else None, preview, cross_page), actor)

    @app.get("/reports/{id}/revisions/{v}/revision-memos/{memo_id}")
    def memo_get(id: str, v: int, memo_id: str, db=Depends(storage)):
        result = load(db, id, v, memo_id)
        forecasts = [row for row in db.earnings_status(id, v)["forecasts"]
                     if row["key"]["period_end"] == result["memo"]["period_end"]]
        return {**result, "outcomes": {purpose: {
            "registered": sum(row["purpose"] == purpose for row in forecasts),
            "reported": sum(row["purpose"] == purpose and (row["resolution"] or {}).get("outcome") in {"hit", "miss"}
                            for row in forecasts),
            "records": [row for row in forecasts if row["purpose"] == purpose],
        } for purpose in ("live", "historical_replay")}}

    @app.get("/reports/{id}/revisions/{v}/revision-memos/{memo_id}/exports/{kind}")
    def memo_export(id: str, v: int, memo_id: str, kind: Literal["html", "xlsx"], db=Depends(storage)):
        memo = load(db, id, v, memo_id)["memo"]
        if kind == "html":
            return Response(printable(memo), media_type="text/html", headers={
                "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
            })
        return Response(workbook(memo), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f'attachment; filename="{memo_id}.xlsx"'})

    @app.post("/reports/{id}/revisions/{v}/revision-memos/{memo_id}/signoffs")
    def memo_sign(id: str, v: int, memo_id: str, body: MemoSignoff, request: Request, db=Depends(storage)):
        return sign(db, id, v, memo_id, body, identity(request.headers.get("authorization"), required=True))

    @app.post("/reports/{id}/questions")
    def question(id: str, body: Question, db=Depends(storage), engine=Depends(generator)):
        try:
            return db.question(id, body, engine)
        except ValueError as exc:
            return JSONResponse(status_code=422, content={"detail": str(exc)})

    return app


app = create_app()
