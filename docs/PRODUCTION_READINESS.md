# Production Readiness Checklist

This checklist is an engineering gate, not a claim that the listed controls already exist.

## Current verified baseline

- [x] Public GitHub repository is accessible.
- [x] A standalone HTML prototype exists.
- [x] Demo chat responses are simulated in client-side JavaScript.
- [x] Sample personal-data counts and insights are hard-coded in the interface.
- [ ] Real AI provider integration
- [ ] Backend API and server-side secret management
- [ ] Authentication and authorization
- [ ] Durable, access-controlled storage and per-user isolation
- [ ] Document ingestion, retrieval, and source citations
- [ ] User-controlled memory, export, and deletion
- [ ] Automated unit, integration, and end-to-end tests
- [ ] CI checks and dependency/security scanning
- [ ] Rate limiting, abuse controls, and operational monitoring
- [ ] Backup and restore test
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

**Current decision: NOT READY for production use with real or sensitive data.** This repository is currently a front-end prototype. Reassess this decision only after the unchecked controls are implemented, tested, and reviewed with evidence.
