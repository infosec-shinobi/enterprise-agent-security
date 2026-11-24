# ADR-001 — Playground application technology stack

- Status: Accepted (existing B01 implementation)
- Date: 2026-11-24
- Scope: Enterprise Agent Security Playground
- Related work: B01–B07, C01–C07, F01–F03, G01–G06

## Context

The project is an interactive learning and security-control validation platform backed by real lab infrastructure, not merely a documentation site or reporting dashboard. The existing Python CLI, manifest validator, lifecycle runner and evidence collector must remain independently usable.

B01 needs only navigation, theme management and API connectivity. Future requirements include dynamic lab discovery, live execution events, interactive topology, controlled security experiments, evidence exploration and versioned framework views. The project should remain lightweight enough for local development and homelab deployment, accessible to contributors, and maintainable as an open-source security project.

## Decision

Retain React and TypeScript for the browser UI, Vite for development and static asset builds, and FastAPI/Pydantic for the Python application API. Use plain CSS initially. Keep the versioned API and execution engine independent of the frontend. Canonical control IDs remain authoritative; external framework mappings are separate backend data contracts, not frontend-specific execution logic.

React provides component composition and declarative synchronization of changing UI state. TypeScript catches contract and state errors at build time but does not replace runtime validation. Vite provides development reloads, API proxying and optimized static builds; Node.js need not be a runtime dependency in a packaged deployment.

## Alternatives considered

| Alternative | Benefits | Tradeoffs and rationale |
| --- | --- | --- |
| Vanilla HTML/CSS/JavaScript | Minimal dependencies, no required frontend build, sufficient for B01 | Complex shared state, component lifecycle and interactive topology would require more custom implementation. Viable if scope remains simple. |
| FastAPI + Jinja2 + HTMX | Python-first, server-rendered HTML, simpler deployment and fewer frontend dependencies | Strongest alternative for catalog, instructions and scorecards; richer client-side topology and synchronized sandbox interactions would still need JavaScript. |
| NiceGUI | Python-first interactive UI, rapid prototyping | Additional framework abstraction and less direct control over browser-side architecture. |
| Streamlit / Dash / Gradio | Rapid dashboards, analytics or AI demonstrations | Less natural fit for the intended custom multi-workspace security engineering application; not inherently incapable of these features. |
| React + TypeScript + Vite | Reusable components, typed contracts, ecosystem for interactive graphs and streaming interfaces | Additional language, build toolchain, dependencies and contributor learning curve. Selected for anticipated complexity rather than current B01 needs. |

## Consequences

Positive: independent CLI/API usage, reusable UI components, explicit frontend contracts, flexibility to replace the frontend, and access to graph libraries such as React Flow if justified later.

Negative: npm supply-chain exposure, two development toolchains, dependency upgrades and additional build/testing requirements. React does not guarantee maintainability or security.

Mitigations:
- Minimize dependencies; review and commit the npm lockfile, use reproducible installs and audit dependencies. Python transitive locking also remains outstanding.
- Validate API responses and backend inputs at runtime; never trust client-side types or state as enforcement.
- Render actual backend observations and distinguish unavailable, unknown, denied and failed states. Mocked results must not be presented as real evidence.
- Keep security policy, credentials, execution and evidence validation in the backend or lab services. Do not expose arbitrary commands or unrestricted Docker socket access.
- Bind development services to loopback. B01 has no application authentication; do not expose it to other machines.
- Avoid adding state-management libraries, component frameworks or databases until justified.

## Deployment

Current B01 development uses Vite on 127.0.0.1:5173 with a same-origin /api proxy to FastAPI on 127.0.0.1:8090. Existing lab ports are unchanged. In B07, evaluate building static frontend assets and serving them through FastAPI or a dedicated static server. A Node.js runtime is not required for static assets. Packaging and safe host-runner integration remain separate decisions.

## Validation and review

B01 was validated by the user on Windows: all 14 acceptance checks passed, including four API tests, frontend build, navigation, theme persistence, backend failure/recovery and existing regression tests. Linux/macOS validation, dependency audit and lockfile review remain outstanding. No comparative performance benchmark was performed.

Revisit this decision if the interactive sandbox/topology scope is substantially reduced, frontend maintenance becomes disproportionate, deployment constraints change, or dependency risk cannot be managed. Prefer a superseding ADR rather than silently rewriting the decision.

## References

- [Dashboard implementation and startup](../../dashboard/README.md)
- [Project roadmap](../../ROADMAP.md)
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vite.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [HTMX](https://htmx.org/)
