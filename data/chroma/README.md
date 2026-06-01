# Chroma Runtime Data

This directory is for local Chroma runtime state only.

Rules:

- `chroma.sqlite3` and any related runtime files are local, rebuildable state
- they are not canonical AAIS source truth
- they should not be used as documentation, product fixtures, or long-term repo-owned data
- git should ignore runtime contents in this directory

If the local retrieval store needs to be reset, the runtime can recreate it.
