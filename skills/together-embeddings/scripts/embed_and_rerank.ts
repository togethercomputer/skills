#!/usr/bin/env -S npx tsx
/**
 * Source: mintlify-docs-main/openapi.yaml x-codeSamples
 * Operations: embeddings, rerank
 * Minimal edits: wrapped in main() for script execution.
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main() {
  const embeddingsResponse = await client.embeddings.create({
    model: "BAAI/bge-large-en-v1.5",
    input: "New York City",
  });

  console.log(embeddingsResponse.data[0].embedding);

  const documents = [
    {
      title: "Llama",
      text: "The llama is a domesticated South American camelid, widely used as a meat and pack animal by Andean cultures since the pre-Columbian era.",
    },
    {
      title: "Panda",
      text: "The giant panda (Ailuropoda melanoleuca), also known as the panda bear or simply panda, is a bear species endemic to China.",
    },
    {
      title: "Guanaco",
      text: "The guanaco is a camelid native to South America, closely related to the llama. Guanacos are one of two wild South American camelids; the other species is the vicuna, which lives at higher elevations.",
    },
    {
      title: "Wild Bactrian camel",
      text: "The wild Bactrian camel (Camelus ferus) is an endangered species of camel endemic to Northwest China and southwestern Mongolia.",
    },
  ];

  const rerankResponse = await client.rerank.create({
    model: "Salesforce/Llama-Rank-v1",
    query: "What animals can I find near Peru?",
    documents,
  });

  for (const result of rerankResponse.results) {
    console.log(`Rank: ${result.index + 1}`);
    console.log(`Title: ${documents[result.index].title}`);
    console.log(`Text: ${documents[result.index].text}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
