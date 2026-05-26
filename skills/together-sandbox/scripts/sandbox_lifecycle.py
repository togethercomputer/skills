#!/usr/bin/env python3
"""
Together Sandbox — Create, Execute, and Manage Sandbox Lifecycle

Demonstrates the full sandbox lifecycle: create a snapshot from a Docker image,
start a sandbox, execute commands, read/write files, and shut down.

Usage:
    python sandbox_lifecycle.py

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


async def main():
    async with TogetherSandbox() as sdk:
        # --- Step 1: Create a snapshot from a Docker image ---
        print("=== Creating snapshot from python:3.11-slim ===")
        t0 = time.time()
        snap_result = await sdk.snapshots.create(CreateImageSnapshotParams(
            image="python:3.11-slim",
        ))
        print(f"Snapshot created: {snap_result.snapshot_id} ({time.time() - t0:.1f}s)")

        # --- Step 2: Create and start a sandbox ---
        print("\n=== Creating and starting sandbox ===")
        t0 = time.time()
        model = await sdk.sandboxes.create(
            snapshot_id=snap_result.snapshot_id,
            millicpu=2000,
            memory_bytes=4 * 1024**3,
            disk_bytes=10 * 1024**3,
            ephemeral=True,
        )
        sandbox = await sdk.sandboxes.start(model.id)
        print(f"Sandbox running: {sandbox.id} ({time.time() - t0:.1f}s)")

        # --- Step 3: Configure DNS (required for network access) ---
        print("\n=== Configuring DNS ===")
        result = await sandbox.execs.exec("bash", ["-c",
            'echo "nameserver 1.1.1.1" > /etc/resolv.conf && '
            'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
        ])
        print(f"DNS configured (exit: {result['exit_code']})")

        # --- Step 4: Execute commands ---
        print("\n=== Executing commands ===")
        result = await sandbox.execs.exec("bash", ["-c", "python3 --version"])
        print(f"Python version: {result['output'].strip()}")

        result = await sandbox.execs.exec("bash", ["-c", "echo hello from sandbox"])
        print(f"Output: {result['output'].strip()}")
        print(f"Exit code: {result['exit_code']}")

        # --- Step 5: File operations ---
        print("\n=== File operations ===")

        # Write a Python script
        script = """
import sys
print(f"Python {sys.version}")
print(f"Platform: {sys.platform}")
total = sum(range(1, 101))
print(f"Sum 1-100: {total}")
"""
        await sandbox.files.create("/tmp/info.py", script)
        print("Wrote /tmp/info.py")

        # Read it back
        content = await sandbox.files.read("/tmp/info.py")
        print(f"Read back: {len(content)} chars")

        # Execute it
        result = await sandbox.execs.exec("python3", ["/tmp/info.py"])
        print(f"Script output:\n{result['output']}")

        # List directory
        files = await sandbox.directories.list("/tmp")
        print(f"Files in /tmp: {len(files)} items")

        # --- Step 6: Shutdown ---
        print("\n=== Shutting down ===")
        await sdk.sandboxes.shutdown(sandbox.id)
        print("Sandbox shut down")

        # --- Step 7: Clean up snapshot ---
        await sdk.snapshots.delete_by_id(snap_result.snapshot_id)
        print("Snapshot deleted")


if __name__ == "__main__":
    asyncio.run(main())
