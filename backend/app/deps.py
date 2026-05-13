from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.services.ai_provider import AIProvider, FakeAIProvider, OpenAIProvider


def get_ai_provider(settings: Settings | None = None) -> AIProvider:
    settings = settings or get_settings()
    if settings.should_use_fake_ai:
        return FakeAIProvider()
    return OpenAIProvider(api_key=settings.openai_api_key or "", model=settings.openai_model)


DbSession = Session
