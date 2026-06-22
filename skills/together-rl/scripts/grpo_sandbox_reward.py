#!/usr/bin/env python3
"""
Together RL — GRPO post-training with sandboxed code-execution rewards.

Drives a GRPO training loop on the Together RL training API and scores each
sampled candidate by EXECUTING it inside an isolated together-sandbox: write the
candidate solution into a sandbox, run its test suite, and use pass/fail as the
reward.

This is the integration the rl-cookbook's grpo_train.py leaves out — that demo
scores GSM8K answers with a local string match. Real coding/agentic RL has to
*run* the model's output to score it, which must happen in a sandbox.

Status:
    The RL training API (client.beta.rl) is in BETA and is not yet in the public
    `together` package. This script targets that public surface; until the RL
    release ships, the `client.beta.rl` calls (and the operations helper import)
    will not resolve. The reward half (compute_rewards) runs today against
    together-sandbox v1.12.0 — see the `together-sandbox` skill.

Requires:
    pip install together            # client.beta.rl (beta; pending public release)
    pip install together-sandbox    # reward execution (on PyPI today)
    pip install transformers        # tokenizer
    export TOGETHER_API_KEY=...

Run (once the RL API is public):
    python grpo_sandbox_reward.py \
        --base-url https://<rl-service-url> \
        --model meta-llama/Llama-3.2-1B-Instruct \
        --snapshot-alias coding-rl-env@v1

References:
    GRPO loop mechanics      -> references/grpo-loop.md
    Sandbox reward pattern   -> references/sandbox-rewards.md
    Sandbox SDK              -> the `together-sandbox` skill
"""

from __future__ import annotations

import argparse
import asyncio
import re
import time
from dataclasses import dataclass
from typing import Any

from transformers import AutoTokenizer

from together import Together

# NOTE: requires the `together` release where the RL training API ships (beta).
# In the rl-cookbook this helper lives at `together.lib.beta.rl.operations`; the
# public import path may differ once published — adjust to the shipped SDK.
from together.lib.beta.rl import operations as rl_ops  # type: ignore

from together_sandbox import TogetherSandbox


# --------------------------------------------------------------------------- #
# Toy coding tasks. Each rollout asks the model to implement `solution`; the
# reward is whether the bundled test passes in a sandbox. Swap this for your
# real dataset (e.g. SWE-bench / Terminal-Bench task specs).
# --------------------------------------------------------------------------- #
TASKS: list[dict[str, str]] = [
    {
        "prompt": "Write a Python function `solution(n)` that returns the n-th Fibonacci number "
                  "(0-indexed, solution(0)=0, solution(1)=1). Reply with a ```python code block.",
        "test": "from solution import solution\n"
                "def test_fib():\n"
                "    assert [solution(i) for i in range(7)] == [0, 1, 1, 2, 3, 5, 8]\n",
    },
    {
        "prompt": "Write a Python function `solution(s)` that returns True if string `s` is a "
                  "palindrome ignoring case and non-alphanumerics. Reply with a ```python code block.",
        "test": "from solution import solution\n"
                "def test_palindrome():\n"
                "    assert solution('A man, a plan, a canal: Panama')\n"
                "    assert not solution('hello')\n",
    },
]


@dataclass
class Config:
    base_url: str
    model: str
    snapshot_alias: str
    group_size: int
    max_steps: int
    max_prompt_length: int
    max_model_length: int
    max_sample_tokens: int
    learning_rate: float
    poll_interval: float
    timeout: float


def parse_args() -> Config:
    p = argparse.ArgumentParser(description="GRPO with sandboxed code-execution rewards")
    p.add_argument("--base-url", required=True, help="RL service base URL")
    p.add_argument("--model", required=True, help="Base model for the training session")
    p.add_argument("--snapshot-alias", required=True,
                   help="together-sandbox snapshot alias with python + pytest preinstalled")
    p.add_argument("--group-size", type=int, default=8, help="Samples per prompt (GRPO group size)")
    p.add_argument("--max-steps", type=int, default=20)
    p.add_argument("--max-prompt-length", type=int, default=512)
    p.add_argument("--max-model-length", type=int, default=2048)
    p.add_argument("--max-sample-tokens", type=int, default=512)
    p.add_argument("--learning-rate", type=float, default=8e-5)
    p.add_argument("--poll-interval", type=float, default=1.0)
    p.add_argument("--timeout", type=float, default=7200.0)
    a = p.parse_args()
    return Config(
        base_url=a.base_url, model=a.model, snapshot_alias=a.snapshot_alias,
        group_size=a.group_size, max_steps=a.max_steps,
        max_prompt_length=a.max_prompt_length, max_model_length=a.max_model_length,
        max_sample_tokens=a.max_sample_tokens, learning_rate=a.learning_rate,
        poll_interval=a.poll_interval, timeout=a.timeout,
    )


# --------------------------------------------------------------------------- #
# Tokenization
# --------------------------------------------------------------------------- #
def build_prompt_tokens(tokenizer, question: str, *, max_length: int) -> list[int]:
    messages = [{"role": "user", "content": question}]
    try:
        tokens = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=True)
    except Exception:
        tokens = tokenizer.encode(question, add_special_tokens=False)
    return list(tokens)[:max_length]


def extract_code(text: str) -> str:
    """Pull the first ```python ... ``` block; fall back to the whole response."""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


# --------------------------------------------------------------------------- #
# GRPO sample assembly (see references/grpo-loop.md)
# --------------------------------------------------------------------------- #
def build_grpo_sample(prompt_tokens, response_tokens, response_logprobs, advantage, max_model_length):
    available = max(max_model_length - len(prompt_tokens), 0)
    response_tokens = response_tokens[:available]
    response_logprobs = response_logprobs[:available]
    if not response_tokens:
        return None
    model_tokens = prompt_tokens + response_tokens
    loss_mask = [0] * len(prompt_tokens) + [1] * len(response_tokens)
    targets = model_tokens[1:] + [0]
    advantages = [0.0] * len(prompt_tokens) + [advantage] * len(response_tokens)
    logprobs = [0.0] * len(prompt_tokens) + [float(x) for x in response_logprobs]
    return {
        "model_input": {"chunks": [{"encoded_text": {"tokens": model_tokens}}]},
        "loss_inputs": {
            "loss_mask": {"data": loss_mask, "dtype": "D_TYPE_INT64"},
            "target_tokens": {"data": targets, "dtype": "D_TYPE_INT64"},
            "grpo_inputs": {
                "advantages": {"data": advantages, "dtype": "D_TYPE_FLOAT32"},
                "generator_logprobs": {"data": logprobs, "dtype": "D_TYPE_FLOAT32"},
            },
        },
    }


def pad_samples(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not samples:
        return samples
    max_len = max(len(s["model_input"]["chunks"][0]["encoded_text"]["tokens"]) for s in samples)

    def _pad_int(values, fill=0):
        return [str(v) for v in (list(values) + [fill] * (max_len - len(values)))[:max_len]]

    def _pad_float(values, fill=0.0):
        return (list(values) + [fill] * (max_len - len(values)))[:max_len]

    padded = []
    for s in samples:
        tokens = s["model_input"]["chunks"][0]["encoded_text"]["tokens"]
        li = s["loss_inputs"]
        padded.append({
            "model_input": {"chunks": [{"encoded_text": {"tokens": _pad_int(tokens)}}]},
            "loss_inputs": {
                "loss_mask": {"data": _pad_int(li["loss_mask"]["data"]), "dtype": "D_TYPE_INT64"},
                "target_tokens": {"data": _pad_int(li["target_tokens"]["data"]), "dtype": "D_TYPE_INT64"},
                "grpo_inputs": {
                    "advantages": {"data": _pad_float(li["grpo_inputs"]["advantages"]["data"]),
                                   "dtype": "D_TYPE_FLOAT32"},
                    "generator_logprobs": {"data": _pad_float(li["grpo_inputs"]["generator_logprobs"]["data"]),
                                           "dtype": "D_TYPE_FLOAT32"},
                },
            },
        })
    return padded


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# --------------------------------------------------------------------------- #
# RL operation polling
# --------------------------------------------------------------------------- #
def wait_for_operation(client, *, session_id, operation, kind, timeout, interval):
    deadline = time.monotonic() + timeout
    while True:
        operation = rl_ops.retrieve_operation(client, session_id=session_id, operation=operation, kind=kind)
        if rl_ops.is_operation_complete(operation):
            if rl_ops.get_operation_status(operation) == "TRAINING_OPERATION_STATUS_FAILED":
                raise RuntimeError(f"operation {kind} failed: {rl_ops.get_operation_error(operation)}")
            return operation
        if time.monotonic() >= deadline:
            raise TimeoutError(f"operation {kind} timed out")
        time.sleep(interval)


def wait_for_session_running(client, *, session_id, timeout, interval):
    deadline = time.monotonic() + timeout
    while True:
        status = client.beta.rl.sessions.retrieve(session_id).status
        print(f"[session:{session_id}] status={status}")
        if status == "TRAINING_SESSION_STATUS_RUNNING":
            return
        if time.monotonic() >= deadline:
            raise TimeoutError("session did not reach RUNNING")
        time.sleep(interval)


# --------------------------------------------------------------------------- #
# Sandbox code-execution reward (see references/sandbox-rewards.md)
# --------------------------------------------------------------------------- #
async def score_candidate(sdk, snapshot_alias, candidate_code, test_code) -> float:
    model = await sdk.sandboxes.create(snapshot_alias=snapshot_alias, ephemeral=True)
    sandbox = await sdk.sandboxes.start(model.id)
    try:
        await sandbox.files.create("/workspace/solution.py", candidate_code)
        await sandbox.files.create("/workspace/test_solution.py", test_code)
        result = await sandbox.execs.exec(
            "bash", ["-c", "cd /workspace && python -m pytest -q test_solution.py"]
        )
        # execs.exec returns {"exit_code": int, "output": str}
        return 1.0 if result["exit_code"] == 0 else 0.0
    finally:
        await sdk.sandboxes.shutdown(sandbox.id)


async def compute_rewards(snapshot_alias, candidates, test_code) -> list[float]:
    async with TogetherSandbox() as sdk:
        results = await asyncio.gather(
            *[score_candidate(sdk, snapshot_alias, c, test_code) for c in candidates],
            return_exceptions=True,
        )
    return [r if isinstance(r, float) else 0.0 for r in results]


# --------------------------------------------------------------------------- #
# Training loop
# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = parse_args()
    tokenizer = AutoTokenizer.from_pretrained(cfg.model)

    client = Together(base_url=cfg.base_url)  # reads TOGETHER_API_KEY from env
    session = client.beta.rl.sessions.create(base_model=cfg.model)
    session_id = session.session_id or getattr(session, "id", None)
    if not session_id:
        raise RuntimeError(f"no session_id in response: {session}")
    print(f"Created session {session_id}")
    wait_for_session_running(client, session_id=session_id, timeout=cfg.timeout, interval=cfg.poll_interval)

    try:
        for step in range(cfg.max_steps):
            task = TASKS[step % len(TASKS)]
            prompt_tokens = build_prompt_tokens(tokenizer, task["prompt"], max_length=cfg.max_prompt_length)

            # 1. Sample a group of completions for this prompt.
            sample_op = client.beta.rl.training.sample(
                session_id=session_id,
                prompt={"chunks": [{"encoded_text": {"tokens": prompt_tokens}}]},
                num_samples=cfg.group_size,
                sampling_params={"max_tokens": cfg.max_sample_tokens},
            )
            sample_res = wait_for_operation(
                client, session_id=session_id, operation=sample_op, kind="sample",
                timeout=cfg.timeout, interval=cfg.poll_interval,
            )
            sequences = (sample_res.output.sequences if sample_res.output else None) or []
            if not sequences:
                raise RuntimeError("sample returned no sequences")

            # 2. Decode each completion and score it by running its tests in a sandbox.
            decoded, seq_tokens_list, seq_logprobs_list = [], [], []
            for seq in sequences:
                toks = [int(t) for t in (seq.tokens or [])]
                seq_tokens_list.append(toks)
                seq_logprobs_list.append([float(x) for x in (seq.logprobs or [])])
                decoded.append(tokenizer.decode(toks, skip_special_tokens=True))
            candidates = [extract_code(d) for d in decoded]
            rewards = asyncio.run(compute_rewards(cfg.snapshot_alias, candidates, task["test"]))

            # 3. GRPO advantages (center within the group), then assemble the batch.
            baseline = mean(rewards)
            samples, kept_rewards = [], []
            for toks, lps, reward in zip(seq_tokens_list, seq_logprobs_list, rewards):
                sample = build_grpo_sample(
                    prompt_tokens=prompt_tokens, response_tokens=toks, response_logprobs=lps,
                    advantage=reward - baseline, max_model_length=cfg.max_model_length,
                )
                if sample:
                    samples.append(sample)
                    kept_rewards.append(reward)
            if len(samples) < 8:
                raise RuntimeError(f"need >= 8 samples for forward_backward, got {len(samples)}")
            samples = pad_samples(samples)

            # 4. forward_backward + optim_step.
            fb_op = client.beta.rl.training.forward_backward(
                session_id=session_id,
                loss={"type": "LOSS_TYPE_GRPO",
                      "grpo_params": {"beta": 0.0, "agg_type": "GRPO_LOSS_AGGREGATION_TYPE_TOKEN_MEAN"}},
                samples=samples,
            )
            fb_res = wait_for_operation(
                client, session_id=session_id, operation=fb_op, kind="forward_backward",
                timeout=cfg.timeout, interval=cfg.poll_interval,
            )
            loss = fb_res.output.loss if fb_res.output else None

            opt_op = client.beta.rl.training.optim_step(session_id=session_id, learning_rate=cfg.learning_rate)
            wait_for_operation(
                client, session_id=session_id, operation=opt_op, kind="optim_step",
                timeout=cfg.timeout, interval=cfg.poll_interval,
            )

            print(f"[step {step}] loss={loss} reward_mean={mean(kept_rewards):.3f} "
                  f"pass={sum(1 for r in kept_rewards if r > 0)}/{len(kept_rewards)}")
    finally:
        client.beta.rl.sessions.stop(session_id)
        print("session stopped")


if __name__ == "__main__":
    main()
