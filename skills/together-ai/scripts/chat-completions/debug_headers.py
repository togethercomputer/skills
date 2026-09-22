#!/usr/bin/env python3
"""
Together AI Chat Completions — Debug Headers and Raw Responses (v2 SDK)

Inspect parsed chat output together with raw response headers for latency, routing,
and rate-limit debugging.

Usage:
    python debug_headers.py

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

from together import Together

client = Together()


def main() -> None:
    """Print a parsed chat response together with selected response headers."""
    response = client.chat.completions.with_raw_response.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        extra_headers={"x-together-debug": "1"},
    )

    parsed = response.parse()
    print("=== Parsed Response ===")
    print(parsed.choices[0].message.content)
    print()

    print("=== Selected Headers ===")
    interesting_headers = [
        "x-request-id",
        "x-together-traceid",
        "x-cluster",
        "x-engine-pod",
        "x-api-received",
        "x-api-call-start",
        "x-api-call-end",
        "x-inference-version",
        "x-ratelimit-limit",
        "x-ratelimit-remaining",
        "x-ratelimit-reset",
        "x-tokenlimit-limit",
        "x-tokenlimit-remaining",
    ]
    header_map = dict(response.headers)
    for key in interesting_headers:
        if key in header_map:
            print(f"{key}: {header_map[key]}")


if __name__ == "__main__":
    main()
