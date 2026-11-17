# Foundational enterprise agent security control matrix

**Scope:** 30 proposed controls. Product entries are *candidate integrations*, not certifications or claims of native feature parity. Many require custom glue and configuration. Initial lab coverage is illustrative, not evidence of validated implementation.

| ID | Control | Control-plane / data-plane enforcement | Open-source candidates | Commercial candidates | Initial lab |
|---|---|---|---|---|---|
| REG-01 | Agent inventory | Registry / admission workflow | FastAPI registry, Backstage | ServiceNow, Microsoft Entra Agent ID | initial lab coverage |
| REG-02 | Accountable ownership | Registry / admission workflow | FastAPI registry, Backstage | ServiceNow, Microsoft Entra Agent ID | planned |
| REG-03 | Risk classification | Registry / admission workflow | FastAPI registry, Backstage | ServiceNow, Microsoft Entra Agent ID | planned |
| REG-04 | Approval gate | Registry / admission workflow | FastAPI registry, Backstage | ServiceNow, Microsoft Entra Agent ID | initial lab coverage |
| IAM-01 | Unique workload identity | Identity provider / API authentication | Keycloak, SPIRE, OpenBao | Okta, Microsoft Entra, CyberArk | planned |
| IAM-02 | Verified authentication | Identity provider / API authentication | Keycloak, SPIRE, OpenBao | Okta, Microsoft Entra, CyberArk | initial lab coverage |
| IAM-03 | Credential expiry and rotation | Identity provider / API authentication | Keycloak, SPIRE, OpenBao | Okta, Microsoft Entra, CyberArk | planned |
| IAM-04 | Identity revocation | Identity provider / API authentication | Keycloak, SPIRE, OpenBao | Okta, Microsoft Entra, CyberArk | planned |
| AUTH-01 | Least privilege | Tool gateway / protected API | OPA, OpenFGA, Envoy | AWS Verified Permissions, Cerbos Hub, Kong | planned |
| AUTH-02 | Tool/action authorization | Tool gateway / protected API | OPA, OpenFGA, Envoy | AWS Verified Permissions, Cerbos Hub, Kong | initial lab coverage |
| AUTH-03 | Resource-scoped authorization | Tool gateway / protected API | OPA, OpenFGA, Envoy | AWS Verified Permissions, Cerbos Hub, Kong | planned |
| AUTH-04 | Default-deny enforcement | Tool gateway / protected API | OPA, OpenFGA, Envoy | AWS Verified Permissions, Cerbos Hub, Kong | initial lab coverage |
| RUN-01 | Artifact provenance | Build pipeline / runtime | Sigstore Cosign, Docker, Cilium | Wiz, Prisma Cloud, CrowdStrike | planned |
| RUN-02 | Runtime isolation | Build pipeline / runtime | Sigstore Cosign, Docker, Cilium | Wiz, Prisma Cloud, CrowdStrike | planned |
| RUN-03 | Network segmentation | Build pipeline / runtime | Sigstore Cosign, Docker, Cilium | Wiz, Prisma Cloud, CrowdStrike | planned |
| TOOL-01 | Tool inventory | Tool gateway / protected API | MCP gateway, Pydantic, Presidio, OPA | Kong, Apigee, Microsoft Purview | planned |
| TOOL-02 | Input/schema validation | Tool gateway / protected API | MCP gateway, Pydantic, Presidio, OPA | Kong, Apigee, Microsoft Purview | planned |
| TOOL-03 | Data access restrictions | Tool gateway / protected API | MCP gateway, Pydantic, Presidio, OPA | Kong, Apigee, Microsoft Purview | planned |
| TOOL-04 | High-impact approval | Tool gateway / protected API | MCP gateway, Pydantic, Presidio, OPA | Kong, Apigee, Microsoft Purview | planned |
| OBS-01 | Correlated traces | Telemetry pipeline / audit store | OpenTelemetry, Loki, Grafana, Tempo | Datadog, Splunk, Microsoft Sentinel | planned |
| OBS-02 | Tamper-aware audit records | Telemetry pipeline / audit store | OpenTelemetry, Loki, Grafana, Tempo | Datadog, Splunk, Microsoft Sentinel | initial lab coverage |
| OBS-03 | Security alerting | Telemetry pipeline / audit store | OpenTelemetry, Loki, Grafana, Tempo | Datadog, Splunk, Microsoft Sentinel | planned |
| OBS-04 | Evidence retention | Telemetry pipeline / audit store | OpenTelemetry, Loki, Grafana, Tempo | Datadog, Splunk, Microsoft Sentinel | planned |
| IR-01 | Emergency suspension | Registry / identity provider / runtime | Registry API, Keycloak, Docker | Okta, CyberArk, Defender | initial lab coverage |
| IR-02 | Credential and runtime containment | Registry / identity provider / runtime | Registry API, Keycloak, Docker | Okta, CyberArk, Defender | planned |
| IR-03 | Recovery verification | Registry / identity provider / runtime | Registry API, Keycloak, Docker | Okta, CyberArk, Defender | planned |
| LIFE-01 | Version/change governance | Registry / identity provider | GitOps, Backstage, registry API | ServiceNow, SailPoint, Saviynt | planned |
| LIFE-02 | Periodic recertification | Registry / identity provider | GitOps, Backstage, registry API | ServiceNow, SailPoint, Saviynt | planned |
| LIFE-03 | Retirement workflow | Registry / identity provider | GitOps, Backstage, registry API | ServiceNow, SailPoint, Saviynt | planned |
| LIFE-04 | Orphan detection | Registry / identity provider | GitOps, Backstage, registry API | ServiceNow, SailPoint, Saviynt | planned |

## Evaluation methodology

For each technology, distinguish **system of record**, **policy decision point**, **policy enforcement point**, **telemetry**, and **orchestration**. Verify licensing, edition, API coverage, workload compatibility, policy semantics, and whether the control is native or custom-integrated before procurement. A product appearing in a row does not mean it independently satisfies the full control.

Each control record includes a proposed owner, test, and evidence schema in [controls.json](controls.json). Threat and standards crosswalks require separate review; no unverified mappings are asserted.
