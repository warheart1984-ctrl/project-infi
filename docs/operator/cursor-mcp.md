# Cursor MCP — Operator Kernel

Expose the running **OperatorKernel** HTTP API to Cursor via stdio MCP.

## Prerequisites

1. **Kernel running** on `http://127.0.0.1:8790` (default):
   - Launch **Operator Desktop** (`dist/operator-desktop/OperatorDesktop.exe`), or
   - From repo root: `python -m operator_kernel`
2. Python 3.10+ with MCP deps (separate from bundled desktop Python):

```powershell
pip install -r requirements-operator-mcp.txt
```

## Cursor configuration

Add to `.cursor/mcp.json` (project) or global MCP settings:

```json
{
  "mcpServers": {
    "operator-kernel": {
      "command": "python",
      "args": ["-m", "operator_mcp"],
      "cwd": "E:/project-infi",
      "env": {
        "OPERATOR_KERNEL_URL": "http://127.0.0.1:8790"
      }
    }
  }
}
```

Adjust `cwd` to your repo root. Use the same Python that has `mcp` installed.

## Tools

| Tool | Maps to |
|------|---------|
| `operator_health` | `GET /health` |
| `operator_list_tasks` | `GET /agent/tasks` |
| `operator_get_task` | `GET /agent/tasks/{id}` |
| `operator_create_task` | `POST /agent/tasks` |
| `operator_cancel_task` | `POST /agent/tasks/{id}/cancel` |
| `operator_append_message` | `POST /agent/tasks/{id}/message` |

## Notes

- MCP does **not** start the desktop app or kernel; it only proxies HTTP.
- For portable installs with bundled Python, the **desktop host** uses `python/python.exe` beside `OperatorDesktop.exe`; MCP in Cursor still uses your dev Python with `operator_mcp` installed.
- SSE live streaming is not exposed as MCP resources yet; use `operator_get_task` to poll events.
