"""Opt-in local audit log - tool name and timing ONLY, never query content.

Unlike the corpus connectors of the fleet (always-on, input-hash included),
boutique-mcp logs strictly {ts, tool, duration_ms, status} and only when the
user opts in, because the catalog connector's constitution (Article II)
forbids persisting anything derived from query content.

Enable with BOUTIQUE_MCP_AUDIT=1 (writes to ~/.matematic/audit/) or point
BOUTIQUE_MCP_AUDIT_DIR at a directory.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

Status = Literal["ok", "error"]

_AUDIT_FILENAME = "boutique-mcp.jsonl"


def _resolve_audit_dir() -> Path | None:
    env_dir = os.environ.get("BOUTIQUE_MCP_AUDIT_DIR")
    if env_dir:
        return Path(env_dir).expanduser()
    if os.environ.get("BOUTIQUE_MCP_AUDIT", "").strip() in ("1", "true", "yes"):
        return Path.home() / ".matematic" / "audit"
    return None


class AuditLogger:
    """Append-only JSONL logger; a no-op unless the user opted in."""

    def __init__(self, audit_dir: Path | None = None) -> None:
        self._dir = audit_dir if audit_dir is not None else _resolve_audit_dir()
        self._path: Path | None = None
        if self._dir is not None:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._path = self._dir / _AUDIT_FILENAME

    @property
    def enabled(self) -> bool:
        return self._path is not None

    @property
    def path(self) -> Path | None:
        return self._path

    def log(self, *, tool: str, duration_ms: int, status: Status, error: str | None = None) -> None:
        if self._path is None:
            return
        record = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "tool": tool,
            "duration_ms": duration_ms,
            "status": status,
        }
        if error is not None:
            record["error"] = error[:200]
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)


class _Timer:
    def __init__(self) -> None:
        self._t0 = 0.0
        self.duration_ms = 0

    def __enter__(self) -> _Timer:
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.duration_ms = int((time.perf_counter() - self._t0) * 1000)


def timer() -> _Timer:
    return _Timer()
