# Skill Quality

This directory holds lightweight evaluation scaffolding for the Together AI skill catalog.

## Trigger evals

Each file in `trigger-evals/` contains realistic prompts for one skill:

- `query`: a plausible user request
- `should_trigger`: whether the named skill should win routing for that request

The sets intentionally include near-miss negative examples so skill descriptions can be tuned
without overfitting to obvious keyword matches.

These files are designed for routing and trigger evaluation. They do not replace deeper workflow
tests or live product validation.
