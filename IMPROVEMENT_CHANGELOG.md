# Improvement Changelog

This file tracks the evolution from a simple review baseline to the final ChangeGuard workflow. Benchmark values must be generated from the fixed evaluation set; do not substitute hand-entered scores.

| Stage | What changed | Why | Evidence / decision |
|---|---|---|---|
| Baseline | Single review pass / simple baseline | Establish a fair starting point | Run on the same benchmark cases as final workflow |
| Iteration 1 | Deterministic infrastructure rules | Catch high-confidence known failure modes without model variance | Keep: strong precision for explicit IaC risks |
| Iteration 2 | Structured GitHub PR ingestion and diff parsing | Give the reviewer bounded, exact change context | Keep: reproducible inputs and file-level evidence |
| Iteration 3 | LLM Risk Agent | Detect semantic risks not covered by static patterns | Keep only when paired with verification |
| Iteration 4 | Exact evidence verifier | Prevent unsupported LLM claims from becoming blocking decisions | Keep: rejected claims become an explicit artifact |
| Final | Evidence-backed decision + trajectories + persisted reports | Produce an auditable end-to-end workflow | Final benchmark compares this workflow with baseline |

## Removed / constrained experiment

**Unverified free-form LLM review.** It was intentionally constrained because a model can infer plausible repository/runtime context that is absent from the PR. The final design requires each LLM risk to cite an exact substring from the referenced diff; claims that fail verification are rejected.

## Hot take

More model freedom did not make the reviewer more trustworthy. Reliability improved when the model was treated as a hypothesis generator and a separate verifier controlled what could influence the final decision.
