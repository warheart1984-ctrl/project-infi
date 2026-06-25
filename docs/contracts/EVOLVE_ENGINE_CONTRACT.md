# Evolve Engine

EvolveEngine is the bounded search lane for AAIS.

## Boundary

- Separate HTTP service and port: `EVOLVE_PORT` defaults to `6062`
- Separate storage root: `EVOLVE_STORAGE` defaults to `.runtime/evolve_engine`
- Jarvis authorizes jobs, but EvolveEngine owns mutation, selection, and generation loops
- ForgeEval scores candidates, but EvolveEngine decides population flow
- Forge remains separate and does not run inside the evolution loop

## Start

```powershell
.\.venv\Scripts\python.exe .\tools\services\start_evolve_engine.py
```

## Health

- `GET /health`

## Request Contract

```json
{
  "job_id": "evolve-job-1",
  "jarvis_run_id": "jarvis-run-1",
  "task": "Improve this candidate until it scores cleanly.",
  "config": {
    "initial_candidate": "draft candidate text",
    "seed_candidates": ["variant one", "variant two"],
    "strategy": "local_search"
  },
  "evaluation": {
    "mode": "forge_eval",
    "forge_eval_mode": "llm_rubric",
    "candidate_field": "program",
    "payload": {
      "config": {
        "criteria": ["clear structure", "goal coverage"]
      }
    },
    "success_threshold": 0.9,
    "failure_threshold": 0.2
  },
  "constraints": {
    "population_size": 4,
    "max_generations": 3,
    "max_evaluations": 12,
    "max_wall_time_seconds": 30,
    "target_score": 0.95
  }
}
```

## Trace Endpoints

- `GET /traces/jobs/<job_id>`
- `GET /traces/jobs/<job_id>/evaluations`
- `GET /traces/runs/<jarvis_run_id>`
- `GET /traces/hall-of-fame`
- `GET /traces/hall-of-shame`

Hall of fame keeps successful mutations. Hall of shame keeps failed mutations and evaluator misses.

