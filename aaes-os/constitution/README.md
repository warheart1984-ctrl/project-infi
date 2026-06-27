# Constitutional Governance Library

Foundational documents for AAES-OS v1.0 → v2.0 transition.

## Documents

| File | Role |
|------|------|
| [AAES-OS-Constitution.md](AAES-OS-Constitution.md) | Highest governing document |
| [Governance-Charter.md](Governance-Charter.md) | Bodies, roles, decision authority |
| [Evidence-Standard.md](Evidence-Standard.md) | Evidence types, traceability, adoption criteria |

## Registries

| File | Role |
|------|------|
| [../registries/governance.yaml](../registries/governance.yaml) | Councils, boards, roles, policies |
| [../registries/requirements.yaml](../registries/requirements.yaml) | Traceable requirements |
| [../registries/artifacts.yaml](../registries/artifacts.yaml) | Immutable artifact index |

## Core Rule (GOV-POL-001)

> Governance should determine how changes are evaluated, but evidence should determine whether changes are adopted.

Encoded as:

- Constitution Article II, principle 8
- Governance Charter § Evaluation vs Adoption
- Evidence Standard § Foundational Rule
- Registry policy `GOV-POL-001` → requirement `REQ-GOV-001`

## PDF builds

```bash
# LaTeX
latexmk -pdf constitution/AAES-OS-Constitution.tex

# Pandoc
pandoc constitution/AAES-OS-Constitution.md -o constitution/AAES-OS-Constitution.pdf
```
