#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- Function Calling Fine-Tuning (v2 SDK)

Prepare function calling training data, upload, fine-tune, and test.

Usage:
    python function_calling_finetune.py
    python function_calling_finetune.py --training-file tools.jsonl --model Qwen/Qwen3-8B
    python function_calling_finetune.py --suffix fc-bot-v2

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import argparse
import json
import tempfile
import time
from pathlib import Path

from together import Together

client = Together()


def build_tools() -> list[dict]:
    """Return sample tool definitions used by the demo dataset and test prompt."""
    return [
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


def sample_training_data(tools: list[dict]) -> list[dict]:
    """Return a small function-calling fine-tuning dataset."""
    return [
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
    ]


def create_temp_dataset(rows: list[dict]) -> Path:
    """Write JSONL rows to a temporary file."""
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as temp_file:
        for example in rows:
            temp_file.write(json.dumps(example) + "\n")
        return Path(temp_file.name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI function-calling fine-tuning workflow")
    parser.add_argument("--training-file", help="Path to a training JSONL file")
    parser.add_argument("--model", default="Qwen/Qwen3-8B", help="Base model to fine-tune")
    parser.add_argument("--suffix", default="fc-bot-v1", help="Suffix for the fine-tuned model")
    parser.add_argument("--n-epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Training learning rate")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between status checks")
    parser.add_argument(
        "--test-prompt",
        default="What's the weather in Boston?",
        help="Prompt to use when probing the fine-tuned model",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tools = build_tools()
    data_path: Path | None = None
    upload_path = args.training_file
    if upload_path is None:
        training_data = sample_training_data(tools)
        data_path = create_temp_dataset(training_data)
        upload_path = str(data_path)
        print(f"Wrote {len(training_data)} function calling examples to {data_path}")

    # --- 2. Upload ---
    try:
        file_resp = client.files.upload(file=upload_path, purpose="fine-tune", check=True)
    finally:
        if data_path is not None:
            data_path.unlink(missing_ok=True)
    print(f"Uploaded file: {file_resp.id}")

    # --- 3. Start LoRA fine-tuning ---
    job = client.fine_tuning.create(
        training_file=file_resp.id,
        model=args.model,
        lora=True,
        n_epochs=args.n_epochs,
        learning_rate=args.learning_rate,
        suffix=args.suffix,
    )
    print(f"Created job: {job.id}")

    # --- 4. Monitor ---
    while True:
        status = client.fine_tuning.retrieve(id=job.id)
        print(f"  Status: {status.status}")
        if status.status == "completed":
            print(f"\nTraining complete! Output: {status.x_model_output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"Job ended: {status.status}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    # --- 5. Deploy and test function calling with fine-tuned model ---
    print("\n--- Deploying fine-tuned model ---")
    output_model = status.x_model_output_name
    endpoint = client.endpoints.create(
        display_name="Function Calling Fine-tuned",
        model=output_model,
        hardware="4x_nvidia_h100_80gb_sxm",
        autoscaling={"min_replicas": 1, "max_replicas": 1},
    )
    print(f"Created endpoint: {endpoint.id}")

    while True:
        ep = client.endpoints.retrieve(endpoint.id)
        print(f"  Endpoint state: {ep.state}")
        if ep.state == "STARTED":
            break
        if ep.state in ("FAILED", "STOPPED"):
            print(f"Endpoint {ep.state}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    print("\n--- Testing function calling ---")
    response = client.chat.completions.create(
        model=endpoint.name,
        messages=[{"role": "user", "content": args.test_prompt}],
        tools=tools,
    )

    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            print(f"  Tool call: {tool_call.function.name}({tool_call.function.arguments})")
    else:
        print(f"  Response: {response.choices[0].message.content}")
    print(f"\nEndpoint is running. Delete it when done to avoid charges:")
    print(f"  client.endpoints.delete(\"{endpoint.id}\")")


if __name__ == "__main__":
    main()
