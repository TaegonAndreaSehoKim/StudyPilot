from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from secrets import compare_digest

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.database import create_db_and_tables
from app.routers import courses, dashboard, documents, flashcards, health, quizzes, schedule, summaries


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.middleware("http")
    async def require_access_token_for_mutations(request, call_next):
        if request.method in {"POST", "PATCH", "DELETE"}:
            current_settings = get_settings()
            token = current_settings.backend_access_token
            if not token and current_settings.is_production:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "BACKEND_ACCESS_TOKEN must be configured in production"},
                )
            supplied_token = request.headers.get("x-studypilot-key") or ""
            if token and not compare_digest(supplied_token, token):
                return JSONResponse(status_code=401, content={"detail": "Invalid or missing StudyPilot access token"})
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(courses.router)
    app.include_router(documents.router)
    app.include_router(summaries.router)
    app.include_router(flashcards.router)
    app.include_router(quizzes.router)
    app.include_router(schedule.router)
    app.include_router(dashboard.router)
    return app


app = create_app()
