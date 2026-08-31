import json
import sqlite3
from app.core.config import settings

DEFAULTS = {
    "github_token": "",
    "default_repository": "",
    "llm_provider": "openai-compatible",
    "llm_base_url": "https://api.openai.com/v1",
    "llm_api_key": "",
    "llm_model": "gpt-5.6",
    "block_threshold": 85,
    "require_evidence": True,
    "reject_unsupported_blast_radius": True,
    "trajectory_logging": True,
}

class ConfigStore:
    def __init__(self):
        self.path = settings.db_path
        self._init()
    def _connect(self):
        conn=sqlite3.connect(self.path); conn.row_factory=sqlite3.Row; return conn
    def _init(self):
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS benchmark_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, payload TEXT NOT NULL)")
            conn.commit()
    def get_all(self):
        out=dict(DEFAULTS)
        with self._connect() as conn:
            for r in conn.execute("SELECT key,value FROM app_settings"):
                try: out[r['key']]=json.loads(r['value'])
                except Exception: out[r['key']]=r['value']
        # env token remains a fallback without exposing it
        if not out.get('github_token') and settings.github_token:
            out['github_token']=settings.github_token
        return out
    def update(self, values: dict):
        allowed=set(DEFAULTS)
        with self._connect() as conn:
            for k,v in values.items():
                if k not in allowed: continue
                conn.execute("INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,json.dumps(v)))
            conn.commit()
        return self.get_all()
    def public(self):
        d=self.get_all()
        return {
            **{k:v for k,v in d.items() if k not in {'github_token','llm_api_key'}},
            'github_configured': bool(d.get('github_token')),
            'github_token_masked': self._mask(d.get('github_token','')),
            'llm_configured': bool(d.get('llm_api_key')),
            'llm_api_key_masked': self._mask(d.get('llm_api_key','')),
        }
    @staticmethod
    def _mask(v):
        if not v: return ''
        return ('*'*8 + v[-4:]) if len(v)>4 else '*'*len(v)
    def save_benchmark(self, created_at, payload):
        with self._connect() as conn:
            conn.execute("INSERT INTO benchmark_runs(created_at,payload) VALUES(?,?)",(created_at,json.dumps(payload)))
            conn.commit()
    def latest_benchmark(self):
        with self._connect() as conn:
            row=conn.execute("SELECT payload FROM benchmark_runs ORDER BY id DESC LIMIT 1").fetchone()
        return json.loads(row['payload']) if row else None

config_store=ConfigStore()
