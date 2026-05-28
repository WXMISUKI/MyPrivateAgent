"""Minimal external Knowledge Provider service for MyPrivateAgent."""

from __future__ import annotations

from fastapi import FastAPI

from .routers import capabilities, catalog, graph, health, rag


app = FastAPI(
    title="unifiedKnowledgeProvider",
    version="0.1.0",
    description="External RAG and GraphRAG provider for MyPrivateAgent.",
)

app.include_router(health.router)
app.include_router(capabilities.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(rag.router, prefix="/api/rag")
app.include_router(graph.router, prefix="/api/graph")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "unifiedKnowledgeProvider",
        "status": "ok",
        "docs": "/docs",
    }

