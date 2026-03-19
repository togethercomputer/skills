#!/usr/bin/env python3
"""
Together AI Function Calling — Complete Tool Call Loop (v2 SDK)

Defines tools, sends a request, executes function calls, and passes
results back to the model for a final response. Handles parallel calls.

Usage:
    python tool_call_loop.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import json
from together import Together

client = Together()

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


FUNCTIONS = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
}


def main() -> None:
    # --- 3. Send request with tools ---
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to weather and stock tools."},
        {"role": "user", "content": "What's the weather in NYC and the current Apple stock price?"},
    ]

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=messages,
        tools=tools,
    )

    # --- 4. Process tool calls (handles parallel calls) ---
    tool_calls = response.choices[0].message.tool_calls

    if tool_calls:
        # Add assistant message with tool calls to history
        messages.append(response.choices[0].message)

        for tc in tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)

            print(f"Calling {fn_name}({fn_args})")
            result = FUNCTIONS[fn_name](**fn_args)

            # Add each tool result to history
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

        # --- 5. Get final response with tool results ---
        final = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=messages,
            tools=tools,
        )
        print(f"\nAssistant: {final.choices[0].message.content}")
    else:
        # Model responded directly without calling tools
        print(f"Assistant: {response.choices[0].message.content}")


if __name__ == "__main__":
    main()
