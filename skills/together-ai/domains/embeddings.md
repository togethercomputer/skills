# Together AI: Embeddings and Reranking

Dense vectors for semantic search and RAG retrieval, plus reranking as a second-stage precision
step. This is retrieval plumbing; the answer-generation step is `domains/chat-completions.md`.

**Availability: Together serves no embedding or rerank models serverless right now.** Calling a
model ID such as `intfloat/multilingual-e5-large-instruct` on the default API returns
`Unable to access non-serverless model` or a 503 `model_not_available`. Retrying, or trying other
embedding IDs, will not help. Either deploy a model on a dedicated endpoint, or stop and tell the
user that embeddings need one. Check once that this is still true before deploying:
`tg beta models public --product serverless --json` and look for `CAPABILITY_EMBEDDING`.

## Workflow

1. Confirm the user needs vectors or retrieval, not direct generation.
2. Get an embedding endpoint. Deploying bills per minute and takes up to ~20 minutes to provision,
   so do it only with the user's go-ahead:
   ```bash
   tg beta models public --product dedicated --json \
     | jq -r '.data[] | select(.displayType=="embedding") | .name'
   tg beta endpoints deploy MODEL_NAME --endpoint my-embeddings --min-replicas 1 --max-replicas 1
   ```
   Follow `domains/dedicated-model-inference.md` to wait for `READY` and to tear it down later.
3. Call it on the dedicated base URL, with the endpoint string (`PROJECT_SLUG/my-embeddings`) as
   `model`:
   ```python
   from together import Together

   dedicated = Together(base_url="https://api-inference.together.ai/v1")
   vecs = dedicated.embeddings.create(model="PROJECT_SLUG/my-embeddings", input=["a", "b"])
   vectors = [d.embedding for d in vecs.data]
   ```
4. Embed corpus and queries with the same model. Chunk documents below the model's context length
   (`contextLength` in its catalog entry; 514 tokens for `multilingual-e5-large-instruct`).
5. Retrieve by cosine similarity: in memory for prototypes, a vector database in production.
6. Rerank only if it is worth a second dedicated endpoint; otherwise keep the cosine order.

## Rules

- Keep the model identical between indexing and querying; vectors from different models are not
  comparable.
- Rerank is a separate model on its own dedicated endpoint (for example
  `mixedbread-ai/mxbai-rerank-large-v2`) called with `rerank.create` on the same base URL.
- Delete the endpoint when the job is done; it bills while replicas run.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/embeddings/semantic_search.py](scripts/embeddings/semantic_search.py) | 181 | embed a corpus, in-memory cosine store, query, optional rerank | building search |
| [scripts/embeddings/rag_pipeline.py](scripts/embeddings/rag_pipeline.py) | 175 | embed, retrieve, then generate an answer with serverless chat | building RAG |
| [scripts/embeddings/embed_and_rerank.py](scripts/embeddings/embed_and_rerank.py) (.ts) | 185 | minimal embed plus similarity, rerank with cosine fallback | smallest working example |
| [references/embeddings/api-reference.md](references/embeddings/api-reference.md) | 174 | `/embeddings` and `/rerank` request and response fields, status codes | a field or error the scripts do not show |
| [references/embeddings/models.md](references/embeddings/models.md) | 98 | embedding and rerank parameters and response shapes, choosing a model | comparing models or parameters |

The scripts read `EMBEDDING_MODEL` (and optional `RERANK_MODEL`) as endpoint strings and exit
with a clear message when it is unset.

## Docs

- [Embeddings overview](https://docs.together.ai/docs/embeddings-overview)
- [Rerank overview](https://docs.together.ai/docs/rerank-overview)
- [Serverless models](https://docs.together.ai/docs/serverless/models) (embedding section)
- [Embeddings API](https://docs.together.ai/reference/embeddings)
