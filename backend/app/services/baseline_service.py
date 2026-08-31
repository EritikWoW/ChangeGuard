import json
import re

import httpx

from app.services.config_store import config_store


BASELINE_SYSTEM = """You are a general-purpose infrastructure pull-request reviewer.
Review the supplied change and return strict JSON only:
{"decision":"pass|warn|block","reason":str}.
Use the diff provided. Do not call tools and do not ask for more context."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def review_case(title: str, path: str, patch: str) -> dict:
    """Single-prompt baseline using the same configured model as ChangeGuard."""
    cfg = config_store.get_all()
    key = cfg.get("llm_api_key")
    if not key:
        raise RuntimeError("LLM API key is required for the single-prompt baseline benchmark")

    base = (cfg.get("llm_base_url") or "").rstrip("/")
    body = {
        "model": cfg.get("llm_model"),
        "messages": [
            {"role": "system", "content": BASELINE_SYSTEM},
            {
                "role": "user",
                "content": f"PR title: {title}\nFILE: {path}\nPATCH:\n{patch}",
            },
        ],
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60, headers=headers) as client:
        response = await client.post(base + "/chat/completions", json=body)
    response.raise_for_status()
    payload = response.json()
    result = _extract_json(payload["choices"][0]["message"]["content"])
    decision = str(result.get("decision", "warn")).lower()
    if decision not in {"pass", "warn", "block"}:
        decision = "warn"
    return {
        "decision": decision,
        "reason": result.get("reason", ""),
        "tokens": (payload.get("usage") or {}).get("total_tokens"),
    }
