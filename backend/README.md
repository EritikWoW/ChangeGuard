# ChangeGuard backend v0.5.0

Python 3.14 + FastAPI backend.

## Run on Windows PowerShell

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000/

## What is live in v0.5

- GitHub PR analysis and saved history
- GitHub token configuration + connection test
- OpenAI-compatible LLM configuration + connection test
- Optional Risk Agent in PR analysis when an LLM API key is configured
- Evidence verifier accepts LLM claims only when its quoted evidence exists verbatim in the referenced diff
- Dashboard from saved SQLite analyses
- Analyses history/search/filter from SQLite
- Reports generated from saved runs + Markdown export
- Executable 10-case benchmark vs simple baseline
- Settings/policy persisted locally in SQLite

Secrets are stored locally in the ChangeGuard SQLite database for this hackathon/local prototype. Do not commit the database file.
