#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- Function Calling Fine-Tuning (v2 SDK)

Prepare function calling training data, upload, fine-tune, and test.

Usage:
    python function_calling_finetune.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import json
import time
import tempfile
from together import Together

client = Together()

def main() -> None:
    # --- 1. Prepare function calling training data ---
    # Each example includes tool definitions, user query, assistant tool_calls,
    # tool results, and final assistant response.
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city name, e.g. San Francisco",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                        },
                    },
                    "required": ["city"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_restaurants",
                "description": "Search for restaurants in a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                        "cuisine": {"type": "string", "description": "Cuisine type"},
                    },
                    "required": ["city"],
                },
            },
        },
    ]

    training_data = [
        {
            "tools": tools,
            "messages": [
                {"role": "user", "content": "What's the weather like in San Francisco?"},
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "San Francisco", "unit": "fahrenheit"}',
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_1",
                    "content": '{"temp": 65, "condition": "foggy", "unit": "fahrenheit"}',
                },
                {
                    "role": "assistant",
                    "content": "It's currently 65F and foggy in San Francisco.",
                },
            ],
        },
        {
            "tools": tools,
            "messages": [
                {"role": "user", "content": "Find me Italian restaurants in NYC"},
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call_2",
                            "type": "function",
                            "function": {
                                "name": "search_restaurants",
                                "arguments": '{"city": "New York", "cuisine": "Italian"}',
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_2",
                    "content": '{"restaurants": ["Carbone", "L\'Artusi", "Via Carota"]}',
                },
                {
                    "role": "assistant",
                    "content": (
                        "Here are some top Italian restaurants in NYC: "
                        "Carbone, L'Artusi, and Via Carota."
                    ),
                },
            ],
        },
        {
            "tools": tools,
            "messages": [
                {
                    "role": "user",
                    "content": "What's the weather in Chicago and find me restaurants there?",
                },
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call_3",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "Chicago", "unit": "fahrenheit"}',
                            },
                        },
                        {
                            "id": "call_4",
                            "type": "function",
                            "function": {
                                "name": "search_restaurants",
                                "arguments": '{"city": "Chicago"}',
                            },
                        },
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_3",
                    "content": '{"temp": 45, "condition": "windy", "unit": "fahrenheit"}',
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_4",
                    "content": '{"restaurants": ["Alinea", "Girl & The Goat", "Au Cheval"]}',
                },
                {
                    "role": "assistant",
                    "content": (
                        "Chicago is currently 45F and windy. For dining, I recommend "
                        "Alinea, Girl & The Goat, or Au Cheval."
                    ),
                },
            ],
        },
        # Add more examples for production use...
    ]

    data_path = tempfile.mktemp(suffix=".jsonl")
    with open(data_path, "w") as f:
        for example in training_data:
            f.write(json.dumps(example) + "\n")

    print(f"Wrote {len(training_data)} function calling examples to {data_path}")

    # --- 2. Upload ---
    file_resp = client.files.upload(file=data_path, purpose="fine-tune", check=True)
    print(f"Uploaded file: {file_resp.id}")

    # --- 3. Start LoRA fine-tuning ---
    job = client.fine_tuning.create(
        training_file=file_resp.id,
        model="Qwen/Qwen3-8B",
        lora=True,
        n_epochs=3,
        learning_rate=1e-5,
        suffix="fc-bot-v1",
    )
    print(f"Created job: {job.id}")

    # --- 4. Monitor ---
    while True:
        status = client.fine_tuning.retrieve(id=job.id)
        print(f"  Status: {status.status}")
        if status.status == "completed":
            print(f"\nTraining complete! Output: {status.output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"Job ended: {status.status}")
            raise SystemExit(1)
        time.sleep(30)

    # --- 5. Test function calling with fine-tuned model ---
    print("\n--- Testing function calling ---")
    response = client.chat.completions.create(
        model=status.output_name,
        messages=[
            {"role": "user", "content": "What's the weather in Boston?"},
        ],
        tools=tools,
    )

    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        for tc in tool_calls:
            print(f"  Tool call: {tc.function.name}({tc.function.arguments})")
    else:
        print(f"  Response: {response.choices[0].message.content}")


if __name__ == "__main__":
    main()
