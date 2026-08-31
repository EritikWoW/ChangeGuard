# Benchmark Protocol

ChangeGuard uses a fixed, labeled 15-case infrastructure-change dataset. The dataset contains safe, warning-level and blocking changes and includes 2 deliberately challenging cases that require more than trivial keyword matching.

## Official comparison

The submission benchmark compares two systems using the **same configured LLM model**:

1. **Baseline:** the raw change is sent to one general-purpose prompt that must return PASS/WARN/BLOCK and a reason.
2. **ChangeGuard:** deterministic checks run first, an LLM Risk Agent may propose additional risks, and every AI claim must include an exact evidence quote. The verifier checks whether that quote occurs in the referenced patch. Exact quote verification establishes provenance; it does not automatically give an LLM-only hypothesis authority to block a change.

The final decision policy is deliberately asymmetric:

- deterministic high/critical evidence can produce BLOCK;
- LLM-only low/medium findings remain advisory and do not change PASS;
- LLM-only high/critical findings produce WARN for human review rather than autonomous BLOCK;
- unmatched LLM claims are rejected.

This isolates workflow quality from model quality while keeping consequential decisions bounded by evidence.

## Primary metric

**Decision accuracy** against fixed ground truth.

Secondary metrics:
- danger detection;
- safe-change accuracy;
- evidence-linked vs rejected AI claims;
- token usage;
- performance on designated challenging cases.

## Official measured result

The final submission run used **GPT-5.6 Luna** for both baseline and ChangeGuard.

| Metric | Baseline | ChangeGuard |
|---|---:|---:|
| Decision accuracy | 87% | **100%** |
| Danger detection | 100% | **100%** |
| Safe-change accuracy | 80% | **100%** |

- Cases: **15**
- Challenging cases: **2**
- Decision-accuracy improvement: **+13 percentage points**
- Baseline token usage: **2,964**
- ChangeGuard token usage: **4,792**
- Evidence-linked AI claims: **13**
- Rejected unmatched AI claims: **0**

The first real run on the same dataset and same model scored **87% vs 87%**. That result was retained as an experiment rather than hidden. It exposed two workflow defects: a case-sensitive readiness-probe removal check and a false-positive decision policy for medium LLM-only hypotheses. After correcting those defects, the unchanged benchmark produced the final 87% vs 100% result.

## Reproduction

Configure an OpenAI-compatible provider in Settings and run **Run Agentic Benchmark** in the UI, or call:

```bash
curl -X POST http://127.0.0.1:8000/api/benchmarks/run-agentic
```

Export the latest result as Markdown:

```bash
curl http://127.0.0.1:8000/api/hackathon/benchmarks/latest.md
```

For the submission configuration, GitHub Actions can also run `.github/workflows/agentic-benchmark.yml` using the repository secret `OPENAI_API_KEY`; the workflow uploads the full JSON and Markdown outputs as the `changeguard-agentic-benchmark` artifact.

When reproducing the published score, keep the dataset, model and decision policy unchanged. Report a new result rather than replacing the historical run if any of those inputs change.
