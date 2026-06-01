export interface SigilBindableInvocation {
  trace: string;
  echo?: string;
  spawnNewThread?: boolean;
}

export const DEFAULT_SIGIL_BINDING = {
  sigil: "breath-weaver",
  modeToken: "mode:single",
  bindingToken: "sigilBinding:default",
} as const;

function normalize(value: string | undefined): string {
  return (value || "").trim();
}

function normalizeEchoTokens(value: string | undefined): string[] {
  return normalize(value)
    .split(/\s+/)
    .filter(Boolean);
}

function stripEchoControlTokens(tokens: string[]): string[] {
  return tokens.filter((token) => {
    const normalized = token.toLowerCase();
    if (normalized.startsWith("mode:")) return false;
    if (normalized.startsWith("sigil:")) return false;
    if (normalized.startsWith("sigilbinding:")) return false;
    return true;
  });
}

function withDefaultTraceBinding(trace: string): string {
  const normalizedTrace = normalize(trace)
    .replace(/\bsigilbinding:[^\s]+\b/gi, "")
    .replace(/\s+/g, " ")
    .trim();
  return [normalizedTrace, DEFAULT_SIGIL_BINDING.bindingToken].filter(Boolean).join(" ");
}

export function applyDefaultSigilBinding<T extends SigilBindableInvocation>(invocation: T): T {
  const retainedEchoTokens = stripEchoControlTokens(normalizeEchoTokens(invocation.echo));
  const echoTokens = [
    ...retainedEchoTokens,
    DEFAULT_SIGIL_BINDING.modeToken,
    `sigil:${DEFAULT_SIGIL_BINDING.sigil}`,
    DEFAULT_SIGIL_BINDING.bindingToken,
  ];

  return {
    ...invocation,
    trace: withDefaultTraceBinding(invocation.trace),
    echo: echoTokens.join(" "),
    spawnNewThread: true,
  };
}
