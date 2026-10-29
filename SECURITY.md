# Security Policy

## Status

This repository currently contains a front-end prototype. It does not yet provide a production backend, authenticated accounts, a real AI provider integration, or verified secure storage. Do not enter secrets, credentials, or sensitive personal information into the demo.

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
- Treat user prompts, uploaded documents, retrieved passages, and tool results as untrusted data.
- Apply least privilege to tools and require explicit approval for consequential actions.
- Use request size limits, rate limiting, timeouts, and cost controls.
- Avoid logging secrets or unnecessary sensitive prompt/document contents.
- Provide data export and deletion, documented retention, and secure backup/restore.
- Pin and audit dependencies, run automated tests and security checks, and review deployment configuration.
