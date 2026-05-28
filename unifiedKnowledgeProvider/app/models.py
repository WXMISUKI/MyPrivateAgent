"""Provider HTTP contract models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CatalogSource(BaseModel):
    id: str
    type: Literal["rag", "graph"]
    status: Literal["ready", "degraded", "unavailable"]
    owner: str
    version: str
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagRetrieveRequest(BaseModel):
    query: str
    knowledge_base_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)


class RagDocument(BaseModel):
    source_id: str
    document_id: str
    title: str
    snippet: str
    score: float
    citation: str


class RagRetrieveResult(BaseModel):
    answer_context: str
    documents: list[RagDocument]


class GraphQueryRequest(BaseModel):
    graph_id: str = ""
    query: str = ""
    entity_ids: list[str] = Field(default_factory=list)
    relation_types: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)


class GraphQueryResult(BaseModel):
    graph_id: str
    entities: list[dict[str, Any]]
    relations: list[dict[str, Any]]
    paths: list[dict[str, Any]]
    evidence: list[dict[str, Any]]

