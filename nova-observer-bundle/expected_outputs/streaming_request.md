# Expected Output — Streaming Request

## Prompt

```text
Stream a 5-sentence response, one sentence at a time.
```

## Expected characteristics

- The response is delivered in multiple chunks, not as a single buffered message.
- You can observe tokens or sentences arriving incrementally.
- The final response consists of approximately 5 sentences.
- There are no streaming errors or protocol failures.

## Examples of acceptable behavior

- You see sentence 1 appear, then sentence 2, etc., with small pauses.
- Cursor’s UI shows streaming indicators (if applicable).

You are checking that:

- Streaming is enabled and functioning.
- The integration supports incremental output over the tunnel.
