# Tasks: Lokalny konektor-katalog Boutique

## Phase 1 - Setup
- [ ] T001 Init repo boutique-mcp (pyproject, LICENSE Apache-2.0, README szkielet, .gitignore)
- [ ] T002 [P] Konfiguracja ruff + pytest (wzorzec pk-eli-mcp)

## Phase 2 - Foundational (BLOKUJE user stories)
- [ ] T004 [US5] Generator tools/generate-catalog.py w www-matematic (JSON-LD 3 lokali -> catalog.json wg contracts/catalog.schema.json)
- [ ] T005 [US5] Walidacja preflight (liczba wpisow == kafelki; schemat) + podpiecie do CI
- [ ] T006 [US5] .well-known/mcp/server-card.json + wpis catalog.json w loggerze adopcji
- [ ] T007 models.py (pydantic CatalogEntry/CatalogFile) + bundlowany snapshot z wygenerowanego catalog.json

## Phase 3 - US1+US2 (P1, MVP)
- [ ] T010 catalog.py: load siec ETag -> cache dysk -> snapshot, provenance stamp (depends T007)
- [ ] T011 search.py: scoring + filtry + gaps[] (depends T007)
- [ ] T012 server.py: FastMCP INSTRUCTIONS + boutique_search + boutique_get, read-only annotations, audit opt-in
- [ ] T013 [P] testy: test_search.py + test_catalog_provisioning.py na fixture

**Checkpoint:** MVP - search+get dzialaja offline na snapshocie.

## Phase 4 - US3+US4 (P2)
- [ ] T020 boutique_whats_new (since_date, domyslnie 30 dni od daty generacji katalogu)
- [ ] T021 boutique_request_coverage (draft only, zero sieci)
- [ ] T022 [P] testy US3/US4 + test_instructions_drift.py + test_smoke.py

## Phase N - Polish + publikacja
- [ ] T030 README EN (humanizer-en -> reviewer-en), CHANGELOG
- [ ] T031 ruff clean + pytest zielone + leak-scan
- [ ] T032 server.json (desc <=100 zn, lockstep) + glama.json + release.yml + marker mcp-name w README
- [ ] T033 Publikacja: repo GitHub, tag v0.1.0 -> PyPI (budzet nowych projektow!) + MCP Registry
- [ ] T034 Kafel Boutique 3 jezyki wg checklisty + humanizer-pl -> marko-pl (karta PL) + $pypiPkgs logger
- [ ] T035 Weryfikacja: uv run --isolated --with boutique-mcp==0.1.0 + curl produkcji (catalog.json, server-card, karty)

## Parallel Opportunities
T002 rownolegle z T001; T013/T022 rownolegle z kolejnymi toolami; T030 rownolegle z T032.
