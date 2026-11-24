# Enterprise Agent Security — development roadmap

## Vision

An interactive, local-first enterprise agent security playground with a vendor-neutral lifecycle framework, control catalog and ten hands-on labs. Three modes: manual (Bash and Windows PowerShell 5.1/7+), autopilot (real automated tests), and sandbox (controlled security experiments). No LLM required for core labs.

## Current baseline

- [x] Lab 01 manually completed by a Windows PowerShell user; other platforms and automation unverified.
- [x] Initial architecture and 30-control catalog published.
- [x] Lab 02 SPIRE bootstrap scaffold and Lab 03 OpenBao exercise published; execution unverified, SVID issuance and trust integration incomplete.
- [ ] Playground, runner, evidence dashboard and remaining labs not implemented.

## How we work

Pick one work ID per session. Read its dependencies, agree on the change, implement, review, run the smallest relevant test, record actual results and commit. Estimates are timeboxes, not guarantees; split unfinished tasks into smaller follow-ups. Do not mark a task complete solely because code was committed. Use GitHub issues optionally for discussion; this file is the canonical backlog. Update status and next action after each session.

**Next recommended task: A01 — Define manifest schema.** D01 and D04 can be picked independently for hands-on infrastructure sessions. Build the GUI MVP before expanding the remaining lab suite.

## Work packages

### A — Foundation and lab automation

| Status / ID | Task | Timebox | Depends on | Deliverable | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| Open · A01 | Define manifest schema | 30–45m | None | JSON Schema and example manifest | Valid manifest accepted; malformed manifest rejected |
| Open · A02 | Add Lab 01 manifest | 30m | A01 | Map existing scenarios to catalog IDs | All five gateway outcomes represented; IDs checked against catalog |
| Open · A03 | Build HTTP runner | 60–90m | A02 | Python runner with timeouts and token handling | Executes real HTTP requests; redacts tokens; distinguishes 401/403/503 |
| Open · A04 | Automate Lab 01 lifecycle | 60–90m | A03 | Setup, five assertions and cleanup | Fresh isolated state produces 403/403/200/403/403; repeatable |
| Open · A05 | Add evidence format and CLI | 45–60m | A04 | JSON results and CLI exit codes | Expected and actual status, timestamps, run ID and failure reason recorded |
| Open · A06 | Add regression tests | 45–90m | A05 | Unit tests and opt-in Compose integration test | Unit tests pass; integration result recorded separately |

### B — Playground MVP

| Status / ID | Task | Timebox | Depends on | Deliverable | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| Open · B01 | Scaffold dashboard and API | 60–90m | A01 | React/TypeScript and FastAPI skeleton | Local UI loads and API health endpoint responds |
| Open · B02 | Discover lab manifests | 45m | A02,B01 | Read-only lab catalog endpoint and cards | Lab 01 appears without hardcoded frontend metadata |
| Open · B03 | Service health view | 45–60m | B01 | Bounded probes and health cards | Running, unavailable and unknown states distinguished |
| Open · B04 | Run Lab 01 from UI | 60–90m | A05,B02 | Run endpoint and single-run lock | Click starts real runner; duplicate run rejected |
| Open · B05 | Stream run events | 60–90m | B04 | SSE endpoint and timeline | Ordered real events appear; disconnect/reconnect supported |
| Open · B06 | Show results and manual mode | 45–60m | B05 | Expected/actual results and manual instructions | UI displays pass/fail/error and links Bash/PowerShell guide |
| Open · B07 | Package MVP | 45–90m | B06 | Compose profile and startup docs | Localhost-only startup; Windows and Bash walkthroughs |

### C — Interactive sandbox

| Status / ID | Task | Timebox | Depends on | Deliverable | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| Open · C01 | Define switch semantics | 30–45m | B07 | Service availability vs enforcement vs fault model | Each switch has explicit effect, default and reset behavior |
| Open · C02 | Build safe control configuration API | 60–90m | C01 | Allowlisted settings, isolated sandbox and reset | No arbitrary shell commands or Docker socket; defaults secure |
| Open · C03 | Implement OPA outage scenario | 45–60m | C02 | Controlled dependency fault | Real request returns 503; never interpreted as policy deny |
| Open · C04 | Implement explicit enforcement bypass demo | 60–90m | C02 | Synthetic-only insecure sandbox mode | Warning shown; actual bypass tested; reset restores enforcement |
| Open · C05 | Add toggles and scenario presets | 45–90m | C03,C04 | UI controls with actual backend state | Switches reflect acknowledged state, not optimistic claims |
| Open · C06 | Add live topology | 60–90m | B05,C05 | React Flow nodes and event-linked edges | Real events highlight observed paths; unobserved paths marked unknown |
| Open · C07 | Add safe service provisioning design | 45–60m | C01 | Host CLI/allowlisted helper ADR | No unrestricted Docker socket or arbitrary commands; service start/stop deferred until reviewed |

### D — Identity and credentials

| Status / ID | Task | Timebox | Depends on | Deliverable | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| Open · D01 | Fix and smoke-test SPIRE bootstrap | 60–90m | None | Working server/agent Compose overlay | Fresh bootstrap succeeds; no unresolved token interpolation |
| Open · D02 | Register workload and fetch SVID | 60–90m | D01 | Constrained selector and workload client | Authorized workload gets SVID; unauthorized workload denied |
| Open · D03 | Validate SVID trust and expiry | 60–90m | D02 | Verifier and negative tests | Wrong identity/audience or expired credential rejected as applicable |
| Open · D04 | Complete OpenBao standalone lab | 45–90m | None | Test scoped token issuance and revocation | Allowed read 200; restricted and revoked reads denied |
| Open · D05 | Configure SPIRE to OpenBao trust | 60–90m | D03,D04 | JWT-SVID or certificate trust ADR and configuration | Correct identity obtains scoped token; wrong identity denied |
| Open · D06 | Test credential lifecycle | 60–90m | D05 | Expiry, rotation, stolen credential and suspension tests | Existing token behavior measured separately from new issuance |
| Open · D07 | Integrate Labs 02–04 with runner/UI | 60–90m | D06,B07 | Manifests, scenarios and visualization | Real results appear in UI; split into per-lab follow-up tickets if needed |

### E — Remaining lab suite

| Status / ID | Task | Timebox | Depends on | Deliverable | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| Open · E01 | Lab 05 MCP tool inventory and authorization | 60–90m | B07 | Minimal MCP service and policy test | Unapproved tool denied |
| Open · E02 | Lab 06 human approval | 60–90m | E01 | Approval state and protected action | High-impact action waits for valid approval |
| Open · E03 | Lab 07 prompt injection boundary | 60–90m | E01 | Synthetic malicious tool response and policy test | Untrusted instructions cannot grant permissions |
| Open · E04 | Lab 08 telemetry pipeline | 60–90m | B05 | OTel collector and initial trace correlation | Trace IDs correlate real events across components |
| Open · E05 | Lab 08 visualization and audit tests | 60–90m | E04 | Grafana or dashboard trace view | Missing telemetry identified; trace evidence exportable |
| Open · E06 | Lab 09 emergency containment | 60–90m | D06,E04 | Suspension and revocation scenario | Previously valid credential tested; propagation measured |
| Open · E07 | Lab 10 retirement and recertification | 60–90m | E06 | Retirement and orphan checks | Retired agent denied; residual credentials accounted for |
| Open · E08 | Integrate remaining labs in UI | 60–90m | E01,E02,E03,E05,E06,E07 | Per-lab manifests and runner adapters | Each lab has manual and automated paths; split by lab as needed |

### F — Evidence and release

| Status / ID | Task | Timebox | Depends on | Deliverable | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| Open · F01 | Map test results to control catalog | 45–60m | A05 | Evidence aggregation rules | Untested controls remain untested; no inferred pass |
| Open · F02 | Build control scorecard | 60–90m | F01,B07 | Control drilldown and coverage view | Latest result, test ID and timestamp visible |
| Open · F03 | Export evidence | 45–60m | F02 | JSON and Markdown export | No tokens or sensitive values in export |
| Open · F04 | Cross-platform validation | 60–90m | B07 | Windows/Linux/macOS test matrix | Actual platform results recorded; untested combinations labeled |
| Open · F05 | CI and release checklist | 60–90m | A06,F04 | CI, dependency checks and release notes | Tests run in CI; limitations documented |
| Open · F06 | Architecture and catalog review | 60–90m | F02 | Updated diagrams and advanced control backlog | Implemented vs proposed components clearly distinguished |

## Definition of done

- Small reviewable commit; documentation and relevant tests updated.
- Actual results recorded, including platform, expected/actual outcome and limitations.
- Manual commands follow the [cross-platform standard](docs/labs/cross-platform-standard.md).
- Each lab ultimately has manual instructions, manifest, automated assertions, evidence and visualization.
- Autopilot uses real service responses; simulated diagrams explicitly labeled.
- Service outage, policy denial and intentional enforcement bypass remain distinct.
- Localhost-only UI, synthetic data, secure defaults, bounded operations, no unrestricted Docker socket, no arbitrary command execution. Sandbox bypass never changes the default environment.
- No production readiness or control effectiveness claims without supporting evidence.

## Session log

| Session | Work ID | Outcome | Next action |
| --- | --- | --- | --- |
| Roadmap revision | Planning | Playground direction and backlog established | A01 |
