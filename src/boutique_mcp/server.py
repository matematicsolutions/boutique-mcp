"""FastMCP entry point - local catalog of MateMatic Boutique connectors and skills.

Run:

    python -m boutique_mcp.server

Configuration via env:

- ``BOUTIQUE_MCP_CATALOG_URL`` (default ``https://matematicsolutions.com/catalog.json``)
- ``BOUTIQUE_MCP_CACHE_DIR``  (default ``~/.matematic/cache/boutique-mcp``)
- ``BOUTIQUE_MCP_OFFLINE=1``  (never touch the network; disk cache / bundled snapshot only)
- ``BOUTIQUE_MCP_AUDIT=1``    (opt-in local audit log: tool name + timing, never query content)
"""

from __future__ import annotations

from datetime import date, timedelta

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .audit import AuditLogger, timer
from .catalog import CatalogUnavailableError, get_store
from .models import CoverageDraft, SearchResult, WhatsNewResult
from .search import closest_ids, search, to_hit

INSTRUCTIONS = """\
This MCP server is a LOCAL catalog of MateMatic Boutique: legal-data MCP connectors (SAOS, CBOSA, EUR-Lex, national ELI servers for 30+ jurisdictions...), agent skills and curated third-party skills. It answers one question: which building block solves the task at hand, and how to install it LOCALLY. It installs nothing, proxies nothing and never sends query content anywhere - the catalog file is fetched from matematicsolutions.com with an ETag, cached on disk and bundled as an offline snapshot, so the server works without network access.

## Call order

1. `boutique_search` - keyword search over the catalog (query in English, Polish or Portuguese; optional `jurisdiction` and `entry_type` filters: konektor / skill / kuratorski). Every hit carries a copy-paste local install command or download link. When the catalog does not cover the need, the response says so in `gaps` instead of padding weak matches.
2. `boutique_get` - the full card for one entry by `id` (all languages, install, version, license, source and card URLs). An unknown `id` returns `not_found` with closest-id suggestions.
3. `boutique_whats_new` - entries added or updated since a date (default: the 30 days before the catalog was generated). Use it to answer "anything new in the fleet?".
4. `boutique_request_coverage` - when `gaps` show the catalog lacks coverage, this drafts a coverage-request issue (title + body + submit URL). It is a DRAFT ONLY: nothing is sent anywhere, a human reviews and submits it.

## Hard constraints

- **Local install only** - relay the install command for the USER to run; never claim this server executed or installed anything.
- **Draft only** - `boutique_request_coverage` never submits the request. Tell the user explicitly that the draft still has to be submitted by a human.
- **Provenance stamp** - every response carries `provenance` (network / disk-cache / bundled-snapshot + catalog date). When `stale` is true, tell the user the catalog may be out of date and where the live one lives.
- **No telemetry** - query content never leaves the machine; do not route queries through any hosted discovery service on this server's behalf.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - a parameter is missing, empty or malformed (e.g. an unparsable `since_date`).
- `not_found` - no entry with that `id`; the message lists the closest ids.
- `catalog_unavailable` - no network, no disk cache and the bundled snapshot is unreadable. Do not retry in a loop; report it.

## Response style

- Present the install command verbatim in a code block, plus the card URL for humans.
- Prefer `konektor` entries when the user needs live legal data, `skill` entries for editorial or workflow procedures, `kuratorski` for vetted third-party skills (mention the external author and license).
- Relay `gaps` to the user instead of silently dropping them.
"""


class ToolError(Exception):
    """Structured error for boutique-mcp tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "not_found", "catalog_unavailable"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

LOCAL_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=False,
)

mcp: FastMCP = FastMCP(name="boutique-mcp", instructions=INSTRUCTIONS)


def _load_catalog():
    try:
        return get_store().load()
    except CatalogUnavailableError as exc:
        raise ToolError("catalog_unavailable", str(exc)) from exc


@mcp.tool(annotations=READ_ONLY)
async def boutique_search(
    query: str,
    jurisdiction: str | None = None,
    entry_type: str | None = None,
    limit: int = 10,
) -> SearchResult:
    """Search the MateMatic Boutique catalog for connectors and skills.

    Args:
        query: keywords in English, Polish or Portuguese (e.g. "case law Poland",
            "anonimizacja", "German law").
        jurisdiction: optional filter, matched against the entry's jurisdiction
            label (e.g. "Polska", "EU", "Brasil").
        entry_type: optional filter: "konektor" (MCP connector), "skill"
            (MateMatic skill) or "kuratorski" (curated third-party skill).
        limit: max hits (1-25, default 10).

    Returns hits with a local install command each, gaps[] naming what the
    catalog does not cover, and a provenance stamp for the catalog data.

    Errors: [invalid_arg] empty query or bad filter; [catalog_unavailable].
    """
    audit = AuditLogger()
    with timer() as t:
        try:
            if not query or not query.strip():
                raise ToolError("invalid_arg", "query must be a non-empty string")
            if entry_type and entry_type not in ("konektor", "skill", "kuratorski"):
                raise ToolError(
                    "invalid_arg",
                    f"entry_type '{entry_type}' invalid - use konektor, skill or kuratorski",
                )
            limit = max(1, min(int(limit), 25))
            catalog, provenance = _load_catalog()
            hits, gaps = search(
                catalog.entries, query, jurisdiction=jurisdiction,
                entry_type=entry_type, limit=limit,
            )
            result = SearchResult(query=query, hits=hits, gaps=gaps, provenance=provenance)
        except Exception as exc:
            audit.log(tool="boutique_search", duration_ms=t.duration_ms, status="error",
                      error=type(exc).__name__)
            raise
    audit.log(tool="boutique_search", duration_ms=t.duration_ms, status="ok")
    return result


@mcp.tool(annotations=READ_ONLY)
async def boutique_get(id: str) -> dict:
    """Full catalog card for one entry: names, descriptions and card URLs in
    every available language, install command, version, license, source URL.

    Args:
        id: the entry id from boutique_search (e.g. "mcp-saos", "de-eli-mcp",
            "humanizer-pl").

    Errors: [invalid_arg] empty id; [not_found] unknown id (message lists the
    closest ids); [catalog_unavailable].
    """
    audit = AuditLogger()
    with timer() as t:
        try:
            if not id or not id.strip():
                raise ToolError("invalid_arg", "id must be a non-empty string")
            catalog, provenance = _load_catalog()
            wanted = id.strip()
            entry = next((e for e in catalog.entries if e.id == wanted), None)
            if entry is None:
                suggestions = closest_ids(catalog.entries, wanted)
                raise ToolError(
                    "not_found",
                    f"no catalog entry '{wanted}'. Closest ids: {', '.join(suggestions) or 'none'}",
                )
            result = {"entry": entry.model_dump(), "provenance": provenance.model_dump()}
        except Exception as exc:
            audit.log(tool="boutique_get", duration_ms=t.duration_ms, status="error",
                      error=type(exc).__name__)
            raise
    audit.log(tool="boutique_get", duration_ms=t.duration_ms, status="ok")
    return result


@mcp.tool(annotations=READ_ONLY)
async def boutique_whats_new(since_date: str | None = None) -> WhatsNewResult:
    """What was added to or updated in the Boutique catalog since a date.

    Args:
        since_date: ISO date (YYYY-MM-DD). Default: 30 days before the catalog's
            generated_at date (deterministic offline - no system clock involved).

    Errors: [invalid_arg] unparsable since_date; [catalog_unavailable].
    """
    audit = AuditLogger()
    with timer() as t:
        try:
            catalog, provenance = _load_catalog()
            if since_date is None:
                gen = date.fromisoformat(catalog.generated_at[:10])
                since = gen - timedelta(days=30)
            else:
                try:
                    since = date.fromisoformat(since_date.strip()[:10])
                except ValueError as exc:
                    raise ToolError(
                        "invalid_arg", f"since_date '{since_date}' is not YYYY-MM-DD"
                    ) from exc
            iso = since.isoformat()
            added, updated = [], []
            for e in catalog.entries:
                if e.added_at and e.added_at >= iso:
                    added.append(to_hit(e, 0.0))
                elif e.updated_at and e.updated_at >= iso:
                    updated.append(to_hit(e, 0.0))
            result = WhatsNewResult(since=iso, added=added, updated=updated,
                                    provenance=provenance)
        except Exception as exc:
            audit.log(tool="boutique_whats_new", duration_ms=t.duration_ms, status="error",
                      error=type(exc).__name__)
            raise
    audit.log(tool="boutique_whats_new", duration_ms=t.duration_ms, status="ok")
    return result


@mcp.tool(annotations=LOCAL_ONLY)
async def boutique_request_coverage(
    description: str,
    jurisdiction: str | None = None,
) -> CoverageDraft:
    """Draft a coverage-request issue for a gap in the Boutique catalog.

    DRAFT ONLY - this tool performs no network call and submits nothing.
    A human reviews the draft and submits it at the returned URL.

    Args:
        description: what is missing and for what task (plain language).
        jurisdiction: optional jurisdiction the gap concerns.

    Errors: [invalid_arg] empty description.
    """
    audit = AuditLogger()
    with timer() as t:
        try:
            if not description or not description.strip():
                raise ToolError("invalid_arg", "description must be a non-empty string")
            jur = f" ({jurisdiction})" if jurisdiction else ""
            title = f"Coverage request{jur}: {description.strip()[:80]}"
            body = (
                "## Coverage request\n\n"
                f"**What is missing:** {description.strip()}\n\n"
                f"**Jurisdiction:** {jurisdiction or 'not specified'}\n\n"
                "**Context:** drafted locally by boutique-mcp after a catalog search "
                "returned gaps. No query log was collected; this text is everything "
                "the requester chose to share.\n"
            )
            result = CoverageDraft(
                title=title,
                body=body,
                submit_url="https://github.com/matematicsolutions/boutique-mcp/issues/new",
                disclaimer=(
                    "Nothing has been sent. Review the draft and submit it yourself "
                    "at submit_url."
                ),
            )
        except Exception as exc:
            audit.log(tool="boutique_request_coverage", duration_ms=t.duration_ms,
                      status="error", error=type(exc).__name__)
            raise
    audit.log(tool="boutique_request_coverage", duration_ms=t.duration_ms, status="ok")
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
