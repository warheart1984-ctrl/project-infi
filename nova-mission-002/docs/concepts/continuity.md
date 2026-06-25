# Continuity

The continuity substrate provides snapshots, diffs, and replay.

```typescript
const snap = await continuity.snapshot();
const replay = await continuity.replay(snap.id);
const delta = await continuity.diff(snapA, snapB);
```

Every successful action updates the continuity hash.
