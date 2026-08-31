# micro1 Agentic Workflows Hackathon — Submission Notes

## Project

**ChangeGuard — Agentic Infrastructure Change Reviewer**

ChangeGuard predicts deployment risks before infrastructure changes reach production. It reviews real GitHub pull requests and produces an evidence-backed PASS / WARN / BLOCK decision.

## User and problem

**User:** DevOps, SRE and platform engineers reviewing infrastructure pull requests.

**Bottleneck:** A small Kubernetes, Terraform, Dockerfile or CI change can trigger a severe production failure. Reviewers must understand the diff, connect it to failure modes and avoid false positives or unsupported assumptions.

## Why agents

A single LLM is useful for semantic reasoning, but it can also produce plausible claims that are not actually supported by the submitted change.

ChangeGuard therefore separates responsibilities:

1. GitHub Collector reads the real PR and changed-file patches.
2. Change Parser bounds the context to submitted changes.
3. Deterministic Risk Rules catch explicit, reproducible failure modes.
4. Risk Agent proposes additional semantic risks.
5. Evidence Verifier checks every AI claim against exact diff evidence and rejects unsupported claims.
6. Decision stage produces PASS / WARN / BLOCK only from the verified finding set.

## Baseline

The official baseline is a **single-prompt reviewer using the same configured LLM model** as the final workflow. It receives the change and directly returns PASS / WARN / BLOCK plus a reason.

This means the benchmark measures the workflow, not a stronger model.

## Evaluation

Primary metric: **decision accuracy on a fixed 15-case labeled infrastructure-change benchmark**.

Secondary metrics:
- dangerous-change detection;
- safe-change accuracy;
- supported and rejected AI claims;
- token usage;
- performance on designated challenging cases.

The benchmark is executable from the UI or `POST /api/benchmarks/run-agentic`. Results are persisted and exportable as Markdown.

## Reproducibility

- setup: `REPRODUCE.md`;
- benchmark protocol: `docs/BENCHMARK_PROTOCOL.md`;
- improvement history: `IMPROVEMENT_CHANGELOG.md`;
- representative trajectories: `docs/TRAJECTORIES.md`;
- five-minute demo: `docs/DEMO_SCRIPT.md`.

Stored runs can export their trajectory, claims and evidence as JSON. Reports and benchmark results can also be exported directly from the application.

## End-to-end quality

A user can paste a real GitHub PR, inspect changed files and evidence, review rejected claims, inspect the agent trajectory, receive a final decision and explicitly publish the evidence-backed report back to the GitHub PR as a comment.

ChangeGuard never deploys infrastructure or applies Terraform/Kubernetes changes automatically.

## Removed / constrained experiment

The unconstrained free-form LLM reviewer was rejected as the final architecture because it could infer plausible repository/runtime context that was not actually present in the PR. The final design makes unsupported claims visible as rejected artifacts instead of hiding them.

## Main failure mode

ChangeGuard can miss risks that require runtime data or cross-repository context that is not available in the submitted PR. The system reports that limitation rather than inventing a blast radius.

## Hot take

> More context did not automatically make the infrastructure agent safer. Reliability improved when every consequential AI claim was required to carry evidence that an independent verifier could check.
