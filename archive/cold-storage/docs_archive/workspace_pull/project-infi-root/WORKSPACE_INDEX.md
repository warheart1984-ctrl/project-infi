# Project Infi Workspace Index

This folder contains multiple separate projects, prototypes, and archive files.

## Active Product

- `AAIS-main`
  - main local AI app
  - current base for the private UI Jarvis direction

## Delivery Rule

Project Infi now treats lawful completion as a workspace-level rule:

- a build is not the same thing as completion
- completion requires verification, declared release artifacts, and successful post-package execution
- if the delivered artifact cannot run, the system is not complete

The canonical repo statement lives in:

- [LAWFUL_COMPLETION_OF_A_SYSTEM.md](/C:/Users/randj/Desktop/project%20infi/code/code/LAWFUL_COMPLETION_OF_A_SYSTEM.md)

## Reference Projects

- `Ui jarvis`
  - prototype visuals and voice ideas
- `code`
  - architecture reference project
- `jarvis`
  - feature-heavy reference project
- `NVIDIA`
  - separate private API / Spiral research sandbox
- `mystic`
  - separate small project
- `Spiral-Companion-main`
  - separate substantial project

## Cleanup Rule

- Do not mix these projects into the parent repo
- Treat the parent folder as a workspace and storage layer only
- Keep real development inside each project folder's own repo

## Archives

Top-level zip backups are stored under:

- `_archives\zip-backups`

These are kept for safety, but moved out of the workspace root so the active folders are easier to reason about.

Top-level loose doctrine/spec cleanup is documented in:

- `AAIS-main\docs\workspace\TOP_LEVEL_WORKSPACE_ROOT_RELOCATION_PLAN.md`

Current root-file result:

- loose `.docx`, legacy `.md`, `.txt`, and `.zip` files have been moved off the
  workspace root
- archived root docs now live under `_archives\workspace-root-docs`
- archived root notes now live under `_archives\workspace-root-notes`
- release bundles now live under `_archives\release-bundles`
