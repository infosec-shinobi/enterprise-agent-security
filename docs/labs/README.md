# Hands-on lab roadmap

The labs build on Docker Compose incrementally. Lab 01 was completed successfully by a Windows PowerShell user. Lab 02 is an experimental SPIRE server/agent scaffold; Lab 03 is an unverified OpenBao policy/revocation exercise. Neither SPIFFE-to-OpenBao integration nor workload SVID retrieval is yet implemented. See the [cross-platform standard](cross-platform-standard.md).

| Lab | Scenario | Proof |
| --- | --- | --- |
| 01 | Registry and approval | Unregistered/unapproved agents denied |
| [02](../../labs/02-spiffe-spire/README.md) | SPIRE node bootstrap (experimental) | Workload SVID/impersonation test pending |
| [03](../../labs/03-openbao/README.md) | OpenBao policy and token revocation (experimental) | Scoped read allowed; other read denied; revoked token denied |
| 04 | Credential lifecycle | Scoped issuance and revocation |
| 05 | MCP tool governance | Unapproved tool denied |
| 06 | Human approval | High-impact action waits for approval |
| 07 | Prompt injection | Untrusted instructions cannot bypass authorization |
| 08 | Observability | End-to-end correlated trace |
| 09 | Emergency containment | Suspended agent denied with valid token |
| 10 | Retirement | Retired identity cannot reconnect |

Every lab should provide prerequisites, architecture, guided steps, attack/failure scenario, automated assertions, expected telemetry, evidence artifact and cleanup steps. All APIs and records are synthetic.
