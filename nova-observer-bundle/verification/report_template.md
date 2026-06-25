# Mission #002 — Nova Integration Verification Report

## 1. Observer & Environment

**Observer Name:**  
**Date / Time (UTC):**  

**Machine Type (laptop/desktop/VM):**  
**CPU / RAM (optional):**  

**OS Name & Version:**  
**Cursor Version:**  
**Nova Version (if known):**  
**Nemotron Model:**  

**Tunnel URL Used:**  

---

## 2. Basic Request Test

**Prompt:**

```text
Hello Nova. Please confirm you are routing to Nemotron Ultra.
```

**Observed behavior:**

- Did the request succeed? YES / NO
- Any visible errors? (describe)
- Approximate latency:

**Response snippet (or attach logs):**

```text
<paste key part of the response here>
```

**Result:** PASS / FAIL

---

## 3. Agent Test

**Task:**

```text
Create a file named test.txt with the text "Nova integration test successful."
```

**Observed behavior:**

- Did the Agent activate? YES / NO
- Did tools appear to be used? YES / NO
- Was test.txt created? YES / NO
- Did test.txt contain the expected text? YES / NO

**Response snippet (or attach logs):**

```text
<paste key part of the response here>
```

**Result:** PASS / FAIL

---

## 4. Streaming Test

**Prompt:**

```text
Stream a 5-sentence response, one sentence at a time.
```

**Observed behavior:**

- Did the response arrive in multiple chunks? YES / NO
- Approximate number of chunks:
- Any streaming errors or glitches? (describe)

**Response snippet (or attach logs):**

```text
<paste key part of the response here>
```

**Result:** PASS / FAIL

---

## 5. Integration Hash

From `tools/integration_hash.py`:

**Observed metadata (if available):**

```json
<paste printed metadata here>
```

**Observed hash:**

```text
<observed hash>
```

**Expected hash (from expected_integration_hash.txt):**

```text
<expected hash>
```

**Match:** YES / NO

---

## 6. Founder Assistance

Did you require any help from a founder to complete these steps?  
**Answer:** YES / NO

If YES, describe exactly what was needed:

```text
<description>
```

---

## 7. Final Verdict

**Overall result:**

- [ ] All tests passed without founder assistance
- [ ] Some tests failed
- [ ] Founder assistance was required

**Summary (1–3 sentences):**

```text
<your summary of how the integration behaved>
```

**Additional notes / suggestions:**

```text
<anything else you think is important>
```
