#!/usr/bin/env python3
"""
Together AI Chat Completions — Reasoning Models (v2 SDK)

Demonstrates reasoning with separate reasoning field, DeepSeek R1 <think> tags,
reasoning effort control, and enabling/disabling reasoning on hybrid models.

Usage:
    python reasoning_models.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import re
from together import Together

client = Together()


def reasoning_field_streaming() -> None:
    """Most reasoning models return a separate `reasoning` field."""
    print("=== Reasoning Field (Kimi K2.5 streaming) ===")
    stream = client.chat.completions.create(
        model="moonshotai/Kimi-K2.5",
        messages=[
            {"role": "user", "content": "Which number is bigger, 9.11 or 9.9?"},
        ],
        stream=True,
    )

    reasoning_text = ""
    content_text = ""
    for chunk in stream:
        if chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning") and delta.reasoning:
                reasoning_text += delta.reasoning
            if hasattr(delta, "content") and delta.content:
                content_text += delta.content

    print(f"Reasoning: {reasoning_text[:200]}...")
    print(f"Answer: {content_text}")
    print()


def reasoning_field_non_streaming() -> None:
    """Non-streaming access to reasoning field."""
    print("=== Reasoning Field (non-streaming) ===")
    response = client.chat.completions.create(
        model="moonshotai/Kimi-K2.5",
        messages=[{"role": "user", "content": "What is 15% of 240?"}],
    )
    print(f"Reasoning: {response.choices[0].message.reasoning[:200]}...")
    print(f"Answer: {response.choices[0].message.content}")
    print()


def deepseek_r1_think_tags() -> None:
    """DeepSeek R1 outputs reasoning in <think> tags within content."""
    print("=== DeepSeek R1 (<think> tags) ===")
    stream = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1",
        messages=[
            {"role": "user", "content": "Which number is bigger 9.9 or 9.11?"},
        ],
        stream=True,
    )

    full_content = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content or ""
        full_content += content

    # Parse <think> tags
    think_match = re.search(r"<think>(.*?)</think>", full_content, re.DOTALL)
    thinking = think_match.group(1).strip() if think_match else ""
    answer = re.sub(r"<think>.*?</think>", "", full_content, flags=re.DOTALL).strip()

    print(f"Thinking: {thinking[:200]}...")
    print(f"Answer: {answer}")
    print()


def reasoning_effort_example() -> None:
    """Control reasoning depth with reasoning_effort (GPT-OSS)."""
    print("=== Reasoning Effort (GPT-OSS) ===")
    for effort in ["low", "medium", "high"]:
        stream = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": "Is 17 a prime number?"}],
            temperature=1.0,
            top_p=1.0,
            reasoning_effort=effort,
            stream=True,
        )

        content = ""
        for chunk in stream:
            content += chunk.choices[0].delta.content or ""

        print(f"  effort={effort}: {content[:100]}...")
    print()


def toggle_reasoning() -> None:
    """Enable/disable reasoning on hybrid models."""
    print("=== Toggle Reasoning (Kimi K2.5) ===")

    # Reasoning enabled (thinking mode)
    print("  [reasoning=True]")
    stream = client.chat.completions.create(
        model="moonshotai/Kimi-K2.5",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        reasoning={"enabled": True},
        temperature=1.0,
        stream=True,
    )

    reasoning_text = ""
    content_text = ""
    for chunk in stream:
        if chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning") and delta.reasoning:
                reasoning_text += delta.reasoning
            if hasattr(delta, "content") and delta.content:
                content_text += delta.content

    print(f"  Reasoning tokens: {len(reasoning_text)} chars")
    print(f"  Answer: {content_text[:100]}")

    # Reasoning disabled (instant mode)
    print("  [reasoning=False]")
    response = client.chat.completions.create(
        model="moonshotai/Kimi-K2.5",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        reasoning={"enabled": False},
        temperature=0.6,
    )
    print(f"  Answer: {response.choices[0].message.content[:100]}")


if __name__ == "__main__":
    reasoning_field_streaming()
    reasoning_field_non_streaming()
    deepseek_r1_think_tags()
    reasoning_effort_example()
    toggle_reasoning()
