#!/usr/bin/env python3
"""
Together AI Semantic Search Pipeline (v2 SDK)

Embed a product corpus, store vectors in memory, query by similarity,
and optionally rerank results with a dedicated endpoint.

This example sits between the basic similarity demo (embed_and_rerank.py)
and the full RAG pipeline (rag_pipeline.py). It covers the common case of
pure vector search without a chat-generation step.

Usage:
    python semantic_search.py

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

# No embedding or rerank model is served serverless today. Deploy one on a dedicated
# endpoint (see domains/embeddings.md), then set EMBEDDING_MODEL (and optionally
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
            "EMBEDDING_MODEL is not set. Together serves no embedding models serverless; "
            "deploy one on a dedicated endpoint and export its endpoint string. "
            "See domains/embeddings.md."
        )
    return EMBEDDING_MODEL


# ---------------------------------------------------------------------------
# In-memory vector store
# ---------------------------------------------------------------------------

class VectorStore:
    """Minimal in-memory vector store using cosine similarity.

    Good enough for prototyping and small corpora. For production, swap in a
    dedicated vector database (Pinecone, Weaviate, Chroma, pgvector, etc.).
    """

    def __init__(self) -> None:
        self.texts: list[str] = []
        self.embeddings: list[list[float]] = []

    def add(self, texts: list[str], batch_size: int = 100) -> None:
        """Embed and store texts. Batches requests to stay within limits."""
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = dedicated_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
            )
            for i, item in enumerate(response.data):
                self.texts.append(batch[i])
                self.embeddings.append(item.embedding)
        print(f"Indexed {len(self.texts)} documents "
              f"({len(self.embeddings[0])} dimensions each)")

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Embed a query and return the top_k most similar documents."""
        query_emb = dedicated_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query,
        ).data[0].embedding

        scored: list[dict] = []
        for idx, emb in enumerate(self.embeddings):
            sim = _cosine_similarity(query_emb, emb)
            scored.append({"index": idx, "text": self.texts[idx], "score": sim})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


# ---------------------------------------------------------------------------
# Optional rerank stage
# ---------------------------------------------------------------------------

def rerank(
    query: str,
    candidates: list[dict],
    top_n: int = 5,
) -> list[dict]:
    """Rerank candidates via a dedicated endpoint, or fall back to
    cosine-similarity order when no endpoint is configured."""
    if RERANK_MODEL is None:
        print("  (no dedicated rerank endpoint -- keeping cosine-similarity order)")
        return candidates[:top_n]

    documents = [c["text"] for c in candidates]
    response = dedicated_client.rerank.create(
        model=RERANK_MODEL,
        query=query,
        documents=documents,
        top_n=top_n,
        return_documents=True,
    )
    return [
        {
            "index": candidates[item.index]["index"],
            "text": documents[item.index],
            "score": item.relevance_score,
        }
        for item in response.results
    ]


# ---------------------------------------------------------------------------
# Example corpus and queries
# ---------------------------------------------------------------------------

PRODUCTS = [
    "Lightweight mesh running shoes with responsive foam cushioning",
    "Waterproof leather hiking boots with Vibram sole",
    "Classic white canvas sneakers for everyday casual wear",
    "Memory foam slip-on walking shoes for all-day comfort",
    "Carbon-plate racing flats for marathon runners",
    "Breathable trail running shoes with aggressive lug pattern",
    "Minimalist barefoot running sandals with adjustable straps",
    "Cushioned stability running shoes for overpronation support",
    "High-top basketball shoes with ankle support and air units",
    "Vegan leather formal Oxford shoes in matte black",
    "Steel-toe work boots with electrical hazard protection",
    "Soft knit slip-on sneakers with cloud-like insole",
    "Women's lightweight cross-training shoes for HIIT workouts",
    "Men's cushioned walking shoes with arch support inserts",
    "Kids' velcro running shoes in neon green",
    "Ultra-boost energy-return running shoes for long distances",
    "Slip-resistant restaurant work clogs with padded collar",
    "Retro suede skateboarding shoes with vulcanized sole",
    "Waterproof Gore-Tex trail running shoes for wet conditions",
    "Orthopedic walking shoes recommended by podiatrists",
]


if __name__ == "__main__":
    require_embedding_model()
    # 1. Build the index
    print("=== Indexing ===")
    store = VectorStore()
    store.add(PRODUCTS)

    # 2. Search
    query = "comfortable running shoes"
    print(f"\n=== Search: \"{query}\" ===")
    results = store.search(query, top_k=10)
    for rank, r in enumerate(results, 1):
        print(f"  {rank:>2}. [{r['score']:.4f}] {r['text']}")

    # 3. Rerank (falls back to cosine order without a dedicated endpoint)
    print(f"\n=== Rerank top 5 ===")
    top_5 = rerank(query, results, top_n=5)
    for rank, r in enumerate(top_5, 1):
        print(f"  {rank:>2}. [{r['score']:.4f}] {r['text']}")
