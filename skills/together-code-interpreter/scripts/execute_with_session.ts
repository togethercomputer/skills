#!/usr/bin/env -S npx tsx
/**
 * Together AI Code Interpreter — Execute Code with Session Reuse (TypeScript SDK)
 *
 * Run Python code in a sandboxed environment, reuse sessions to persist state,
 * upload files, and handle display outputs.
 *
 * Usage:
 *     npx tsx execute_with_session.ts
 *
 * Requires:
 *     npm install together-ai
 *     export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";

const client = new Together();

async function executeCode(
  code: string,
  sessionId?: string,
  files?: { name: string; encoding: string; content: string }[]
): Promise<{ sessionId: string | null; outputs: any[] }> {
  const params: any = { code, language: "python" };
  if (sessionId) params.session_id = sessionId;
  if (files) params.files = files;

  const response = await client.codeInterpreter.execute(params);

  if (response.errors) {
    console.error(`Errors: ${JSON.stringify(response.errors)}`);
    return { sessionId: null, outputs: [] };
  }

  const outputs: any[] = [];
  for (const output of response.data.outputs) {
    if (output.type === "stdout" || output.type === "stderr") {
      console.log(`  [${output.type}] ${output.data}`);
    } else if (output.type === "error") {
      console.log(`  [error] ${output.data}`);
    } else if (output.type === "display_data" || output.type === "execute_result") {
      const keys =
        typeof output.data === "object" ? Object.keys(output.data) : [];
      console.log(`  [${output.type}] ${JSON.stringify(keys)}`);
    }
    outputs.push({ type: output.type, data: output.data });
  }

  return { sessionId: response.data.session_id, outputs };
}

async function listSessions() {
  const response = await client.codeInterpreter.sessions.list();
  for (const session of response.data?.sessions ?? []) {
    console.log(
      `  Session ${session.id}: ${session.execute_count} executions, expires ${session.expires_at}`
    );
  }
}

async function main() {
  // --- Example 1: Single execution ---
  console.log("=== Single execution ===");
  const result = await executeCode(
    'print("Hello from Together Code Interpreter!")'
  );
  const sessionId = result.sessionId!;
  console.log(`Session ID: ${sessionId}\n`);

  // --- Example 2: Reuse session (state persists) ---
  console.log("=== Session reuse -- define variable ===");
  await executeCode("x = 42\nprint(f'Set x = {x}')", sessionId);

  console.log("\n=== Session reuse -- access variable ===");
  await executeCode("print(f'x is still {x}')", sessionId);

  // --- Example 3: Data analysis ---
  console.log("\n=== Data analysis ===");
  await executeCode(
    `
import numpy as np

data = np.random.randn(1000)
print(f"Mean: {data.mean():.4f}")
print(f"Std:  {data.std():.4f}")
print(f"Min:  {data.min():.4f}")
print(f"Max:  {data.max():.4f}")
`,
    sessionId
  );

  // --- Example 4: Chart generation ---
  console.log("\n=== Chart generation ===");
  await executeCode(
    `
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
plt.figure(figsize=(8, 4))
plt.plot(x, np.sin(x), label='sin(x)')
plt.plot(x, np.cos(x), label='cos(x)')
plt.legend()
plt.title('Trig Functions')
plt.show()
`,
    sessionId
  );

  // --- Example 5: File upload ---
  console.log("\n=== File upload ===");
  await executeCode("!python myscript.py", undefined, [
    {
      name: "myscript.py",
      encoding: "string",
      content: "import sys\nprint(f'Hello from {sys.argv[0]}!')",
    },
  ]);

  // --- List active sessions ---
  console.log("\n=== Active sessions ===");
  await listSessions();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
