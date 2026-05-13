from pathlib import Path

from app.models import Document


def remove_document_files(documents: list[Document], storage_dir: Path) -> None:
    for document in documents:
        remove_file_if_in_storage(Path(document.storage_path), storage_dir)


def remove_file_if_in_storage(path: Path, storage_dir: Path) -> None:
    try:
        resolved_path = path.resolve()
        resolved_storage = storage_dir.resolve()
    except OSError:
        return

    if not _is_relative_to(resolved_path, resolved_storage):
        return
    if resolved_path.is_file():
        try:
            resolved_path.unlink(missing_ok=True)
        except OSError:
            return


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
