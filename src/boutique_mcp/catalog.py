"""Catalog loading: network (ETag) -> disk cache -> bundled snapshot.

The connector always works offline: if the network refresh fails, it serves
the last catalog cached on disk, and if there is no cache yet, the snapshot
bundled with the package. Every response carries a Provenance stamp saying
which of the three sources answered and how old the catalog is.

No query content ever leaves the machine. The only network request this
module makes is a conditional GET of the public catalog.json.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime
from importlib import resources
from pathlib import Path

import httpx

from .models import CatalogFile, Provenance

CATALOG_URL = os.environ.get(
    "BOUTIQUE_MCP_CATALOG_URL", "https://matematicsolutions.com/catalog.json"
)
STALE_AFTER_DAYS = 60


class CatalogUnavailableError(Exception):
    """Neither network, disk cache nor bundled snapshot could provide a catalog."""


def _cache_dir() -> Path:
    env = os.environ.get("BOUTIQUE_MCP_CACHE_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".matematic" / "cache" / "boutique-mcp"


def _offline() -> bool:
    return os.environ.get("BOUTIQUE_MCP_OFFLINE", "").strip() in ("1", "true", "yes")


def _staleness(generated_at: str) -> tuple[bool, str]:
    try:
        gen = date.fromisoformat(generated_at[:10])
        age = (datetime.now(UTC).date() - gen).days
    except ValueError:
        return True, f"catalog date unparsable ({generated_at})"
    if age > STALE_AFTER_DAYS:
        return True, (
            f"catalog generated {generated_at}, {age} days old - consider checking {CATALOG_URL}"
        )
    return False, f"catalog generated {generated_at}, {age} days old"


class CatalogStore:
    """Loads and caches the Boutique catalog with explicit provenance."""

    def __init__(self, cache_dir: Path | None = None, url: str | None = None) -> None:
        self._dir = cache_dir or _cache_dir()
        self._url = url or CATALOG_URL
        self._catalog: CatalogFile | None = None
        self._provenance: Provenance | None = None

    @property
    def cache_path(self) -> Path:
        return self._dir / "catalog.json"

    @property
    def etag_path(self) -> Path:
        return self._dir / "catalog.etag"

    def load(self) -> tuple[CatalogFile, Provenance]:
        """Return the freshest available catalog, memoized per process."""
        if self._catalog is not None and self._provenance is not None:
            return self._catalog, self._provenance

        catalog, provenance = self._load_uncached()
        self._catalog, self._provenance = catalog, provenance
        return catalog, provenance

    def _load_uncached(self) -> tuple[CatalogFile, Provenance]:
        if not _offline():
            fetched = self._try_network()
            if fetched is not None:
                return fetched

        cached = self._try_disk()
        if cached is not None:
            return cached

        return self._bundled()

    def _try_network(self) -> tuple[CatalogFile, Provenance] | None:
        headers = {}
        if self.etag_path.exists() and self.cache_path.exists():
            headers["If-None-Match"] = self.etag_path.read_text(encoding="utf-8").strip()
        try:
            resp = httpx.get(self._url, headers=headers, timeout=10.0, follow_redirects=True)
        except httpx.HTTPError:
            return None

        now = datetime.now(UTC).isoformat(timespec="seconds")
        if resp.status_code == 304:
            disk = self._try_disk()
            if disk is None:
                return None
            catalog, _ = disk
            stale, note = _staleness(catalog.generated_at)
            return catalog, Provenance(
                origin="network",
                catalog_generated_at=catalog.generated_at,
                fetched_at=now,
                stale=stale,
                note=f"revalidated by ETag (304), {note}",
            )
        if resp.status_code != 200:
            return None
        try:
            catalog = CatalogFile.model_validate(resp.json())
        except (json.JSONDecodeError, ValueError):
            return None

        self._dir.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(resp.json(), ensure_ascii=False), encoding="utf-8"
        )
        etag = resp.headers.get("etag")
        if etag:
            self.etag_path.write_text(etag, encoding="utf-8")
        stale, note = _staleness(catalog.generated_at)
        return catalog, Provenance(
            origin="network",
            catalog_generated_at=catalog.generated_at,
            fetched_at=now,
            stale=stale,
            note=note,
        )

    def _try_disk(self) -> tuple[CatalogFile, Provenance] | None:
        if not self.cache_path.exists():
            return None
        try:
            catalog = CatalogFile.model_validate(
                json.loads(self.cache_path.read_text(encoding="utf-8"))
            )
        except (json.JSONDecodeError, ValueError):
            return None
        stale, note = _staleness(catalog.generated_at)
        return catalog, Provenance(
            origin="disk-cache",
            catalog_generated_at=catalog.generated_at,
            stale=stale,
            note=f"network unavailable, serving last cached catalog; {note}",
        )

    def _bundled(self) -> tuple[CatalogFile, Provenance]:
        try:
            raw = (
                resources.files("boutique_mcp")
                .joinpath("data/catalog-snapshot.json")
                .read_text(encoding="utf-8")
            )
            catalog = CatalogFile.model_validate(json.loads(raw))
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
            raise CatalogUnavailableError(
                "no network, no disk cache and the bundled snapshot is unreadable"
            ) from exc
        stale, note = _staleness(catalog.generated_at)
        return catalog, Provenance(
            origin="bundled-snapshot",
            catalog_generated_at=catalog.generated_at,
            stale=stale,
            note=f"offline, serving the snapshot bundled with the package; {note}",
        )


_store: CatalogStore | None = None


def get_store() -> CatalogStore:
    global _store
    if _store is None:
        _store = CatalogStore()
    return _store
