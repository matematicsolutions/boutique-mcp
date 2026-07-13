from __future__ import annotations

from boutique_mcp.search import closest_ids, search


def test_search_finds_saos(fixture_catalog):
    hits, gaps = search(fixture_catalog.entries, "saos")
    assert hits and hits[0].id == "mcp-saos"
    assert hits[0].install.command == "npx -y @matematicsolutions/mcp-saos"
    assert not gaps


def test_search_diacritics_folded(fixture_catalog):
    hits, _ = search(fixture_catalog.entries, "orzecznictwo sąd")
    assert any(h.id == "mcp-saos" for h in hits)


def test_search_cross_language(fixture_catalog):
    hits, _ = search(fixture_catalog.entries, "german legislation")
    assert hits and hits[0].id == "de-eli-mcp"


def test_search_no_match_yields_gap(fixture_catalog):
    hits, gaps = search(fixture_catalog.entries, "prawo marsjanskie kosmiczne")
    assert not hits
    assert gaps and gaps[0].kind == "no_match"
    assert "boutique_request_coverage" in gaps[0].suggestion


def test_search_jurisdiction_filter(fixture_catalog):
    hits, _ = search(fixture_catalog.entries, "eli", jurisdiction="Niemcy")
    assert hits and all(h.id == "de-eli-mcp" for h in hits)
    # filtr dziala tez po etykiecie w innym jezyku
    hits_en, _ = search(fixture_catalog.entries, "eli", jurisdiction="Germany")
    assert {h.id for h in hits_en} == {h.id for h in hits}
    hits2, gaps2 = search(fixture_catalog.entries, "eli", jurisdiction="Francja")
    assert not hits2
    assert any(g.kind == "jurisdiction_uncovered" for g in gaps2)


def test_search_type_filter(fixture_catalog):
    hits, _ = search(fixture_catalog.entries, "ai act", entry_type="kuratorski")
    assert hits and hits[0].id == "morellid/ai-act-skill"
    assert hits[0].install.kind == "github"


def test_search_skill_download_install(fixture_catalog):
    hits, _ = search(fixture_catalog.entries, "humanizer redakcja")
    assert hits and hits[0].id == "humanizer-pl"
    assert hits[0].install.kind == "download"
    assert hits[0].install.url.endswith("humanizer-pl.zip")


def test_closest_ids(fixture_catalog):
    got = closest_ids(fixture_catalog.entries, "mcp-soas")
    assert "mcp-saos" in got
