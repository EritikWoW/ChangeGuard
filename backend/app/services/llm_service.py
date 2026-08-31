import json, re
import httpx
from app.services.config_store import config_store

SYSTEM = """You are ChangeGuard Risk Agent. Review ONLY the supplied pull-request diff excerpts for infrastructure/deployment risk. Do not invent repository context. Return strict JSON only: {\"risks\":[{\"title\":str,\"detail\":str,\"severity\":\"low|medium|high|critical\",\"file\":str,\"evidence_quote\":str,\"recommendation\":str}],\"summary\":str}. evidence_quote must be a short exact substring copied from the supplied patch. If there is no defensible risk, return an empty risks array."""

def _extract_json(text: str):
    text=text.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*','',text); text=re.sub(r'\s*```$','',text)
    return json.loads(text)

def _raise_api_error(response: httpx.Response) -> None:
    if response.is_success:
        return
    try:
        detail = response.json().get('error', {}).get('message') or response.text
    except Exception:
        detail = response.text
    raise RuntimeError(f"LLM API HTTP {response.status_code}: {detail[:800]}")

async def analyze_with_llm(title: str, files: list[dict]):
    cfg=config_store.get_all()
    if not cfg.get('llm_api_key'):
        return None
    excerpts=[]; total=0
    for f in files:
        patch=f.get('patch') or ''
        if not patch: continue
        # Prioritize config / IaC and cap request size.
        path=f.get('filename','')
        relevant=path.endswith(('.yaml','.yml','.tf','.tfvars')) or path.lower().endswith(('dockerfile','containerfile')) or '.github/workflows/' in path
        if not relevant and len(excerpts)>=4: continue
        chunk=patch[:7000]
        if total+len(chunk)>30000: break
        excerpts.append(f"FILE: {path}\nPATCH:\n{chunk}"); total+=len(chunk)
        if len(excerpts)>=12: break
    if not excerpts: return {'risks':[],'summary':'No diff excerpts suitable for LLM review.'}
    body={
        'model':cfg.get('llm_model'),
        'messages':[
            {'role':'system','content':SYSTEM},
            {'role':'user','content':f"PR title: {title}\n\n"+'\n\n'.join(excerpts)}
        ],
        'reasoning_effort':'low',
        'response_format':{'type':'json_object'},
    }
    headers={'Authorization':f"Bearer {cfg['llm_api_key']}",'Content-Type':'application/json'}
    base=(cfg.get('llm_base_url') or '').rstrip('/')
    async with httpx.AsyncClient(timeout=60,headers=headers) as client:
        r=await client.post(base+'/chat/completions',json=body)
    _raise_api_error(r)
    payload=r.json()
    content=payload['choices'][0]['message']['content']
    result=_extract_json(content)
    usage=payload.get('usage') or {}
    result['_usage']={'tokens':usage.get('total_tokens')}
    return result
