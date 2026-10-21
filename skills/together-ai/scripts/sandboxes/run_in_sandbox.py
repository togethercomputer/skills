#!/usr/bin/env python3
"""
Together AI Code Sandbox -- Run Code in an Isolated Sandbox (together-sandbox SDK)

Reuse or build a snapshot, create a sandbox with a TTL backstop, write input
files and a script into it, run the script, read its result file back, and
terminate. This replaces the retired Code Interpreter (client.code_interpreter).

Usage:
    python run_in_sandbox.py
    python run_in_sandbox.py --snapshot-alias my-python@v1 --image python:3.12-slim
    python run_in_sandbox.py --ttl 300

Requires:
    pip install together-sandbox   # Python 3.10+; must be enabled for your organization
    export TOGETHER_API_KEY=your_key
    # together-sandbox reads TOGETHER_BASE_URL as its own API host: unset it if it
    # is set for the together SDK.

Lifecycle note: a sandbox runs until it is terminated or its TTL elapses. This
script terminates it in a finally block, and the TTL covers a crash.
"""

import argparse
import asyncio
import json

from together_sandbox import CreateImageSnapshotParams, HttpError, TogetherSandbox

SALES_CSV = "month,revenue\nJan,100\nFeb,150\nMar,130\n"

# Runs inside the sandbox. Standard library only, so a stock Python image works.
ANALYSIS_SCRIPT = """\
import csv, json, statistics

with open("/tmp/sales.csv") as f:
    rows = list(csv.DictReader(f))
revenue = [float(row["revenue"]) for row in rows]
summary = {"months": len(rows), "total": sum(revenue), "mean": statistics.mean(revenue)}
with open("/tmp/summary.json", "w") as f:
    json.dump(summary, f)
print(f"Analyzed {len(rows)} months")
"""


async def ensure_snapshot(sdk: TogetherSandbox, alias: str, image: str) -> None:
    """Reuse the snapshot behind ``alias``, or build it once from a public image."""
    try:
        snapshot = await sdk.snapshots.get_by_alias(alias)
        print(f"Reusing snapshot {snapshot.id} ({alias})")
        return
    except HttpError as e:
        if e.status != 404:
            raise

    # Not idempotent: a blind retry can register a duplicate snapshot.
    print(f"Building snapshot {alias} from {image}...")
    result = await sdk.snapshots.create(
        CreateImageSnapshotParams(
            image=image,
            alias=alias,
            on_progress=lambda progress: print(f"  [{progress.step}] {progress.output}"),
        )
    )
    print(f"Created snapshot {result.snapshot_id}")


async def run(snapshot_alias: str, image: str, ttl: int) -> dict:
    """Run the analysis script in a fresh sandbox and return its parsed summary."""
    async with TogetherSandbox() as sdk:
        await ensure_snapshot(sdk, snapshot_alias, image)

        sandbox = await sdk.sandboxes.create(snapshot_alias=snapshot_alias, ttl=ttl)
        print(f"Sandbox {sandbox.id} is running (auto-terminates after {ttl}s)")
        try:
            await sandbox.files.create("/tmp/sales.csv", SALES_CSV)
            await sandbox.files.create("/tmp/analyze.py", ANALYSIS_SCRIPT)

            result = await sandbox.execs.exec("python3", ["/tmp/analyze.py"])
            print(f"exit_code={result['exit_code']}")
            print(result["output"])
            if result["exit_code"] != 0:
                raise RuntimeError("Sandbox script failed; see output above")

            # Files persist across execs in one sandbox; Python variables do not.
            return json.loads(await sandbox.files.read("/tmp/summary.json"))
        finally:
            # Leaving the async with block only closes HTTP connections.
            await sandbox.terminate()
            print(f"Terminated sandbox {sandbox.id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run code in a Together code sandbox")
    parser.add_argument(
        "--snapshot-alias",
        default="skills-python@v1",
        help="Snapshot alias (namespace@tag) to reuse, or to create if it does not exist",
    )
    parser.add_argument(
        "--image",
        default="python:3.12-slim",
        help="Public Docker image to build the snapshot from when the alias does not exist",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=600,
        help="Seconds before the sandbox terminates itself if this script does not",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    summary = asyncio.run(run(args.snapshot_alias, args.image, args.ttl))
    print(f"Summary: {summary}")
