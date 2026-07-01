# Stage 18 Co-Builders — GitHub Project setup

One-time setup for the **Backlog → In Progress → Review** board and linking open entry issues (#2–#8).

## Prerequisites

`gh` CLI with **project** scopes:

```powershell
gh auth refresh -h github.com -s project,read:project
```

Verify:

```powershell
gh auth status
```

## Create project and link repo

```powershell
$owner = "warheart1984-ctrl"
$repo  = "Project-Infinity1"

# Create user-owned project (returns number + URL)
gh project create --owner $owner --title "Stage 18 Co-Builders" --format json

# Note PROJECT_NUMBER from output, then link to repo:
gh project link $PROJECT_NUMBER --owner $owner --repo "$owner/$repo"
```

## Column layout (Projects v2)

GitHub Projects v2 uses **Status** (or custom fields). In the project UI:

1. Open the new project → **Settings** (or **⋯**)
2. Ensure a **Status** field with options: **Backlog**, **In Progress**, **Review** (rename defaults if needed: Todo → Backlog, In Progress, Done → Review or add Review before Done)
3. Default new items to **Backlog**

Alternatively run field setup via API after `gh project field-list` — UI is fastest for three columns.

## Add entry issues to Backlog

```powershell
$PROJECT_NUMBER = 2   # Stage 18 Co-Builders — https://github.com/users/warheart1984-ctrl/projects/2

foreach ($n in 2..8) {
  gh project item-add $PROJECT_NUMBER --owner warheart1984-ctrl --url "https://github.com/warheart1984-ctrl/Project-Infinity1/issues/$n"
}
```

## Update discussion link

After the project exists, edit [discussion #9](https://github.com/warheart1984-ctrl/Project-Infinity1/discussions/9) **Project board** line to the direct project URL, e.g.:

`https://github.com/users/warheart1984-ctrl/projects/<number>`

Also update `docs/community/HELP_WANTED_HUB.md` if you want a stable in-repo URL.

## Pin discussion #9

No GraphQL `pinDiscussion` mutation exists (only `pinIssue`). Pin manually:

**Discussions → Stage 18 — Call for Co-Builders → Pin discussion**
