import type { Invariant } from "../../../agent/types/invariants";

export const invariants: Invariant[] = [
  {
    id: "no-dangerous-shell",
    description: "Disallow dangerous shell commands.",
    severity: "error",
    check: (state) => {
      const text = [state.prompt, state.code, state.diff].filter(Boolean).join(" ");
      return !text.includes("rm -rf") && !text.includes("curl | sh");
    },
  },
];
