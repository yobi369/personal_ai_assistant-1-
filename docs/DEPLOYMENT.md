# Deployment Guide

This guide helps run the application reproducibly. It does **not** certify the service as production-ready.

## Local development

1. Install Python 3.11 or newer.
2. Copy `.env.example` to `.env` and use local-only settings:
   - `APP_ORIGIN=http://127.0.0.1:8000`
   - `ALLOW_REGISTRATION=true`
   - `COOKIE_SECURE=false`
3. Optionally configure an HTTPS OpenAI-compatible `MODEL_API_URL`, `MODEL_API_KEY`, and `MODEL_NAME`. Keep real keys only in your local `.env` or hosting secret store.
4. Run `pip install -r requirements.txt` and `uvicorn app:app --reload`.
5. Open `http://127.0.0.1:8000/` and check `/health`.

For an optional local model, run an OpenAI-compatible local model server and point `MODEL_API_URL` at its loopback `/v1/chat/completions` endpoint. Because local endpoints use HTTP, `ALLOW_INSECURE_MODEL_URL=true` is required for that local-only setup. Never enable this flag for a publicly reachable endpoint.

Do not expose the local development server directly to the internet.

## Container smoke run

After creating a local `.env` with the development values above:

```bash
docker build -t personal-ai-assistant:local .
docker run --rm --name personal-ai-assistant \
  --env-file .env \
  -p 127.0.0.1:8000:8000 \
  -v personal-ai-assistant-data:/app/data \
  personal-ai-assistant:local
```

The named volume preserves the SQLite database across container recreation. Back it up regularly and test restoring a copy. The included CI workflow builds the image but does not publish or deploy it. After deployment, run `python scripts/smoke_test.py --url https://your-real-domain --require-ai --require-postgres --require-redis` to verify health, static assets, CSP, and required services. Remove flags for components you intentionally do not configure.

For SQLite, create a local backup with `python scripts/backup_db.py --source ./data/assistant.sqlite3 --backup-dir ./backups`. These scripts intentionally refuse PostgreSQL URLs; use your managed PostgreSQL provider's native backup/export and restore procedures instead. Store a second copy somewhere separate and access-controlled; a backup on the same host or volume is not disaster recovery. To restore, stop the app first, then run `python scripts/restore_db.py --source ./backups/<verified-backup>.sqlite3 --destination ./data/assistant.sqlite3 --backup-dir ./backups --confirm`. The restore script validates the source and creates a pre-restore backup of the current database when one exists.

## Before any public deployment

- Terminate HTTPS at a correctly configured reverse proxy and set `COOKIE_SECURE=true` and `APP_ORIGIN=https://your-real-domain`.
- Keep the service behind a trusted proxy/firewall; configure proxy trust explicitly before using forwarded headers.
- For a private installation, create the first account from a trusted shell with `python scripts/create_user.py`, then set `ALLOW_REGISTRATION=false` and restart the service. The script prompts for a password without echoing it. To recover an account from a trusted shell, run `python scripts/reset_password.py`; it resets the password and revokes existing sessions. The product does not yet provide email invitations or self-service email-based recovery.
- Use a durable, private disk with restricted access and verified backups. Set `DATABASE_URL` to a managed PostgreSQL connection string with TLS required (for example, include `sslmode=require`) to select the optional PostgreSQL adapter. The adapter creates the current schema on startup and CI tests it against PostgreSQL 16, but your managed provider's TLS settings, connection limits, and backup/restore procedures still need a smoke test. It does not migrate existing SQLite data. Validate backups before production. If using SQLite instead, use durable private storage; ephemeral container filesystems will lose user data on redeploy.
- Configure `REDIS_URL` to a Redis service for shared rate limits across workers; use `rediss://` for remote Redis endpoints. When Redis is configured, rate-limit failures fail closed with HTTP 503 instead of silently dropping to per-process limits.
- Configure the AI provider's privacy/retention settings, usage quotas, request limits, and spending alerts before enabling real user traffic.
- Add password reset/email verification, session revocation UI, persistent distributed rate limiting, monitoring, incident response, and dependency vulnerability scanning.
- Run a production-like smoke test, backup/restore drill, load test, and independent security review.

## Rollback

Keep a known-good image tag and a verified database backup before upgrading. Roll back the image first if the service fails its smoke tests; restore data only using a tested procedure appropriate to the backup and migration state.
