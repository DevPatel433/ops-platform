import re
from pathlib import Path

from .config import settings

_SAFE_NAME = re.compile(r"[a-z0-9-]+")


def list_runbooks() -> list[str]:
    directory = Path(settings.runbook_dir)
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob("*.md"))


def read_runbook(name: str) -> str | None:
    # Only allow simple slugs so user input can never escape the runbook directory.
    if not _SAFE_NAME.fullmatch(name):
        return None
    path = Path(settings.runbook_dir) / f"{name}.md"
    return path.read_text() if path.is_file() else None
