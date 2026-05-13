from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_db_and_tables
from app.routers import courses, dashboard, documents, flashcards, health, quizzes, summaries


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
    app.include_router(dashboard.router)
    return app


app = create_app()
