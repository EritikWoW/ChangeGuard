import re
from dataclasses import dataclass
import httpx
from app.core.config import settings
from app.services.config_store import config_store

PR_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


def parse_pr_url(url: str) -> PullRequestRef:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("Expected GitHub pull request URL: https://github.com/OWNER/REPO/pull/NUMBER")
    return PullRequestRef(match.group(1), match.group(2), int(match.group(3)))


class GitHubService:
    def __init__(self) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ChangeGuard/0.4",
        }
        token = config_store.get_all().get("github_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=settings.github_api_url,
            headers=headers,
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **params):
        response = await self._client.get(path, params=params or None)
        if response.status_code == 404:
            raise LookupError("Pull request or repository not found, or it is private and no GitHub token is configured")
        if response.status_code == 403:
            raise PermissionError("GitHub API access denied or rate limit exceeded. Configure CHANGEGUARD_GITHUB_TOKEN")
        response.raise_for_status()
        return response.json()

    async def get_pull_request(self, ref: PullRequestRef) -> dict:
        return await self._get(f"/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}")

    async def get_pull_files(self, ref: PullRequestRef) -> list[dict]:
        files: list[dict] = []
        page = 1
        while True:
            batch = await self._get(
                f"/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}/files",
                per_page=100,
                page=page,
            )
            files.extend(batch)
            if len(batch) < 100:
                break
            page += 1
            if page > 10:
                break
        return files
