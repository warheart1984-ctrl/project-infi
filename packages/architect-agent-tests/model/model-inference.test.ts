import child_process from "child_process"

describe("Real Model Inference", () => {
  test("qwen2.5-coder:3b returns structured JSON", () => {
    const out = child_process.execSync(`
      ollama run qwen2.5-coder:3b "Generate a structured JSON proposal for updating index.js"
    `).toString()

    const parsed = JSON.parse(out)

    expect(parsed.schemaVersion).toBeDefined()
    expect(parsed.goal).toBeDefined()
    expect(Array.isArray(parsed.operations)).toBe(true)
  })
})

