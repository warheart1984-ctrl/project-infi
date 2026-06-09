# Appwrite Governance Projection (optional)

Optional cloud sink for **governance contracts** and **operator ledger event mirrors**.
JSONL operator receipts remain the accountability write authority.

## Why Appwrite here

| Surface | Role |
|---------|------|
| Local JSONL ledger | Constitutional write authority (unchanged) |
| Turbopuffer (`scripts/tpuf_governance_search_demo.py`) | Agent retrieval / BM25 search |
| **Appwrite Tables** | Durable queryable store for dashboards, mobile, multi-operator visibility |

## Prerequisites

1. [Appwrite Cloud](https://cloud.appwrite.io/) project (or self-hosted instance)
2. Server API key with Tables read/write scope
3. Python SDK: `pip install appwrite` (see `requirements-advanced.txt`)

## Tables setup

Create database `governance` (or set `APPWRITE_DATABASE_ID`), then two tables.

### Option A — Python bootstrap (recommended on Windows)

No Appwrite CLI required. In [Appwrite Console](https://cloud.appwrite.io/) create a **Server API key** with **Tables** read/write.

```powershell
cd e:\project-infi
pip install appwrite

$env:APPWRITE_ENDPOINT = "https://<REGION>.cloud.appwrite.io/v1"
$env:APPWRITE_PROJECT_ID = "<your-project-id>"
$env:APPWRITE_API_KEY = "<your-server-api-key>"

python scripts/appwrite_bootstrap_tables.py
```

### Option B — Appwrite CLI

Install CLI (Node/npm on PATH):

```powershell
npm install -g appwrite-cli
cd e:\project-infi\deploy\appwrite
appwrite login
# Edit appwrite.config.json — set projectId and endpoint
appwrite push tables --all --force
```

Declarative schema: [`deploy/appwrite/appwrite.config.json`](appwrite.config.json).

### Option C — Console (manual)

Create database `governance`, then two tables:

### `governance_contracts`

| Column | Type | Notes |
|--------|------|-------|
| `path` | varchar(512) | Unique contract path, indexed |
| `title` | varchar(255) | Display title |
| `content` | mediumtext | Contract body (truncated to 12k in indexer) |
| `doc_type` | varchar(64) | e.g. `contract` |
| `indexed_at` | varchar(32) | ISO timestamp |

### `ledger_events`

| Column | Type | Notes |
|--------|------|-------|
| `scope_id` | varchar(128) | Ledger scope |
| `decision_id` | varchar(64) | e.g. `odl_…` |
| `decision_kind` | varchar(64) | pipeline_turn, otem_approval, … |
| `decision` | varchar(32) | allow, approve, block, … |
| `summary` | varchar(2000) | Human-readable summary |
| `row_hash` | varchar(128) | Chain hash from local ledger |
| `recorded_at` | varchar(32) | ISO timestamp |
| `event_json` | mediumtext | Full normalized event payload |

## Configure

1. Copy [`deploy/appwrite/.env.example`](.env.example) into your environment
2. Set `AAIS_APPWRITE_SINK=1`
3. Index contracts:

```bash
python scripts/appwrite_governance_index_demo.py
```

4. Ledger events mirror automatically when `OperatorDecisionLedgerStore.append` runs

## Verify

With sink enabled, append a test ledger event and confirm a row appears in `ledger_events`.
Local chain verification (`verify_chain`) remains the source of truth.

## Cursor MCP (optional)

The Appwrite plugin ships two MCP servers. They let the agent list rows, manage users, and read docs inline.

### 1. Appwrite API MCP (`appwrite-api`)

Requires `uvx` **or** Python module fallback.

1. Create a server API key (Tables + any scopes you want the agent to manage).
2. In **Cursor → Settings → MCP**, enable the Appwrite plugin servers (or add manually):

```json
{
  "mcpServers": {
    "appwrite-api": {
      "command": "python",
      "args": ["-m", "mcp_server_appwrite", "--users"],
      "env": {
        "APPWRITE_API_KEY": "<server-api-key>",
        "APPWRITE_PROJECT_ID": "<project-id>",
        "APPWRITE_ENDPOINT": "https://<REGION>.cloud.appwrite.io/v1"
      }
    }
  }
}
```

Install once: `pip install mcp-server-appwrite`  
(Plugin default uses `uvx mcp-server-appwrite` if you have [uv](https://docs.astral.sh/uv/) installed.)

### 2. Appwrite Docs MCP (`appwrite-docs`)

Needs `npx` on PATH (install [Node.js LTS](https://nodejs.org/) — Cursor’s bundled `node.exe` alone is not enough).

```json
"appwrite-docs": {
  "command": "npx",
  "args": ["mcp-remote", "https://mcp-for-docs.appwrite.io"]
}
```

### 3. Verify MCP

After saving MCP config, restart Cursor. The agent should see `appwrite-api` tools (e.g. list rows) and `appwrite-docs` for documentation lookup.

**This workspace today:** Node is present but `npx`, `uvx`, and `appwrite` CLI were not on PATH during setup — use **Option A (Python bootstrap)** first, then add MCP once `pip install mcp-server-appwrite` and/or Node LTS are installed.

## Admission

Follows the same optional-projection pattern as
[`docs/contracts/MEMORY_VECTOR_BACKEND_ADMISSION.md`](../../docs/contracts/MEMORY_VECTOR_BACKEND_ADMISSION.md).
