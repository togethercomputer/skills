# Sandbox Code-Execution Rewards

## Contents

- [Why a Sandbox](#why-a-sandbox)
- [The Integration Point](#the-integration-point)
- [Bridging Sync RL and Async Sandboxes](#bridging-sync-rl-and-async-sandboxes)
- [Scoring One Candidate](#scoring-one-candidate)
- [Batch Reward Collection](#batch-reward-collection)
- [Pre-build the Environment](#pre-build-the-environment)

## Why a Sandbox

For coding and agentic RL the reward is not a string match — it is the result of **running** the model's
output: execute the candidate solution against a test suite and use pass/fail (or a parsed score) as the
reward. That code is untrusted and must run in isolation. This skill computes rewards with the
`together-sandbox` SDK; the sandbox API itself (snapshots, sandboxes, exec, files) is owned by the
**`together-sandbox` skill** — read it for the full surface and its
[Python SDK docs](https://github.com/togethercomputer/together-sandbox/blob/main/docs/python-sdk.md). The
reward patterns below mirror that skill's `references/rl-patterns.md` (batch fan-out, reward collection).

## The Integration Point

In the GRPO loop ([grpo-loop.md](grpo-loop.md)), `training.sample` returns token sequences. Decode each to
text, then — instead of scoring locally — score by executing in a sandbox:

```
sample group  ->  decode tokens  ->  [SANDBOX] write candidate, run tests, read reward  ->  advantages  ->  forward_backward
```

## Bridging Sync RL and Async Sandboxes

The RL training SDK is synchronous; the `together-sandbox` SDK is async. Run the whole batch's rewards in
**one** `asyncio.run(...)` call per training step, fanning out sandboxes concurrently:

```python
rewards = asyncio.run(compute_rewards(snapshot_alias, candidates, test_code))
```

Never open an event loop per candidate or per RL call — collect all of a step's candidates first, then
fan out once.

## Scoring One Candidate

```python
async def score_candidate(sdk, snapshot_alias, candidate_code, test_code) -> float:
    model = await sdk.sandboxes.create(snapshot_alias=snapshot_alias, ephemeral=True)
    sandbox = await sdk.sandboxes.start(model.id)
    try:
        # Sandboxes have no DNS by default; set it as the first exec if tests need network.
        await sandbox.execs.exec("bash", ["-c", 'echo "nameserver 1.1.1.1" > /etc/resolv.conf'])
        await sandbox.files.create("/workspace/solution.py", candidate_code)
        await sandbox.files.create("/workspace/test_solution.py", test_code)
        result = await sandbox.execs.exec(
            "bash", ["-c", "cd /workspace && python -m pytest -q test_solution.py"]
        )
        # execs.exec returns {"exit_code": int, "output": str}
        return 1.0 if result["exit_code"] == 0 else 0.0
    finally:
        await sdk.sandboxes.shutdown(sandbox.id)   # ephemeral; clean up every rollout
```

## Batch Reward Collection

Fan out one sandbox per candidate for the whole step, then return rewards in the original order so they
line up with the RL samples:

```python
async def compute_rewards(snapshot_alias, candidates, test_code) -> list[float]:
    async with TogetherSandbox() as sdk:
        results = await asyncio.gather(
            *[score_candidate(sdk, snapshot_alias, c, test_code) for c in candidates],
            return_exceptions=True,
        )
    # A crashed sandbox should score 0.0, not abort the whole step.
    return [r if isinstance(r, float) else 0.0 for r in results]
```

Order matters: `gather` preserves input order, so `rewards[i]` corresponds to `candidates[i]`. A failed or
timed-out sandbox is scored `0.0` so one bad rollout never invalidates the batch — but watch the failure
rate, since GRPO needs reward diversity *within* each group to learn.

## Pre-build the Environment

Bake the task harness, dependencies, and (optionally) the tests into a **snapshot once**, then create
ephemeral sandboxes from it per rollout. Building the image inside every rollout wastes minutes per step
and serializes the batch behind `pip install`. See the `together-sandbox` skill's golden-image pattern
(`references/rl-patterns.md`, Pattern 1) for `snapshots.create` + `hibernate` to capture a reusable image,
and reference it here by `snapshot_alias`.
