#!/usr/bin/env python3
"""
Together AI Dedicated Model Inference -- Roll Out a New Deployment

Replace a live deployment with a new one (new model version, new config, or
new hardware) without downtime: create the target and wait for READY, start a rollout
(blue-green or metric-gated canary), watch it, and control its lifecycle.

Usage:
    python rollout_new_version.py prepare --endpoint ep_abc123 --model ml_abc123 --config cr_abc123 --name v2
    python rollout_new_version.py start --endpoint ep_abc123 --source dep_src --target dep_tgt --replicas 4
    python rollout_new_version.py start --endpoint ep_abc123 --source dep_src --target dep_tgt \
        --replicas 4 --canary --steps 25,50,100 --gate-latency-regression 50
    python rollout_new_version.py watch --endpoint ep_abc123 --rollout rol_abc123
    python rollout_new_version.py pause|resume|complete|abort --endpoint ep_abc123 --rollout rol_abc123

Requires:
    uv pip install --upgrade together   # a release with the beta DMI surface (client.beta.*)
    export TOGETHER_API_KEY=your_key

Notes:
    - The target must have at least one replica and be READY before the rollout
      starts (a 0/0 target risks deployment_stopped errors mid-shift). `prepare`
      creates it with one replica and waits; keep it OUT of the traffic split.
    - The source must be in the endpoint's traffic split, or the rollout shifts nothing.
    - Metric gates are canary-only and need live traffic on the endpoint to evaluate.
    - After COMPLETED there's no rollback; revert by rolling out in reverse.
"""

import argparse
import sys
import time

from together import Together

client = Together()
PROJECT_ID = client.whoami().project_id

TERMINAL_STATES = {"ROLLOUT_STATE_COMPLETED", "ROLLOUT_STATE_ABORTED"}


def prepare_target(endpoint_id: str, model_id: str, config_id: str, config_project_id: str, name: str):
    """Create the target deployment with one replica and wait for READY.

    The rollout adjusts the target's replica count after it starts, but it must
    already be READY when the rollout begins — traffic can shift before a 0/0
    target has a ready replica, causing deployment_stopped errors.
    """
    deployment = client.beta.endpoints.deployments.create(
        endpoint_id,
        project_id=PROJECT_ID,
        name=name,
        model=f"projects/{PROJECT_ID}/models/{model_id}",
        config=f"projects/{config_project_id}/configs/{config_id}",
        autoscaling={"min_replicas": 1, "max_replicas": 1},
    )
    print(f"Created target deployment: {deployment.id} — waiting for READY...")
    while True:
        d = client.beta.endpoints.deployments.retrieve(
            deployment.id, project_id=PROJECT_ID, endpoint_id=endpoint_id
        )
        print(f"  {d.status.state}")
        if d.status.state == "DEPLOYMENT_STATE_READY":
            break
        if d.status.state == "DEPLOYMENT_STATE_FAILED":
            raise RuntimeError(f"Target deployment failed: {d.status.message}")
        time.sleep(15)
    print("Target READY. Do NOT add it to the traffic split; the rollout moves traffic itself.")
    return deployment


def start_rollout(
    endpoint_id: str,
    source_id: str,
    target_id: str,
    final_replicas: int,
    canary: bool = False,
    steps: list[int] | None = None,
    step_interval: str = "600s",
    gate_latency_regression: int | None = None,
):
    """Create and start a rollout. Blue-green by default; --canary for a staged ladder.

    With a canary, an optional serving_latency regression gate pauses the rollout
    (SYSTEM_PAUSED) if the target's p95 regresses more than the given percent vs the source.
    """
    kwargs: dict = {
        "project_id": PROJECT_ID,
        "source_deployment_id": source_id,
        "target_deployment_id": target_id,
        "source_cleanup": "SOURCE_CLEANUP_POLICY_DRAIN",
        "final_source_replicas": 0,
        "final_target_replicas": final_replicas,
    }
    if canary:
        ladder = steps or [10, 50, 100]
        kwargs["canary"] = {
            "steps": [
                # Scale target replicas proportionally to each traffic step.
                {"traffic": pct, "replicas": max(1, round(final_replicas * pct / 100))}
                for pct in ladder
            ],
            "step_interval": step_interval,
        }
        if gate_latency_regression is not None:
            kwargs["metrics"] = [
                {
                    "name": "serving_latency",
                    "stat": "METRIC_STAT_TYPE_PERCENTILE",
                    "percentile": 95,
                    "regression_check": {
                        "max_regression_percent": gate_latency_regression,
                        "direction": "REGRESSION_DIRECTION_HIGHER_IS_WORSE",
                    },
                    # 300s window for histogram percentiles; keep step_interval >= window + ~90s.
                    "window": "300s",
                }
            ]
    else:
        kwargs["blue_green"] = {}

    rollout = client.beta.endpoints.rollouts.create(endpoint_id, **kwargs)
    client.beta.endpoints.rollouts.start(rollout.id, project_id=PROJECT_ID, endpoint_id=endpoint_id)
    print(f"Rollout started: {rollout.id} ({'canary' if canary else 'blue-green'})")
    return rollout


def watch(endpoint_id: str, rollout_id: str, poll: int = 30):
    """Poll the rollout until it reaches a terminal state, printing progress."""
    while True:
        r = client.beta.endpoints.rollouts.retrieve(
            rollout_id, project_id=PROJECT_ID, endpoint_id=endpoint_id
        )
        line = f"  {r.state}  step={getattr(r, 'current_step', None)}  traffic={getattr(r, 'current_traffic_percent', None)}%"
        condition = getattr(getattr(r, "status", None), "condition", None)
        if condition is not None and getattr(condition, "category", None):
            line += f"  condition={condition.category}: {getattr(condition, 'message', '')}"
        print(line)
        if r.state in TERMINAL_STATES:
            return r
        if r.state == "ROLLOUT_STATE_SYSTEM_PAUSED":
            print(
                "  Platform paused the rollout. Transient causes (METRICS_UNAVAILABLE,"
                " CAPACITY_EXHAUSTED): fix and `resume`. Regressions (METRIC_REGRESSION,"
                " HEALTH_REGRESSION): `abort` to revert to the source."
            )
        time.sleep(poll)


def control(endpoint_id: str, rollout_id: str, action: str, reason: str | None = None):
    """pause / resume / complete (fast-forward to target) / abort (revert to source)."""
    rollouts = client.beta.endpoints.rollouts
    common = {"project_id": PROJECT_ID, "endpoint_id": endpoint_id}
    if action == "pause":
        rollouts.pause(rollout_id, **common, reason=reason)
    elif action == "resume":
        rollouts.resume(rollout_id, **common)
    elif action == "complete":
        rollouts.promote(rollout_id, **common)
    elif action == "abort":
        rollouts.abort(rollout_id, **common, reason=reason)
    print(f"{action}: {rollout_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="Create the target deployment and wait for READY")
    p.add_argument("--endpoint", required=True)
    p.add_argument("--model", required=True, help="Model ID (ml_...)")
    p.add_argument("--config", required=True, help="Config revision ID (cr_...)")
    p.add_argument("--config-project", default=PROJECT_ID)
    p.add_argument("--name", required=True, help="Target deployment name")

    p = sub.add_parser("start", help="Create and start the rollout")
    p.add_argument("--endpoint", required=True)
    p.add_argument("--source", required=True, help="Source deployment ID (currently serving)")
    p.add_argument("--target", required=True, help="Target deployment ID (READY, not in the split)")
    p.add_argument("--replicas", type=int, required=True, help="Final target replica count (>= 1)")
    p.add_argument("--canary", action="store_true", help="Staged ladder instead of blue-green")
    p.add_argument("--steps", default=None, help="Canary traffic ladder, e.g. 25,50,100")
    p.add_argument("--interval", default="600s", help="Canary soak per step (default 600s)")
    p.add_argument(
        "--gate-latency-regression", type=int, default=None,
        help="Canary gate: max p95 serving_latency regression percent vs source",
    )

    p = sub.add_parser("watch", help="Poll the rollout until terminal")
    p.add_argument("--endpoint", required=True)
    p.add_argument("--rollout", required=True)

    for action in ("pause", "resume", "complete", "abort"):
        p = sub.add_parser(action, help=f"{action} a running rollout")
        p.add_argument("--endpoint", required=True)
        p.add_argument("--rollout", required=True)
        p.add_argument("--reason", default=None)

    args = parser.parse_args()
    if args.command == "prepare":
        prepare_target(args.endpoint, args.model, args.config, args.config_project, args.name)
    elif args.command == "start":
        steps = [int(s) for s in args.steps.split(",")] if args.steps else None
        start_rollout(
            args.endpoint, args.source, args.target, args.replicas,
            canary=args.canary, steps=steps, step_interval=args.interval,
            gate_latency_regression=args.gate_latency_regression,
        )
    elif args.command == "watch":
        watch(args.endpoint, args.rollout)
    else:
        control(args.endpoint, args.rollout, args.command, getattr(args, "reason", None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
