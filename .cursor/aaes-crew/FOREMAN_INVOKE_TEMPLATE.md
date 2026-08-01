# AAES Foreman invoke brief

Copy this block into a chat or Task prompt. ModeKey is **guidance**, not Node-enforced.

```markdown
## AAES Crew Invoke

- **ModeKey:** sage__navigator__evidence-strict
- **Phase:** <vision | architecture | design | implementation | testing | operations | esfr>
- **Role skill:** <aaes-architect | aaes-builder | aaes-coding | aaes-implementor | aaes-reviewer | aaes-inspector | aaes-esfr>
- **Foreman:** aaes-crew (not one of the six)

### Objective
<one sentence>

### In scope files
- …

### Out of scope
- Mandala 100 clone
- …

### Success evidence
- [ ] Commands/tests run (list)
- [ ] Artifacts written (paths)
- [ ] Claim boundary stated (pass | hold | fail)

### Vendor skills (optional)
Resolve paths from `.cursor/aaes-crew/vendor-skills-paths.json`:
- …

### Hand-off
Next role: <…> after success evidence above.
ESFR last when readiness evidence exists.
```

Registry: `.cursor/aaes-crew/modes-registry.json`  
Phases: `.cursor/aaes-crew/phases.json`
