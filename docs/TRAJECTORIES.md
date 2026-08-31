# Representative Agent Trajectories

Every stored analysis exposes its execution path in the UI and through:

```text
GET /api/hackathon/analyses/{analysis_id}/trajectory.json
```

The export contains run metadata, ordered trajectory steps, claims and evidence. This is intended to satisfy the hackathon requirement that representative agent trajectories be inspectable rather than reconstructed after the fact.

A typical run contains:

1. **GitHub Collector** — reads PR metadata, changed files and patches.
2. **Change Parser** — normalizes infrastructure/configuration changes.
3. **Risk Rules** — evaluates deterministic safety patterns.
4. **Risk Agent** — proposes non-trivial risks when an LLM is configured.
5. **Verifier** — links each AI claim to exact submitted diff evidence and rejects unsupported claims.
6. **Decision** — produces PASS/WARN/BLOCK from the verified finding set.

The important property is not the number of stages. It is that an LLM hypothesis cannot become a blocking claim merely because another model agrees with it; the claim must survive evidence verification.
