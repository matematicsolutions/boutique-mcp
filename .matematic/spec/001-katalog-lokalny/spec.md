# Feature: Lokalny konektor-katalog Boutique (MVP)

**Branch:** `001-katalog-lokalny`
**Date:** 2026-07-13
**Status:** Planned

## Problem statement
Agent (Claude Code, Cursor, dowolny klient MCP) nie wie, ktory z 43+ konektorow i 35+ skilli MateMatic rozwiazuje jego problem. Dzis musi przegladac strone Boutique reka. Kategoria discovery jest zagospodarowywana przez hostowane proxy (Lawstronaut, ThomasMore), ktore loguja zapytania prawnikow. Lokalny katalog daje discovery bez wycieku zapytan.

## User Stories

### US1 (P1, MVP) - Znajdz klocek
**Jako** agent MCP **chce** wyszukac po katalogu Boutique ("orzecznictwo SN", "german law", "anonimizacja") **zeby** dostac karty pasujacych klockow z komenda instalacji lokalnej.

**Acceptance Criteria:**
- [ ] AC1.1: boutique_search(query) zwraca liste kart (id, nazwa, opis, typ, jurysdykcja, install command, url karty) posortowana wg trafnosci.
- [ ] AC1.2: filtry opcjonalne jurysdykcja i typ (konektor/skill/kuratorski) zawezaja wyniki.
- [ ] AC1.3: przy braku pokrycia wynik zawiera gaps[] z opisem luki i wskazaniem boutique_request_coverage.
- [ ] AC1.4: wyszukiwanie dziala offline na bundlowanym snapshocie; kazda odpowiedz ma stamp "katalog z dnia X, zrodlo: siec/cache/snapshot".

**Independent Test:** na fixture catalog.json zapytanie "saos" zwraca mcp-saos z komenda `npx @matematicsolutions/mcp-saos`; zapytanie "prawo marsjanskie" zwraca gaps[].

### US2 (P1) - Pelna karta klocka
**Jako** agent **chce** boutique_get(id) **zeby** dostac pelna karte: opis 3-jezyczny, instalacje, wersje, licencje, link do karty Boutique i repo.

**Acceptance Criteria:**
- [ ] AC2.1: boutique_get zwraca komplet pol wpisu katalogu.
- [ ] AC2.2: nieznane id zwraca czytelny blad z podpowiedzia najblizszych id (bez wyjatku).

**Independent Test:** boutique_get("mcp-saos") na fixture zwraca karte z install i licencja; boutique_get("nie-ma") zwraca blad z sugestiami.

### US3 (P2) - Co nowego
**Jako** agent **chce** boutique_whats_new(since_date?) **zeby** zobaczyc, co doszlo lub zostalo zbumpowane od danej daty.

**Acceptance Criteria:**
- [ ] AC3.1: zwraca wpisy z added_at/updated_at >= since_date, podzielone na nowe i zaktualizowane.
- [ ] AC3.2: bez since_date domyslnie ostatnie 30 dni wzgledem daty generacji katalogu (nie zegara systemowego, zeby dzialac deterministycznie offline).

**Independent Test:** fixture z 3 wpisami o roznych datach; since_date odcina prawidlowo.

### US4 (P2) - Draft zgloszenia luki
**Jako** agent **chce** boutique_request_coverage(opis) **zeby** dostac gotowy DRAFT zgloszenia (tytul + body issue na github.com/matematicsolutions), ktory czlowiek sam wysle.

**Acceptance Criteria:**
- [ ] AC4.1: zwraca tekst draftu (tytul, body, sugerowany URL formularza new issue) i JAWNE zastrzezenie, ze niczego nie wyslano.
- [ ] AC4.2: tool nie wykonuje zadnego zapisu ani wywolania sieciowego.

**Independent Test:** wywolanie zwraca draft; monkeypatch httpx potwierdza zero requestow.

### US5 (P1, infrastruktura) - catalog.json z CI www-matematic
**Jako** maintainer **chce** generator catalog.json w CI www-matematic z tego samego zrodla co JSON-LD kafelkow **zeby** katalog nigdy nie rozjechal sie ze strona.

**Acceptance Criteria:**
- [ ] AC5.1: generator czyta kafelki/JSON-LD z 3 lokali (PL/EN/PT) i emituje catalog.json (schemat w contracts/catalog.schema.json).
- [ ] AC5.2: preflight: liczba wpisow == liczba kafelkow `id="conn-"` + kafelki skilli; rozjazd = fail CI.
- [ ] AC5.3: catalog.json publikowany na matematicsolutions.com/catalog.json; .well-known/mcp/server-card.json opisuje boutique-mcp (wersja otwarta wzorca Lawstronaut).
- [ ] AC5.4: pobrania catalog.json dopisane do loggera adopcji (wzorzec licznika llms.txt).

**Independent Test:** uruchomienie generatora lokalnie na repo www-matematic produkuje catalog.json przechodzacy walidacje schematu i zgodnosc liczby wpisow.

## Non-Goals (anti-scope)
- Zadnego hostowanego discover/invoke proxy (czerwona linia WM).
- Zadnego logowania tresci zapytan (czerwona linia WM).
- Zadnej instalacji klockow przez serwer (tylko komenda do skopiowania).
- Rollout chassis v2 verify_citations na flote - osobny tor.
- Rekomendacje konkurencyjnych narzedzi spoza katalogu MateMatic.

## Open Questions / NEEDS CLARIFICATION
- (rozstrzygniete w briefie WM 2026-07-13: nazwa paczki boutique-mcp, PyPI, chassis Python)
