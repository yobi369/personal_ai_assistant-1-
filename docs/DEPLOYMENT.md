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

For an optional local model, run an OpenAI-compatible local model server and point `MODEL_API_URL` at its loopback `/v1/chat/completions` endpoint. Because local endpoints use HTTP, `ALLOW_INSECURE_MODEL_URL=true` is required for that local-only setup. Never enable this flag for a publicly reachable endpoint.\n\nDo not expose the local development server directly to the internet.

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

The named volume preserves the SQLite database across container recreation. Back it up regularly and test restoring a copy. The included CI workflow builds the image but does not publish or deploy it.

## Before any public deployment

- Terminate HTTPS at a correctly configured reverse proxy and set `COOKIE_SECURE=true` and `APP_ORIGIN=https://your-real-domain`.
- Keep the service behind a trusted proxy/firewall; configure proxy trust explicitly before using forwarded headers.
- Set `ALLOW_REGISTRATION=false` after a reviewed account bootstrap/invitation process is available. The current product does not yet provide invitations or account bootstrap, so plan this carefully before disabling sign-up.
- Use a durable, private disk with restricted access and verified backups. The current database layer is SQLite; ephemeral container filesystems will lose user data on redeploy. A managed PostgreSQL adapter/migration is not implemented yet.
- Configure the AI provider's privacy/retention settings, usage quotas, request limits, and spending alerts before enabling real user traffic.
- Add password reset/email verification, session revocation UI, persistent distributed rate limiting, monitoring, incident response, and dependency vulnerability scanning.
- Run a production-like smoke test, backup/restore drill, load test, and independent security review.

## Rollback

Keep a known-good image tag and a verified database backup before upgrading. Roll back the image first if the service fails its smoke tests; restore data only using a tested procedure appropriate to the backup and migration state.
