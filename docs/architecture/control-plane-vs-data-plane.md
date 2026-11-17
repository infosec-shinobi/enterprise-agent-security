# Security control plane vs. execution / data plane

## The distinction

The **security control plane** manages the agent's authorized existence and permitted behavior: what is registered, approved, trusted, permitted, suspended, and retired.

The **execution / data plane** runs agents, calls models, invokes tools, and accesses enterprise resources. It contains enforcement points that act on control-plane decisions.

This is a **logical separation**, not necessarily a set of distinct clusters or networks.

| Component | Plane / function | Responsibility | Candidate implementation |
| --- | --- | --- | --- |
| Agent registry | Control: governance/lifecycle | Inventory, owner, purpose, version, approval, status | FastAPI + PostgreSQL |
| Identity & trust | Control: identity | Authenticate humans/services, establish workload identity, revoke trust | Keycloak, SPIRE |
| Policy decision point | Control: authorization | Decide whether an identified subject may perform a specific action on a resource in context | OPA; OpenFGA later |
| Lifecycle orchestration | Control: coordination | Propagate suspension, retirement, access and runtime changes | Registry events + controllers |
| Agent runtime | Data: execution | Plan and execute work | Python agent in Docker |
| Tool/MCP gateway | Data: enforcement | Verify identity, check policy, enforce decision, audit invocation | FastAPI proxy |
| Model gateway | Data: model access | Route and govern model calls, budgets and rate limits | LiteLLM |
| Enterprise API/data | Data: protected resource | Enforce resource-specific permissions and data boundaries | Synthetic REST API |
| Telemetry & response | Cross-cutting | Observe both planes; detect and coordinate containment | OpenTelemetry, Loki, Tempo, Grafana |

## Critical boundaries

**Identity is not authorization.** An authenticated agent can still be forbidden from deleting records.

**Decision is not enforcement.** OPA returns a decision; a gateway or API must enforce it. A policy engine outage must not silently allow protected operations.

**Registry status is not runtime state.** Changing an agent to `suspended` must cause policy denial and appropriate runtime/credential action. Stopping a container alone does not invalidate previously issued credentials.

**Model governance is not tool governance.** LiteLLM may control model requests; a separate tool/API boundary must authorize tool actions and data access.

**Observability is not prevention.** Logs and traces record what happened; a policy enforcement point prevents prohibited actions before execution.

**Control plane compromise matters.** Protect registry writes, policy changes, signing keys, and response APIs with distinct administrative roles, audit logs, and change review.

## Example request path

1. Agent is registered and approved, with an accountable owner and allowed capabilities.
2. Agent authenticates with a distinct identity. Later labs use SPIRE for workload attestation.
3. Agent requests `records:read` through a protected tool gateway.
4. Gateway validates the identity and sends subject, action, resource, agent version, lifecycle state, and request context to the policy decision point.
5. Policy allows only if registration/approval and resource-level permission are satisfied.
6. Gateway enforces allow/deny; protected API must not be reachable through a bypass route.
7. Logs and traces correlate identity, policy version, decision, resource and result.
8. On suspension, the next request is denied even if a token has not expired. Credential revocation and runtime containment follow; their completion is independently checked.

## Control-plane and data-plane failure scenarios

| Scenario | Expected secure behavior |
| --- | --- |
| OPA unreachable | Protected action fails closed |
| Registry unreachable | Defined cached-policy behavior with bounded freshness; fail closed when state cannot be trusted |
| Token valid, agent suspended | Deny at action boundary |
| Agent bypasses gateway | Network isolation / API-side enforcement denies direct access |
| Model prompt instructs tool misuse | Tool gateway evaluates independently of model text |
| Agent container terminated | Existing credentials are still revoked or bounded; termination alone is insufficient |
| Telemetry unavailable | Security-critical audit path has an explicit buffering / fail-mode policy; never silently report evidence as complete |

## Trust and evidence

Each authorization test should emit an evidence record with: agent ID, workload identity, action, resource, lifecycle state, policy version, decision, enforcement outcome, timestamp, trace ID, and test case ID. Avoid storing raw secrets, unnecessary personal data, or full sensitive prompts.

## Design caution

The phrase **agent control plane** is not a universally fixed product boundary. Some products combine gateways, registries, identity, policy, and monitoring. This project uses a transparent logical taxonomy to compare implementations without assuming one vendor's packaging.
