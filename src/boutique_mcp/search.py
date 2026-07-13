"""In-memory scoring over the catalog. ~100 entries - no index needed.

Scoring is deliberately simple and dependency-free: token overlap across id,
name, category, jurisdiction and description in every language the entry has.
When nothing clears the threshold the result names the gap explicitly instead
of returning weak matches (the banhmi gaps[] pattern).
"""

from __future__ import annotations

import re
import unicodedata

from .models import CatalogEntry, Gap, SearchHit

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9-]{1,}")
_MIN_SCORE = 1.0


def _fold(text: str) -> str:
    """Lowercase + strip diacritics so 'sąd'/'sad' and 'São'/'Sao' match."""
    norm = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in norm if not unicodedata.combining(c))


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(_fold(text))


def _entry_fields(entry: CatalogEntry) -> list[tuple[str, float]]:
    fields: list[tuple[str, float]] = [(entry.id, 3.0)]
    fields.extend((v, 2.5) for v in entry.jurisdiction.values())
    fields.extend((v, 2.5) for v in entry.name.values())
    fields.extend((v, 2.0) for v in entry.category.values())
    fields.extend((v, 1.0) for v in entry.description.values())
    fields.extend((v, 0.5) for v in entry.problem.values())
    return fields


def score_entry(entry: CatalogEntry, query_tokens: list[str]) -> float:
    """Per query token take the BEST matching field, then sum over tokens.

    Summing every language variant of every field would triple-count a hit
    ('legislation' appearing in the PL, EN and PT description is one signal,
    not three), so a token contributes its single strongest field weight.
    """
    score = 0.0
    fields = [(_fold(t), set(_tokens(t)), w) for t, w in _entry_fields(entry)]
    for qt in query_tokens:
        best = 0.0
        for folded, field_tokens, weight in fields:
            if qt in field_tokens:
                best = max(best, weight)
            elif len(qt) >= 4 and qt in folded:
                best = max(best, weight * 0.5)
        score += best
    return score


def _pick_lang(d: dict[str, str], languages: list[str]) -> str | None:
    for lang in ("en", "pl", "pt"):
        if d.get(lang):
            return d[lang]
    for lang in languages:
        if d.get(lang):
            return d[lang]
    return next(iter(d.values()), None)


def to_hit(entry: CatalogEntry, score: float) -> SearchHit:
    return SearchHit(
        id=entry.id,
        type=entry.type,
        name=_pick_lang(entry.name, entry.languages) or entry.id,
        description=_pick_lang(entry.description, entry.languages),
        category=_pick_lang(entry.category, entry.languages),
        jurisdiction=_pick_lang(entry.jurisdiction, entry.languages),
        install=entry.install,
        version=entry.version,
        license=entry.license,
        card_url=_pick_lang(entry.card_url, entry.languages),
        score=round(score, 2),
    )


def search(
    entries: list[CatalogEntry],
    query: str,
    jurisdiction: str | None = None,
    entry_type: str | None = None,
    limit: int = 10,
) -> tuple[list[SearchHit], list[Gap]]:
    query_tokens = _tokens(query)
    gaps: list[Gap] = []

    pool = entries
    if entry_type:
        pool = [e for e in pool if e.type == entry_type]
        if not pool:
            gaps.append(
                Gap(
                    kind="type_uncovered",
                    detail=f"no catalog entries of type '{entry_type}'",
                    suggestion="valid types: konektor, skill, kuratorski",
                )
            )
    if jurisdiction:
        jur = _fold(jurisdiction)
        matched = [
            e for e in pool
            if any(jur in _fold(label) for label in e.jurisdiction.values())
        ]
        if not matched:
            gaps.append(
                Gap(
                    kind="jurisdiction_uncovered",
                    detail=f"no entry covers jurisdiction '{jurisdiction}'",
                    suggestion=(
                        "call boutique_request_coverage to draft a coverage request "
                        "a human can submit"
                    ),
                )
            )
        pool = matched

    scored = sorted(
        ((score_entry(e, query_tokens), e) for e in pool),
        key=lambda pair: (-pair[0], pair[1].id),
    )
    hits = [to_hit(e, s) for s, e in scored if s >= _MIN_SCORE][:limit]

    if not hits and not any(g.kind != "no_match" for g in gaps):
        gaps.append(
            Gap(
                kind="no_match",
                detail=f"nothing in the catalog matches '{query}'",
                suggestion=(
                    "broaden the query (try an English or Polish keyword), or call "
                    "boutique_request_coverage to draft a coverage request"
                ),
            )
        )
    return hits, gaps


def closest_ids(entries: list[CatalogEntry], wanted: str, n: int = 5) -> list[str]:
    """Cheap did-you-mean for boutique_get: rank ids by shared character bigrams."""
    w = _fold(wanted)
    grams = {w[i : i + 2] for i in range(len(w) - 1)}

    def sim(eid: str) -> float:
        f = _fold(eid)
        egrams = {f[i : i + 2] for i in range(len(f) - 1)}
        return len(grams & egrams) / max(1, len(grams | egrams))

    ranked = sorted(entries, key=lambda e: -sim(e.id))
    return [e.id for e in ranked[:n] if sim(e.id) > 0.1]
