---
name: together-dedicated-containers-routing
description: "Client-side routing for synchronous requests to a running Together AI Dedicated Container Inference deployment through a customer-supplied list of router hosts: rendezvous-hash sticky sessions on together-affinity-key, replica pinning, failover across hosts, and streamed pass-through without buffering for SSE and gRPC in an app client or a gateway. Reach for it when the deployment already exists and the user wants lower latency or sticky routing to it. Use together-dedicated-containers to build, deploy or queue jobs, and together-dedicated-model-inference for sticky routing on dedicated model endpoints."
---

# Together Dedicated Containers Routing

Send synchronous traffic for a running Dedicated Container Inference (DCI) deployment straight to
the router hosts Together lists for it, without the shared `api.together.ai` edge. Each request
ranks the hosts with a published rendezvous hash on `together-affinity-key`, fails over down the
ranking when a host cannot take it, and streams bodies through. Build it as an in-process client
that hooks the app's HTTP layer, or as a gateway the customer runs.

## Hand Off To Another Skill

- `together-dedicated-containers`: build, configure or deploy the container, or submit queue jobs
- `together-dedicated-model-inference`: dedicated model endpoints, including their sticky routing
- No router host list from Together: use the documented
  `https://api.together.ai/v1/deployment-request/<name>` URL; this skill does not apply

## Workflow

1. Read [references/routing-spec.md](references/routing-spec.md). It is the contract: every rule,
   `classify` and the `send` loop.
2. Implement normalization, key validation and `order`, and pass every case in
   [references/test-vectors.json](references/test-vectors.json) before writing network code.
3. Build `classify` and `send` on one shared connection pool, using
   [references/streaming-passthrough.md](references/streaming-passthrough.md) for the shape and
   language.
4. Verify: N requests with one key reach one host; with one host black-holed, only the first
   request pays a connect timeout until its demotion expires; SSE chunks reach the caller as the
   container emits them.

## Official Docs

- [Dedicated Container Inference](https://docs.together.ai/docs/dedicated-container-inference)
- [Deployments API](https://docs.together.ai/reference/deployments-create)
