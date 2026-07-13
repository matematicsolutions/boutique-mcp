"""Tool-level smoke tests over the offline fixture (no network)."""

from __future__ import annotations

import pytest

import boutique_mcp.server as server_mod
from boutique_mcp.server import (
    ToolError,
    boutique_get,
    boutique_request_coverage,
    boutique_search,
    boutique_whats_new,
)


@pytest.fixture(autouse=True)
def _wire_store(offline_store, monkeypatch):
    monkeypatch.setattr(server_mod, "get_store", lambda: offline_store)


def _fn(tool):
    return getattr(tool, "fn", tool)


async def test_search_tool_returns_hits_and_stamp():
    result = await _fn(boutique_search)("saos orzecznictwo")
    assert result.hits[0].id == "mcp-saos"
    assert result.provenance.origin == "bundled-snapshot"


async def test_search_tool_rejects_empty_query():
    with pytest.raises(ToolError, match=r"\[invalid_arg\]"):
        await _fn(boutique_search)("   ")


async def test_search_tool_rejects_bad_type():
    with pytest.raises(ToolError, match=r"\[invalid_arg\]"):
        await _fn(boutique_search)("saos", entry_type="plugin")


async def test_get_tool_full_card():
    result = await _fn(boutique_get)("de-eli-mcp")
    assert result["entry"]["install"]["command"] == "uvx de-eli-mcp"
    assert result["entry"]["license"] == "Apache-2.0"
    assert result["provenance"]["origin"] == "bundled-snapshot"


async def test_get_tool_not_found_suggests():
    with pytest.raises(ToolError, match=r"\[not_found\].*mcp-saos"):
        await _fn(boutique_get)("mcp-soas")


async def test_whats_new_default_window():
    result = await _fn(boutique_whats_new)()
    # generated_at 2026-07-13 => since 2026-06-13
    assert result.since == "2026-06-13"
    added_ids = {h.id for h in result.added}
    updated_ids = {h.id for h in result.updated}
    assert "de-eli-mcp" in added_ids  # added 2026-06-20
    assert "mcp-saos" in updated_ids  # added in May, updated 2026-07-13
    assert "humanizer-pl" not in added_ids | updated_ids


async def test_whats_new_explicit_date_and_invalid():
    result = await _fn(boutique_whats_new)("2026-07-05")
    assert {h.id for h in result.updated} == {"mcp-saos"}
    with pytest.raises(ToolError, match=r"\[invalid_arg\]"):
        await _fn(boutique_whats_new)("wczoraj")


async def test_request_coverage_is_draft_only(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("request_coverage must not touch the network")

    import boutique_mcp.catalog as catalog_mod

    monkeypatch.setattr(catalog_mod.httpx, "get", _boom)
    draft = await _fn(boutique_request_coverage)(
        "Czech case law connector", jurisdiction="Czechy"
    )
    assert draft.title.startswith("Coverage request (Czechy):")
    assert "Nothing has been sent" in draft.disclaimer
    assert draft.submit_url.startswith("https://github.com/matematicsolutions/")
