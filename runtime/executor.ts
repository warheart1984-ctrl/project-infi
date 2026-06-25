/** MVP stub: records tool execution metadata only (no external I/O). */
export function executeSummarize(input: string): { output: string; tool: string } {
  return { output: input, tool: "fixture_summarizer_v0" };
}
