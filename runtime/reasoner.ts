/** MVP stub: deterministic summarization without LLM side effects. */
export function summarizeBottlenecks(headings: string[]): string {
  return headings.map((h, i) => `${i + 1}. ${h}`).join("\n");
}
