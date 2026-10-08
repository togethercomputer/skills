#!/usr/bin/env -S npx tsx
/**
 * Together AI Embeddings Pipeline
 *
 * Embed documents and compute similarity.
 *
 * Note: Reranking requires a dedicated endpoint. The rerank function in this
 * file has been removed. See https://docs.together.ai/docs/rerank-overview
 * for setup instructions.
 *
 * Usage:
 *   npx tsx embed_and_rerank.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 *   export EMBEDDING_MODEL=your-project/your-embedding-endpoint  # dedicated endpoint string
 */

import Together from "together-ai";

// Together does not currently offer embedding models (see domains/embeddings.md).
// If you already have an embedding endpoint, set EMBEDDING_MODEL to its endpoint string.
// Dedicated inference is served from its own base URL.
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL ?? "";
const dedicatedClient = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
  baseURL: process.env.DEDICATED_BASE_URL ?? "https://api-inference.together.ai/v1",
});

function requireEmbeddingModel(): string {
  if (!EMBEDDING_MODEL) {
    console.error(
      "EMBEDDING_MODEL is not set. Together does not currently offer embedding models " +
        "(serverless or in the dedicated catalog). If you already have an embedding " +
        "endpoint, export its endpoint string. See domains/embeddings.md.",
    );
    process.exit(1);
  }
  return EMBEDDING_MODEL;
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

async function embedTexts(texts: string[]): Promise<number[][]> {
  const response = await dedicatedClient.embeddings.create({
    model: requireEmbeddingModel(),
    input: texts,
  });
  return response.data.map((item) => item.embedding);
}

async function embeddingSimilarity(): Promise<void> {
  console.log("=== Embedding Similarity ===");
  const texts = [
    "Python is a popular programming language",
    "JavaScript is used for web development",
    "Machine learning uses statistical models",
  ];
  const query = "What language is good for data science?";

  const embeddings = await embedTexts([...texts, query]);
  const queryEmb = embeddings[embeddings.length - 1];

  for (let i = 0; i < texts.length; i++) {
    const sim = cosineSimilarity(queryEmb, embeddings[i]);
    console.log(`  ${sim.toFixed(4)} -- ${texts[i]}`);
  }
}

// Note: Reranking requires a dedicated endpoint.
// See https://docs.together.ai/docs/rerank-overview for setup instructions.

async function main(): Promise<void> {
  await embeddingSimilarity();
}

main();
