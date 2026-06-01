# Legacy Root Scripts

This folder contains older shell helpers that were previously loose at the
repository root.

## Why They Were Moved

These scripts were high-clutter root items and were not referenced by the live
runtime or current build/test path.

They are retained for recovery and historical operations context, but they are
not part of the active root structure anymore.

## Contents

- deploy helpers
- docker convenience wrappers
- advanced setup and upgrade scripts

## Rule

If one of these scripts ever needs to return to active use, it should come back
through an owned runtime or tooling path instead of drifting back into the root
without explanation.
