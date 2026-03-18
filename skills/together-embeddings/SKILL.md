---
name: together-embeddings
description: Generate text embeddings via Together AI using the Multilingual E5 model with 1024-dimension vectors. Reranking available via dedicated endpoints. Use when users need text embeddings, vector search, semantic similarity, RAG pipeline components, or retrieval-augmented generation.
---

# Together Embeddings & Reranking

## Overview

Generate vector embeddings for text and rerank documents by relevance.

- Embeddings endpoint: `/v1/embeddings`
- Rerank endpoint: `/v1/rerank` (requires dedicated endpoint)

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together # for quick install without setting project
```

```shell
# or with pip
pip install together
```

```shell
# TypeScript / JavaScript
npm install together-ai
```

Set your API key:

```shell
export TOGETHER_API_KEY=<your-api-key>
```

## Embeddings

### Generate Embeddings

```python
from together import Together
client = Together()

response = client.embeddings.create(
    model="intfloat/multilingual-e5-large-instruct",
    input="Our solar system orbits the Milky Way galaxy at about 515,000 mph",
)
print(response.data[0].embedding[:5])  # First 5 dimensions
```

```typescript
import Together from "together-ai";
const together = new Together();

const response = await together.embeddings.create({
  model: "intfloat/multilingual-e5-large-instruct",
  input: "Our solar system orbits the Milky Way galaxy at about 515,000 mph",
});
console.log(response.data[0].embedding.slice(0, 5));
```

```shell
curl -X POST "https://api.together.xyz/v1/embeddings" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "intfloat/multilingual-e5-large-instruct",
    "input": "Our solar system orbits the Milky Way galaxy at about 515,000 mph"
  }'
```

### Batch Embeddings

Pass an array to `input` for batch processing:

```python
texts = ["First document", "Second document", "Third document"]
response = client.embeddings.create(
    model="intfloat/multilingual-e5-large-instruct",
    input=texts,
)
for i, item in enumerate(response.data):
    print(f"Text {i}: {len(item.embedding)} dimensions")
```

```typescript
const response = await together.embeddings.create({
  model: "intfloat/multilingual-e5-large-instruct",
  input: ["First document", "Second document", "Third document"],
});
for (const item of response.data) {
  console.log(`Index ${item.index}: ${item.embedding.length} dimensions`);
}
```

```shell
curl -X POST "https://api.together.xyz/v1/embeddings" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "intfloat/multilingual-e5-large-instruct",
    "input": ["First document", "Second document", "Third document"]
  }'
```

### Embedding Models

| Model | API String | Dimensions | Max Input |
|-------|-----------|------------|-----------|
| Multilingual E5 Large | `intfloat/multilingual-e5-large-instruct` | 1,024 | 514 tokens |

See [references/models.md](references/models.md) for model details and selection guidance.

### Embeddings Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Embedding model identifier |
| `input` | string or string[] | Yes | Text(s) to embed |

## Reranking

Reranking is currently available exclusively via dedicated endpoints. Deploy a rerank model
as a dedicated endpoint, then use the `/v1/rerank` API.

See the [Rerank Overview](https://docs.together.ai/docs/rerank-overview) for current models
and setup instructions.

### Rerank Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Rerank model identifier |
| `query` | string | Yes | Search query |
| `documents` | string[] or object[] | Yes | Documents to rerank |
| `top_n` | int | No | Return only top N results |
| `return_documents` | bool | No | Include document text in response |
| `rank_fields` | string[] | No | Fields to rank by for JSON objects |

## RAG Pipeline Pattern

Embed -> Retrieve -> Generate:

```python
from together import Together
client = Together()

# 1. Generate query embedding
query = "How does photosynthesis work?"
query_embedding = client.embeddings.create(
    model="intfloat/multilingual-e5-large-instruct",
    input=query,
).data[0].embedding

# 2. Retrieve candidates from vector DB (your code)
candidates = vector_db.search(query_embedding, top_k=5)

# 3. Use top results as context for LLM
context = "\n".join([c.text for c in candidates])
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": f"Answer based on this context:\n{context}"},
        {"role": "user", "content": query},
    ],
)
print(response.choices[0].message.content)
```

## Resources

- **Model details**: See [references/models.md](references/models.md)
- **API reference**: See [references/api-reference.md](references/api-reference.md)
- **Runnable scripts**: See [scripts/](scripts/) for Python and TypeScript examples
- **Official docs**: [Embeddings Overview](https://docs.together.ai/docs/embeddings-overview)
- **Official docs**: [Rerank Overview](https://docs.together.ai/docs/rerank-overview)
- **API reference**: [Embeddings API](https://docs.together.ai/reference/embeddings)
- **API reference**: [Rerank API](https://docs.together.ai/reference/rerank)
