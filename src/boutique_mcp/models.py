"""Pydantic models for the Boutique catalog and tool responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EntryType = Literal["konektor", "skill", "kuratorski"]
Origin = Literal["network", "disk-cache", "bundled-snapshot"]


class Install(BaseModel):
    """How to install a catalog entry LOCALLY. The catalog never proxies anything."""

    model_config = ConfigDict(extra="allow")

    kind: str = Field(description="uvx | npx | download | github")
    command: str | None = Field(default=None, description="Copy-paste local install command")
    url: str | None = Field(default=None, description="Download or repository URL")


class CatalogEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    type: EntryType
    name: dict[str, str] = Field(default_factory=dict)
    problem: dict[str, str] = Field(default_factory=dict)
    description: dict[str, str] = Field(default_factory=dict)
    category: dict[str, str] = Field(default_factory=dict)
    jurisdiction: dict[str, str] = Field(default_factory=dict)
    languages: list[str] = Field(default_factory=list)
    install: Install
    version: str | None = None
    license: str | None = None
    author: str | None = None
    source_url: str | None = None
    card_url: dict[str, str] = Field(default_factory=dict)
    added_at: str | None = None
    updated_at: str | None = None


class CatalogFile(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    schema_version: str
    generated_at: str
    source: str
    counts: dict[str, int] = Field(default_factory=dict)
    entries: list[CatalogEntry] = Field(default_factory=list)


class Provenance(BaseModel):
    """Where the catalog data in this response came from, and how old it is."""

    origin: Origin
    catalog_generated_at: str
    fetched_at: str | None = None
    stale: bool = False
    note: str


class SearchHit(BaseModel):
    id: str
    type: EntryType
    name: str
    description: str | None = None
    category: str | None = None
    jurisdiction: str | None = None
    install: Install
    version: str | None = None
    license: str | None = None
    card_url: str | None = None
    score: float


class Gap(BaseModel):
    """Explicit statement of what the catalog does NOT cover for this query."""

    kind: Literal["no_match", "jurisdiction_uncovered", "type_uncovered"]
    detail: str
    suggestion: str


class SearchResult(BaseModel):
    query: str
    hits: list[SearchHit] = Field(default_factory=list)
    gaps: list[Gap] = Field(default_factory=list)
    provenance: Provenance


class WhatsNewResult(BaseModel):
    since: str
    added: list[SearchHit] = Field(default_factory=list)
    updated: list[SearchHit] = Field(default_factory=list)
    provenance: Provenance


class CoverageDraft(BaseModel):
    """A DRAFT coverage request. Nothing is sent anywhere - a human submits it."""

    title: str
    body: str
    submit_url: str
    disclaimer: str
