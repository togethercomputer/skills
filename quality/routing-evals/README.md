# Routing evals

`trigger-evals/` answers *"does the `together-ai` skill fire at all?"*

These answer the question that replaced it. Before the merge, 14 separate skill descriptions
did the routing, and each skill's trigger-eval negatives implicitly tested it: a query that
belonged to a sibling skill was a `should_trigger: false` case. With one skill, triggering is
easy and **routing is the hard part** — so routing needs its own fixture.

## Format

```json
[
  { "query": "...", "expected_domain": "domains/video.md", "near_miss": true }
]
```

- `expected_domain` — the one guide under `skills/together-ai/domains/` that a correct run
  should open before answering.
- `near_miss` (optional) — marks a case lifted from an old per-skill eval set where it was a
  *negative*, i.e. a query deliberately built to look like a neighbouring product. These are
  the cases most likely to regress, so weight them accordingly.

## How to use

There is no runner in this repo (the same is true of `trigger-evals/`). Run these by hand or
from `skill-creator`: give a subagent the skill, send the query, and check which
`domains/*.md` it reads. Two failure modes count as wrong:

1. it opens the wrong guide, or
2. it answers out of `SKILL.md` without opening any guide at all.

The second is the subtler regression — the router is written to be unable to answer on its
own (no API shapes, no model names, no parameter lists) specifically so this shows up as an
obviously thin answer rather than a plausible wrong one.
