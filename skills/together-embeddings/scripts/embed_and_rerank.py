#!/usr/bin/env python3
"""
Together AI Embeddings + Reranking Pipeline (v2 SDK)

Embed documents, compute similarity, rerank results, and demonstrate
structured document reranking.

Usage:
    python embed_and_rerank.py

Requires:
    pip install together
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


def rerank_documents(
    query: str,
    documents: list[str],
    top_n: int = 3,
    model: str = "mixedbread-ai/Mxbai-Rerank-Large-V2",
) -> list[dict]:
    """Rerank text documents by relevance to a query."""
    response = client.rerank.create(
        model=model,
        query=query,
        documents=documents,
        top_n=top_n,
    )
    results = []
    for item in response.results:
        results.append({
            "index": item.index,
            "score": item.relevance_score,
            "document": documents[item.index],
        })
    return results


def rerank_structured(
    query: str,
    documents: list[dict],
    rank_fields: list[str],
    model: str = "Salesforce/Llama-Rank-V1",
    top_n: int | None = None,
) -> list[dict]:
    """Rerank structured JSON documents by specific fields.

    Requires Salesforce/Llama-Rank-V1 on a dedicated endpoint.
    """
    kwargs: dict = {
        "model": model,
        "query": query,
        "documents": documents,
        "rank_fields": rank_fields,
        "return_documents": True,
    }
    if top_n:
        kwargs["top_n"] = top_n

    response = client.rerank.create(**kwargs)
    results = []
    for item in response.results:
        results.append({
            "index": item.index,
            "score": item.relevance_score,
            "document": documents[item.index],
        })
    return results


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

    # --- Example 2: Text reranking ---
    print(f"\n=== Text Reranking ===")
    documents = [
        "Python is widely used in data science and machine learning.",
        "Java is a popular language for enterprise applications.",
        "R is a language designed for statistical computing.",
        "JavaScript powers most web applications.",
        "SQL is essential for database querying.",
    ]

    print(f"Query: '{query}'")
    ranked = rerank_documents(query, documents, top_n=3)
    for r in ranked:
        print(f"  [{r['score']:.4f}] {r['document']}")

    # --- Example 3: Structured document reranking (requires dedicated endpoint) ---
    # Uncomment below if you have a Salesforce/Llama-Rank-V1 dedicated endpoint
    #
    # print(f"\n=== Structured Document Reranking ===")
    # emails = [
    #     {
    #         "from": "Paul Doe <paul@oracle.com>",
    #         "subject": "Cloud pricing follow-up",
    #         "text": "We are happy to offer the following pricing for our services...",
    #     },
    #     {
    #         "from": "Jane Smith <jane@company.com>",
    #         "subject": "Team lunch tomorrow",
    #         "text": "Hi everyone, let's meet at noon for lunch...",
    #     },
    #     {
    #         "from": "Bob Lee <bob@aws.com>",
    #         "subject": "AWS pricing proposal",
    #         "text": "Attached is our competitive pricing for your workload...",
    #     },
    # ]
    # ranked = rerank_structured(
    #     query="Which pricing did we get from Oracle?",
    #     documents=emails,
    #     rank_fields=["from", "subject", "text"],
    # )
    # for r in ranked:
    #     print(f"  [{r['score']:.4f}] {r['document']['subject']}")
