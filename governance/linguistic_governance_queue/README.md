# Linguistic governance queue (Wave 13)

Unified operator backlog merging forecast, preemptive playbooks, remediation playbooks, and calibration misses.

**Build:**

```bash
make linguistic-governance-queue
python tools/linguistic_governance_queue.py --markdown --top 30
```

Instance: [../linguistic_governance_queue.v1.json](../linguistic_governance_queue.v1.json)

No auto-apply — `recommended_actions` are watch and schedule commands only.
