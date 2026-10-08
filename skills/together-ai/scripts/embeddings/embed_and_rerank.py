#!/usr/bin/env python3
"""
Together AI Embeddings Pipeline (v2 SDK)

Embed documents, compute similarity, and optionally rerank results.

Reranking requires a dedicated endpoint. When no endpoint is configured the
rerank helper falls back to cosine-similarity order. See
https://docs.together.ai/docs/rerank-overview for setup instructions.

Usage:
    python embed_and_rerank.py

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
    export EMBEDDING_MODEL=your-project/your-embedding-endpoint  # dedicated endpoint string
"""

import math
import os
import sys

from together import Together

client = Together()

# Together does not currently offer embedding or rerank models (see domains/embeddings.md).
# If you already have an embedding endpoint, set EMBEDDING_MODEL (and optionally
# RERANK_MODEL) to its endpoint string, e.g. "my-project/my-embeddings".
# Dedicated inference is served from its own base URL.
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "")
RERANK_MODEL: str | None = os.environ.get("RERANK_MODEL") or None
dedicated_client = Together(
    base_url=os.environ.get("DEDICATED_BASE_URL", "https://api-inference.together.ai/v1")
)


def require_embedding_model() -> str:
    """Exit with an actionable message instead of failing request by request."""
    if not EMBEDDING_MODEL:
        sys.exit(
            "EMBEDDING_MODEL is not set. Together does not currently offer embedding models "
            "(serverless or in the dedicated catalog). If you already have an embedding "
            "endpoint, export its endpoint string. See domains/embeddings.md."
        )
    return EMBEDDING_MODEL


def embed_texts(
    texts: list[str],
    model: str | None = None,
) -> list[list[float]]:
    """Embed a list of texts, returns list of embedding vectors."""
    response = dedicated_client.embeddings.create(
        model=model or require_embedding_model(),
        input=texts,
    )
    return [item.embedding for item in response.data]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


# --- Rerank with fallback ---

def rerank_documents(
    query: str,
    documents: list[str],
    scores: list[float] | None = None,
    top_n: int = 3,
) -> list[dict]:
    """Rerank documents by relevance to a query.

    When RERANK_MODEL is set, calls the dedicated rerank endpoint.
    Otherwise falls back to the cosine-similarity scores passed in.
    """
    if RERANK_MODEL is not None:
        response = dedicated_client.rerank.create(
            model=RERANK_MODEL,
            query=query,
            documents=documents,
            top_n=top_n,
        )
        return [
            {
                "index": item.index,
                "score": item.relevance_score,
                "document": documents[item.index],
            }
            for item in response.results
        ]

    # Fallback: rank by pre-computed cosine-similarity scores
    if scores is None:
        query_emb = embed_texts([query])[0]
        doc_embs = embed_texts(documents)
        scores = [cosine_similarity(query_emb, d) for d in doc_embs]

    ranked = sorted(
        [{"index": i, "score": s, "document": d}
         for i, (d, s) in enumerate(zip(documents, scores))],
        key=lambda x: x["score"],
        reverse=True,
    )
    return ranked[:top_n]


def rerank_structured(
    query: str,
    documents: list[dict],
    rank_fields: list[str],
    top_n: int | None = None,
) -> list[dict]:
    """Rerank structured JSON documents by specific fields.

    Requires a dedicated rerank endpoint (RERANK_MODEL must be set).
    """
    if RERANK_MODEL is None:
        raise RuntimeError(
            "Structured reranking requires a dedicated endpoint. "
            "Set RERANK_MODEL to your endpoint model name."
        )
    kwargs: dict = {
        "model": RERANK_MODEL,
        "query": query,
        "documents": documents,
        "rank_fields": rank_fields,
        "return_documents": True,
    }
    if top_n:
        kwargs["top_n"] = top_n

    response = dedicated_client.rerank.create(**kwargs)
    return [
        {
            "index": item.index,
            "score": item.relevance_score,
            "document": documents[item.index],
        }
        for item in response.results
    ]


if __name__ == "__main__":
    require_embedding_model()
    # --- Example 1: Embed and compute similarity ---
    print("=== Embedding Similarity ===")
    texts = [
        "Python is a popular programming language",
        "JavaScript is used for web development",
        "Machine learning uses statistical models",
    ]
    query = "What language is good for data science?"

    embeddings = embed_texts(texts + [query])
    query_emb = embeddings[-1]
    doc_embs = embeddings[:-1]

    scores = []
    for i, text in enumerate(texts):
        sim = cosine_similarity(query_emb, doc_embs[i])
        scores.append(sim)
        print(f"  {sim:.4f} -- {text}")

    # --- Example 2: Rerank (dedicated endpoint or cosine-similarity fallback) ---
    print(f"\n=== Reranking ===")
    if RERANK_MODEL is None:
        print("  (no dedicated rerank endpoint -- using cosine-similarity fallback)")

    documents = [
        "Python is widely used in data science and machine learning.",
        "Java is a popular language for enterprise applications.",
        "R is a language designed for statistical computing.",
        "JavaScript powers most web applications.",
        "SQL is essential for database querying.",
    ]
    ranked = rerank_documents(query, documents, top_n=3)
    for r in ranked:
        print(f"  [{r['score']:.4f}] {r['document']}")
