# Mission #002 sync pointer

**Canonical source:** [warheart1984-ctrl/agentic-coding-agent](https://github.com/warheart1984-ctrl/agentic-coding-agent)

This directory is a **downstream mirror** inside `project-infi`. Do not treat it as an independent source of truth.

| Field | Value |
|-------|-------|
| Last synced | 2026-06-25 |
| From | `E:\agentic-coding-agent` |
| Version | 0.2.0-mission-002 (CRK-2, `agent/`) |
| Previous backup | `../nova-mission-002.v0.1.0.bak` |

## Re-sync

```powershell
# From project-infi root
Rename-Item nova-mission-002 nova-mission-002.bak-$(Get-Date -Format yyyyMMdd)
New-Item -ItemType Directory nova-mission-002 | Out-Null
robocopy E:\agentic-coding-agent nova-mission-002 /E /XD shell .git node_modules dist /XF RELEASE.md
```

Edit Mission #002 in `agentic-coding-agent` first, then re-run the mirror step above.
