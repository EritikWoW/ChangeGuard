# Final Submission Checklist

## Code and engineering

- [x] Real GitHub PR ingestion
- [x] Deterministic infrastructure checks
- [x] Optional same-provider LLM Risk Agent
- [x] Exact evidence verification
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
- [ ] Run the official agentic benchmark with the final submission LLM/model configuration
- [ ] Copy the resulting measured values into the HackerEarth submission/video narrative

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

- [ ] Configure the final LLM API key/model in ChangeGuard Settings
- [ ] Run **Agentic Benchmark** and export the report
- [ ] Pick one representative real PR run and export its trajectory
- [ ] Record the 5-minute demo using `docs/DEMO_SCRIPT.md`
- [ ] Upload/code-link the repository and video to HackerEarth before the deadline

The live application also exposes `GET /api/hackathon/submission-status` for a machine-readable readiness summary.
