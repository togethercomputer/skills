#!/usr/bin/env python3
"""
Together Sandbox — Parallel Fan-out for RL Batch Evaluation

Creates N sandboxes in parallel, executes a command in each, collects results,
and cleans up. Demonstrates the GRPO batch creation pattern where GPU sits idle
until all sandboxes are running.

Usage:
    python parallel_fanout.py

Requires:
    pip install "together-sandbox @ git+https://github.com/togethercomputer/together-sandbox.git#subdirectory=together-sandbox-python"
    export TOGETHER_API_KEY=your_key
"""

import asyncio
import time

from together_sandbox import (
    TogetherSandbox,
    CreateImageSnapshotParams,
)

BATCH_SIZE = 4  # Number of parallel sandboxes (set low for demo; production uses 32-256)


async def run_exec(
    sandbox,
    command: str,
    args: list[str] | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    poll_interval: float = 0.5,
) -> tuple[int, str]:
    """Execute a command and wait for completion. Returns (exit_code, output)."""
    if args is None:
        args = ["-c", command]
        command = "bash"

    exec_item = await sandbox.execs.create(
        command, args, autorun=True, cwd=cwd, env=env,
    )

    while True:
        exec_info = await sandbox.execs.get(exec_item.id)
        if exec_info.status == "finished":
            break
        await asyncio.sleep(poll_interval)

    outputs = await sandbox.execs.get_output(exec_item.id)
    full_output = "".join(o.output for o in outputs)
    return exec_info.exit_code, full_output


async def main():
    async with TogetherSandbox() as sdk:
        # --- Step 1: Create a shared snapshot ---
        print(f"=== Creating snapshot (shared across {BATCH_SIZE} sandboxes) ===")
        snap = await sdk.snapshots.create(CreateImageSnapshotParams(
            image="python:3.11-slim",
        ))
        print(f"Snapshot: {snap.snapshot_id}")

        # --- Step 2: Create all sandboxes concurrently ---
        print(f"\n=== Creating {BATCH_SIZE} ephemeral sandboxes ===")
        models = await asyncio.gather(*[
            sdk.sandboxes.create(
                snapshot_id=snap.snapshot_id,
                millicpu=1000,
                memory_bytes=2 * 1024**3,
                disk_bytes=5 * 1024**3,
                ephemeral=True,
            )
            for _ in range(BATCH_SIZE)
        ])
        print(f"Created: {[m.id for m in models]}")

        # --- Step 3: Start all concurrently and measure timing ---
        print(f"\n=== Starting all {BATCH_SIZE} sandboxes (GPU waits for slowest) ===")
        batch_start = time.time()

        async def start_timed(model):
            t0 = time.time()
            sandbox = await sdk.sandboxes.start(model.id)
            elapsed = time.time() - t0
            return sandbox, elapsed

        results = await asyncio.gather(*[start_timed(m) for m in models])
        sandboxes = [r[0] for r in results]
        startup_times = sorted([r[1] for r in results])

        batch_elapsed = time.time() - batch_start
        print(f"All running in {batch_elapsed:.1f}s")
        print(f"  Fastest: {startup_times[0]:.1f}s")
        print(f"  Median:  {startup_times[len(startup_times)//2]:.1f}s")
        print(f"  Slowest: {startup_times[-1]:.1f}s (GPU idle time)")

        # --- Step 4: Execute in all sandboxes concurrently ---
        print(f"\n=== Executing in all {BATCH_SIZE} sandboxes ===")

        async def execute_task(sandbox, index: int) -> dict:
            exit_code, output = await run_exec(sandbox,
                f"python3 -c 'import random; random.seed({index}); "
                f"reward = random.uniform(0.0, 1.0); "
                f"print(f\"Sandbox {index}: reward = {{reward:.4f}}\")'")
            return {
                "sandbox_id": sandbox.id,
                "index": index,
                "output": output.strip(),
                "exit_code": exit_code,
            }

        exec_results = await asyncio.gather(*[
            execute_task(sbx, i) for i, sbx in enumerate(sandboxes)
        ])

        for r in exec_results:
            print(f"  [{r['sandbox_id']}] {r['output']} (exit: {r['exit_code']})")

        # --- Step 5: Cleanup ---
        print(f"\n=== Cleaning up {BATCH_SIZE} sandboxes ===")
        await asyncio.gather(*[sbx.shutdown() for sbx in sandboxes])
        await sdk.snapshots.delete_by_id(snap.snapshot_id)
        print("All resources cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
