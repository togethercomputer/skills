# Sandboxes API Reference
## Contents

- [Endpoints](#endpoints)
- [Execute Code](#execute-code)
- [List Sessions](#list-sessions)
- [Pre-installed Packages](#pre-installed-packages)
- [Pricing](#pricing)
- [Alternative Access](#alternative-access)


## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /tci/execute` | Execute code | Run a code snippet in a sandboxed session |
| `GET /tci/sessions` | List sessions | List all active sessions |

Base URL: `https://api.together.ai`
Authentication: `Authorization: Bearer $TOGETHER_API_KEY`

## Execute Code

### Request (ExecuteRequest)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `language` | string | Yes | Programming language (`python`) |
| `code` | string | Yes | Code snippet to execute |
| `session_id` | string | No | Reuse an existing session for persistent state |
| `files` | array | No | Files to upload before execution |

### File Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | File name (e.g., `data.py`) |
| `encoding` | string | Yes | `string` or `base64` |
| `content` | string | Yes | File content |

### Response (ExecuteResponse)

| Field | Type | Description |
|-------|------|-------------|
| `data.session_id` | string | Session ID for follow-up calls |
| `data.status` | string | `success` |
| `data.outputs` | array | Execution results (see Output Types) |
| `errors` | array or null | Error details if execution failed |

### Output Types

| Type | Description | Data format |
|------|-------------|-------------|
| `stdout` | Standard output | string |
| `stderr` | Standard error | string |
| `error` | Exception/failure | string |
| `display_data` | Rich output | object (see below) |
| `execute_result` | Expression result | object (see below) |

**display_data / execute_result** data object may contain:

| Key | Description |
|-----|-------------|
| `application/json` | JSON data |
| `text/html` | HTML content |
| `text/markdown` | Markdown content |
| `text/latex` | LaTeX content |
| `image/png` | Base64-encoded PNG |
| `image/jpeg` | Base64-encoded JPEG |
| `image/gif` | Base64-encoded GIF |
| `image/svg+xml` | SVG content |
| `application/pdf` | Base64-encoded PDF |
| `application/vnd.vegalite.v5+json` | Vega-Lite visualization |
| `application/vnd.vega.v5+json` | Vega visualization |
| `application/geo+json` | GeoJSON data |

### Examples

```python
from together import Together
client = Together()

response = client.code_interpreter.execute(
    code='print("Hello world!")',
    language="python",
)
print(response.data.outputs[0].data)
```

```typescript
import Together from "together-ai";
const client = new Together();

const response = await client.codeInterpreter.execute({
  code: 'print("Hello world!")',
  language: "python",
});
console.log(response.data?.outputs?.[0]?.data);
```

```shell
curl -X POST "https://api.together.ai/tci/execute" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello world!\")", "language": "python"}'
```

### Session Reuse

```python
# First call creates a session
response1 = client.code_interpreter.execute(code="x = 42", language="python")
session_id = response1.data.session_id

# Second call reuses state
response2 = client.code_interpreter.execute(
    code='print(f"x = {x}")',
    language="python",
    session_id=session_id,
)
```

```typescript
const response1 = await client.codeInterpreter.execute({
  code: "x = 42",
  language: "python",
});
const sessionId = response1.data.session_id;

const response2 = await client.codeInterpreter.execute({
  code: 'print(f"x = {x}")',
  language: "python",
  session_id: sessionId,
});
```

```shell
# Use session_id from first response in subsequent calls
curl -X POST "https://api.together.ai/tci/execute" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"language": "python", "code": "x = 42"}'

curl -X POST "https://api.together.ai/tci/execute" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"language": "python", "code": "print(f\"x = {x}\")", "session_id": "ses_..."}'
```

### File Upload

```python
response = client.code_interpreter.execute(
    code="!python myscript.py",
    language="python",
    files=[{
        "name": "myscript.py",
        "encoding": "string",
        "content": "import sys\nprint(f'Hello from {sys.argv[0]}!')",
    }],
)
```

```typescript
const response = await client.codeInterpreter.execute({
  code: "!python myscript.py",
  language: "python",
  files: [{
    name: "myscript.py",
    encoding: "string",
    content: "import sys\nprint(f'Hello from {sys.argv[0]}!')",
  }],
});
```

```shell
curl -X POST "https://api.together.ai/tci/execute" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "files": [{"name": "myscript.py", "encoding": "string", "content": "print(\"hello\")"}],
    "code": "!python myscript.py"
  }'
```

### Retrieving Charts

`plt.show()` with the Agg backend does not reliably produce `display_data` outputs containing
`image/png`. To get chart images back to the client, save explicitly and base64-encode via stdout:

```python
# --- Remote code (runs in the sandbox) ---
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64, io

fig, ax = plt.subplots()
ax.bar(["Jan", "Feb", "Mar"], [100, 150, 130])

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=150)
buf.seek(0)
print("chart_b64:" + base64.b64encode(buf.read()).decode())
plt.close(fig)
```

```python
# --- Client side ---
import base64

for output in response.data.outputs:
    if output.type == "stdout" and "chart_b64:" in output.data:
        b64 = output.data.split("chart_b64:", 1)[1].strip()
        with open("chart.png", "wb") as f:
            f.write(base64.b64decode(b64))
```

If the API does return a `display_data` output with an `image/png` key, prefer that over stdout
parsing. Check both paths for maximum reliability.

## List Sessions

### Response (SessionListResponse)

| Field | Type | Description |
|-------|------|-------------|
| `data.sessions` | array | List of active session objects |

### Session Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session identifier (e.g., `ses_abcDEF123`) |
| `execute_count` | integer | Number of executions in this session |
| `started_at` | datetime | Session start timestamp |
| `last_execute_at` | datetime | Most recent execution timestamp |
| `expires_at` | datetime | Session expiration timestamp |

### Examples

```python
response = client.code_interpreter.sessions.list()
for session in response.data.sessions:
    print(f"{session.id}: {session.execute_count} executions, expires {session.expires_at}")
```

```typescript
const response = await client.codeInterpreter.sessions.list();
for (const session of response.data?.sessions ?? []) {
  console.log(`${session.id}: ${session.execute_count} executions`);
}
```

```shell
curl -X GET "https://api.together.ai/tci/sessions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"
```

## Pre-installed Packages

aiohttp, beautifulsoup4, bokeh, gensim, imageio, joblib, librosa, matplotlib, nltk, numpy, opencv-python, openpyxl, pandas, plotly, pytest, python-docx, pytz, requests, scikit-image, scikit-learn, scipy, seaborn, soundfile, spacy, sympy, textblob, tornado, urllib3, xarray, xlrd

Install additional packages at runtime with `!pip install <package>`.

## Pricing

$0.03 per session. Sessions last 60 minutes and support multiple executions.

## Alternative Access

Together AI also exposes MCP-compatible tooling for agent workflows that prefer MCP over direct API
calls. Use the direct TCI API when you need explicit SDK control over sessions, files, and response
objects; use MCP when the surrounding agent framework already speaks MCP.
