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
5. Evidence Verifier checks every AI claim against exact diff evidence and rejects unmatched claims.
6. Decision stage distinguishes evidence provenance from decision authority: deterministic findings can block; LLM-only low/medium findings remain advisory; LLM-only high/critical findings require human review.

## Baseline

The official baseline is a **single-prompt reviewer using the same configured LLM model** as the final workflow. It receives the change and directly returns PASS / WARN / BLOCK plus a reason.

This means the benchmark measures the workflow, not a stronger model.

## Evaluation

The final official benchmark used **GPT-5.6 Luna** for both systems on the same fixed 15 labeled cases, including 2 designated challenging cases.

Primary metric: **decision accuracy**.

| Metric | Baseline | ChangeGuard |
|---|---:|---:|
| Decision accuracy | 87% | **100%** |
| Danger detection | 100% | **100%** |
| Safe-change accuracy | 80% | **100%** |

Measured improvement: **+13 percentage points** in decision accuracy.

Token usage was **2,964** for the single-prompt baseline and **4,792** for ChangeGuard. The final run contained **13 evidence-linked AI claims** and **0 unmatched claims**. ChangeGuard classified all 15 cases correctly, including both challenging cases.

The measured improvement followed a real failed iteration: the first live run scored 87% for both systems. That run exposed a case-sensitive Kubernetes readiness-probe removal check and a false-positive policy where a quote-verified medium LLM hypothesis could change the merge gate without deterministic corroboration. The dataset was not changed; those workflow defects were fixed and the same-model benchmark was rerun.

The benchmark is executable from the UI or `POST /api/benchmarks/run-agentic`. Results are persisted and exportable as Markdown. A GitHub Actions workflow also produces `agentic-benchmark.json` and `agentic-benchmark.md` artifacts.

## Reproducibility

- setup: `REPRODUCE.md`;
- benchmark protocol: `docs/BENCHMARK_PROTOCOL.md`;
- improvement history: `IMPROVEMENT_CHANGELOG.md`;
- representative trajectories: `docs/TRAJECTORIES.md`;
- five-minute demo: `docs/DEMO_SCRIPT.md`.

Stored runs can export their trajectory, claims and evidence as JSON. Reports and benchmark results can also be exported directly from the application.

## End-to-end quality

A user can paste a real GitHub PR, inspect changed files and evidence, review rejected/advisory claims, inspect the agent trajectory, receive a final decision and explicitly publish the evidence-backed report back to the GitHub PR as a comment.

ChangeGuard never deploys infrastructure or applies Terraform/Kubernetes changes automatically.

## Removed / constrained experiment

The unconstrained free-form LLM reviewer was rejected as the final architecture because it could infer plausible repository/runtime context that was not actually present in the PR. The final design makes unsupported claims visible as rejected artifacts instead of hiding them.

A second constraint came directly from evaluation: **an exact quote is proof of provenance, not proof that the model's risk interpretation is correct**. Therefore a low/medium LLM-only hypothesis remains advisory. High/critical LLM-only findings are surfaced for human review but cannot autonomously produce BLOCK without deterministic corroboration.

## Main failure mode

ChangeGuard can miss risks that require runtime data or cross-repository context that is not available in the submitted PR. The system reports that limitation rather than inventing a blast radius.

## Hot take

> More context and more model authority did not automatically make the infrastructure agent safer. Reliability improved when the model generated hypotheses, evidence provenance was verified independently, and the final gate required stronger proof before making a consequential decision.
