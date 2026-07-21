import fs from "fs"
import path from "path"
import child_process from "child_process"

describe("Dist Smoke Test", () => {
  const root = path.resolve(__dirname, "../../../")
  const smokeDir = path.join(__dirname, "smoke-workspace")

  beforeAll(() => {
    if (fs.existsSync(smokeDir)) {
      fs.rmSync(smokeDir, { recursive: true })
    }
    fs.mkdirSync(smokeDir)
  })

  test("tarballs install and pipeline runs", () => {
    // 1. Build packages
    child_process.execSync("pnpm -w build", { cwd: root })

    // 2. Pack architect-agent
    const tarball = child_process
      .execSync("pnpm pack", { cwd: path.join(root, "packages/architect-agent") })
      .toString()
      .trim()

    const tarballPath = path.join(root, "packages/architect-agent", tarball)

    // 3. Install tarball into smoke workspace
    child_process.execSync(`pnpm add ${tarballPath}`, { cwd: smokeDir })

    // 4. Run minimal governed pipeline
    const result = child_process
      .execSync(`node -e "
        const { ArchitectAgent } = require("architect-agent")
        const agent = new ArchitectAgent()
        const out = agent.run({
          goal: "refactor",
          operations: [{ file: "index.js", type: "update", content: "// ok" }]
        })
        console.log(JSON.stringify(out))
      "`, { cwd: smokeDir })
      .toString()

    const parsed = JSON.parse(result)

    expect(parsed.envelope).toBeDefined()
    expect(parsed.envelope.ucrDecision.ok).toBe(true)
    expect(parsed.envelope.safetyDecision.ok).toBe(true)
    expect(parsed.replay.ok).toBe(true)
    expect(parsed.receipt.signature).toBeDefined()
  })
})
