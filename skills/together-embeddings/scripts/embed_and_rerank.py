#!/usr/bin/env python3
"""
Together AI Embeddings Pipeline (v2 SDK)

Embed documents and compute similarity.

Note: Reranking requires a dedicated endpoint. The rerank functions in this
file are commented out. See https://docs.together.ai/docs/rerank-overview
for setup instructions.

Usage:
    python embed_and_rerank.py

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import math
from together import Together

client = Together()


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


# --- Rerank functions (require a dedicated endpoint) ---
# Reranking is currently available exclusively via dedicated endpoints.
# Deploy a rerank model as a dedicated endpoint, then uncomment and update
# the model parameter below with your endpoint model name.
# See https://docs.together.ai/docs/rerank-overview

# def rerank_documents(
#     query: str,
#     documents: list[str],
#     top_n: int = 3,
#     model: str = "<your-dedicated-endpoint-model>",
# ) -> list[dict]:
#     """Rerank text documents by relevance to a query."""
#     response = client.rerank.create(
#         model=model,
#         query=query,
#         documents=documents,
#         top_n=top_n,
#     )
#     results = []
#     for item in response.results:
#         results.append({
#             "index": item.index,
#             "score": item.relevance_score,
#             "document": documents[item.index],
#         })
#     return results


# def rerank_structured(
#     query: str,
#     documents: list[dict],
#     rank_fields: list[str],
#     model: str = "<your-dedicated-endpoint-model>",
#     top_n: int | None = None,
# ) -> list[dict]:
#     """Rerank structured JSON documents by specific fields.
#
#     Requires a rerank model on a dedicated endpoint.
#     """
#     kwargs: dict = {
#         "model": model,
#         "query": query,
#         "documents": documents,
#         "rank_fields": rank_fields,
#         "return_documents": True,
#     }
#     if top_n:
#         kwargs["top_n"] = top_n
#
#     response = client.rerank.create(**kwargs)
#     results = []
#     for item in response.results:
#         results.append({
#             "index": item.index,
#             "score": item.relevance_score,
#             "document": documents[item.index],
#         })
#     return results


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

    for i, text in enumerate(texts):
        sim = cosine_similarity(query_emb, doc_embs[i])
        print(f"  {sim:.4f} -- {text}")

    # --- Reranking examples (require a dedicated endpoint) ---
    # Reranking is currently available exclusively via dedicated endpoints.
    # See https://docs.together.ai/docs/rerank-overview for setup instructions.
    #
    # print(f"\n=== Text Reranking ===")
    # documents = [
    #     "Python is widely used in data science and machine learning.",
    #     "Java is a popular language for enterprise applications.",
    #     "R is a language designed for statistical computing.",
    #     "JavaScript powers most web applications.",
    #     "SQL is essential for database querying.",
    # ]
    # print(f"Query: '{query}'")
    # ranked = rerank_documents(query, documents, top_n=3)
    # for r in ranked:
    #     print(f"  [{r['score']:.4f}] {r['document']}")
