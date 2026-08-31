# Architecture

## Workflow

```mermaid
flowchart TD
  PR[GitHub Pull Request] --> GC[GitHub Collector]
  GC --> CP[Change Parser]
  CP --> RR[Deterministic Risk Rules]
  CP --> RA[Risk Agent]
  RR --> ES[Evidence Set]
  RA --> EV[Evidence Verifier]
  EV --> ES
  ES --> DE[Decision Engine]
  DE --> OUT[PASS / WARN / BLOCK]
  OUT --> DB[(SQLite)]
  DB --> UI[Dashboard / Analyses / Reports / Benchmarks]
```

## Design principle

LLM output is advisory until verified. Risk Agent candidates must include a file path and an exact evidence quote. The verifier checks that quote against the collected patch before the claim is allowed into the supported evidence set.

## Deterministic layer

Current rules cover representative high-impact changes in:

- Kubernetes YAML;
- Terraform;
- Dockerfiles / Containerfiles;
- GitHub Actions workflows.

The deterministic layer is intentionally auditable and provides a stable fallback when no LLM is configured.

## Persistence

SQLite stores analyses, settings and benchmark runs. Secrets are excluded from public settings API responses, but production deployments should use a dedicated secret store.
