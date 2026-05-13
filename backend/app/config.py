from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "StudyPilot"
    database_url: str = "sqlite:///./studypilot.db"
    storage_dir: Path = Path("backend/app/storage")
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.5"
    use_fake_ai: bool = False
    max_upload_mb: int = 10
    allowed_extensions: tuple[str, ...] = (".txt", ".md", ".pdf")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def should_use_fake_ai(self) -> bool:
        return self.use_fake_ai or not self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
