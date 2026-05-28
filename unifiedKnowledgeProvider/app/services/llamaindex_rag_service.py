"""Document RAG service boundary.

Production implementation should replace the static demo retrieval with
LlamaIndex ingestion, index, retriever, query engine, and reranker components.
"""

from __future__ import annotations

from ..models import RagDocument, RagRetrieveRequest, RagRetrieveResult
from .source_catalog import RAG_SOURCES


_DOCUMENTS: list[RagDocument] = [
    RagDocument(
        source_id="refund_policy_docs",
        document_id="refund_policy_2026",
        title="售后退款规则",
        snippet="超时未发货场景下，客服应先核验订单状态、发货承诺时效和商家责任，再给出退款建议。",
        score=0.91,
        citation="refund_policy_2026#section-3",
    ),
    RagDocument(
        source_id="logistics_faq",
        document_id="logistics_faq_2026",
        title="物流异常处理 FAQ",
        snippet="物流无揽收或长时间无更新时，应查询物流轨迹并区分仓库未发出、承运商延迟和地址异常。",
        score=0.84,
        citation="logistics_faq_2026#delay",
    ),
]


def retrieve(request: RagRetrieveRequest) -> RagRetrieveResult:
    source_ids = request.knowledge_base_ids or list(RAG_SOURCES)
    allowed_sources = {source_id for source_id in source_ids if source_id in RAG_SOURCES}
    candidates = [doc for doc in _DOCUMENTS if doc.source_id in allowed_sources]

    query_terms = _normalize_terms(request.query)
    ranked = sorted(
        candidates,
        key=lambda doc: (_term_overlap(query_terms, doc.title + doc.snippet), doc.score),
        reverse=True,
    )
    documents = ranked[: request.top_k]
    answer_context = "\n".join(
        f"[{doc.citation}] {doc.title}: {doc.snippet}" for doc in documents
    )
    return RagRetrieveResult(answer_context=answer_context, documents=documents)


def _normalize_terms(text: str) -> set[str]:
    return {token.strip().lower() for token in text.replace("？", " ").replace("?", " ").split() if token.strip()}


def _term_overlap(terms: set[str], text: str) -> int:
    normalized = text.lower()
    return sum(1 for term in terms if term in normalized)

