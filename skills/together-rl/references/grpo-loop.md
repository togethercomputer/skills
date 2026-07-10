# GRPO Training Loop Reference

## Contents

- [Overview](#overview)
- [Session Lifecycle](#session-lifecycle)
- [Operations and Polling](#operations-and-polling)
- [The Three Training Operations](#the-three-training-operations)
- [GRPO Sample Schema](#grpo-sample-schema)
- [Advantages](#advantages)
- [Batch Padding](#batch-padding)

## Overview

GRPO (Group Relative Policy Optimization) post-training on Together runs as a loop over the low-level RL
training API. Each step: sample a group of completions per prompt, score them into rewards, center the
rewards within each group to get advantages, then push one `forward_backward` + `optim_step`.

This doc covers the **training mechanics** (the request/response shapes you assemble). It does not restate
the full API — for authoritative request/response definitions see the RL training API docs and the
`/rl/training-sessions` family in the OpenAPI spec. The canonical reference implementation is
[`rl-cookbook/grpo_train.py`](https://github.com/togethercomputer/rl-cookbook/blob/main/grpo_train.py);
the only thing this skill changes is **where the reward comes from** (a sandbox — see
[sandbox-rewards.md](sandbox-rewards.md)).

## Session Lifecycle

```python
session = client.beta.rl.sessions.create(base_model="meta-llama/Llama-3.2-1B-Instruct")
session_id = session.session_id or getattr(session, "id", None)
# Poll client.beta.rl.sessions.retrieve(session_id).status until:
#   TRAINING_SESSION_STATUS_RUNNING
# ... run training steps ...
client.beta.rl.sessions.stop(session_id)   # always, in a finally block
```

A session holds the live model weights on the training service. Create once, run many steps, stop when
done (stopping releases the GPU — orphaned sessions keep billing).

## Operations and Polling

`sample`, `forward_backward`, and `optim_step` are **asynchronous operations**: each returns an operation
handle, not a finished result. Poll until complete before reading the output. The cookbook's helpers in
`together.lib.beta.rl.operations` (`retrieve_operation`, `get_operation_status`, `is_operation_complete`,
`get_operation_error`) wrap this:

```python
def wait_for_operation(client, *, session_id, operation, kind, timeout, interval):
    deadline = time.monotonic() + timeout
    while True:
        operation = rl_ops.retrieve_operation(client, session_id=session_id, operation=operation, kind=kind)
        if rl_ops.is_operation_complete(operation):
            if rl_ops.get_operation_status(operation) == "TRAINING_OPERATION_STATUS_FAILED":
                raise RuntimeError(rl_ops.get_operation_error(operation))
            return operation
        if time.monotonic() >= deadline:
            raise TimeoutError(f"operation {kind} timed out")
        time.sleep(interval)
```

## The Three Training Operations

```python
# 1. Sample a group of completions for one prompt (num_samples = group size)
sample_op = client.beta.rl.training.sample(
    session_id=session_id,
    prompt={"chunks": [{"encoded_text": {"tokens": prompt_tokens}}]},
    num_samples=group_size,
    sampling_params={"max_tokens": max_sample_tokens},
)
result = wait_for_operation(...)            # result.output.sequences[i].tokens / .logprobs

# 2. One gradient pass over the assembled, advantage-weighted batch
fb_op = client.beta.rl.training.forward_backward(
    session_id=session_id,
    loss={"type": "LOSS_TYPE_GRPO",
          "grpo_params": {"beta": 0.0, "agg_type": "GRPO_LOSS_AGGREGATION_TYPE_TOKEN_MEAN"}},
    samples=samples,
)
loss = wait_for_operation(...).output.loss

# 3. Optimizer step
opt_op = client.beta.rl.training.optim_step(session_id=session_id, learning_rate=8e-5)
wait_for_operation(...)
```

## GRPO Sample Schema

Each training sample concatenates prompt + response tokens, masks the prompt out of the loss, and attaches
the per-token advantage and the generator's logprobs:

```python
def build_grpo_sample(prompt_tokens, response_tokens, response_logprobs, advantage, max_model_length):
    available = max(max_model_length - len(prompt_tokens), 0)
    response_tokens = response_tokens[:available]
    response_logprobs = response_logprobs[:available]
    if not response_tokens:
        return None
    model_tokens = prompt_tokens + response_tokens
    loss_mask  = [0] * len(prompt_tokens) + [1] * len(response_tokens)   # train on response only
    targets    = model_tokens[1:] + [0]                                  # next-token targets
    advantages = [0.0] * len(prompt_tokens) + [advantage] * len(response_tokens)
    logprobs   = [0.0] * len(prompt_tokens) + [float(x) for x in response_logprobs]
    return {
        "model_input": {"chunks": [{"encoded_text": {"tokens": model_tokens}}]},
        "loss_inputs": {
            "loss_mask":     {"data": loss_mask,  "dtype": "D_TYPE_INT64"},
            "target_tokens": {"data": targets,    "dtype": "D_TYPE_INT64"},
            "grpo_inputs": {
                "advantages":         {"data": advantages, "dtype": "D_TYPE_FLOAT32"},
                "generator_logprobs": {"data": logprobs,    "dtype": "D_TYPE_FLOAT32"},
            },
        },
    }
```

## Advantages

GRPO centers rewards **within each prompt's group**:

```python
baseline = sum(group_rewards) / len(group_rewards)
advantage = reward - baseline
```

A group where every sample earns the same reward has zero advantage everywhere and contributes no
gradient — reward diversity within a group is what drives learning. `forward_backward` needs a minimum
batch (the cookbook requires ≥ 8 assembled samples).

## Batch Padding

All samples in a `forward_backward` batch must be padded to the longest sequence. Pad `tokens`,
`loss_mask`, and `target_tokens` with `0`, and `advantages` / `generator_logprobs` with `0.0`. See
`_pad_samples` in [rl-cookbook/grpo_train.py](https://github.com/togethercomputer/rl-cookbook/blob/main/grpo_train.py)
for the exact padding (note: the integer fields are serialized as strings in the padded request).
