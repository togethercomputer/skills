#!/usr/bin/env python3
"""
Together AI Chat Completions — Structured Outputs (v2 SDK)

Demonstrates json_schema, json_object, and regex response formats.

Usage:
    python structured_outputs.py

Requires:
    pip install together pydantic
    export TOGETHER_API_KEY=your_key
"""

import json
from together import Together
from pydantic import BaseModel, Field

client = Together()


# --- 1. json_schema with Pydantic ---
class VoiceNote(BaseModel):
    title: str = Field(description="A title for the voice note")
    summary: str = Field(description="A short one sentence summary of the voice note.")
    actionItems: list[str] = Field(description="A list of action items from the voice note")


def json_schema_example() -> None:
    """Constrain output to match a Pydantic schema exactly."""
    print("=== json_schema (Pydantic) ===")
    transcript = (
        "Good morning! Today is going to be a busy day. First, I need to make a quick "
        "breakfast. While cooking, I'll also check my emails to see if there's anything urgent. "
        "Then I have a meeting at 10am to discuss the Q4 roadmap."
    )

    extract = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "The following is a voice message transcript. Only answer in JSON "
                    f"and follow this schema {json.dumps(VoiceNote.model_json_schema())}."
                ),
            },
            {"role": "user", "content": transcript},
        ],
        model="openai/gpt-oss-20b",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "voice_note",
                "schema": VoiceNote.model_json_schema(),
            },
        },
    )

    output = json.loads(extract.choices[0].message.content)
    print(json.dumps(output, indent=2))
    print()


# --- 2. json_object (simple) ---
def json_object_example() -> None:
    """Model outputs valid JSON, structure guided by prompt only."""
    print("=== json_object (simple) ===")
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "Respond in JSON with keys: name, age, city, hobby"},
            {"role": "user", "content": "Make up a character for a story"},
        ],
        response_format={"type": "json_object"},
    )
    output = json.loads(response.choices[0].message.content)
    print(json.dumps(output, indent=2))
    print()


# --- 3. regex (pattern matching) ---
def regex_example() -> None:
    """Constrain output to match a regex pattern."""
    print("=== regex (classification) ===")
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        temperature=0.2,
        max_tokens=10,
        messages=[
            {
                "role": "system",
                "content": "Classify the sentiment of the text as positive, neutral, or negative.",
            },
            {"role": "user", "content": "The food was absolutely amazing, best meal I've ever had!"},
        ],
        response_format={"type": "regex", "pattern": "(positive|neutral|negative)"},
    )
    print(f"Sentiment: {response.choices[0].message.content}")
    print()


# --- 4. json_schema with reasoning model ---
class Step(BaseModel):
    explanation: str
    output: str


class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str


def reasoning_json_example() -> None:
    """Extract structured JSON from a reasoning model."""
    print("=== json_schema + reasoning model ===")
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
            },
            {"role": "user", "content": "how can I solve 8x + 7 = -23"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "math_reasoning",
                "schema": MathReasoning.model_json_schema(),
            },
        },
    )

    result = json.loads(completion.choices[0].message.content)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    json_schema_example()
    json_object_example()
    regex_example()
    reasoning_json_example()
