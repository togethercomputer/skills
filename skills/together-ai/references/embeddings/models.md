# Embedding & Rerank Models Reference

## Embedding Models

Together does not currently offer embedding or rerank models (checked 2026-10-26): the serverless
catalog lists none, and the [deprecations page](https://docs.together.ai/docs/deprecations) shows
the models below removed. They are kept here for reference only.

| Model | API String | Size | Dimensions | Context | Best For |
|-------|-----------|------|-----------|---------|----------|
| Multilingual E5 Large | `intfloat/multilingual-e5-large-instruct` | 560M | 1,024 | 514 tokens | Removed 2026-09-15 |

## Rerank Models

No rerank model is currently offered: `mixedbread-ai/Mxbai-Rerank-Large-V2` was removed on
2026-03-06 and the dedicated deployment catalog lists no rerank models. The `/v1/rerank` API
shape below applies if the user already has a rerank endpoint.


## Embeddings API Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Embedding model identifier |
| `input` | string or string[] | Yes | Text(s) to embed |

## Embeddings Response

```json
{
  "object": "list",
  "model": "your-project/your-embedding-endpoint",
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

No embedding model is offered serverless. The last one, `intfloat/multilingual-e5-large-instruct`, was
removed on 2026-09-15 with no replacement and is not available on dedicated endpoints either. If
the user already serves an embedding model on a dedicated endpoint, pass that endpoint string as
`model` and follow that model's own dimensions and input limit.

### Practical Notes

- **Respect the model's input limit.** Text beyond it can be truncated silently, so split long
  documents (articles, product pages, support tickets) into chunks before embedding. The removed
  E5 model stopped at 514 tokens, roughly a short paragraph.
- **Use the same model for indexing and querying.** Mixing embedding models between corpus
  and query will produce meaningless similarity scores.
- **Prefer cosine similarity.** It ranks the same as dot product when the model returns
  normalized vectors, and stays correct when it does not.

### Reranking

No rerank model is currently offered, serverless or in the dedicated catalog. Without one, keep
the cosine-similarity order.
