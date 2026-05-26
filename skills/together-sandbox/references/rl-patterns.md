# RL Training Patterns with Together Sandbox

## Contents

- [Overview](#overview)
- [The GRPO Training Loop](#the-grpo-training-loop)
- [Pattern 1: Golden Image Setup](#pattern-1-golden-image-setup)
- [Pattern 2: Batch Sandbox Fan-out](#pattern-2-batch-sandbox-fan-out)
- [Pattern 3: Multi-turn Agent Rollout](#pattern-3-multi-turn-agent-rollout)
- [Pattern 4: Reward Collection](#pattern-4-reward-collection)
- [Pattern 5: Resource Cleanup](#pattern-5-resource-cleanup)
- [Scale Reference](#scale-reference)

## Overview

Together Sandbox is the execution layer for RL training loops that interleave model inference with sandbox-based code execution. The primary workload is GRPO (Group Relative Policy Optimization), where each training step creates a batch of sandboxes, runs coding agent rollouts, computes rewards via test suites, and feeds trajectories back to the training service.

The customer orchestrates the RL loop. Together controls the capacity behind the APIs.

## The GRPO Training Loop

```
for step in training_steps:
    create N sandboxes (groups_per_batch x group_size; default 8x4=32)
    in parallel xN:
        multi-turn rollout: inference -> sandbox exec -> observe (1-10 turns)
        compute reward inside sandbox (run test suite, read reward file)
        close sandbox
    center rewards within each group (GRPO advantage)
    assemble training batch from trajectories
    train step (forward/backward + optimizer on GPU)
    save weights, get new inference client
    loop
```

Five integration points where sandbox behavior affects training:

| Integration point | What happens | Why it matters |
|-------------------|-------------|----------------|
| Image onboarding | Task Dockerfile to snapshot, once per task | Blocks training start |
| Batch creation | All sandboxes must reach "running" before rollouts | GPU sits idle waiting for slowest sandbox |
| Multi-turn exec | 1-10 bash commands per rollout, sandbox must survive all | Dead sandbox wastes all prior inference cost |
| Reward collection | Read reward file from sandbox after test suite | Missing reward invalidates entire GRPO group |
| Cleanup | Destroy sandboxes after reward collection | Orphans accumulate over multi-day runs |

## Pattern 1: Golden Image Setup

Build a reusable snapshot with dependencies and agent tools installed. Run once before training begins.

```python
import asyncio
from together_sandbox import (
    TogetherSandbox,
    CreateImageSnapshotParams,
)

async def setup_golden_image():
    async with TogetherSandbox() as sdk:
        # Create base snapshot from Docker image
        result = await sdk.snapshots.create(CreateImageSnapshotParams(
            image="python:3.11-slim",
            alias="python-base",
        ))

        # Create a non-ephemeral sandbox to customize
        model = await sdk.sandboxes.create(
            snapshot_id=result.snapshot_id,
            millicpu=2000,
            memory_bytes=4 * 1024**3,
            disk_bytes=10 * 1024**3,
            ephemeral=False,  # Must be non-ephemeral to hibernate
        )
        sandbox = await sdk.sandboxes.start(model.id)

        # Configure DNS (required for pip install)
        await sandbox.execs.exec("bash", ["-c",
            'echo "nameserver 1.1.1.1" > /etc/resolv.conf && '
            'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
        ])

        # Install dependencies
        result = await sandbox.execs.exec("bash", ["-c",
            'pip install numpy pytest torch transformers'
        ])
        print(f"pip install: exit {result['exit_code']}")

        # Upload reward function
        await sandbox.files.create("/app/reward_fn.py", """
import subprocess
def compute_reward(test_file: str) -> float:
    result = subprocess.run(["python3", "-m", "pytest", test_file, "-q"],
                            capture_output=True, text=True)
    return 1.0 if result.returncode == 0 else 0.0
""")

        # Hibernate to capture state as new snapshot
        await sdk.sandboxes.hibernate(sandbox.id)
        print("Golden image created via hibernate.")

asyncio.run(setup_golden_image())
```

## Pattern 2: Batch Sandbox Fan-out

Create N sandboxes in parallel for one GRPO training step. GPU sits idle until all are running.

```python
import asyncio
import time
from together_sandbox import TogetherSandbox, CreateImageSnapshotParams

async def batch_fanout(snapshot_alias: str, count: int = 32):
    async with TogetherSandbox() as sdk:
        # Create all sandboxes concurrently
        models = await asyncio.gather(*[
            sdk.sandboxes.create(
                snapshot_alias=snapshot_alias,
                millicpu=2000,
                memory_bytes=4 * 1024**3,
                disk_bytes=10 * 1024**3,
                ephemeral=True,
            )
            for _ in range(count)
        ])

        # Start all concurrently and measure timing
        start_time = time.time()

        async def start_and_time(model):
            t0 = time.time()
            sandbox = await sdk.sandboxes.start(model.id)
            return sandbox, time.time() - t0

        results = await asyncio.gather(*[start_and_time(m) for m in models])
        sandboxes = [r[0] for r in results]
        times = [r[1] for r in results]

        total = time.time() - start_time
        times.sort()
        print(f"Batch of {count}: {total:.1f}s total")
        print(f"  p50: {times[len(times)//2]:.1f}s")
        print(f"  max: {times[-1]:.1f}s (this is how long GPU waits)")

        return sandboxes

asyncio.run(batch_fanout("rl-env-v1", count=8))
```

## Pattern 3: Multi-turn Agent Rollout

Simulate a coding agent executing sequential commands inside a sandbox. Each turn depends on the previous one.

```python
async def execute_rollout(sandbox, task_prompt: str) -> list[dict]:
    """Execute a multi-turn rollout. Returns list of (action, observation) pairs."""
    trajectory = []

    # Configure environment
    await sandbox.execs.exec("bash", ["-c",
        'echo "nameserver 1.1.1.1" > /etc/resolv.conf && '
        'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
    ])

    for turn in range(10):  # max 10 turns
        # In a real RL loop, the command comes from the inference API
        command = get_next_command(task_prompt, trajectory)

        if command is None:
            break  # Agent decided to stop

        result = await sandbox.execs.exec("bash", ["-c", command])
        observation = {
            "turn": turn,
            "command": command,
            "stdout": result["output"],
            "exit_code": result["exit_code"],
        }
        trajectory.append(observation)

    return trajectory


def get_next_command(task: str, history: list[dict]) -> str | None:
    """Placeholder: in production, this calls the Together inference API."""
    # Replace with: response = client.chat.completions.create(...)
    if len(history) >= 5:
        return None
    commands = [
        "echo 'def add(a, b): return a + b' > /tmp/solution.py",
        "cd /tmp && python3 -c 'from solution import add; print(add(2,3))'",
        "python3 -m pytest /tmp/test_solution.py -q 2>&1 || true",
        "cat /tmp/test_solution.py 2>&1 || echo 'no test file'",
        "echo 'done'",
    ]
    return commands[len(history)] if len(history) < len(commands) else None
```

## Pattern 4: Reward Collection

Collect rewards from all sandboxes in a GRPO group. All rewards must be present for the group to be valid.

```python
async def collect_group_rewards(
    sdk,
    sandboxes: list,
    test_command: str = "python3 -m pytest /tmp/tests/ -q",
    reward_path: str = "/tmp/reward.txt",
) -> dict:
    """Collect rewards from a GRPO group. Returns rewards and group validity."""

    async def collect_one(sandbox) -> float | None:
        try:
            # Run test suite
            result = await sandbox.execs.exec("bash", ["-c", test_command])

            # Write reward based on test result
            reward = 1.0 if result["exit_code"] == 0 else 0.0
            await sandbox.files.create(reward_path, str(reward))

            # Read it back (validates file API round-trip)
            content = await sandbox.files.read(reward_path)
            return float(content.strip())
        except Exception as e:
            print(f"Sandbox {sandbox.id} failed: {e}")
            return None

    rewards = await asyncio.gather(*[collect_one(sbx) for sbx in sandboxes])

    valid_rewards = [r for r in rewards if r is not None]
    group_complete = len(valid_rewards) == len(sandboxes)

    return {
        "rewards": rewards,
        "group_complete": group_complete,
        "group_mean": sum(valid_rewards) / len(valid_rewards) if valid_rewards else 0.0,
        "collected": len(valid_rewards),
        "expected": len(sandboxes),
    }
```

## Pattern 5: Resource Cleanup

Clean up orphaned resources after training. Critical for multi-day runs with 400,000+ sandbox instantiations.

```python
async def cleanup_orphans():
    async with TogetherSandbox() as sdk:
        snapshots = await sdk.snapshots.list()

        # Snapshot objects do not carry alias information.
        # To check if a snapshot is aliased, you must try get_by_alias()
        # for known aliases, or track aliases separately in your application.
        print(f"Total snapshots: {len(snapshots)}")

        for s in snapshots:
            print(f"  {s.id}: {s.byte_size} bytes, created {s.created_at}")

asyncio.run(cleanup_orphans())
```

Note: The `Snapshot` model does not include an `alias` field. Aliases are separate entities managed via `sdk.snapshots.alias()`, `get_by_alias()`, and `delete_by_alias()`. To determine if a snapshot is aliased, maintain a mapping in your application or attempt `get_by_alias()` for known names.

## Scale Reference

| Dimension | Eval | Training (GRPO) | Production |
|-----------|------|-----------------|------------|
| Concurrent sandboxes | 50-200 | 32-256 per batch | 500-1,000 sustained |
| Sandbox lifetime | Up to 1 hour | ~10 minutes | ~15 minutes average |
| Unique task images | 50-500 | 89 (Terminal-Bench) | 25,000+ |
| Run duration | Hours | 8+ hours | 5+ days |
| Total instantiations | 200-500 | Hundreds per run | 400,000+ |

Default GRPO batch: `groups_per_batch=8`, `group_size=4` = 32 sandboxes per step. Both parameters are configurable with no upper bound. Async mode doubles effective concurrency.
