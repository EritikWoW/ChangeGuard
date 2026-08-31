# Reproduction Guide

This guide is written for a clean environment.

## Requirements

- Python 3.14, or Docker
- Internet access for GitHub PR analysis
- Optional GitHub PAT for private repositories / higher rate limits
- OpenAI-compatible API key for the official agentic benchmark

## Install

### Windows PowerShell

```powershell
git clone https://github.com/EritikWoW/ChangeGuard.git
cd ChangeGuard\backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

### Linux/macOS

```bash
git clone https://github.com/EritikWoW/ChangeGuard.git
cd ChangeGuard/backend
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
cp .env.example .env
```

## Run

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected health response at `http://127.0.0.1:8000/api/health`:

```json
{"status":"ok","service":"ChangeGuard","version":"0.6.0"}
```

Open `http://127.0.0.1:8000/`.

## Docker

From the repository root:

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8000/`. SQLite data is persisted in a named Docker volume.

## Run tests

```bash
cd backend
python -m pytest -q
```

GitHub Actions runs the same Python 3.14 test suite and also verifies that the Docker image builds from a clean checkout.

## Reproduce a GitHub analysis

1. Open **New Analysis**.
2. Paste a GitHub pull-request URL.
3. Run the analysis.
4. Inspect changed files, evidence, rejected claims, decision and trajectory.
5. Export the trajectory JSON if needed.
6. Re-run the same analysis to test repeatability against the same PR state.
7. With a configured GitHub token, **Create GitHub Review** explicitly publishes the evidence-backed report as a PR comment.

## Run benchmarks

### Zero-cost smoke benchmark

Use **Run Smoke Benchmark** or:

```bash
curl -X POST http://127.0.0.1:8000/api/benchmarks/run
```

This is intended for development and CI sanity checking. It is not the official hackathon comparison.

### Official same-model agentic benchmark

Configure one fixed OpenAI-compatible model in **Settings → LLM Provider**, then use **Run Agentic Benchmark** or:

```bash
curl -X POST http://127.0.0.1:8000/api/benchmarks/run-agentic
```

The same model is used for the single-prompt baseline and the final ChangeGuard workflow across the same 15 labeled cases.

Export the latest benchmark result:

```bash
curl http://127.0.0.1:8000/api/hackathon/benchmarks/latest.md
```

See `docs/BENCHMARK_PROTOCOL.md` for metric definitions.

## Runtime and cost

Deterministic-only analysis uses no LLM tokens. Agentic runtime/cost depends on the configured provider, model and PR size. Benchmark output records baseline and ChangeGuard token usage when the provider reports it.
