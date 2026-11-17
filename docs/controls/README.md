# Control catalog design

Controls are grouped by lifecycle domain and labeled foundational or advanced. Each control will have a stable ID, objective, threats addressed, accountable owner, enforcement point, test procedure, evidence schema, open-source options, commercial options, and relevant framework crosswalks.

## Foundational groups (30 proposed controls)

| Domain | IDs | Count |
| --- | --- | --- |
| Registry and governance | REG-01 through REG-04 | 4 |
| Identity and trust | IAM-01 through IAM-04 | 4 |
| Authorization | AUTH-01 through AUTH-04 | 4 |
| Runtime and supply chain | RUN-01 through RUN-03 | 3 |
| Tool and data security | TOOL-01 through TOOL-04 | 4 |
| Observability | OBS-01 through OBS-04 | 4 |
| Incident response | IR-01 through IR-03 | 3 |
| Lifecycle | LIFE-01 through LIFE-04 | 4 |

**Total: 30.** This table establishes namespaces and scope; individual control definitions require review before being called normative.

## Advanced areas

Agent-to-agent trust, delegated user permissions, credential brokering, just-in-time privilege, contextual risk, MCP tool discovery, agent memory security, prompt injection containment, transaction limits, cross-agent delegation, dynamic containment, provenance, federation, policy simulation, and continuous validation.

## Scorecard rule

Track **implemented**, **tested**, **passed**, **failed**, **not applicable**, and **exception** separately. A configured control is not a verified control. Test evidence must reference agent version, policy version, environment and timestamp.
