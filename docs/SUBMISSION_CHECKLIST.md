# Final Submission Checklist

## Code and engineering

- [x] Real GitHub PR ingestion
- [x] Deterministic infrastructure checks
- [x] Optional same-provider LLM Risk Agent
- [x] Exact evidence verification
- [x] Evidence-aware decision authority (LLM-only low/medium advisory; high/critical human review)
- [x] PASS / WARN / BLOCK decision
- [x] Persisted runs and reports
- [x] Representative trajectory export
- [x] Explicit GitHub PR review write-back
- [x] Python 3.14 CI
- [x] Clean Docker build verified by CI

## Evaluation

- [x] Fixed 15-case labeled dataset
- [x] Challenging cases included
- [x] Same-model single-prompt baseline implemented
- [x] Agentic benchmark implemented
- [x] Smoke benchmark for zero-cost CI/development
- [x] Benchmark Markdown export
- [x] Run the official agentic benchmark with the final submission model configuration (`gpt-5.6-luna`)
- [x] Record measured values: baseline **87%**, ChangeGuard **100%**, improvement **+13 pp**
- [x] Danger detection measured: **100% → 100%**
- [x] Safe-change accuracy measured: **80% → 100%**
- [x] Preserve the initial 87% → 87% run and resulting iteration in the Improvement Changelog

## Documentation

- [x] README
- [x] REPRODUCE.md
- [x] IMPROVEMENT_CHANGELOG.md
- [x] Architecture notes
- [x] Benchmark protocol
- [x] Representative trajectory documentation
- [x] Hackathon submission notes
- [x] Five-minute demo script
- [x] Security notes
- [x] Source-available evaluation license

## Final human actions

- [x] Configure the final LLM API key/model for the benchmark via GitHub Actions Secret
- [x] Run **Agentic Benchmark** and produce the JSON/Markdown artifact
- [ ] Copy the measured 87% → 100% (+13 pp) result into the HackerEarth submission form
- [ ] Pick one representative real PR run and export its trajectory
- [ ] Record the 5-minute demo using `docs/DEMO_SCRIPT.md`
- [ ] Upload/code-link the repository and video to HackerEarth before the deadline

The official benchmark artifact is produced by the `Agentic Benchmark` GitHub Actions workflow. The live application also exposes `GET /api/hackathon/submission-status` for a machine-readable readiness summary.
