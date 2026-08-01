# Recovery / Failure Testing — AAES-OS Production Baseline v1.0

**Baseline:** `AAES-OS-PRODUCTION-BASELINE-v1.0`  
**Frozen commit:** `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`  
**Status:** Procedures frozen; execution pending-cluster-execution

## Failure contracts

| Failure mode | Expected behavior | Recovery action |
| --- | --- | --- |
| Container crash | Liveness fails → kubelet restarts container | Automatic; verify Ready returns |
| Dependency down | Readiness fails → endpoints drained | Restore dependency; confirm `/ready` |
| Bad image roll | New ReplicaSet unhealthy | Rollback to previous digest-pinned Deployment |
| Node drain | PDB honors minAvailable | Reschedule; confirm HPA/PDB |
| NetworkPolicy misconfig | Legitimate traffic denied | Diff against frozen NetworkPolicy checksum; re-apply freeze set |
| Registry unavailable | ImagePullBackOff | Use pre-pulled digest pins / mirror |

## Rollback procedure (frozen)

1. Identify last known-good image digests from `image-tags.json` (once filled)
2. `kubectl set image` or re-apply prior Deployment revision with digest pins
3. `kubectl rollout status deployment/<name> -n aaes-os`
4. Re-run health/readiness checks
5. Record outputs in this file's results log

```bash
kubectl rollout history deployment/platform-api -n aaes-os
kubectl rollout undo deployment/platform-api -n aaes-os
kubectl rollout status deployment/platform-api -n aaes-os
```

## Chaos / injection checklist (reference)

1. Delete one `platform-api` pod → replacement Ready within probe windows
2. Block egress to a declared dependency (if applicable) → readiness not Ready
3. Deploy intentionally broken tag → rollout stalls; undo restores service
4. Drain a node hosting a replica → PDB respected

## Results log

| Scenario | Result | Evidence |
| --- | --- | --- |
| Procedure documented | Pass | this file |
| Pod delete recovery | Pending | `pending-cluster-execution` |
| Rollout undo | Pending | `pending-cluster-execution` |
| Dependency readiness fail | Pending | `pending-cluster-execution` |

## Truth boundary

Recovery procedures are part of the operational baseline. Unexecuted checklists do not constitute completed failure testing.
