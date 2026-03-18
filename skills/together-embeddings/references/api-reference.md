# Embeddings & Rerank API Reference

Base URL: `https://api.together.xyz/v1`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /embeddings` | Generate embeddings | Convert text to vector representations |
| `POST /rerank` | Rerank documents | Reorder documents by relevance to a query |

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

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Embedding model identifier |
| `input` | string or string[] | Yes | Text(s) to embed |

### Supported Models

- `intfloat/multilingual-e5-large-instruct`
- `BAAI/bge-base-en-v1.5`
- `WhereIsAI/UAE-Large-V1`
- `togethercomputer/m2-bert-80M-8k-retrieval`
- `BAAI/bge-large-en-v1.5` (deprecated)

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

### Text Reranking

```python
from together import Together
client = Together()

response = client.rerank.create(
    model="mixedbread-ai/Mxbai-Rerank-Large-V2",
    query="What animals can I find near Peru?",
    documents=[
        "The llama is a domesticated South American camelid.",
        "The giant panda is a bear species endemic to China.",
        "The guanaco is a camelid native to South America.",
        "The wild Bactrian camel is endemic to Northwest China.",
    ],
    top_n=2,
)
for result in response.results:
    print(f"Index: {result.index}, Score: {result.relevance_score:.4f}")
```

```typescript
import Together from "together-ai";
const client = new Together();

const response = await client.rerank.create({
  model: "mixedbread-ai/Mxbai-Rerank-Large-V2",
  query: "What animals can I find near Peru?",
  documents: [
    "The llama is a domesticated South American camelid.",
    "The giant panda is a bear species endemic to China.",
    "The guanaco is a camelid native to South America.",
    "The wild Bactrian camel is endemic to Northwest China.",
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
    "query": "What animals can I find near Peru?",
    "documents": [
      "The llama is a domesticated South American camelid.",
      "The giant panda is a bear species endemic to China.",
      "The guanaco is a camelid native to South America.",
      "The wild Bactrian camel is endemic to Northwest China."
    ],
    "top_n": 2
  }'
```

### Structured Document Reranking

Use `rank_fields` to rerank JSON objects by specific fields (Salesforce/Llama-Rank-V1 only):

```python
response = client.rerank.create(
    model="Salesforce/Llama-Rank-V1",
    query="Which pricing did we get from Oracle?",
    documents=[
        {
            "from": "Paul Doe <paul_fake_doe@oracle.com>",
            "subject": "Follow-up on cloud pricing",
            "text": "We are happy to give you the following pricing...",
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
```

```typescript
const response = await client.rerank.create({
  model: "Salesforce/Llama-Rank-V1",
  query: "Which pricing did we get from Oracle?",
  documents: [
    {
      from: "Paul Doe <paul_fake_doe@oracle.com>",
      subject: "Follow-up on cloud pricing",
      text: "We are happy to give you the following pricing...",
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
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Rerank model identifier |
| `query` | string | Yes | Search query |
| `documents` | string[] or object[] | Yes | Documents to rerank |
| `top_n` | integer | No | Return only top N results |
| `return_documents` | boolean | No | Include document text in response |
| `rank_fields` | string[] | No | Fields to rank by for JSON objects (Llama-Rank-V1 only) |

### Supported Models

- `mixedbread-ai/Mxbai-Rerank-Large-V2` (serverless, text reranking)
- `Salesforce/Llama-Rank-V1` (dedicated endpoint, JSON rank_fields support)

### Response Schema

```json
{
  "object": "rerank",
  "id": "rerank-abc123",
  "model": "mixedbread-ai/Mxbai-Rerank-Large-V2",
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
