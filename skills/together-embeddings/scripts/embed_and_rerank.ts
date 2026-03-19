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
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

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
  const response = await client.embeddings.create({
    model: "intfloat/multilingual-e5-large-instruct",
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
