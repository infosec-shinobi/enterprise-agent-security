# Reference architecture

The architecture has a **governance/lifecycle**, **identity/trust**, and **policy/authorization** control plane; an **agent execution/data plane**; and **cross-cutting observability and response**.

See [control plane vs data plane](control-plane-vs-data-plane.md) for precise responsibilities and failure modes, and [agent lifecycle](agent-lifecycle.md) for the chronological view.

```mermaid
flowchart TB
  subgraph C["CONTROL PLANE"]
    G["Registry / governance / approvals"]
    I["Identity & trust: Keycloak + SPIRE"]
    P["Policy decisions: OPA + optional OpenFGA"]
    L["Lifecycle / response orchestration"]
    G --> I
    G --> P
    G --> L
  end
  subgraph D["DATA PLANE"]
    A["Agent runtime"]
    T["Tool / MCP policy enforcement point"]
    M["Model gateway: LiteLLM"]
    R["Protected synthetic enterprise API"]
    A --> T --> R
    A --> M
  end
  I -. "authentication / trust" .-> T
  P -. "authorization decisions" .-> T
  L -. "suspend / contain" .-> A
  L -. "deny access" .-> T
  O["CROSS-CUTTING: OpenTelemetry / Loki / Tempo / Grafana"]
  A --> O
  T --> O
  M --> O
  G --> O
```

### Important deployment details

- The gateway and protected API must reject direct bypass traffic.
- Policy decisions must be bound to the authenticated workload and requested resource.
- Registry approval is necessary but not sufficient for access.
- Revocation is not assumed instantaneous: measure time-to-denial and document residual risks from cached tokens or decisions.
- All example data is synthetic.
- Docker Compose is the baseline; Kubernetes extensions can be added later.
