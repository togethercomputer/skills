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
"""

import math
from together import Together

client = Together()

# Set to your dedicated rerank endpoint model name to enable API reranking.
# See https://docs.together.ai/docs/rerank-overview
RERANK_MODEL: str | None = None


def embed_texts(
    texts: list[str],
    model: str = "intfloat/multilingual-e5-large-instruct",
) -> list[list[float]]:
    """Embed a list of texts, returns list of embedding vectors."""
    response = client.embeddings.create(
        model=model,
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
        response = client.rerank.create(
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

    response = client.rerank.create(**kwargs)
    return [
        {
            "index": item.index,
            "score": item.relevance_score,
            "document": documents[item.index],
        }
        for item in response.results
    ]


if __name__ == "__main__":
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
