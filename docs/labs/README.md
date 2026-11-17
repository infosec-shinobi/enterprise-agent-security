# Hands-on lab roadmap

The first release will build one Docker Compose environment incrementally. Labs are planned, not yet deployable.

| Lab | Scenario | Proof |
| --- | --- | --- |
| 01 | Registry and approval | Unregistered/unapproved agents denied |
| 02 | Workload identity | Impersonation rejected |
| 03 | Tool authorization | Read allowed; delete denied |
| 04 | Credential lifecycle | Scoped issuance and revocation |
| 05 | MCP tool governance | Unapproved tool denied |
| 06 | Human approval | High-impact action waits for approval |
| 07 | Prompt injection | Untrusted instructions cannot bypass authorization |
| 08 | Observability | End-to-end correlated trace |
| 09 | Emergency containment | Suspended agent denied with valid token |
| 10 | Retirement | Retired identity cannot reconnect |

Every lab should provide prerequisites, architecture, guided steps, attack/failure scenario, automated assertions, expected telemetry, evidence artifact and cleanup steps. All APIs and records are synthetic.
