# boutique-mcp - Konstytucja

## Mission (1 zdanie)
Agent z zainstalowanym boutique-mcp znajduje wlasciwy klocek MateMatic (konektor lub skill) jednym wywolaniem i dostaje komende instalacji LOKALNEJ - katalog wskazuje, niczego nie proxuje.

## Core Principles

### Article I - Lokalna instalacja, zero proxy (CZERWONA LINIA)
Serwer MUST NOT hostowac zadnego discover/invoke proxy (model ThomasMore). Kazdy wynik wyszukiwania MUST konczyc sie komenda instalacji lokalnej (uvx/npx) lub linkiem do zrodla. Serwer MUST NOT wykonywac ani posredniczyc w wywolaniach innych konektorow.

### Article II - Zero telemetrii zapytan (CZERWONA LINIA)
Serwer MUST NOT logowac, wysylac ani przechowywac tresci zapytan uzytkownika poza pamiecia procesu. Jedyna dopuszczalna metryka adopcji to licznik pobran catalog.json po stronie CDN (Cloudflare), bez tresci zapytan. Audit log (lokalny, opt-in przez env) MUST zapisywac wylacznie nazwe toola i timestamp, nigdy parametry zapytania.

### Article III - Single source of truth katalogu
catalog.json MUST byc generowany w CI www-matematic z tego samego zrodla co JSON-LD kafelkow (3 jezyki PL/EN/PT). Reczna edycja catalog.json poza generatorem = zakazana. Preflight MUST walidowac zgodnosc liczby wpisow z kafelkami; drift = fail CI.

### Article IV - Offline-first z jawna provenance
Konektor MUST dzialac bez sieci na bundlowanym snapshocie katalogu. Kazda odpowiedz MUST zawierac jawny stamp zrodla i wieku danych ("katalog z dnia X, zrodlo: siec/cache/snapshot"). Cache sieciowy przez ETag/If-None-Match.

### Article V - Granica governance dla aktow na zewnatrz
boutique_request_coverage MUST przygotowac wylacznie DRAFT zgloszenia (tekst issue). Wyslanie = czlowiek. Zaden tool MUST NOT wykonywac aktow na zewnatrz (issue, mail, HTTP POST).

### Article VI - Read-only i limit rozmiaru
Wszystkie toole MUST miec ToolAnnotations readOnlyHint=true. Pliki z logika biznesowa MUST pozostac <= 800 linii; przekroczenie wymaga rozbicia modulu, nie wyjatku w konstytucji.

### Article VII - Drift INSTRUCTIONS <-> TOOLS
INSTRUCTIONS serwera MUST wymieniac dokladnie te toole, ktore serwer rejestruje; test driftu w pytest MUST pilnowac spojnosci (wzorzec matematic-mcp-fastmcp-instructions-pl).

## Boundaries (granice)
- **Robi:** wyszukiwanie po lokalnej kopii katalogu Boutique, karta klocka z komenda instalacji, przeglad nowosci od daty, draft zgloszenia luki pokrycia.
- **Nie robi:** nie instaluje niczego, nie wykonuje konektorow, nie hostuje API, nie zbiera telemetrii, nie tlumaczy tresci prawnych (od tego sa konektory floty).
- **Wspolpracuje z:** www-matematic (generator catalog.json w CI), flota konektorow matematicsolutions (obiekty katalogu), logger adopcji (licznik pobran CDN).

## Governance (kto decyduje)
- Owner: Wieslaw Mazur
- Reviewers: reviewer-en (docs EN), marko-pl-content (karta Boutique PL), pytest/ruff/leak-scan (kod)
- Amendment process: zmiana konstytucji przez WM, SEMVER + wpis w Amendments

## Compliance Map
- Licencja projektu: Apache-2.0 (zgodna z fastmcp Apache-2.0, httpx BSD, pydantic MIT)
- RODO: katalog zawiera wylacznie publiczne metadane produktow MateMatic, zero danych osobowych; zero-cloud (stdio)
- AI Act art. 12: audit log lokalny opt-in (nazwa toola + timestamp)

## Amendments
- 0.1.0 (2026-07-13): ratyfikacja.

**Version:** 0.1.0 | **Ratified:** 2026-07-13 | **Last Amended:** 2026-07-13
