#!/usr/bin/env python3
"""Generate agents/openai.yaml files for Together AI skills.

Usage:
    python scripts/generate_openai_yaml.py
    python scripts/generate_openai_yaml.py --check
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

INTERFACE_OVERRIDES: dict[str, dict[str, str]] = {
    "together-audio": {
        "display_name": "Together Audio",
        "short_description": "Together AI TTS and STT workflows",
        "default_prompt": (
            "Use $together-audio to build a Together AI voice workflow with TTS, STT, "
            "streaming, or realtime audio."
        ),
    },
    "together-batch-inference": {
        "display_name": "Together Batch Inference",
        "short_description": "Together AI offline batch inference",
        "default_prompt": (
            "Use $together-batch-inference to build a Together AI batch job pipeline for "
            "large-scale offline inference."
        ),
    },
    "together-chat-completions": {
        "display_name": "Together Chat Completions",
        "short_description": "Together AI serverless chat workflows",
        "default_prompt": (
            "Use $together-chat-completions to build a Together AI chat app with streaming, "
            "tool use, structured outputs, or reasoning."
        ),
    },
    "together-code-interpreter": {
        "display_name": "Together Code Interpreter",
        "short_description": "Together AI remote Python execution",
        "default_prompt": (
            "Use $together-code-interpreter to run Python remotely on Together AI with session "
            "reuse, uploads, and chart outputs."
        ),
    },
    "together-dedicated-containers": {
        "display_name": "Together Dedicated Containers",
        "short_description": "Together AI container deployment help",
        "default_prompt": (
            "Use $together-dedicated-containers to deploy a custom inference container on "
            "Together AI with Jig, Sprocket, or the queue API."
        ),
    },
    "together-dedicated-endpoints": {
        "display_name": "Together Dedicated Endpoints",
        "short_description": "Together AI single-tenant endpoints",
        "default_prompt": (
            "Use $together-dedicated-endpoints to deploy or manage a dedicated Together AI "
            "endpoint for a model, fine-tune, or custom upload."
        ),
    },
    "together-embeddings": {
        "display_name": "Together Embeddings",
        "short_description": "Together AI embeddings and rerank",
        "default_prompt": (
            "Use $together-embeddings to build a Together AI embedding, retrieval, or reranking "
            "workflow."
        ),
    },
    "together-evaluations": {
        "display_name": "Together Evaluations",
        "short_description": "Together AI LLM evaluation workflows",
        "default_prompt": (
            "Use $together-evaluations to build a Together AI classify, score, or compare "
            "evaluation workflow."
        ),
    },
    "together-fine-tuning": {
        "display_name": "Together Fine-Tuning",
        "short_description": "Together AI fine-tuning workflows",
        "default_prompt": (
            "Use $together-fine-tuning to fine-tune a Together AI model with LoRA, DPO, VLM, "
            "function-calling, or reasoning data."
        ),
    },
    "together-gpu-clusters": {
        "display_name": "Together GPU Clusters",
        "short_description": "Together AI cluster provisioning help",
        "default_prompt": (
            "Use $together-gpu-clusters to provision or manage a Together AI GPU cluster with "
            "Kubernetes, Slurm, or shared storage."
        ),
    },
    "together-images": {
        "display_name": "Together Images",
        "short_description": "Together AI image generation help",
        "default_prompt": (
            "Use $together-images to build a Together AI image generation or editing workflow "
            "with FLUX, Kontext, or LoRAs."
        ),
    },
    "together-video": {
        "display_name": "Together Video",
        "short_description": "Together AI video generation help",
        "default_prompt": (
            "Use $together-video to build a Together AI text-to-video or image-to-video "
            "workflow with polling and downloads."
        ),
    },
}


def quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_yaml(skill_name: str) -> str:
    interface = INTERFACE_OVERRIDES[skill_name]
    return (
        "interface:\n"
        f"  display_name: {quote(interface['display_name'])}\n"
        f"  short_description: {quote(interface['short_description'])}\n"
        f"  default_prompt: {quote(interface['default_prompt'])}\n"
    )


def main() -> int:
    check_mode = "--check" in sys.argv
    errors = 0

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name not in INTERFACE_OVERRIDES:
            continue

        output_dir = skill_dir / "agents"
        output_path = output_dir / "openai.yaml"
        rendered = render_yaml(skill_dir.name)

        if check_mode:
            if not output_path.exists():
                print(f"FAIL: Missing {output_path}")
                errors += 1
                continue
            current = output_path.read_text(encoding="utf-8")
            if current != rendered:
                print(f"FAIL: {output_path} is out of date")
                errors += 1
            else:
                print(f"OK: {output_path}")
            continue

        output_dir.mkdir(exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote {output_path}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
