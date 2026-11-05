"""Structured logging: JSON lines to a file plus a readable line on stderr.

Each event is one JSON object with at least ``ts``, ``level``, ``event`` and, when known,
``extract`` and ``run_id``. The file is append-only so every historical run stays
inspectable (``logs/pipeline.jsonl``).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        extra = getattr(record, "ctx", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class HumanFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ctx = getattr(record, "ctx", None)
        suffix = ""
        if isinstance(ctx, dict) and ctx:
            suffix = "  " + " ".join(f"{k}={v}" for k, v in ctx.items() if k != "validation")
        return f"{record.levelname:7s} {record.getMessage()}{suffix}"


def configure_logging(log_dir: Path, level: str = "INFO", filename: str = "pipeline.jsonl") -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("gss")
    root.setLevel(level)
    root.handlers.clear()
    root.propagate = False

    file_handler = logging.FileHandler(log_dir / filename, encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())
    root.addHandler(file_handler)

    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(HumanFormatter())
    root.addHandler(stream)
    return root


def log(logger: logging.Logger, level: int, event: str, **ctx) -> None:
    """Emit ``event`` with context fields; keeps call sites short."""
    logger.log(level, event, extra={"ctx": ctx})
