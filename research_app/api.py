import os
from functools import lru_cache

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from .adapters import AdapterError, configured_adapter
from .schema import Event, Question
from .store import MissingReport, Store


@lru_cache
def default_store():
    return Store(os.getenv("RESEARCH_DB", "output/research.sqlite3"))


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
