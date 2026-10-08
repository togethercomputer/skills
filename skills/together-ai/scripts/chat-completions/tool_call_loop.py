#!/usr/bin/env python3
"""
Together AI Function Calling — Complete Tool Call Loop (v2 SDK)

Runs a multi-round tool loop: the model calls tools, the tools run, results go
back, and the loop repeats until the model answers without calling a tool. It
also enforces grounding: if the task requires an action (for example "open a
ticket") and no tool result exists for it, the loop does not accept the answer.
It tells the model what is missing and continues, so a model that skips a step
and then claims it happened cannot end the run with an invented result.

Usage:
    python tool_call_loop.py

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import json
from typing import Any, Callable

from together import Together

client = Together()

MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

# --- 1. Define tools ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name, e.g. 'San Francisco, CA'"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price for a ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker, e.g. 'AAPL'"},
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
        },
    },
]


# --- 2. Implement your functions ---
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    """Replace with real API call."""
    return {"location": location, "temperature": 72, "unit": unit, "condition": "sunny"}


def get_stock_price(symbol: str) -> dict:
    """Replace with real API call."""
    return {"symbol": symbol, "price": 185.50, "currency": "USD"}


FUNCTIONS: dict[str, Callable[..., Any]] = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
}


def execute_tool_call(tc: Any) -> tuple[str, bool]:
    """Run one tool call. Returns (JSON result for the model, whether it succeeded).

    Errors go back to the model as a result rather than raising, so it can correct
    bad arguments or pick another tool on the next round.
    """
    fn = FUNCTIONS.get(tc.function.name)
    if fn is None:
        return json.dumps({"error": f"unknown tool {tc.function.name!r}"}), False
    try:
        args = json.loads(tc.function.arguments or "{}")
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"arguments were not valid JSON: {exc}"}), False
    try:
        return json.dumps(fn(**args)), True
    except Exception as exc:  # report tool failures to the model instead of crashing
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"}), False


def run_tool_loop(
    messages: list[dict],
    required_tools: set[str] | None = None,
    max_rounds: int = 8,
) -> tuple[str, set[str], set[str]]:
    """Loop until the model answers without tool calls and every required tool has run.

    Returns (final answer, tools that succeeded, required tools still missing).
    A non-empty "missing" set means the task is NOT done: surface it as a failure
    instead of showing the model's answer as if the action happened.
    """
    required = set(required_tools or ())
    succeeded: set[str] = set()

    for _ in range(max_rounds):
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tc in message.tool_calls:
                result, ok = execute_tool_call(tc)
                print(f"  tool {tc.function.name}({tc.function.arguments}) -> {result}")
                if ok:
                    succeeded.add(tc.function.name)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        missing = required - succeeded
        if not missing:
            return message.content or "", succeeded, set()

        # Grounding check: the model wants to finish, but a required action has no
        # tool result. Detecting this is not enough; push the loop to finish the work.
        messages.append({"role": "assistant", "content": message.content or ""})
        messages.append({
            "role": "user",
            "content": (
                f"You have not called {', '.join(sorted(missing))} yet, so that action has not "
                "happened. Call it now, or say plainly that you could not. Only report IDs and "
                "values that a tool result returned."
            ),
        })

    return "", succeeded, required - succeeded


def main() -> None:
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to weather and stock tools."},
        {"role": "user", "content": "What's the weather in NYC and the current Apple stock price?"},
    ]
    answer, succeeded, missing = run_tool_loop(
        messages, required_tools={"get_weather", "get_stock_price"}
    )
    if missing:
        print(f"\nIncomplete: required tools never succeeded: {sorted(missing)}")
    else:
        print(f"\nTools used: {sorted(succeeded)}")
        print(f"Assistant: {answer}")


if __name__ == "__main__":
    main()
