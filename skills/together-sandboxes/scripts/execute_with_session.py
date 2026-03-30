#!/usr/bin/env python3
"""
Together AI Code Interpreter — Execute Code with Session Reuse (v2 SDK)

Run Python code in a sandboxed environment, reuse sessions to persist state,
and handle file outputs.

Usage:
    python execute_with_session.py

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

from together import Together

client = Together()


def execute_code(code: str, session_id: str | None = None) -> dict:
    """Execute Python code, optionally in an existing session."""
    response = client.code_interpreter.execute(
        code=code,
        language="python",
        **({"session_id": session_id} if session_id else {}),
    )

    if response.errors:
        print(f"Errors: {response.errors}")
        return {"session_id": None, "outputs": [], "errors": response.errors}

    outputs = []
    for output in response.data.outputs:
        if output.type in ("stdout", "stderr"):
            print(f"  [{output.type}] {output.data}")
            outputs.append({"type": output.type, "data": output.data})
        elif output.type == "error":
            print(f"  [error] {output.data}")
            outputs.append({"type": "error", "data": output.data})
        elif output.type in ("display_data", "execute_result"):
            print(f"  [{output.type}] {list(output.data.keys()) if isinstance(output.data, dict) else output.data}")
            outputs.append({"type": output.type, "data": output.data})

    return {
        "session_id": response.data.session_id,
        "outputs": outputs,
        "errors": None,
    }


def list_sessions():
    """List active code interpreter sessions."""
    response = client.code_interpreter.sessions.list()
    for s in response.data.sessions:
        print(f"  Session {s.id}: {s.execute_count} executions, expires {s.expires_at}")
    return response.data.sessions


if __name__ == "__main__":
    # --- Example 1: Single execution ---
    print("=== Single execution ===")
    result = execute_code("print('Hello from Together Code Interpreter!')")
    session_id = result["session_id"]
    print(f"Session ID: {session_id}\n")

    # --- Example 2: Reuse session (state persists) ---
    print("=== Session reuse — define variable ===")
    execute_code("x = 42\nprint(f'Set x = {x}')", session_id=session_id)

    print("\n=== Session reuse — access variable ===")
    execute_code("print(f'x is still {x}')", session_id=session_id)

    # --- Example 3: Data analysis with packages ---
    print("\n=== Data analysis ===")
    execute_code(
        """
import numpy as np

data = np.random.randn(1000)
print(f"Mean: {data.mean():.4f}")
print(f"Std:  {data.std():.4f}")
print(f"Min:  {data.min():.4f}")
print(f"Max:  {data.max():.4f}")
""",
        session_id=session_id,
    )

    # --- Example 4: Generate a chart and retrieve as base64 PNG ---
    # plt.show() with the Agg backend does not reliably produce display_data
    # outputs. Instead, save the figure to a buffer and encode it explicitly.
    print("\n=== Chart generation ===")
    chart_result = execute_code(
        """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import base64, io

x = np.linspace(0, 10, 100)
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(x, np.sin(x), label='sin(x)')
ax.plot(x, np.cos(x), label='cos(x)')
ax.legend()
ax.set_title('Trig Functions')

buf = io.BytesIO()
fig.savefig(buf, format='png', dpi=150)
buf.seek(0)
png_b64 = base64.b64encode(buf.read()).decode()
plt.close(fig)
print(f"chart_png_base64:{png_b64}")
""",
        session_id=session_id,
    )

    # Extract and save the chart locally
    import base64 as _b64

    for out in chart_result["outputs"]:
        if out["type"] == "stdout" and "chart_png_base64:" in out["data"]:
            b64_str = out["data"].split("chart_png_base64:", 1)[1].strip()
            with open("trig_chart.png", "wb") as f:
                f.write(_b64.b64decode(b64_str))
            print(f"  Chart saved to trig_chart.png ({len(b64_str)} bytes b64)")

    # --- List active sessions ---
    print("\n=== Active sessions ===")
    list_sessions()
