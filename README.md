# Personal AI Knowledge Assistant

A personal knowledge assistant project evolving from a standalone HTML concept into a small API-backed application. The API adds account sessions, per-user notes, and an optional OpenAI-compatible chat-completions endpoint.

> **Status: early development, not production-ready.** Authentication and notes are implemented as an initial vertical slice, but this is not yet a complete or independently security-reviewed product. Do not use it for highly sensitive information or critical decisions.

## Current capabilities

- FastAPI backend with a health endpoint.
- Email/password registration controlled by the server's `ALLOW_REGISTRATION` setting.
- PBKDF2-SHA256 password hashing and opaque server-validated sessions stored as hashed tokens.
- HttpOnly, SameSite=Strict session cookie; enable Secure cookies behind HTTPS.
- SQLite persistence with foreign-key constraints and indexes.
- Notes CRUD queries scoped to the authenticated user, including cross-account isolation checks in tests.
- User data export and password-confirmed account deletion, including cascading deletion of notes and sessions.
- Optional AI chat through a configurable OpenAI-compatible Chat Completions endpoint. Provider credentials remain server-side.
- Note excerpts are labelled as untrusted reference material; model answers are instructed to cite note IDs and acknowledge missing evidence.
- Security headers, request size check, basic per-process rate limits, safe provider/database error messages.
- Docker image runs as a non-root user.

## Run locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Set the variables from `.env.example` in your shell or deployment configuration. For local development, set:

- `APP_ORIGIN=http://127.0.0.1:8000`
- `ALLOW_REGISTRATION=true`
- `COOKIE_SECURE=false`

Then run:

```bash
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/` for the browser workspace and `http://127.0.0.1:8000/health` for the health check. Interactive API documentation is disabled by default.

## Configure an AI provider

Set these **on the server only**:

- `MODEL_API_URL`: full HTTPS URL for a compatible `/chat/completions` endpoint.
- `MODEL_API_KEY`: secret API key; never commit it or put it in browser JavaScript.
- `MODEL_NAME`: provider-supported model name.

The AI endpoint remains unavailable if the URL or key is missing. The application does not silently fabricate AI answers. A compatible provider may still receive the user question and selected note excerpts, so review its privacy and retention terms before enabling it.

## API overview

- `GET /health` — service status and whether AI settings exist (never returns credentials).
- `POST /api/auth/register` — create an account when registration is enabled.
- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.
- `GET /api/account/export` — download the signed-in user's notes and account data.
- `DELETE /api/account` — delete the signed-in account after password confirmation.
- `GET /api/notes`, `GET /api/notes/{id}`, `POST /api/notes`, `PUT /api/notes/{id}`, `DELETE /api/notes/{id}`.
- `POST /api/chat` — ask a question with excerpts from the signed-in user's matching notes.

Write requests validate browser Origin when present. Set `APP_ORIGIN` to the exact public origin. API clients that do not send an Origin header are supported; if you expose this API to untrusted clients, add an explicit API-client CSRF/authentication policy and network-level abuse controls.

## Tests

```bash
pytest -q
python -m unittest discover -s tests -v
```

Tests cover unauthenticated access, session logout, account isolation, note CRUD, origin checks, password policy, missing AI configuration, response security headers, data export, and account deletion.

## Production deployment checklist

Before public launch:
1. Set `COOKIE_SECURE=true`, `APP_ORIGIN` to the exact HTTPS origin, and `ALLOW_REGISTRATION=false` unless open registration is intentionally required.
2. Add a reviewed account bootstrap/invitation flow before disabling registration for all new installations.
3. Use durable private storage or a managed database; back up and test restore. SQLite on ephemeral container disks loses data on redeploy.
4. Add persistent distributed rate limiting, abuse detection, quotas, and provider spend limits; the current limiter is per-process only.
5. Configure trusted proxy handling correctly for the deployment; do not trust arbitrary forwarded headers.
6. Add password reset, email verification, session management/revocation UI, account deletion, and data export.
7. Add document upload/indexing only with file-type validation, malware scanning, storage limits, deletion propagation, and tenant isolation.
8. Review prompt-injection and retrieval-based data exfiltration risks; the current app intentionally has no tool execution.
9. Run dependency/security scanning, load tests, independent security review, deployment smoke tests, and backup/restore drills.
10. Configure logging and monitoring without recording secrets, passwords, session tokens, or unnecessary note contents.

See [SECURITY.md](SECURITY.md) and [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md). The new responsive interface at `web/index.html` is served by the API and supports sign-in, note CRUD, and chat. The original standalone HTML remains a separate design prototype.
