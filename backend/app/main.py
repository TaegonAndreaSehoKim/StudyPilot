from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from secrets import compare_digest

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.database import create_db_and_tables
from app.routers import courses, dashboard, documents, flashcards, health, quizzes, schedule, summaries
from app.services.rate_limiter import InMemoryRateLimiter, is_ai_cost_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    mutation_limiter = InMemoryRateLimiter()
    ai_limiter = InMemoryRateLimiter()

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

            if current_settings.rate_limit_enabled:
                identity = supplied_token or (request.client.host if request.client else "unknown")
                mutation_key = f"mutation:{identity}"
                allowed, remaining = mutation_limiter.allow(
                    mutation_key,
                    current_settings.mutation_rate_limit_per_minute,
                )
                if not allowed:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many write requests. Please wait before trying again."},
                        headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
                    )

                if is_ai_cost_endpoint(request.method, request.url.path):
                    ai_key = f"ai:{identity}"
                    allowed, remaining = ai_limiter.allow(ai_key, current_settings.ai_rate_limit_per_minute)
                    if not allowed:
                        return JSONResponse(
                            status_code=429,
                            content={"detail": "Too many OCR or AI generation requests. Please wait before trying again."},
                            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
                        )
                request.state.rate_limit_remaining = remaining
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
