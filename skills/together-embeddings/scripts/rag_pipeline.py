#!/usr/bin/env python3
"""
Together AI RAG Pipeline -- Embed, Retrieve, Rerank, Generate (v2 SDK)

Demonstrates a complete Retrieval-Augmented Generation pipeline using
Together AI embeddings, reranking, and chat completions.

Uses an in-memory vector store for simplicity. Replace with your preferred
vector database (Pinecone, Weaviate, Chroma, etc.) for production use.

Usage:
    python rag_pipeline.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import math
from together import Together

client = Together()

EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
RERANK_MODEL = "mixedbread-ai/Mxbai-Rerank-Large-V2"
CHAT_MODEL = "openai/gpt-oss-20b"


# --- Simple in-memory vector store ---

class Document:
    """A document with text and its embedding vector."""

    def __init__(self, text: str, embedding: list[float] | None = None):
        self.text = text
        self.embedding = embedding


class VectorStore:
    """Minimal in-memory vector store using cosine similarity."""

    def __init__(self):
        self.documents: list[Document] = []

    def add(self, texts: list[str]) -> None:
        """Embed and store a list of texts."""
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )
        for i, item in enumerate(response.data):
            self.documents.append(Document(texts[i], item.embedding))
        print(f"Indexed {len(texts)} documents ({len(self.documents)} total)")

    def search(self, query_embedding: list[float], top_k: int = 10) -> list[Document]:
        """Return top_k most similar documents by cosine similarity."""
        scored = []
        for doc in self.documents:
            sim = self._cosine_similarity(query_embedding, doc.embedding)
            scored.append((sim, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


# --- RAG Pipeline ---

def rag_query(store: VectorStore, query: str, top_k: int = 10, top_n: int = 3) -> str:
    """Run the full RAG pipeline: embed -> retrieve -> rerank -> generate."""

    # 1. Embed the query
    query_embedding = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    ).data[0].embedding

    # 2. Retrieve candidates from vector store
    candidates = store.search(query_embedding, top_k=top_k)
    print(f"Retrieved {len(candidates)} candidates")

    # 3. Rerank for precision
    reranked = client.rerank.create(
        model=RERANK_MODEL,
        query=query,
        documents=[c.text for c in candidates],
        top_n=top_n,
    )
    top_docs = [candidates[r.index].text for r in reranked.results]
    print(f"Reranked to top {len(top_docs)} documents:")
    for i, doc in enumerate(top_docs):
        score = reranked.results[i].relevance_score
        print(f"  [{score:.4f}] {doc[:80]}...")

    # 4. Generate answer using top documents as context
    context = "\n\n".join(top_docs)
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer the user's question based on the following context. "
                    "If the context doesn't contain enough information, say so.\n\n"
                    f"Context:\n{context}"
                ),
            },
            {"role": "user", "content": query},
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # Sample knowledge base
    knowledge = [
        "Photosynthesis is the process by which green plants convert sunlight into "
        "chemical energy. It takes place primarily in the leaves using chlorophyll.",
        "The mitochondria is the powerhouse of the cell, responsible for producing "
        "ATP through cellular respiration.",
        "DNA replication is the process by which a cell copies its DNA before cell "
        "division. It involves enzymes like helicase and DNA polymerase.",
        "The water cycle describes how water evaporates from surfaces, rises into "
        "the atmosphere, cools and condenses into clouds, and falls as precipitation.",
        "Plate tectonics is a theory explaining the movement of Earth's lithospheric "
        "plates. It accounts for earthquakes, volcanic activity, and mountain building.",
        "The human immune system has two main components: innate immunity (immediate, "
        "non-specific) and adaptive immunity (delayed, specific to pathogens).",
        "Gravity is a fundamental force of attraction between objects with mass. "
        "Einstein's general relativity describes it as the curvature of spacetime.",
        "Evolution by natural selection is the process where organisms with favorable "
        "traits are more likely to survive and reproduce.",
        "The periodic table organizes chemical elements by atomic number. Elements in "
        "the same group share similar chemical properties.",
        "Neural networks are computing systems inspired by biological neurons. They "
        "consist of layers of interconnected nodes that process information.",
    ]

    # Build the vector store
    store = VectorStore()
    store.add(knowledge)

    # Run RAG queries
    queries = [
        "How does photosynthesis work?",
        "What causes earthquakes?",
        "How does the immune system fight disease?",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        answer = rag_query(store, query)
        print(f"\nAnswer: {answer}")
