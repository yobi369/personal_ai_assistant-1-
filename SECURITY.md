# Security Policy

## Status

This repository now includes an early FastAPI backend, account sessions, user-scoped notes and conversations, data export/deletion, and an optional OpenAI-compatible provider adapter. It is **not production-ready or independently security-reviewed**. Provider credentials and production storage have not been configured or verified in a live deployment. Do not use highly sensitive personal information or rely on it for critical decisions.

## Reporting a vulnerability

Please do not publish exploitable details in a public issue. Contact the repository maintainer privately through GitHub's available security reporting channel, if enabled, or request a private contact route.

Include:
- A concise description and potential impact
- Reproduction steps or a minimal proof of concept
- Affected commit, file, and environment
- Any suggested mitigation

Do not access, alter, or retain data belonging to other people while investigating.

## Security requirements before production

- Keep model-provider keys and other secrets on the server, never in browser code or committed files.
- Enforce authentication, authorization, and per-user data isolation server-side.
- Validate inputs and outputs; render untrusted text safely.
- Keep browser assets external and use a restrictive Content Security Policy to reduce inline-script injection risk.
- Treat user prompts, uploaded documents, retrieved passages, and tool results as untrusted data.
- Apply least privilege to tools and require explicit approval for consequential actions.
- Use request size limits, rate limiting, timeouts, and cost controls.
- Avoid logging secrets or unnecessary sensitive prompt/document contents.
- Provide data export and deletion, documented retention, and secure backup/restore. Export/deletion controls exist for the current notes and conversations, but retention and backup/restore still require deployment-level implementation.
- Pin and audit dependencies, run automated tests and security checks, and review deployment configuration. CI runs regression tests and builds the container; independent security review and production smoke tests remain outstanding.
