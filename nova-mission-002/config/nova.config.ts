import type { Invariant } from "../agent/types/invariants";

const dangerousShell = ["rm -rf", "curl | sh", "curl|sh", ":(){ :|:& };:"];

export const invariants: Invariant[] = [
  {
    id: "no-credentials",
    description: "Do not leak secrets or credentials in generated code or prompts.",
    severity: "error",
    check: (state) => {
      const text = [state.prompt, state.code, state.diff].filter(Boolean).join(" ");
      return !/API_KEY|SECRET_KEY|password\s*=\s*["'][^"']+["']/i.test(text);
    },
  },
  {
    id: "no-dangerous-shell",
    description: "Disallow dangerous shell commands in prompts and diffs.",
    severity: "error",
    check: (state) => {
      const text = [state.prompt, state.code, state.diff].filter(Boolean).join(" ");
      return !dangerousShell.some((p) => text.includes(p));
    },
  },
  {
    id: "no-silent-actions",
    description: "All actions must be governable (non-empty action type).",
    severity: "error",
    check: (state) => Boolean(state.action?.type),
  },
];
