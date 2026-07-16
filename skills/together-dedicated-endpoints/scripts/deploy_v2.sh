#!/usr/bin/env bash
# Together AI Dedicated Model Inference (v2) -- End-to-end CLI walkthrough
#
# Deploys a supported model on DMI v2, waits for the deployment to become ready,
# sends a chat completion, and tears the deployment down.
#
# Every management operation goes through the `tg beta` CLI (Together CLI 2.24.0+).
# The v2 Python/TypeScript SDK surface (client.beta.endpoints.*) is still being
# published, so this script uses the CLI plus curl for inference.
#
# Usage:
#   ./deploy_v2.sh                      # runs the default demo (google/gemma-4-E4B-it)
#   MODEL=zai-org/GLM-5.2 ./deploy_v2.sh
#
# Requirements:
#   uv tool install "together[cli]"     # or: pip install together
#   export TOGETHER_API_KEY=your_key
#   # Optional: pin the project explicitly
#   export TOGETHER_PROJECT_ID=proj_...
#
# Notes:
#   - Set CONFIG_ID when the chosen model has more than one deployment profile.
#     A bare `tg beta endpoints deploy <model>` errors with the available
#     profiles when a config is required.
#   - Set NO_TEARDOWN=1 to keep the endpoint after inference.

set -euo pipefail

MODEL="${MODEL:-google/gemma-4-E4B-it}"
ENDPOINT_NAME="${ENDPOINT_NAME:-dmi-demo-$(date +%s)}"
MIN_REPLICAS="${MIN_REPLICAS:-1}"
MAX_REPLICAS="${MAX_REPLICAS:-1}"
CONFIG_ID="${CONFIG_ID:-}"
PROMPT="${PROMPT:-What is 2 + 2?}"
POLL_INTERVAL="${POLL_INTERVAL:-15}"
POLL_TIMEOUT="${POLL_TIMEOUT:-1200}"
NO_TEARDOWN="${NO_TEARDOWN:-}"

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1"; exit 1; }
}
require tg
require jq
require curl

: "${TOGETHER_API_KEY:?Set TOGETHER_API_KEY before running}"

echo "=== whoami ==="
tg whoami

echo
echo "=== deploy $MODEL as endpoint $ENDPOINT_NAME ==="
deploy_args=(
  beta endpoints deploy "$MODEL"
  --endpoint "$ENDPOINT_NAME"
  --min-replicas "$MIN_REPLICAS"
  --max-replicas "$MAX_REPLICAS"
  --json
)
if [ -n "$CONFIG_ID" ]; then
  deploy_args+=(--config "$CONFIG_ID")
fi

deploy_json=$(tg "${deploy_args[@]}")
echo "$deploy_json" | jq .

endpoint_id=$(echo "$deploy_json" | jq -r '.endpoint.id // .id // empty')
deployment_id=$(echo "$deploy_json" | jq -r '.deployment.id // .deployments[0].id // empty')
inference_name=$(echo "$deploy_json" | jq -r '.endpoint.name // .name // .inferenceName // empty')

if [ -z "$endpoint_id" ] || [ -z "$deployment_id" ]; then
  echo "Could not parse endpoint or deployment ID from deploy output." >&2
  exit 1
fi

echo
echo "endpoint_id=$endpoint_id"
echo "deployment_id=$deployment_id"
echo "inference_name=$inference_name"

echo
echo "=== wait for DEPLOYMENT_STATE_READY (up to ${POLL_TIMEOUT}s) ==="
elapsed=0
while [ "$elapsed" -lt "$POLL_TIMEOUT" ]; do
  status_json=$(tg beta endpoints get "$endpoint_id" --json)
  state=$(echo "$status_json" | jq -r --arg dep "$deployment_id" \
    '.deployments[] | select(.id == $dep) | .status.state // empty')
  ready=$(echo "$status_json" | jq -r --arg dep "$deployment_id" \
    '.deployments[] | select(.id == $dep) | .status.readyReplicas // 0')
  message=$(echo "$status_json" | jq -r --arg dep "$deployment_id" \
    '.deployments[] | select(.id == $dep) | .status.message // ""')
  printf "  state=%s ready=%s message=%q (%ss)\n" "$state" "$ready" "$message" "$elapsed"

  case "$state" in
    DEPLOYMENT_STATE_READY) break ;;
    DEPLOYMENT_STATE_FAILED)
      echo "Deployment failed. Full status:" >&2
      echo "$status_json" | jq . >&2
      exit 1
      ;;
  esac

  sleep "$POLL_INTERVAL"
  elapsed=$((elapsed + POLL_INTERVAL))
done

if [ "$state" != "DEPLOYMENT_STATE_READY" ]; then
  echo "Deployment did not reach READY within ${POLL_TIMEOUT}s (last state: $state)." >&2
  exit 1
fi

echo
echo "=== send a chat completion to $inference_name ==="
curl -s -X POST https://api-inference.together.ai/v1/chat/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg m "$inference_name" --arg p "$PROMPT" '{
    model: $m,
    messages: [{role: "user", content: $p}],
    max_tokens: 256
  }')" | jq .

if [ -n "$NO_TEARDOWN" ]; then
  echo
  echo "NO_TEARDOWN set; leaving endpoint $endpoint_id (deployment $deployment_id) running."
  echo "Scale down later with:"
  echo "  tg beta endpoints update $deployment_id --min-replicas 0 --max-replicas 0"
  echo "Or delete both resources with:"
  echo "  tg beta endpoints rm $endpoint_id --force"
  exit 0
fi

echo
echo "=== teardown: delete endpoint $endpoint_id ==="
tg beta endpoints rm "$endpoint_id" --force
echo "Done."
