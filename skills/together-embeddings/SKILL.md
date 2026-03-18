---
name: together-embeddings
description: Generate text embeddings and rerank documents via Together AI. Embedding models include Multilingual E5, BGE, UAE, and M2-BERT families with up to 8K token context. Reranking via MixedBread (serverless) and Salesforce Llama Rank (dedicated, structured JSON support). Use when users need text embeddings, vector search, semantic similarity, document reranking, RAG pipeline components, or retrieval-augmented generation.
---

# Together Embeddings & Reranking

## Overview

Generate vector embeddings for text and rerank documents by relevance.

- Embeddings endpoint: `/v1/embeddings`
- Rerank endpoint: `/v1/rerank`

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
| Multilingual E5 Large (recommended) | `intfloat/multilingual-e5-large-instruct` | 1,024 | 514 tokens |
| BGE Base EN v1.5 | `BAAI/bge-base-en-v1.5` | 768 | 512 tokens |
| UAE Large V1 | `WhereIsAI/UAE-Large-V1` | 1,024 | 512 tokens |
| M2-BERT Retrieval 8k | `togethercomputer/m2-bert-80M-8k-retrieval` | 768 | 8,192 tokens |

See [references/models.md](references/models.md) for the full model list including deprecated
models and selection guidance.

### Embeddings Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Embedding model identifier |
| `input` | string or string[] | Yes | Text(s) to embed |

## Reranking

Rerank a set of documents by relevance to a query. A reranker reassesses and reorders
retrieved documents for improved search precision.

### Text Reranking

```python
from together import Together
client = Together()

response = client.rerank.create(
    model="mixedbread-ai/Mxbai-Rerank-Large-V2",
    query="What is the capital of France?",
    documents=[
        "Paris is the capital of France.",
        "Berlin is the capital of Germany.",
        "London is the capital of England.",
        "The Eiffel Tower is in Paris.",
    ],
    top_n=2,
)
for result in response.results:
    print(f"Index: {result.index}, Score: {result.relevance_score:.4f}")
```

```typescript
import Together from "together-ai";
const together = new Together();

const response = await together.rerank.create({
  model: "mixedbread-ai/Mxbai-Rerank-Large-V2",
  query: "What is the capital of France?",
  documents: [
    "Paris is the capital of France.",
    "Berlin is the capital of Germany.",
    "London is the capital of England.",
    "The Eiffel Tower is in Paris.",
  ],
  top_n: 2,
});
for (const result of response.results) {
  console.log(`Index: ${result.index}, Score: ${result.relevance_score}`);
}
```

```shell
curl -X POST "https://api.together.xyz/v1/rerank" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mixedbread-ai/Mxbai-Rerank-Large-V2",
    "query": "What is the capital of France?",
    "documents": [
      "Paris is the capital of France.",
      "Berlin is the capital of Germany.",
      "London is the capital of England.",
      "The Eiffel Tower is in Paris."
    ],
    "top_n": 2
  }'
```

### Structured Document Reranking

Use `rank_fields` to rerank JSON objects by specific fields (Salesforce/Llama-Rank-V1 only,
requires dedicated endpoint):

```python
response = client.rerank.create(
    model="Salesforce/Llama-Rank-V1",
    query="Which pricing did we get from Oracle?",
    documents=[
        {
            "from": "Paul Doe <paul_fake_doe@oracle.com>",
            "subject": "Follow-up on cloud pricing",
            "text": "We are happy to give you the following pricing for our cloud services...",
        },
        {
            "from": "Jane Smith <jane@company.com>",
            "subject": "Team lunch tomorrow",
            "text": "Hi everyone, let's meet at noon for lunch...",
        },
    ],
    return_documents=True,
    rank_fields=["from", "subject", "text"],
)
for result in response.results:
    print(f"Index: {result.index}, Score: {result.relevance_score:.4f}")
```

```typescript
const response = await together.rerank.create({
  model: "Salesforce/Llama-Rank-V1",
  query: "Which pricing did we get from Oracle?",
  documents: [
    {
      from: "Paul Doe <paul_fake_doe@oracle.com>",
      subject: "Follow-up on cloud pricing",
      text: "We are happy to give you the following pricing for our cloud services...",
    },
    {
      from: "Jane Smith <jane@company.com>",
      subject: "Team lunch tomorrow",
      text: "Hi everyone, let's meet at noon for lunch...",
    },
  ],
  return_documents: true,
  rank_fields: ["from", "subject", "text"],
});
for (const result of response.results) {
  console.log(`Index: ${result.index}, Score: ${result.relevance_score}`);
}
```

### Rerank Models

| Model | API String | Max Context/Doc | Notes |
|-------|-----------|----------------|-------|
| MixedBread Rerank Large V2 | `mixedbread-ai/Mxbai-Rerank-Large-V2` | 32K tokens | Serverless, text reranking |
| Salesforce Llama Rank V1 | `Salesforce/Llama-Rank-V1` | 8K tokens | Dedicated endpoint, JSON rank_fields |

### Rerank Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Rerank model identifier |
| `query` | string | Yes | Search query |
| `documents` | string[] or object[] | Yes | Documents to rerank |
| `top_n` | int | No | Return only top N results |
| `return_documents` | bool | No | Include document text in response |
| `rank_fields` | string[] | No | Fields to rank by for JSON objects (Llama-Rank-V1 only) |

## RAG Pipeline Pattern

Embed -> Retrieve -> Rerank -> Generate:

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
candidates = vector_db.search(query_embedding, top_k=20)

# 3. Rerank for precision
reranked = client.rerank.create(
    model="mixedbread-ai/Mxbai-Rerank-Large-V2",
    query=query,
    documents=[c.text for c in candidates],
    top_n=5,
)

# 4. Use top results as context for LLM
context = "\n".join([candidates[r.index].text for r in reranked.results])
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
