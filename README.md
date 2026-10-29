# Personal AI Knowledge Assistant

A privacy-conscious personal knowledge assistant concept focused on helping people organize notes and documents, explore information, and work with their own knowledge base.

> **Project status:** prototype / development foundation. The current HTML interface includes simulated insights and canned chat responses. It is not yet a connected AI system, and its sample data is illustrative rather than real user data. Do not rely on the current interface for real decisions or sensitive information.

## Product direction

- **Local-first by default:** keep personal notes and documents under the user's control wherever feasible.
- **Grounded answers:** when retrieval is implemented, cite the documents or passages used and clearly state when evidence is missing.
- **User-controlled memory:** provide inspect, edit, export, and delete controls for saved memories.
- **Least-privilege tools:** tools should have explicit permissions; require confirmation before sending messages, modifying files, or taking other consequential actions.
- **Transparent operation:** distinguish real integrations and computed metrics from demo content.

## Current repository

- `personal_ai_assistant (1).html` — standalone visual prototype.
- `AI Personal Knowledge Assistant - Documentation.pdf` — original project documentation.

## Development roadmap

1. Replace demo-only responses and fabricated metrics with clearly labelled sample states and real application state.
2. Establish a maintainable app structure, dependency management, formatting/linting, automated tests, and CI.
3. Implement a secure server/API boundary and a configurable model-provider interface; never expose provider keys in browser code.
4. Add authenticated user data isolation, persistent storage, document ingestion, retrieval, and source-linked answers.
5. Implement privacy controls, export/deletion, retention settings, and safe logging.
6. Add rate limits, input and output validation, prompt-injection defenses, least-privilege tool execution, and approval gates for consequential actions.
7. Verify deployment, backup/restore, monitoring, and security tests before making production claims.

## Security principles

Follow the current [OWASP GenAI security guidance](https://genai.owasp.org/) for prompt injection, sensitive information disclosure, excessive agency, supply-chain risk, and unbounded consumption. Model instructions are not an authorization boundary: enforce access control in application code.

See [SECURITY.md](SECURITY.md) and [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md).

## Running the prototype

Open `personal_ai_assistant (1).html` in a modern browser. The current interface is a front-end demonstration only; chat responses are simulated and no AI provider or document index is connected.

## Production readiness

This repository is **not certified production-ready**. A real deployment requires implementation and verification of authentication, persistence, data isolation, provider integration, automated tests, deployment controls, and operational recovery procedures. See the readiness checklist before using real personal data.
