from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import boutique_mcp.catalog as catalog_mod
from boutique_mcp.models import CatalogFile

FIXTURE = Path(__file__).parent / "fixtures" / "catalog-fixture.json"


@pytest.fixture()
def fixture_catalog() -> CatalogFile:
    return CatalogFile.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


@pytest.fixture()
def offline_store(tmp_path, monkeypatch):
    """A CatalogStore that never touches the network and has no disk cache,
    with the test fixture standing in for the bundled snapshot."""
    monkeypatch.setenv("BOUTIQUE_MCP_OFFLINE", "1")
    snapshot_dir = tmp_path / "pkg" / "data"
    snapshot_dir.mkdir(parents=True)
    shutil.copy(FIXTURE, snapshot_dir / "catalog-snapshot.json")

    store = catalog_mod.CatalogStore(cache_dir=tmp_path / "cache")

    class _FakeResources:
        def joinpath(self, name):
            return tmp_path / "pkg" / name

    monkeypatch.setattr(catalog_mod.resources, "files", lambda _pkg: _FakeResources())
    return store


@pytest.fixture(autouse=True)
def _no_audit(monkeypatch):
    monkeypatch.delenv("BOUTIQUE_MCP_AUDIT", raising=False)
    monkeypatch.delenv("BOUTIQUE_MCP_AUDIT_DIR", raising=False)


@pytest.fixture(autouse=True)
def _reset_store_singleton(monkeypatch):
    monkeypatch.setattr(catalog_mod, "_store", None)
