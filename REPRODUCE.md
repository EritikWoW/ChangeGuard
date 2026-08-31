# Reproduction Guide

This guide is written for a clean environment.

## Requirements

- Python 3.14
- Internet access for GitHub PR analysis
- Optional GitHub PAT for private repositories / higher rate limits
- Optional OpenAI-compatible API key for agentic analysis

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
{"status":"ok","service":"ChangeGuard","version":"0.5.0"}
```

Open `http://127.0.0.1:8000/`.

## Run tests

```bash
python -m pytest -q
```

## Reproduce a GitHub analysis

1. Open **New Analysis**.
2. Paste a GitHub pull-request URL.
3. Run the analysis.
4. Inspect changed files, evidence, rejected claims, decision and trajectory.
5. Re-run the same analysis to test repeatability against the same PR state.

## Run the benchmark

Open **Benchmarks** and click **Run Benchmark**. The backend executes the benchmark suite and persists the generated result in SQLite.

For hackathon reporting, use one fixed LLM model/configuration when comparing a single-prompt baseline with the final agentic workflow.

## Runtime and cost

Deterministic-only analysis uses no LLM tokens. Agentic runtime/cost depends on the configured provider, model and PR size. Run details record model and token usage when the provider reports it.
