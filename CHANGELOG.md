# Changelog

## 0.1.0 (2026-07-13)

First release.

- `boutique_search` - keyword search over the Boutique catalog with `gaps[]`
  when coverage is missing (jurisdiction, type filters, diacritics folding).
- `boutique_get` - full catalog card with closest-id suggestions on miss.
- `boutique_whats_new` - added/updated entries since a date, deterministic
  default window (30 days before catalog generation).
- `boutique_request_coverage` - draft-only coverage request (no network call).
- Catalog ladder: network (ETag/If-None-Match) -> disk cache -> bundled
  snapshot, every response stamped with provenance and staleness.
- Opt-in local audit log (tool name + timing only, never query content).
