#!/usr/bin/env python3
"""
Together AI Chat Completions — Basic Chat and Streaming (v2 SDK)

Demonstrates single-query chat, streaming, and multi-turn conversation.

Usage:
    python chat_basic.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

from together import Together

client = Together()


def basic_chat() -> None:
    """Send a single chat completion request."""
    print("=== Basic Chat ===")
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": "What are some fun things to do in NYC?"}],
    )
    print(response.choices[0].message.content)
    print()


def streaming_chat() -> None:
    """Stream tokens incrementally."""
    print("=== Streaming ===")
    stream = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": "Write a haiku about coding"}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices:
            print(chunk.choices[0].delta.content or "", end="", flush=True)
    print("\n")


def multi_turn_chat() -> None:
    """Multi-turn conversation with system prompt."""
    print("=== Multi-Turn ===")
    messages = [
        {"role": "system", "content": "You are a helpful travel guide. Keep answers brief."},
        {"role": "user", "content": "What should I do in Paris?"},
    ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
    )
    assistant_reply = response.choices[0].message.content
    print(f"User: What should I do in Paris?")
    print(f"Assistant: {assistant_reply}\n")

    # Continue the conversation
    messages.append({"role": "assistant", "content": assistant_reply})
    messages.append({"role": "user", "content": "How about food recommendations?"})

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
    )
    print(f"User: How about food recommendations?")
    print(f"Assistant: {response.choices[0].message.content}")


if __name__ == "__main__":
    basic_chat()
    streaming_chat()
    multi_turn_chat()
