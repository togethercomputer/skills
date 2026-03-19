---
name: together-code-interpreter
description: Execute Python code in a sandboxed environment via Together Code Interpreter (TCI). $0.03 per session, 60-minute lifespan, stateful sessions with pre-installed data science packages. Use when users need to run Python code remotely, execute computations, data analysis, generate plots, RL training environments, or agentic code execution workflows.
---

# Together Code Interpreter

## Overview

Execute Python code in sandboxed sessions via a simple API call. Sessions persist state for 60 minutes and come pre-installed with popular data science packages.

- Endpoint: `https://api.together.ai/tci/execute`
- Pricing: $0.03 per session
- Session lifespan: 60 minutes (reusable via `session_id`)
- Also available as an MCP server via Smithery

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together
```

```shell
# or with pip
pip install together
```

```shell
# TypeScript / JavaScript
npm install together-ai
```

Set your API key:

```shell
export TOGETHER_API_KEY=<your-api-key>
```

## Quick Start

### Execute Code

```python
from together import Together
client = Together()

response = client.code_interpreter.execute(
    code='print("Hello from TCI!")',
    language="python",
)
print(f"Status: {response.data.status}")
for output in response.data.outputs:
    print(f"{output.type}: {output.data}")
```

```typescript
import Together from "together-ai";
const client = new Together();

const response = await client.codeInterpreter.execute({
  code: 'print("Hello from TCI!")',
  language: "python",
});
if (response.errors) {
  console.log(`Errors: ${response.errors}`);
} else {
  for (const output of response.data.outputs) {
    console.log(`${output.type}: ${output.data}`);
  }
}
```

```shell
curl -X POST "https://api.together.ai/tci/execute" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"language": "python", "code": "print(\"Hello from TCI!\")"}'
```

### Reuse Sessions (Maintain State)

```python
# First call -- creates a session
response1 = client.code_interpreter.execute(code="x = 42", language="python")
session_id = response1.data.session_id

# Second call -- reuses state
response2 = client.code_interpreter.execute(
    code='print(f"x = {x}")',
    language="python",
    session_id=session_id,
)
# Output: stdout: x = 42
```

```typescript
import Together from "together-ai";
const client = new Together();

// First call -- creates a session
const response1 = await client.codeInterpreter.execute({
  code: "x = 42",
  language: "python",
});

if (response1.errors) {
  console.log(`Errors: ${response1.errors}`);
} else {
  const sessionId = response1.data.session_id;

  // Second call -- reuses state
  const response2 = await client.codeInterpreter.execute({
    code: 'print(f"The value of x is {x}")',
    language: "python",
    session_id: sessionId,
  });

  if (!response2.errors) {
    for (const output of response2.data.outputs) {
      console.log(`${output.type}: ${output.data}`);
    }
  }
}
```

```shell
# First call -- creates a session
curl -X POST "https://api.together.ai/tci/execute" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"language": "python", "code": "x = 42"}'

# Second call -- reuse session_id from the first response
curl -X POST "https://api.together.ai/tci/execute" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "code": "print(f\"The value of x is {x}\")",
    "session_id": "YOUR_SESSION_ID_FROM_FIRST_RESPONSE"
  }'
```

### Upload Files

```python
script_file = {
    "name": "myscript.py",
    "encoding": "string",
    "content": "import sys\nprint(f'Hello from inside {sys.argv[0]}!')",
}

response = client.code_interpreter.execute(
    code="!python myscript.py",
    language="python",
    files=[script_file],
)
```

```typescript
const scriptFile = {
  name: "myscript.py",
  encoding: "string",
  content: "import sys\nprint(f'Hello from inside {sys.argv[0]}!')",
};

const response = await client.codeInterpreter.execute({
  code: "!python myscript.py",
  language: "python",
  files: [scriptFile],
});
```

```shell
curl -X POST "https://api.together.ai/tci/execute" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "files": [{"name": "myscript.py", "encoding": "string", "content": "import sys\nprint(f'"'"'Hello from {sys.argv[0]}!'"'"')"}],
    "code": "!python myscript.py"
  }'
```

### Data Analysis and Charts

```python
response = client.code_interpreter.execute(
    code="""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

data = np.random.randn(1000)
print(f"Mean: {data.mean():.4f}, Std: {data.std():.4f}")

plt.figure(figsize=(8, 4))
plt.hist(data, bins=30, edgecolor='black')
plt.title('Normal Distribution')
plt.show()
""",
    language="python",
)
# stdout output + display_data with {"image/png": "base64..."} for the chart
```

### Install Packages

```python
response = client.code_interpreter.execute(
    code="!pip install transformers\nimport transformers\nprint(transformers.__version__)",
    language="python",
)
```

## Response Format

```json
{
  "data": {
    "session_id": "ses_CM42NfvvzCab123",
    "status": "success",
    "outputs": [
      {"type": "stdout", "data": "Hello!\n"},
      {"type": "display_data", "data": {"image/png": "iVBOR..."}}
    ]
  },
  "errors": null
}
```

### Output Types

| Type | Description |
|------|-------------|
| `stdout` | Standard output text |
| `stderr` | Standard error text |
| `error` | Exception/failure message |
| `display_data` | Rich output: images (PNG/JPEG/GIF/SVG), HTML, Markdown, LaTeX, PDF, Vega/Vega-Lite, GeoJSON |
| `execute_result` | Expression result (same formats as display_data) |

## List Active Sessions

```python
response = client.code_interpreter.sessions.list()
for session in response.data.sessions:
    print(f"{session.id}: {session.execute_count} executions, expires {session.expires_at}")
```

```typescript
const response = await client.codeInterpreter.sessions.list();
for (const session of response.data?.sessions ?? []) {
  console.log(`${session.id}: executions=${session.execute_count}, expires=${session.expires_at}`);
}
```

```shell
curl -X GET "https://api.together.ai/tci/sessions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"
```

## Pre-installed Packages

aiohttp, beautifulsoup4, bokeh, gensim, imageio, joblib, librosa, matplotlib, nltk, numpy, opencv-python, openpyxl, pandas, plotly, pytest, python-docx, pytz, requests, scikit-image, scikit-learn, scipy, seaborn, soundfile, spacy, sympy, textblob, tornado, urllib3, xarray, xlrd

Install additional packages with `!pip install <package>`.

## Use Cases

- **Data analysis**: Pandas, NumPy, matplotlib workflows
- **RL training**: Interactive code execution with reward signals
- **Agentic workflows**: LLM-generated code execution in a loop
- **Visualization**: Generate charts and plots returned as base64 images

## Resources

- **Full API reference**: See [references/api-reference.md](references/api-reference.md)
- **Runnable script**: See [scripts/execute_with_session.py](scripts/execute_with_session.py) -- execute code with session reuse, data analysis, and chart generation (v2 SDK)
- **Runnable script (TypeScript)**: See [scripts/execute_with_session.ts](scripts/execute_with_session.ts) -- execute code with session reuse, file uploads, and chart generation (TypeScript SDK)
- **Official docs**: [Together Code Interpreter](https://docs.together.ai/docs/together-code-interpreter)
- **API reference**: [TCI API](https://docs.together.ai/reference/tci-execute)
