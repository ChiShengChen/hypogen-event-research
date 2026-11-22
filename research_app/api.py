import os
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .adapters import AdapterError, configured_adapter
from .schema import Event, Question
from .store import MissingReport, Store


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

    @app.post("/reports/{id}/questions")
    def question(id: str, body: Question, db=Depends(storage), engine=Depends(generator)):
        try:
            return db.question(id, body, engine)
        except ValueError as exc:
            return JSONResponse(status_code=422, content={"detail": str(exc)})

    return app


app = create_app()
