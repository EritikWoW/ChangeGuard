# micro1 Agentic Workflows Hackathon — Submission Notes

## Problem and user

**User:** DevOps / SRE / platform engineers reviewing infrastructure pull requests.

**Bottleneck:** Small configuration changes can introduce severe production failures. Reviewers must connect diff details to infrastructure failure modes while avoiding false positives and unsupported assumptions.

## Agentic contribution

ChangeGuard uses an LLM as a bounded risk hypothesis generator. A separate verification stage decides whether the model's evidence actually exists in the referenced change. This separation is the core agentic engineering contribution.

## Primary evaluation metric

**Decision accuracy on a fixed, labeled infrastructure-change benchmark.**

Secondary metrics:

- dangerous-change detection;
- safe-change accuracy;
- unsupported claim count;
- evidence precision;
- runtime and token usage.

## Reproducibility

The same benchmark cases are used for baseline and final workflow. Setup and commands are documented in `REPRODUCE.md`.

## Main failure mode / insight

A free-form reviewer can make a plausible claim with nonexistent repository context. The final workflow therefore separates generation from verification and retains rejected claims as auditable evidence of what the agent attempted but could not prove.
