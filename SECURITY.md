# Security

## Hackathon/local build

ChangeGuard does not execute infrastructure changes. It reviews diffs and produces recommendations.

GitHub and LLM credentials configured through the current local UI are stored in the local SQLite settings database and are masked in API responses. Do not commit the database or `.env` file.

## Production hardening

Before a production deployment:

- move credentials to an OS keychain or external secret manager;
- encrypt sensitive configuration at rest;
- use least-privilege GitHub tokens;
- add authentication/authorization around ChangeGuard itself;
- disable permissive CORS;
- add audit logging for configuration and GitHub review publication;
- use HTTPS and secure session handling.

## Reporting vulnerabilities

Please report security issues privately to the repository owner rather than opening a public issue containing exploit details.
