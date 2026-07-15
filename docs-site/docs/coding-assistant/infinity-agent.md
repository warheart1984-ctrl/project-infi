# Infinity Coding Agent

Infinity is a multi-step governed coding planner.

## How It Works

1. **Plan** — generates a step-by-step plan for the task
2. **Execute** — runs each step through the CodingRouter
3. **Return** — plan, steps, results, and full response trace

## Usage

```ts
const infinity = assistant.infinity({ actorId: 'jon', role: 'developer' });
const solution = await infinity.solve('Create a CLI todo app in Rust');

console.log(solution.plan);
console.log(solution.steps);
console.log(solution.results);
```

## Governance

Infinity tags requests with `agentic`, which routes agentic tool-use tasks to Devin when configured in the policy pack.
