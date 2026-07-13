"""Network -> disk cache -> bundled snapshot ladder + provenance stamps."""

from __future__ import annotations

import json

import httpx
import pytest

import boutique_mcp.catalog as catalog_mod
from boutique_mcp.catalog import CatalogStore, CatalogUnavailableError


def test_offline_falls_back_to_bundled_snapshot(offline_store):
    catalog, provenance = offline_store.load()
    assert catalog.counts["total"] == 4
    assert provenance.origin == "bundled-snapshot"
    assert provenance.catalog_generated_at == "2026-07-13"
    assert "snapshot" in provenance.note


def test_disk_cache_preferred_over_snapshot(offline_store, fixture_catalog, tmp_path):
    cache = offline_store.cache_path
    cache.parent.mkdir(parents=True, exist_ok=True)
    data = fixture_catalog.model_dump()
    data["generated_at"] = "2026-07-10"
    cache.write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")

    catalog, provenance = offline_store.load()
    assert provenance.origin == "disk-cache"
    assert catalog.generated_at == "2026-07-10"


def test_network_200_writes_cache_and_etag(monkeypatch, tmp_path, fixture_catalog):
    monkeypatch.delenv("BOUTIQUE_MCP_OFFLINE", raising=False)
    payload = json.loads(
        json.dumps(fixture_catalog.model_dump(), ensure_ascii=False, default=str)
    )

    def fake_get(url, headers=None, timeout=None, follow_redirects=None):
        return httpx.Response(
            200, json=payload, headers={"etag": 'W/"abc123"'},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(catalog_mod.httpx, "get", fake_get)
    store = CatalogStore(cache_dir=tmp_path / "cache")
    _, provenance = store.load()
    assert provenance.origin == "network"
    assert store.cache_path.exists()
    assert store.etag_path.read_text(encoding="utf-8") == 'W/"abc123"'


def test_network_304_serves_disk_with_network_provenance(monkeypatch, tmp_path, fixture_catalog):
    monkeypatch.delenv("BOUTIQUE_MCP_OFFLINE", raising=False)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "catalog.json").write_text(
        json.dumps(fixture_catalog.model_dump(), ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (cache_dir / "catalog.etag").write_text('W/"abc123"', encoding="utf-8")

    seen = {}

    def fake_get(url, headers=None, timeout=None, follow_redirects=None):
        seen.update(headers or {})
        return httpx.Response(304, request=httpx.Request("GET", url))

    monkeypatch.setattr(catalog_mod.httpx, "get", fake_get)
    store = CatalogStore(cache_dir=cache_dir)
    _, provenance = store.load()
    assert seen.get("If-None-Match") == 'W/"abc123"'
    assert provenance.origin == "network"
    assert "304" in provenance.note


def test_network_error_falls_back_to_disk(monkeypatch, tmp_path, fixture_catalog):
    monkeypatch.delenv("BOUTIQUE_MCP_OFFLINE", raising=False)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "catalog.json").write_text(
        json.dumps(fixture_catalog.model_dump(), ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    def fake_get(url, headers=None, timeout=None, follow_redirects=None):
        raise httpx.ConnectError("no network")

    monkeypatch.setattr(catalog_mod.httpx, "get", fake_get)
    store = CatalogStore(cache_dir=cache_dir)
    _, provenance = store.load()
    assert provenance.origin == "disk-cache"


def test_everything_missing_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("BOUTIQUE_MCP_OFFLINE", "1")

    class _FakeResources:
        def joinpath(self, name):
            return tmp_path / "nonexistent" / name

    monkeypatch.setattr(catalog_mod.resources, "files", lambda _pkg: _FakeResources())
    store = CatalogStore(cache_dir=tmp_path / "cache")
    with pytest.raises(CatalogUnavailableError):
        store.load()


def test_stale_catalog_flagged(offline_store, monkeypatch):
    import boutique_mcp.catalog as cm

    stale, note = cm._staleness("2020-01-01")
    assert stale is True
    assert "days old" in note
