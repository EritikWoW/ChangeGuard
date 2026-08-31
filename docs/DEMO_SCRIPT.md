# 5-minute Demo Script

## 0:00–0:35 — Problem
Show a small infrastructure PR. Explain that generic AI review is fast but may invent dependencies or risks that are not supported by the change.

## 0:35–1:05 — Baseline
Open **Benchmarks**. Explain the baseline: same LLM, one prompt, one decision. Emphasize that model choice is held constant.

## 1:05–2:35 — Real end-to-end run
Paste a real GitHub PR URL into **New Analysis**. Show changed files, diff, deterministic findings, Risk Agent, Evidence, rejected claims, trajectory and final PASS/WARN/BLOCK decision.

Click an evidence item to jump to its source diff. Export the trajectory JSON briefly to demonstrate auditability.

## 2:35–3:15 — Verification
Show a rejected AI claim. Explain: ChangeGuard allows the model to propose a risk, but not to invent proof. Claims without exact evidence do not influence a blocking decision.

## 3:15–4:05 — Measured improvement
Run **Agentic Benchmark**. Show the 15 fixed cases, ground-truth decisions, baseline score, ChangeGuard score, challenging cases, supported/rejected AI claims and token usage.

Do not quote a pre-recorded number; show the result produced by the run used for submission.

## 4:05–4:40 — Improvement changelog
Open `IMPROVEMENT_CHANGELOG.md`. Cover the progression from a single prompt to deterministic parsing, evidence IDs, risk generation and verification. Mention the constrained experiment: unconstrained repository-wide context increased plausible but unsupported claims.

## 4:40–5:00 — Hot take
> More context did not automatically make the infrastructure agent safer. Reliability improved when the system forced every consequential claim to carry evidence that an independent verifier could check.

Close on the final decision and GitHub review write-back.
