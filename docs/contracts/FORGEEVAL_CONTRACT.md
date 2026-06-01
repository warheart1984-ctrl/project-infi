# ForgeEval

ForgeEval is the evaluator service that sits beside Forge.

## Boundary

- Separate HTTP service and port: `FORGE_EVAL_PORT` defaults to `6061`
- Separate storage root: `FORGE_EVAL_STORAGE` defaults to `.runtime/forge_eval`
- Evaluator lane only through `POST /evaluate`
- ForgeEval handles scoring and repo-aware checks; Forge does not

## Start

```powershell
.\.venv\Scripts\python.exe .\start_forge_eval.py
```

## Request Contract

```json
{
  "task_id": "eval-task-1",
  "mode": "io_tests",
  "payload": {
    "program": "def add(a, b): return a + b",
    "config": {
      "must_contain": ["return a + b"]
    }
  }
}
```

## Success Contract

```json
{
  "ok": true,
  "task_id": "eval-task-1",
  "mode": "io_tests",
  "result": {
    "score": 1.0,
    "details": {
      "passed": 1,
      "total": 1
    }
  }
}
```

## Error Contract

```json
{
  "ok": false,
  "task_id": "eval-task-1",
  "mode": "repo_patch",
  "error": {
    "code": "sandbox_error",
    "message": "Repo path does not exist"
  }
}
```
