from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings = get_settings()
engine = create_engine(settings.database_url, connect_args=_connect_args(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def configure_database(database_url: str) -> None:
    global engine, SessionLocal
    engine = create_engine(database_url, connect_args=_connect_args(database_url))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables() -> None:
    # Import models before creating metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_sqlite_migrations()


def _apply_sqlite_migrations() -> None:
    if not engine.url.get_backend_name().startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("documents")}
    migrations = {
        "section_id": "ALTER TABLE documents ADD COLUMN section_id INTEGER",
        "page_count": "ALTER TABLE documents ADD COLUMN page_count INTEGER NOT NULL DEFAULT 0",
        "extracted_page_count": "ALTER TABLE documents ADD COLUMN extracted_page_count INTEGER NOT NULL DEFAULT 0",
        "extraction_method": "ALTER TABLE documents ADD COLUMN extraction_method VARCHAR(40) NOT NULL DEFAULT 'native'",
        "extraction_notes": "ALTER TABLE documents ADD COLUMN extraction_notes TEXT",
        "ocr_status": "ALTER TABLE documents ADD COLUMN ocr_status VARCHAR(40) NOT NULL DEFAULT 'not_required'",
    }
    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))

    for table_name in ("summaries", "quizzes"):
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            continue
        existing_output_columns = {column["name"] for column in inspector.get_columns(table_name)}
        with engine.begin() as connection:
            if "section_id" not in existing_output_columns:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN section_id INTEGER"))

    inspector = inspect(engine)
    if "schedule_items" not in inspector.get_table_names():
        return

    existing_schedule_columns = {column["name"] for column in inspector.get_columns("schedule_items")}
    schedule_migrations = {
        "reminder_minutes_before": "ALTER TABLE schedule_items ADD COLUMN reminder_minutes_before INTEGER",
    }
    with engine.begin() as connection:
        for column_name, statement in schedule_migrations.items():
            if column_name not in existing_schedule_columns:
                connection.execute(text(statement))


def drop_db_and_tables() -> None:
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
