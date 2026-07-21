# CEIP Evidence-Based Release Path

| Stage | Meaning | Mandatory promotion evidence |
|---|---|---|
| CEIP v1.0 Reference | Frozen contracts and executable baseline | freeze integrity, lifecycle tests, reference documentation |
| Engineering Candidate | Integrated engineering controls | persistence/outbox/eventing/API/auth/tenancy/observability evidence and failure recovery |
| Production Candidate | Production-like validation | security baseline, load/chaos/replay/DR/backup evidence and live 19-stage console demonstration |
| Certified Reference Runtime | Independent constitutional equivalence | independent CCS result, second implementation interoperability, deterministic cross-runtime replay, independent evidence verification |
| CEIP v1.x Stable | Supported release line | operational SLO history, upgrade/migration compatibility, incident process, adoption evidence |

Promotion is monotonic only while evidence remains valid. A material contract, implementation, environment, dependency, or threat change may expire a gate. Feature completion without evidence cannot promote a release.

Current status: `CEIP v1.0 Reference`. Engineering Candidate, Production Candidate, Certified Reference Runtime, and Stable have not yet been earned.
