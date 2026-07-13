# boutique-mcp

<!-- mcp-name: io.github.matematicsolutions/boutique-mcp -->

A **local MCP catalog** of [MateMatic Boutique](https://matematicsolutions.com/en/boutique):
103 entries at the time of writing - 43 legal-data MCP connectors (SAOS, CBOSA,
EUR-Lex, national ELI servers from Austria to Japan), 52 MateMatic agent skills
and 8 curated third-party skills.

It answers one question: which building block solves the task at hand, and how
to install it locally. The catalog points, it never proxies. Your agent gets a
copy-paste `uvx`/`npx` command or a download link and runs it on your machine.

**Status: v0.1.0** | License: **Apache-2.0** | Maintainer: [MateMatic](https://matematicsolutions.com)

## Why local

A hosted discovery API sees every query it answers, and in legal work the query
itself is often confidential ("counter-arguments to our client's position in...").
This connector never sees anything: search runs in-process over a local copy of
`catalog.json`. The only
network request it ever makes is a conditional GET of the public catalog itself
(ETag / If-None-Match).

No network? You get the last catalog cached on disk, or the snapshot shipped
inside the package. Either way the response says where the data came from and
how old it is: "catalog generated on X, source: network / disk-cache /
bundled-snapshot". Nothing is installed or executed for you. The catalog
returns commands; you run them.

## MCP tools

- **`boutique_search(query, jurisdiction?, entry_type?, limit?)`** - keyword search
  (English, Polish or Portuguese) over the catalog. Every hit carries a local
  install command. When coverage is missing, the response says so in `gaps[]`
  instead of padding weak matches.
- **`boutique_get(id)`** - the full card for one entry: names and descriptions in
  every available language, install, version, license, source and card URLs.
- **`boutique_whats_new(since_date?)`** - what was added or updated since a date
  (default: the 30 days before the catalog was generated).
- **`boutique_request_coverage(description, jurisdiction?)`** - drafts a
  coverage-request issue for a gap. **Draft only**: nothing is sent anywhere;
  a human reviews and submits it.

## Quickstart

```bash
uvx boutique-mcp
```

MCP client configuration (`mcp-servers.json`):

```json
{
  "mcpServers": {
    "boutique": {
      "command": "uvx",
      "args": ["boutique-mcp"]
    }
  }
}
```

## Configuration

| Env | Default | Meaning |
|---|---|---|
| `BOUTIQUE_MCP_CATALOG_URL` | `https://matematicsolutions.com/catalog.json` | Catalog source |
| `BOUTIQUE_MCP_CACHE_DIR` | `~/.matematic/cache/boutique-mcp` | Disk cache location |
| `BOUTIQUE_MCP_OFFLINE` | unset | `1` = never touch the network |
| `BOUTIQUE_MCP_AUDIT` | unset | `1` = opt-in local audit log (tool name + timing only, never query content) |

## Data source

`catalog.json` is generated in the [www-matematic](https://matematicsolutions.com)
repository from the same source as the Boutique page tiles (three languages);
a pre-commit and CI check fails whenever the two drift apart. A machine-readable server card lives
at [`/.well-known/mcp/server-card.json`](https://matematicsolutions.com/.well-known/mcp/server-card.json).

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"        # Windows: .venv\Scripts\pip
.venv/bin/python -m pytest tests/ -q     # offline - fixture catalog
.venv/bin/python -m ruff check src tests
```

## Governance

The project constitution forbids a hosted discover/invoke proxy and any logging
of query content. The only adoption metric MateMatic sees is the CDN download
counter of the public `catalog.json` file. The one tool that produces outbound
text, `boutique_request_coverage`, stops at a draft; a human submits it.

Constitution and spec: [`.matematic/`](.matematic/) in this repository.
