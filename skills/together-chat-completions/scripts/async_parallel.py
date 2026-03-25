#!/usr/bin/env python3
"""
Together AI Chat Completions — Async Parallel Requests (v2 SDK)

Demonstrates using AsyncTogether to run multiple independent
chat completion requests in parallel.

Usage:
    python async_parallel.py

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import asyncio
from together import AsyncTogether


async def main() -> None:
    client = AsyncTogether()

    prompts = [
        "What is the capital of France?",
        "Write a haiku about the ocean",
        "What is 42 * 37?",
        "Name three programming languages created in the 1990s",
    ]

    print(f"Sending {len(prompts)} requests in parallel...\n")

    tasks = [
        client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        for prompt in prompts
    ]

    responses = await asyncio.gather(*tasks)

    for prompt, response in zip(prompts, responses):
        answer = response.choices[0].message.content.strip()
        print(f"Q: {prompt}")
        print(f"A: {answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
