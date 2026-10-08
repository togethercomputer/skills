# Together AI: Embeddings and Reranking

**Together does not currently offer embedding or rerank models.** Checked 2026-10-07:

- The serverless catalog lists no embedding or rerank models.
- The deprecations page shows them removed: `intfloat/multilingual-e5-large-instruct` on
  2026-09-15 (not available on dedicated endpoints either), the BGE, GTE, and M2-BERT embedding
  models earlier, and the rerank model `mixedbread-ai/Mxbai-Rerank-Large-V2` on 2026-03-06.
- The dedicated deployment catalog (`tg beta models public`) lists no embedding or rerank models.

Calls to the old IDs fail with `Unable to access non-serverless model` or a 503
`model_not_available`. Retrying, or trying other embedding IDs, will not help.

## What to do

1. Stop and tell the user that Together does not offer embeddings right now. Do not build a
   pipeline that cannot run, and do not loop on the errors above.
2. If the user already has a Together dedicated endpoint serving an embedding model, the scripts
   below work against it: set `EMBEDDING_MODEL` to the endpoint string. Dedicated inference uses
   `Together(base_url="https://api-inference.together.ai/v1")`.
3. Otherwise ask the user how to proceed (for example, another embedding provider). Do not pick
   one silently.
4. Generation over retrieved text still works on Together: `domains/chat-completions.md`.

## Rules (when an embedding endpoint exists)

- Use the same model for indexing and querying; vectors from different models do not compare.
- Chunk documents below the model's context length.
- Retrieve by cosine similarity: in memory for prototypes, a vector database in production.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/embeddings/semantic_search.py](scripts/embeddings/semantic_search.py) | 181 | embed a corpus, in-memory cosine store, query, optional rerank | the user has an embedding endpoint |
| [scripts/embeddings/rag_pipeline.py](scripts/embeddings/rag_pipeline.py) | 175 | embed, retrieve, then answer with serverless chat | the user has an embedding endpoint |
| [scripts/embeddings/embed_and_rerank.py](scripts/embeddings/embed_and_rerank.py) (.ts) | 185 | minimal embed plus similarity, rerank with cosine fallback | smallest working example |
| [references/embeddings/api-reference.md](references/embeddings/api-reference.md) | 177 | `/embeddings` and `/rerank` request and response fields, status codes | request or response shapes |
| [references/embeddings/models.md](references/embeddings/models.md) | 95 | historical embedding and rerank models, parameters, response shapes | parameter or response details |

The scripts read `EMBEDDING_MODEL` (and optional `RERANK_MODEL`) as endpoint strings and exit
with a clear message when it is unset.

## Docs

- [Serverless models](https://docs.together.ai/docs/serverless/models) (embedding section)
- [Deprecations](https://docs.together.ai/docs/deprecations)
- [Rerank](https://docs.together.ai/docs/inference/embeddings/rerank)
