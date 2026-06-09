# Zscaler egress preflight — Project Infinity Azure pilot

Operators deploying **Project Infinity** from a Zscaler-protected workstation often hit failures that look like Azure or Docker problems but are actually **ZIA URL filtering / SSL inspection** blocking required endpoints. This gate runs **before** `azure-validate` and `azure-deploy` (see [`.azure/deployment-plan.md`](../../.azure/deployment-plan.md)).

Use the **Zscaler Cursor plugin** skill `/investigate-url` (ZIA: Investigate URL Category) and, for the deploying identity, `/check-access`.

---

## Why this matters for this repo

| Workstation task | Egress dependency | Risk if blocked |
|------------------|-------------------|---------------|
| `az login` / `azd up` | `*.azure.com`, `login.microsoftonline.com` | Deploy never starts |
| Push images to ACR | `*.azurecr.io` | Build succeeds, deploy fails |
| ACA runtime + managed services | `*.azurecontainerapps.io`, `*.postgres.database.azure.com`, `*.redis.cache.windows.net`, `*.blob.core.windows.net` | Pilot unhealthy after deploy |
| Clone / release tags | `github.com` | Cannot sync repo on locked-down network |
| Docs / quota references | `learn.microsoft.com` | Operator runbooks break mid-flight |
| Optional ScyllaDB Cloud vectors | `cloud.scylladb.com`, `*.cloud.scylladb.com` | `AAIS_VECTOR_BACKEND=scylladb` fails |
| Optional NVIDIA provider | `build.nvidia.com` | Chat provider `nvidia` unavailable |
| Deploy region topology map | `maps.geo.*.amazonaws.com`, `unpkg.com`, `cdn.jsdelivr.net` | [Deploy region map](./DEPLOY_REGION_GEO_TOPOLOGY.md) tiles/assets blocked |

Zscaler does not know your Azure deployment plan. This document maps **repo-specific hosts** to the plugin workflow so policy gaps surface early.

---

## Prerequisites (this workstation)

| Step | Status | Action |
|------|--------|--------|
| Python ≥ 3.11 | ✅ `py -3.12` | `py -3.12 -m pip install zscaler-mcp` (done) |
| Zscaler MCP in Cursor | ⏳ | Add server block below to `%USERPROFILE%\.cursor\mcp.json` |
| OneAPI credentials | ⏳ | Copy [`deploy/zscaler/.env.example`](../../deploy/zscaler/.env.example) → `deploy/zscaler/.env` |

### Cursor MCP configuration (Windows, no `uv`)

```json
{
  "mcpServers": {
    "zscaler-mcp-server": {
      "command": "C:\\Users\\randj\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\zscaler-mcp.exe",
      "args": [
        "--dotenv-path",
        "e:\\project-infi\\deploy\\zscaler\\.env",
        "--services",
        "zia"
      ]
    }
  }
}
```

Restart Cursor after saving. Write tools stay off by default (plugin safety rule).

---

## Preflight procedure

### 1. Classify each host (`zia_url_lookup`)

In Cursor chat (with MCP connected), run **`/investigate-url`** or ask the agent to call `zia_url_lookup` for each host:

```
management.azure.com
login.microsoftonline.com
github.com
learn.microsoft.com
build.nvidia.com
cloud.scylladb.com
```

Record returned **URL categories** (e.g. `CLOUD_STORAGE`, `DEVELOPER_TOOLS`, `AI_ML`).

> **Note:** Wildcard Azure FQDNs (`*.azurecontainerapps.io`, etc.) are usually not lookup-able as literals. For those, investigate the **parent category** returned for `management.azure.com` / `login.microsoftonline.com`, then confirm custom allow rules exist for Azure PaaS categories your tenant uses.

### 2. Trace policy references (investigate-url skill)

For each category from step 1, the plugin searches:

- URL filtering rules (`zia_list_url_filtering_rules`)
- SSL inspection rules (`zia_list_ssl_inspection_rules`)
- DLP web rules (`zia_list_web_dlp_rules`)
- Cloud firewall rules (`zia_list_cloud_firewall_rules`)

**Pass criteria for deploy operators:**

- **ALLOW** (or acceptable **CAUTION**) on URL filtering for Azure + GitHub + Microsoft identity categories
- SSL inspection **INSPECT** or **DO_NOT_DECRYPT** only where required — not blanket **DO_NOT_INSPECT** on `DEVELOPER_TOOLS` if DLP is expected
- No **BLOCK** on categories covering `login.microsoftonline.com` or `management.azure.com`

### 3. Verify the deploying user (`/check-access`)

Run **`/check-access`** for the operator account against:

- `https://github.com`
- `https://management.azure.com`
- `https://login.microsoftonline.com`

Document effective action (ALLOW / BLOCK / CAUTION) and overriding rule order.

### 4. Optional — ZDX before cutover

If operators will use the pilot daily from the same network, run **`/troubleshoot-experience`** or **`/app-health`** after Azure URLs are reachable to baseline latency to ACA ingress.

---

## Preflight results template

Copy into your deploy ticket after MCP calls complete:

```text
Zscaler Egress Preflight — Project Infinity Azure pilot
Date:
Operator:
ZIA tenant (vanity):

| Host / scope              | Category(ies)     | URL filter | SSL inspect | Operator /check-access |
|---------------------------|-------------------|------------|-------------|-------------------------|
| login.microsoftonline.com |                   |            |             |                         |
| management.azure.com      |                   |            |             |                         |
| github.com                |                   |            |             |                         |
| learn.microsoft.com       |                   |            |             |                         |
| build.nvidia.com          |                   |            |             |                         |
| cloud.scylladb.com        |                   |            |             |                         |
| Azure PaaS (wildcard)     | (custom rule ref) |            |             | n/a                     |

Blockers found:
Remediation owner:
Ready for azure-deploy: YES / NO
```

---

## Placement in deployment checklist

Insert between **Phase 1 approval** and **Phase 2 `azd init`** in [`.azure/deployment-plan.md`](../../.azure/deployment-plan.md):

- [ ] Zscaler egress preflight complete (this document)
- [ ] No BLOCK on Azure identity / ARM / GitHub for deploy operator
- [ ] Custom allow rules ticketed if wildcard Azure PaaS categories missing

---

## Plugin reminders

- **ZIA activation:** After any policy *write*, changes are not live until ZIA is activated (not needed for this read-only preflight).
- **Read-only default:** Preflight uses read tools only; enable writes only for remediation with `--enable-write-tools`.
- **Cross-product:** If user VPN/ZCC issues appear during deploy, escalate with `/troubleshoot-user` (ZCC + ZDX + ZPA + ZIA).
