#!/usr/bin/env -S npx tsx
/**
 * Source: mintlify-docs-main/openapi.yaml x-codeSamples
 * Operations: tci/execute, sessions/list
 * Minimal edits: wrapped in main() for script execution.
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main() {
  const executeResponse = await client.codeInterpreter.execute({
    code: "print('Hello world!')",
    language: "python",
  });

  console.log(executeResponse.data?.outputs?.[0]?.data);

  const sessionsResponse = await client.codeInterpreter.sessions.list();

  for (const session of sessionsResponse.data?.sessions ?? []) {
    console.log(session.id);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
