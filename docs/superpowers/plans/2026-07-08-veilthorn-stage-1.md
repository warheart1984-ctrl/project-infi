# VEILTHORN Stage 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Stage 1 verification spine for VEILTHORN-RUNTIME: docs, proof surface, OpenAPI, Postman, examples, and conformance coverage, while also publishing the Node v0.1 document as a docs artifact.

**Architecture:** Keep the runtime source of truth in `llm-inference-engine`, keep the human-facing contract in `docs-site`, and keep runnable example clients in the existing SDK example locations. The Node v0.1 material from the uploaded DOCX is treated as a documentation landing page under the runtime docs tree, not as a build target or separate runtime.

**Tech Stack:** Markdown, Docusaurus-style docs, OpenAPI 3.1 YAML, Postman JSON, C++17, Python 3, TypeScript, CMake, Node.js.

---

### Task 1: Add the VEILTHORN runtime proof surface to the C++ engine

**Files:**
- Create: `llm-inference-engine/src/proof_surface.h`
- Create: `llm-inference-engine/src/proof_surface.cpp`
- Modify: `llm-inference-engine/src/http_server.h`
- Modify: `llm-inference-engine/src/http_server.cpp`
- Modify: `llm-inference-engine/src/governance.h`
- Modify: `llm-inference-engine/src/governance.cpp`
- Modify: `llm-inference-engine/CMakeLists.txt`
- Test: `llm-inference-engine/tests/test_integration.cpp`
- Create: `llm-inference-engine/tests/test_proof_surface.cpp`

- [ ] **Step 1: Write the failing proof-surface test**

```cpp
// tests/test_proof_surface.cpp
// Verifies every canonical inference response exposes the proof contract.
int test_proof_surface_main() {
    GovernanceConfig config;
    HTTPServer server(config);

    InferenceRequest request;
    request.prompt = "hello";
    request.max_tokens = 8;
    request.temperature = 0.2f;
    request.backend = "cpu";

    const auto response = server.handle_inference(request).to_json();

    assert(response.contains("metadata"));
    assert(response["metadata"].contains("runtime_version"));
    assert(response["metadata"].contains("backend"));
    assert(response["metadata"].contains("model"));
    assert(response["metadata"].contains("proof_level"));
    assert(response["metadata"].contains("evidence_receipt"));
    assert(response["metadata"].contains("replay_id"));
    assert(response["metadata"].contains("verification_status"));
    assert(response["metadata"].contains("governance_decision"));
    assert(response["metadata"].contains("resource_usage"));
    return 0;
}
```

- [ ] **Step 2: Run the focused engine tests and confirm the proof fields fail before implementation**

Run: `cmd.exe /c 'call C:\PROGRA~1\MICROS~1\18\COMMUN~1\VC\Auxiliary\Build\vcvars64.bat && cd /d E:\project-infi\llm-inference-engine && C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe --build build --target llm-engine-tests --parallel && .\build\llm-engine-tests.exe --integration'`
Expected: FAIL until the proof-surface fields exist on the runtime response envelope.

- [ ] **Step 3: Implement the proof receipt model and response serialization**

```cpp
// proof_surface.h
struct ProofReceipt {
    std::string runtime_version;
    std::string backend;
    std::string model;
    std::string proof_level;
    std::string evidence_receipt;
    std::string replay_id;
    std::string verification_status;
    std::string governance_decision;
    nlohmann::json resource_usage;

    nlohmann::json to_json() const;
};
```

```cpp
// proof_surface.cpp
ProofReceipt make_proof_receipt(const InferenceRequest& request, const InferenceResponse& response, const Governance& governance);
```

Update `HTTPServer::dispatch_request()` so `/v1/generate` and `/v1/chat/completions` include the proof receipt fields in the JSON response body, and update `RequestLog` to keep the same evidence/replay identifiers that were returned to the caller.

- [ ] **Step 4: Rebuild and rerun the proof-surface test**

Run: `cmd.exe /c 'call C:\PROGRA~1\MICROS~1\18\COMMUN~1\VC\Auxiliary\Build\vcvars64.bat && cd /d E:\project-infi\llm-inference-engine && C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe --build build --target llm-engine-tests --parallel && .\build\llm-engine-tests.exe --integration'`
Expected: PASS, with the proof fields present in the runtime response envelope.

- [ ] **Step 5: Commit the runtime proof-surface slice**

```bash
git add llm-inference-engine/src/proof_surface.h llm-inference-engine/src/proof_surface.cpp llm-inference-engine/src/http_server.h llm-inference-engine/src/http_server.cpp llm-inference-engine/src/governance.h llm-inference-engine/src/governance.cpp llm-inference-engine/CMakeLists.txt llm-inference-engine/tests/test_integration.cpp llm-inference-engine/tests/test_proof_surface.cpp
git commit -m "feat: add veilthorn proof surface"
```

### Task 2: Publish the VEILTHORN docs spine and the Node v0.1 document landing page

**Files:**
- Create: `docs-site/docs/veilthorn/index.md`
- Create: `docs-site/docs/veilthorn/quick-start.md`
- Create: `docs-site/docs/veilthorn/api-reference.md`
- Create: `docs-site/docs/veilthorn/proof-surface.md`
- Create: `docs-site/docs/veilthorn/examples.md`
- Create: `docs-site/docs/veilthorn/conformance.md`
- Create: `docs-site/docs/runtime/node-v0-1.md`
- Modify: `docs-site/sidebars.js`
- Modify: `docs-site/docusaurus.config.js`
- Modify: `docs-site/src/pages/index.mdx`
- Modify: `docs-site/scripts/smoke-docs-site.mjs`

- [ ] **Step 1: Write the failing docs smoke assertion for the VEILTHORN pages**

```js
// docs-site/scripts/smoke-docs-site.mjs
const requiredPages = [
  'index.html',
  path.join('docs', 'overview.html'),
  path.join('docs', 'runtime', 'node-v0-1.html'),
  path.join('docs', 'veilthorn', 'index.html'),
  path.join('docs', 'veilthorn', 'quick-start.html'),
  path.join('docs', 'veilthorn', 'api-reference.html'),
  path.join('docs', 'veilthorn', 'proof-surface.html'),
  path.join('docs', 'veilthorn', 'examples.html'),
  path.join('docs', 'veilthorn', 'conformance.html')
];
```

- [ ] **Step 2: Add the docs pages and navigation entries**

Create `docs-site/docs/veilthorn/index.md` as the landing page, then add the quick start, API reference, proof surface, examples, and conformance pages. Add `docs-site/docs/runtime/node-v0-1.md` as a document-only landing page for the Node v0.1 spec from the uploaded DOCX.

Update `docs-site/sidebars.js` to add a `VEILTHORN` category and add the Node v0.1 page under `Runtime`.

```js
{
  type: 'category',
  label: 'VEILTHORN',
  items: [
    'veilthorn/index',
    'veilthorn/quick-start',
    'veilthorn/api-reference',
    'veilthorn/proof-surface',
    'veilthorn/examples',
    'veilthorn/conformance',
  ],
},
```

- [ ] **Step 3: Build the docs site and confirm the new pages exist**

Run: `corepack pnpm --dir docs-site verify`
Expected: PASS, with the smoke test seeing the VEILTHORN pages and the Node v0.1 landing page.

- [ ] **Step 4: Commit the docs spine**

```bash
git add docs-site/docs/veilthorn docs-site/docs/runtime/node-v0-1.md docs-site/sidebars.js docs-site/docusaurus.config.js docs-site/src/pages/index.mdx docs-site/scripts/smoke-docs-site.mjs
git commit -m "docs: add veilthorn docs spine and node v0.1 landing page"
```

### Task 3: Ship the OpenAPI spec, Postman collection, and example clients

**Files:**
- Create: `docs-site/static/veilthorn/openapi.yaml`
- Create: `docs-site/static/veilthorn/postman/veilthorn.postman_collection.json`
- Modify: `docs/sdk/examples/typescript-basic.ts`
- Modify: `sdk/python/examples/basic_usage.py`
- Create: `docs/sdk/examples/cpp-basic.cpp`
- Modify: `docs-site/docs/veilthorn/examples.md`
- Modify: `docs-site/docs/veilthorn/api-reference.md`

- [ ] **Step 1: Write the OpenAPI contract as the source of truth**

```yaml
openapi: 3.1.0
info:
  title: VEILTHORN Runtime API
  version: 0.1.0
paths:
  /v1/chat/completions:
    post:
      summary: Canonical inference path
      responses:
        "200":
          description: Successful governed inference
```

- [ ] **Step 2: Add the example clients against the canonical endpoint**

Update the TypeScript example in `docs/sdk/examples/typescript-basic.ts` so it calls `/v1/chat/completions` and prints `proof_level`, `evidence_receipt`, and `verification_status`.

Update `sdk/python/examples/basic_usage.py` so it calls the same endpoint and prints the same proof metadata.

Create `docs/sdk/examples/cpp-basic.cpp` as a minimal `std::httplib`-style or raw-socket client that posts to the same endpoint and prints the proof fields.

- [ ] **Step 3: Add the Postman collection**

Create `docs-site/static/veilthorn/postman/veilthorn.postman_collection.json` with requests for `/health`, `/backends`, `/v1/models`, `/v1/generate`, and `/v1/chat/completions`.

- [ ] **Step 4: Verify the docs references and example payloads stay aligned**

Run: `corepack pnpm --dir docs-site build`
Expected: PASS, and the docs pages should link to the OpenAPI and Postman assets.

- [ ] **Step 5: Commit the contract artifacts and sample clients**

```bash
git add docs-site/static/veilthorn/openapi.yaml docs-site/static/veilthorn/postman/veilthorn.postman_collection.json docs/sdk/examples/typescript-basic.ts sdk/python/examples/basic_usage.py docs/sdk/examples/cpp-basic.cpp docs-site/docs/veilthorn/examples.md docs-site/docs/veilthorn/api-reference.md
git commit -m "docs: add veilthorn api contract and sample clients"
```

### Task 4: Add the conformance suite and support gate

**Files:**
- Create: `llm-inference-engine/tests/test_conformance.cpp`
- Modify: `llm-inference-engine/tests/test_main.cpp`
- Modify: `llm-inference-engine/CMakeLists.txt`
- Modify: `llm-inference-engine/tests/test_backend_comparison.cpp`
- Modify: `docs-site/docs/veilthorn/conformance.md`

- [ ] **Step 1: Write the conformance test before implementing the gate**

```cpp
// tests/test_conformance.cpp
int test_conformance_main() {
    GovernanceConfig config;
    HTTPServer server(config);

    InferenceRequest request;
    request.prompt = "conformance";
    request.max_tokens = 4;
    request.temperature = 0.0f;
    request.backend = "cpu";

    const auto first = server.handle_inference(request).to_json();
    const auto second = server.handle_inference(request).to_json();

    assert(first.contains("metadata"));
    assert(second.contains("metadata"));
    assert(first["metadata"]["governance_decision"] == second["metadata"]["governance_decision"]);
    assert(first["metadata"]["backend"] == "cpu");
    return 0;
}
```

- [ ] **Step 2: Wire the new conformance runner into the aggregate test binary**

Add `extern int test_conformance_main();` to `tests/test_main.cpp`, dispatch `--conformance`, and keep the existing unit/backend/integration flow intact.

- [ ] **Step 3: Implement the backend support gate**

Make the support gate fail closed unless the backend has passed all conformance checks for the declared proof level. The gate should report why a backend is not supported instead of inferring support from existence in code.

- [ ] **Step 4: Run the full engine test suite**

Run: `cmd.exe /c 'call C:\PROGRA~1\MICROS~1\18\COMMUN~1\VC\Auxiliary\Build\vcvars64.bat && cd /d E:\project-infi\llm-inference-engine && C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe --build build --parallel && .\build\llm-engine-tests.exe --all'`
Expected: PASS, with the conformance suite available as a first-class test mode.

- [ ] **Step 5: Commit the conformance gate**

```bash
git add llm-inference-engine/tests/test_conformance.cpp llm-inference-engine/tests/test_main.cpp llm-inference-engine/CMakeLists.txt llm-inference-engine/tests/test_backend_comparison.cpp docs-site/docs/veilthorn/conformance.md
git commit -m "test: add veilthorn conformance gate"
```

### Task 5: Final verification pass and doc/build release proof

**Files:**
- Modify: `docs-site/scripts/smoke-docs-site.mjs`
- Modify: `docs-site/docs/veilthorn/index.md`
- Modify: `docs-site/docs/runtime/node-v0-1.md`
- Modify: `docs-site/docs/overview.md`

- [ ] **Step 1: Make the docs smoke assert the Stage 1 pages and the Node v0.1 landing page**

Ensure the docs smoke fails if the VEILTHORN pages or the Node v0.1 landing page are missing from `dist/`.

- [ ] **Step 2: Rebuild the docs site and the engine from a clean state**

Run:
`corepack pnpm --dir docs-site verify`
`cmd.exe /c 'call C:\PROGRA~1\MICROS~1\18\COMMUN~1\VC\Auxiliary\Build\vcvars64.bat && cd /d E:\project-infi\llm-inference-engine && C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe --build build --parallel && .\build\llm-engine-tests.exe --all'`

Expected:
- Docs site verification passes.
- Engine build passes.
- Engine test binary passes.

- [ ] **Step 3: Update the overview docs to link the VEILTHORN material**

Add the VEILTHORN quick start and proof-surface links to `docs-site/docs/overview.md` so readers can find the new surface from the repo’s main docs landing page.

- [ ] **Step 4: Record the final release slice**

```bash
git add docs-site/docs/overview.md docs-site/docs/veilthorn docs-site/docs/runtime/node-v0-1.md docs-site/scripts/smoke-docs-site.mjs llm-inference-engine
git commit -m "docs: finalize veilthorn stage 1 release slice"
```
