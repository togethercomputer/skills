# Embedding & Rerank Models Reference

## Embedding Models

| Model | API String | Size | Dimensions | Context | Best For |
|-------|-----------|------|-----------|---------|----------|
| Multilingual E5 Large | `intfloat/multilingual-e5-large-instruct` | 560M | 1,024 | 514 tokens | Multilingual retrieval (recommended) |

## Rerank Models

Reranking is currently available exclusively via dedicated endpoints. Deploy a rerank model
as a dedicated endpoint, then use the `/v1/rerank` API.

See the [Rerank Overview](https://docs.together.ai/docs/rerank-overview) for available models
and setup instructions.

## Embeddings API Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Embedding model identifier |
| `input` | string or string[] | Yes | Text(s) to embed |

## Embeddings Response

```json
{
  "object": "list",
  "model": "intfloat/multilingual-e5-large-instruct",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0023, -0.0142, ...],
      "index": 0
    }
  ]
}
```

## Rerank Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Rerank model identifier |
| `query` | string | Yes | Search query |
| `documents` | string[] or object[] | Yes | Documents to rerank. Pass objects with named fields for structured documents. |
| `top_n` | int | No | Return only top N results |
| `return_documents` | bool | No | Include document text in response |
| `rank_fields` | string[] | No | Fields to use for ranking when documents are JSON objects |

## Rerank Response

```json
{
  "object": "rerank",
  "id": "rerank-abc123",
  "model": "<your-dedicated-endpoint-model>",
  "results": [
    {"index": 0, "relevance_score": 0.9823},
    {"index": 3, "relevance_score": 0.8451},
    {"index": 1, "relevance_score": 0.2134}
  ],
  "usage": {
    "prompt_tokens": 150,
    "total_tokens": 150
  }
}
```

## Choosing a Model

### Embeddings

The active serverless embedding model is `intfloat/multilingual-e5-large-instruct` (1024
dimensions, 514 token max input). It supports multilingual text and is recommended for all
embedding use cases including retrieval, semantic similarity, and classification.

### Reranking

There are currently no serverless rerank models. Reranking requires deploying a model on a
dedicated endpoint. See the [Rerank Overview](https://docs.together.ai/docs/rerank-overview)
for available models and instructions.
