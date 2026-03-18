# Embedding & Rerank Models Reference

## Embedding Models

| Model | API String | Size | Dimensions | Context | Best For |
|-------|-----------|------|-----------|---------|----------|
| Multilingual E5 Large | `intfloat/multilingual-e5-large-instruct` | 560M | 1,024 | 514 tokens | Multilingual retrieval (recommended) |
| BGE Base EN v1.5 | `BAAI/bge-base-en-v1.5` | 102M | 768 | 512 tokens | General English retrieval |
| UAE Large V1 | `WhereIsAI/UAE-Large-V1` | 335M | 1,024 | 512 tokens | English retrieval, classification |
| M2-BERT Retrieval 8k | `togethercomputer/m2-bert-80M-8k-retrieval` | 80M | 768 | 8,192 tokens | Long-context retrieval |

**Deprecated models (still functional, being removed):**

| Model | API String | Dimensions | Context | Deprecated |
|-------|-----------|-----------|---------|------------|
| BGE Large EN v1.5 | `BAAI/bge-large-en-v1.5` | 1,024 | 512 tokens | 2026-02-06 |
| E5 Mistral 7B | `intfloat/e5-mistral-7b-instruct` | 4,096 | 32,768 tokens | Limited support |

## Rerank Models

| Model | API String | Size | Max Doc Tokens | Notes |
|-------|-----------|------|---------------|-------|
| MixedBread Rerank Large V2 | `mixedbread-ai/Mxbai-Rerank-Large-V2` | 1.6B | 32,768 | Serverless, text-only |
| Salesforce Llama Rank V1 | `Salesforce/Llama-Rank-V1` | 8B | 8,192 | Dedicated endpoint, JSON rank_fields |

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
| `rank_fields` | string[] | No | Fields to use for ranking when documents are JSON objects (Llama-Rank-V1 only) |

## Rerank Response

```json
{
  "object": "rerank",
  "id": "rerank-abc123",
  "model": "mixedbread-ai/Mxbai-Rerank-Large-V2",
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

- **Multilingual, general use:** `intfloat/multilingual-e5-large-instruct` (1024d, recommended)
- **English-only, fast:** `BAAI/bge-base-en-v1.5` (768d, smaller and faster)
- **English, higher quality:** `WhereIsAI/UAE-Large-V1` (1024d)
- **Long documents:** `togethercomputer/m2-bert-80M-8k-retrieval` (768d, 8K context)

### Reranking

- **Serverless text reranking:** `mixedbread-ai/Mxbai-Rerank-Large-V2` (32K context per doc)
- **Structured JSON reranking:** `Salesforce/Llama-Rank-V1` (8K context, rank_fields support, dedicated endpoint required)
