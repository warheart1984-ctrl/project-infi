export const invariantEngine = {
  checkAll(
    action: { type: string; payload?: Record<string, unknown> },
    context: Record<string, unknown>
  ): { ok: boolean; invariantId?: string } {
    const text = JSON.stringify({ action, context });
    if (text.includes("rm -rf")) {
      return { ok: false, invariantId: "no-dangerous-shell" };
    }
    return { ok: true };
  },
};
