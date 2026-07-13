# Plan: Lokalny konektor-katalog Boutique

**Spec:** ./spec.md
**Project Type:** mcp-server

## Technical Context
- **Language/Version:** Python 3.11+ (chassis fabryki, wzorzec pk-eli-mcp)
- **Primary Dependencies:** fastmcp>=3.4, httpx>=0.27, pydantic>=2.6
- **Storage:** brak bazy; catalog.json (siec z ETag -> cache na dysku ~/.matematic/cache/boutique-mcp/ -> bundlowany snapshot w paczce)
- **Testing:** pytest (fixture catalog.json, drift test, offline fallback, walidacja schematu)
- **Target Platform:** cross-platform (stdio, uvx)
- **Performance Goals:** wyszukiwanie < 50 ms na katalogu ~100 wpisow (scoring w pamieci, bez FTS-bazy - katalog jest maly)
- **Constraints:** zero-cloud (stdio), offline-capable, zero telemetrii zapytan, read-only
- **Scale/Scope:** ~80-100 wpisow katalogu (43 konektory + 35 skilli + 8 kuratorskich), 3 jezyki

## Constitution Check (GATE)

| Bramka konstytucji | Status | Notatka |
|---|---|---|
| Mission alignment | PASS | Dystrybucja calej floty jednym konektorem |
| Article I (zero proxy) | PASS | Toole zwracaja tylko karty + komendy instalacji |
| Article II (zero telemetrii) | PASS | Brak logowania zapytan; audit opt-in = nazwa toola + timestamp |
| Article III (single source) | PASS | Generator w CI www-matematic, zrodlo = JSON-LD kafelkow |
| Article IV (offline-first) | PASS | ETag cache + bundlowany snapshot + stamp provenance |
| Article V (granica governance) | PASS | request_coverage = draft only |
| Article VI (read-only, <=800 linii) | PASS | ToolAnnotations readOnlyHint; moduly rozbite |
| Article VII (drift) | PASS | test_instructions_drift.py w pytest |
| Bramka licencji | PASS | Apache-2.0; zaleznosci Apache/BSD/MIT |
| Bramka ToS / anty-OS | PASS | Wlasny katalog wlasnych produktow; zero scrapingu obcych |
| Bramka jakosci | PASS | Chassis sprawdzony w 33 paczkach floty; utrzymanie = regeneracja katalogu w CI, zero recznej pracy |
| Bramka strategii | PASS | Warstwa discovery floty; kontr-pitch wobec hostowanych proxy (Lawstronaut/ThomasMore) |

## Project Structure
```
boutique-mcp/
├── .matematic/                  # konstytucja + spec (ten katalog)
├── .github/workflows/release.yml  # PyPI (PYPI_API_TOKEN) + MCP Registry (OIDC)
├── src/boutique_mcp/
│   ├── __init__.py
│   ├── server.py                # FastMCP, INSTRUCTIONS, 4 toole, main()
│   ├── catalog.py               # load/refresh: siec ETag -> cache dysk -> snapshot; provenance stamp
│   ├── search.py                # scoring w pamieci + gaps[]
│   ├── models.py                # pydantic: CatalogEntry, CatalogFile, SearchResult, ...
│   ├── audit.py                 # opt-in audit log (nazwa toola + ts), wzorzec floty
│   └── data/catalog-snapshot.json  # bundlowany snapshot z data generacji
├── tests/
│   ├── fixtures/catalog-fixture.json
│   ├── test_search.py
│   ├── test_catalog_provisioning.py   # ETag/cache/offline fallback
│   ├── test_instructions_drift.py
│   └── test_smoke.py
├── pyproject.toml               # boutique-mcp, Apache-2.0, entry point
├── server.json                  # MCP Registry, desc <=100 zn, wersja lockstep
├── glama.json, README.md, LICENSE, CHANGELOG.md
```

W repo www-matematic (osobny commit):
```
tools/generate-catalog.py        # parser JSON-LD/kafelkow 3 lokali -> catalog.json
.github/workflows/catalog.yml    # generacja + walidacja preflight przy pushu (lub istniejacy workflow)
catalog.json                     # artefakt w repo (Cloudflare Pages serwuje statycznie)
.well-known/mcp/server-card.json # karta serwera boutique-mcp
```

## Research notes
- Krok 0: mcp-eureka = konektor EUREKA/KIS, zero overlapu. skills.sh "catalog" i MCP Registry (marketplace/catalog/discovery) = brak gotowego wzorca. Budujemy pierwsi.
- Katalog ~100 wpisow: pelny FTS (SQLite) odrzucony - scoring substring/token w pamieci wystarcza i zeruje zaleznosci (Simpler Alternative wygrywa).
- Zrodlo generatora: JSON-LD ItemList w boutique/konektory.html + en + pt (SoftwareApplication) oraz kafelki skilli; liczniki weryfikowane jak w preflight checkliscie.
- server-card.json: otwarta wersja wzorca Lawstronaut (.well-known discovery), tresc = metadane serwera + install, zero endpointow invoke.

## Complexity Tracking
Brak violations.
