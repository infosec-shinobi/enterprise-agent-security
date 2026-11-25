# ADR-003 — Bounded service observations

Status: Accepted for B03; validation pending.

## Context
The host-side dashboard needs real observations without granting orchestration privileges. Compose publishes Keycloak, registry, gateway and optional OpenBao on loopback; OPA and SPIRE have no published host endpoint.

## Decision
Use immutable server-owned service definitions and async HTTP GET probes. Registry/gateway validate mode and ok, Keycloak checks realm OIDC metadata (not token issuance or management readiness), OpenBao checks active initialized unsealed status. OPA and SPIRE remain unknown; do not publish ports just to monitor them. No client-configurable targets, redirects, environment proxies, credentials, Docker socket, shell or response body exposure. Four concurrent connections, three-second total deadline per probe, 64 KiB raw response cap, identity encoding only, one snapshot at a time per process. Refresh on demand, no background polling or persistence. Unknown IDs return 404; overlapping requests return 429. All observations explicitly mark control effectiveness not assessed.

## Alternatives
Docker inspection would expose orchestration privileges and container state is not application health. TCP checks alone cannot distinguish wrong services. An internal collector or telemetry pipeline could observe internal dependencies but is deferred until packaging/topology design. User-configurable URLs create unnecessary SSRF risk.

## Consequences
Available means the expected endpoint contract responded, unavailable means the probe failed or returned non-200, unknown means no probe or an unrecognized response. None prove process identity, deployment provenance, successful authentication, authorization or dependency readiness. Loopback ports may belong to another process. A local malicious process can imitate the expected response. Observations are point-in-time and not evidence. The current single-process local development architecture is assumed; reassess concurrency and network perspective in B07. No Compose changes.
