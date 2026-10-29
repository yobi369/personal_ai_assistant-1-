# Production Readiness Checklist

This checklist is an engineering gate, not a claim that the listed controls already exist.

## Current verified baseline

- [x] Public GitHub repository is accessible.
- [x] A standalone HTML prototype exists.
- [x] Demo chat responses are simulated in client-side JavaScript.
- [x] Sample personal-data counts and insights are hard-coded in the interface.
- [x] Configurable OpenAI-compatible chat-completions integration (provider setup and real responses still require deployment configuration and tests)
- [ ] AI provider privacy review and retrieval/prompt-injection regression suite
- [x] Initial FastAPI backend and server-side model credential configuration
- [ ] Production secret manager and verified deployment configuration
- [x] Initial password authentication, hashed server-side sessions, and user-scoped note queries
- [x] Trusted-shell account bootstrap and password reset with session revocation
- [ ] Email verification, self-service password reset, session management UI, independent auth review
- [x] SQLite persistence for notes and conversations, with user-scoped reads/writes and isolation tests
- [x] Initial optional PostgreSQL adapter and schema bootstrap
- [ ] Managed-provider smoke test with TLS settings, SQLite-to-PostgreSQL migration plan, durable backup/restore drill, and external isolation review
- [x] Keyword-based retrieval of matching notes and source-note identifiers in chat responses
- [ ] Semantic/vector search, document ingestion, and independent citation-quality verification
- [x] Notes and conversation export plus password-confirmed account/notes/conversation deletion (AI memory beyond saved notes is not implemented)
- [ ] User-controlled AI memory beyond the notes store
- [x] API and prototype regression tests, PostgreSQL/Redis integration services, browser JavaScript syntax check, and container build in CI (check the current branch's latest run before release)
- [ ] Broader browser end-to-end, load, and independent security testing
- [x] Dependency vulnerability audit (`pip-audit`) and backend static security scan (`bandit`) in CI
- [x] Optional Redis-backed distributed rate limiting with fail-closed behavior when configured
- [ ] Configure managed Redis in production, abuse controls, provider quotas, and operational monitoring
- [x] SQLite backup/restore scripts with automated integrity tests
- [ ] Offsite backup and production restore drill
- [ ] Deployment smoke test and independent security review

## Release gates

### Product correctness
- Remove fabricated metrics and simulated answers from any production-facing workflow.
- Label demo data explicitly.
- Return citations for knowledge-base answers; say when evidence is insufficient.
- Test empty, large, malformed, and unsupported files.

### Identity and data protection
- Enforce tenant/user authorization on every server request.
- Test attempts to access another user's conversations, files, and memories.
- Keep API keys server-side and rotate any exposed credentials.
- Define retention, export, deletion, and backup policies.

### AI-specific controls
- Treat prompts, retrieved content, and tool output as untrusted.
- Do not use system prompts as access control.
- Validate tool arguments and enforce permissions outside the model.
- Require explicit, action-specific approval for external or destructive actions.
- Add prompt-injection and data-exfiltration regression tests.
- Bound token use, file size, request duration, and provider spend.

### Operations
- Run CI on every change.
- Add health/readiness endpoints and actionable, privacy-safe logs.
- Test backup restoration and document rollback.
- Verify the deployed build, domain, HTTPS, environment variables, and smoke tests.

## Release decision

**Current decision: NOT READY for production use with real or sensitive data.** The repository now includes an initial API and browser UI, but several production controls and independent verification are still missing. Reassess this decision only after the unchecked controls are implemented, tested, and reviewed with evidence.
