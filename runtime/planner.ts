/** MVP stub: fixture-driven planning for governed vertical slice demos. */
export function planFromFixture(lines: string[]): string[] {
  return lines.filter((l) => l.startsWith("## ")).map((l) => l.replace(/^##\s+/, "").trim());
}
