# Nova Observer Bundle — Mission #002 (Nova ↔ Nemotron ↔ Cursor)

This bundle is designed for an **independent tester** to verify the Nova ↔ Nemotron Ultra ↔ Cursor integration on a **fresh machine**, without founder assistance.

The goal is to reproduce a working integration path:

```
Request → Adapter → Nova → Nemotron Ultra → Response
```

and confirm that the integration is **reproducible, legible, and founder-independent**.

---

## 1. Prerequisites

- Fresh machine (no prior Nova or Cursor configuration)
- Internet connection
- Latest public Cursor build installed
- Public tunnel URL (provided in `tunnel_url.txt`)
- Nemotron Ultra available as a model option in Cursor
- Python 3.10+ installed (for the integration hash tool)

You do **not** need:

- Access to any private repositories
- Founder credentials
- Custom environment variables

---

## 2. High-level checklist

You will:

1. Configure Cursor to use the Nova endpoint via the public tunnel.
2. Confirm a basic request routes to Nemotron Ultra.
3. Confirm Cursor Agent works through the Responses API adapter.
4. Confirm streaming responses work.
5. Compute the integration hash and compare it to the expected value.
6. Fill out and submit the verification report.

---

## 3. Step-by-step instructions

### 3.1 Configure Cursor

1. Open `tunnel_url.txt` and copy the URL.
2. In Cursor, open **Settings → Models** and enable **Override OpenAI Base URL**.
3. Paste the tunnel URL as the endpoint (must end with `/v1`).
4. Set API key to `local-nova` (placeholder accepted by the mission endpoint).
5. Add custom model `lawful-nova` or `nvidia/nemotron-3-ultra-550b-a55b`.
6. Select **Nemotron Ultra** as the backing model, if applicable.

No additional configuration should be required. If connections fail, try **Settings → Network → HTTP/1.1**.

### 3.2 Basic request test

In Cursor, send the following prompt through the Nova endpoint:

```text
Hello Nova. Please confirm you are routing to Nemotron Ultra.
```

**Expected behavior** (see `expected_outputs/basic_request.md`):

- A coherent response that acknowledges the request.
- No errors, no fallbacks, no obvious misrouting.

### 3.3 Agent test

In Cursor, invoke the Agent and issue this task:

```text
Create a file named test.txt with the text "Nova integration test successful."
```

**Expected behavior** (see `expected_outputs/agent_request.md`):

- The Agent calls tools / performs actions.
- A file named `test.txt` is created with the specified content.
- The model provides a summary of what it did.

### 3.4 Streaming test

In Cursor, send:

```text
Stream a 5-sentence response, one sentence at a time.
```

**Expected behavior** (see `expected_outputs/streaming_request.md`):

- The response arrives incrementally (streaming).
- You see multiple chunks, not a single buffered message.

### 3.5 Integration hash

From the `nova-observer-bundle/tools` directory, run:

```bash
python integration_hash.py
```

This will:

- Collect version and configuration details.
- Compute a deterministic SHA-256 digest.
- Print the integration hash.
- Write `integration_hash_observed.txt` in the bundle root.

Compare the printed hash to `expected_integration_hash.txt`. They should match exactly when `tunnel_url.txt` matches the mission dispatch.

Optional: set `CURSOR_VERSION` or `NOVA_VERSION` in your shell before running the hash tool if the mission coordinator supplied those values.

### 3.6 Verification report

Open `verification/report_template.md`.

Fill in all fields, including:

- Environment details
- Observed outputs
- Integration hash
- Whether any founder assistance was required

Save the completed report as `verification/report_<your_name>.md`.

Return this report and any requested logs to the mission coordinator.

---

## 4. Success criteria

Your run is considered a successful reproduction if:

- Basic request works as expected.
- Agent task works as expected.
- Streaming works as expected.
- Integration hash matches `expected_integration_hash.txt`.
- You required no founder assistance.
- You completed and submitted the verification report.

If any step fails, document the behavior in the report template.

---

## 5. Support

You should attempt to complete all steps without live help.

If you become completely blocked, note exactly where and how in the report. That information is still valuable for improving the integration and the observer bundle.

---

## Directory layout

```text
nova-observer-bundle/
├── README.md
├── tunnel_url.txt
├── expected_integration_hash.txt
├── expected_outputs/
│   ├── basic_request.md
│   ├── agent_request.md
│   └── streaming_request.md
├── verification/
│   ├── report_template.md
│   └── instructions.md
└── tools/
    └── integration_hash.py
```

## Related (mission coordinator)

- Full dossier: `docs/proof/NOVA_CURSOR_MISSION_002_DOSSIER.md`
- Mission #001 analogue: `observer-bundle/` (Bone King continuity proof)
