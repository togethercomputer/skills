# Embeddings & Rerank API Reference
## Contents

- [Endpoints](#endpoints)
- [Create Embeddings](#create-embeddings)
- [Rerank Documents](#rerank-documents)
- [HTTP Status Codes](#http-status-codes)


Base URL: `https://api.together.xyz/v1`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /embeddings` | Generate embeddings | Convert text to vector representations |
| `POST /rerank` | Rerank documents | Reorder documents by relevance to a query (dedicated endpoint required) |

## Create Embeddings

### Single Input

```python
from together import Together
client = Together()

response = client.embeddings.create(
    model="intfloat/multilingual-e5-large-instruct",
    input="Our solar system orbits the Milky Way galaxy at about 515,000 mph",
)
print(response.data[0].embedding[:5])
```

```typescript
import Together from "together-ai";
const client = new Together();

const response = await client.embeddings.create({
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

### Batch Input

Pass a list of strings to embed multiple texts in a single request. For large
corpora, batch in groups (e.g. 100 texts per call) to avoid timeouts and stay
within rate limits.

```python
response = client.embeddings.create(
    model="intfloat/multilingual-e5-large-instruct",
    input=["First document", "Second document", "Third document"],
)
for item in response.data:
    print(f"Index {item.index}: {len(item.embedding)} dimensions")
```

```typescript
const response = await client.embeddings.create({
  model: "intfloat/multilingual-e5-large-instruct",
  input: ["First document", "Second document", "Third document"],
});
for (const item of response.data) {
  console.log(`Index ${item.index}: ${item.embedding.length} dimensions`);
}
```

**Batching tip:** For corpora larger than ~100 documents, split into batches:

```python
batch_size = 100
for start in range(0, len(texts), batch_size):
    batch = texts[start : start + batch_size]
    response = client.embeddings.create(
        model="intfloat/multilingual-e5-large-instruct",
        input=batch,
    )
    # store response.data embeddings
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Embedding model identifier |
| `input` | string or string[] | Yes | Text(s) to embed |

### Supported Models

- `intfloat/multilingual-e5-large-instruct`

### Response Schema

```json
{
  "object": "list",
  "model": "intfloat/multilingual-e5-large-instruct",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0023, -0.0142, 0.0381, ...],
      "index": 0
    }
  ]
}
```

## Rerank Documents

Reranking requires a dedicated endpoint. See the
[Rerank Overview](https://docs.together.ai/docs/rerank-overview) for current models and
setup instructions.

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Rerank model identifier |
| `query` | string | Yes | Search query |
| `documents` | string[] or object[] | Yes | Documents to rerank |
| `top_n` | integer | No | Return only top N results |
| `return_documents` | boolean | No | Include document text in response |
| `rank_fields` | string[] | No | Fields to rank by for JSON objects |

### Response Schema

```json
{
  "object": "rerank",
  "id": "rerank-abc123",
  "model": "<your-dedicated-endpoint-model>",
  "results": [
    {
      "index": 0,
      "relevance_score": 0.9823,
      "document": {"text": "..."}
    },
    {
      "index": 2,
      "relevance_score": 0.8451
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "total_tokens": 150
  }
}
```

The `document` field is only present when `return_documents=true`.

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (invalid API key) |
| 404 | Not found (invalid model) |
| 429 | Rate limit exceeded |
| 503 | Service overloaded |
| 504 | Request timeout |
