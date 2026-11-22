import os
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .adapters import AdapterError, configured_adapter
from .earnings import EarningsError
from .schema import EarningsBranch, Event, ForecastRegistration, ForecastResolution, Question, ResearchReview
from .store import MissingReport, Store

PACKAGE = Path(__file__).resolve().parent


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

    @app.get("/reports/{id}/revisions/{v}")
    def revision(id: str, v: int, db=Depends(storage)):
        return db.revision(id, v)

    @app.get("/reports/{id}/revisions/{v}/earnings")
    def earnings_status(id: str, v: int, db=Depends(storage)):
        return db.earnings_status(id, v)

    @app.post("/reports/{id}/earnings/branches")
    def earnings_branch(id: str, body: EarningsBranch, db=Depends(storage)):
        return db.earnings_branch(id, body)

    @app.post("/reports/{id}/revisions/{v}/forecasts")
    def register_forecast(id: str, v: int, body: ForecastRegistration, db=Depends(storage)):
        return db.register_forecast(id, v, body)

    @app.post("/reports/{id}/revisions/{v}/forecasts/{forecast_id}/resolve")
    def resolve_forecast(id: str, v: int, forecast_id: str, body: ForecastResolution, db=Depends(storage)):
        return db.forecast_resolution(id, v, forecast_id, body)

    @app.post("/reports/{id}/revisions/{v}/reviews")
    def research_review(id: str, v: int, body: ResearchReview, db=Depends(storage)):
        return db.research_review(id, v, body)

    @app.post("/reports/{id}/questions")
    def question(id: str, body: Question, db=Depends(storage), engine=Depends(generator)):
        try:
            return db.question(id, body, engine)
        except ValueError as exc:
            return JSONResponse(status_code=422, content={"detail": str(exc)})

    return app


app = create_app()
