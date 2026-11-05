"""Runtime configuration.

Everything environment-specific comes from environment variables prefixed ``GSS_``
(optionally read from a ``.env`` file at the repository root, which is git-ignored).
Nothing here is secret for DuckDB, but the same mechanism carries credentials if the
warehouse is swapped for a server database.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader: KEY=VALUE lines, '#' comments, no interpolation.

    Existing environment variables win over the file, so CI and Docker can override.
    """
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    db_path: Path
    raw_dir: Path
    extracts_manifest: Path
    log_dir: Path
    log_level: str
    dbt_dir: Path
    dbt_target: str

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv(REPO_ROOT / ".env")

        def path(key: str, default: str) -> Path:
            value = os.environ.get(key, default)
            p = Path(value)
            return p if p.is_absolute() else REPO_ROOT / p

        return cls(
            db_path=path("GSS_DB_PATH", "data/gss.duckdb"),
            raw_dir=path("GSS_RAW_DIR", "source/data/raw"),
            extracts_manifest=path("GSS_EXTRACTS_MANIFEST", "source/data/extracts.json"),
            log_dir=path("GSS_LOG_DIR", "logs"),
            log_level=os.environ.get("GSS_LOG_LEVEL", "INFO").upper(),
            dbt_dir=path("GSS_DBT_DIR", "dbt"),
            dbt_target=os.environ.get("DBT_TARGET", "dev"),
        )
