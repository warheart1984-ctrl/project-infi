# Expected Output — Agent Request

## Task

```text
Create a file named test.txt with the text "Nova integration test successful."
```

## Expected characteristics

- Cursor Agent activates and begins a tool-driven workflow.
- You see:
  - A plan or reasoning step.
  - One or more tool calls (e.g., file operations).
  - A final confirmation message.
- After completion, a file named `test.txt` exists in the workspace.
- The contents of `test.txt` are exactly:

```text
Nova integration test successful.
```

## Examples of acceptable final messages

- “I’ve created test.txt with the requested content.”
- “The file test.txt now contains: ‘Nova integration test successful.’”

You are checking that:

- The Agent path works end-to-end.
- Tools are invoked correctly.
- The final state of the workspace matches the request.
