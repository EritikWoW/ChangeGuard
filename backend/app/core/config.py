from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChangeGuard"
    app_version: str = "0.6.0"
    github_token: str | None = None
    github_api_url: str = "https://api.github.com"
    request_timeout_seconds: float = 20.0
    database_path: str = "data/changeguard.db"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CHANGEGUARD_", extra="ignore")

    @property
    def frontend_dir(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def db_path(self) -> Path:
        path = Path(self.database_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
