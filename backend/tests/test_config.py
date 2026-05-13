from pathlib import Path

from app.config import BACKEND_DIR, Settings


def test_relative_storage_dir_resolves_from_backend_dir() -> None:
    settings = Settings(storage_dir=Path("app/storage"))

    assert settings.storage_dir == BACKEND_DIR / "app" / "storage"


def test_legacy_backend_storage_dir_resolves_from_repo_root() -> None:
    settings = Settings(storage_dir=Path("backend/app/storage"))

    assert settings.storage_dir == BACKEND_DIR / "app" / "storage"
