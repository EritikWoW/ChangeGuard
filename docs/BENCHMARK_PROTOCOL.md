# Benchmark Protocol

ChangeGuard uses a fixed, labeled 15-case infrastructure-change dataset. The dataset contains safe, warning-level and blocking changes and includes deliberately challenging cases that require more than trivial keyword matching.

## Official comparison

The submission benchmark compares two systems using the **same configured LLM model**:

1. **Baseline:** the raw change is sent to one general-purpose prompt that must return PASS/WARN/BLOCK and a reason.
2. **ChangeGuard:** deterministic checks run first, an LLM Risk Agent may propose additional risks, and every AI claim must include an exact evidence quote. The verifier only promotes claims whose quote occurs in the referenced patch.

This isolates workflow quality from model quality.

## Primary metric

**Decision accuracy** against fixed ground truth.

Secondary metrics:
- danger detection;
- safe-change accuracy;
- supported vs rejected AI claims;
- token usage;
- performance on designated challenging cases.

## Reproduction

Configure an OpenAI-compatible provider in Settings and run **Run Agentic Benchmark** in the UI, or call:

```bash
curl -X POST http://127.0.0.1:8000/api/benchmarks/run-agentic
```

Export the latest result as Markdown:

```bash
curl http://127.0.0.1:8000/api/hackathon/benchmarks/latest.md
```

No benchmark score should be quoted in a submission until this official same-model benchmark has actually been executed and saved.
