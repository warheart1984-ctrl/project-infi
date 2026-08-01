# AAES crew — import sources

Lean AAES crew pack for `project-infi`. Not a clone of the Mandala 100.

## Sources of truth (referenced, not duplicated)

| Source | Path | What we took |
|--------|------|--------------|
| LineageStudio Mandala pack | `G:/LineageStudio/.cursor/mandala-crew/` | Phase shape, ModeKey pattern, vendor path index shape |
| LineageStudio role skills | `G:/LineageStudio/.cursor/skills/ls-*.md` | Foreman / coding / inspector / reviewer / ESFR role lenses |
| CRE six-role crew | `G:/cre/.cursor/skills/cre-*.md` | Architect → builder → implementor → reviewer → inspector → ESFR pipeline |
| Vendor skill inventory | Host `SKILL.md` trees indexed by LineageStudio | Thin AAES subset in `vendor-skills-paths.json` |
| Drive-G laws | `G:/DRIVE_G_LAWS.md`, Drive-G-1 / Drive-G-2 rules | Evidence-bound claims; five maturity dimensions |

## Honesty limits

- Cursor agents open `SKILL.md` files; nothing in this pack executes vendor skills inside Node.
- ModeKey auto-apply is **declared guidance** via `.cursor/rules/aaes-modekey-auto-apply.mdc`, not a runtime enforcer.
- Full Mandala 100+ESFR product surfaces (`MandalaCrewEngine`, `/api/crew`) remain in LineageStudio.
- Refresh thin vendor paths: `pnpm aaes-crew:sync-vendor` (reads LineageStudio index; does not copy the 100 agents).
- Foreman brief template: `FOREMAN_INVOKE_TEMPLATE.md`
