"""GraphRAG service boundary.

Production implementation should replace the static graph with Neo4j GraphRAG
retrievers, Cypher traversal, and graph evidence normalization.
"""

from __future__ import annotations

from typing import Any

from ..models import GraphQueryRequest, GraphQueryResult
from .source_catalog import GRAPH_SOURCES


_ENTITIES: list[dict[str, Any]] = [
    {"id": "order-1", "type": "order", "properties": {"status": "paid", "shipped": False}},
    {"id": "refund-1", "type": "refund", "properties": {"status": "eligible_for_review"}},
    {"id": "logistics-1", "type": "shipment", "properties": {"status": "not_collected"}},
]

_RELATIONS: list[dict[str, Any]] = [
    {"source": "order-1", "target": "refund-1", "type": "has_refund"},
    {"source": "order-1", "target": "logistics-1", "type": "shipped_by"},
]


def query_graph(request: GraphQueryRequest) -> GraphQueryResult:
    graph_id = request.graph_id or next(iter(GRAPH_SOURCES))
    entity_filter = set(request.entity_ids)
    relation_filter = set(request.relation_types)

    entities = [
        entity for entity in _ENTITIES if not entity_filter or entity["id"] in entity_filter or entity["id"] in _neighbors(entity_filter)
    ]
    relations = [
        relation
        for relation in _RELATIONS
        if (not relation_filter or relation["type"] in relation_filter)
        and (not entity_filter or relation["source"] in entity_filter or relation["target"] in entity_filter)
    ]
    paths = [
        {
            "start": relation["source"],
            "end": relation["target"],
            "relations": [relation],
        }
        for relation in relations
    ]
    evidence = [
        {
            "type": "static_demo",
            "source": "demo_graph_seed",
            "graph_id": graph_id,
            "ontology_version": GRAPH_SOURCES.get(graph_id, next(iter(GRAPH_SOURCES.values()))).metadata.get("ontology_version"),
        }
    ]
    return GraphQueryResult(
        graph_id=graph_id,
        entities=entities,
        relations=relations,
        paths=paths,
        evidence=evidence,
    )


def _neighbors(entity_ids: set[str]) -> set[str]:
    neighbors: set[str] = set()
    for relation in _RELATIONS:
        if relation["source"] in entity_ids:
            neighbors.add(relation["target"])
        if relation["target"] in entity_ids:
            neighbors.add(relation["source"])
    return neighbors

