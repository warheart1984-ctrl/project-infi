#!/usr/bin/env python3
"""One-shot: create Stage 18 co-builders GitHub Discussion via gh api graphql."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
body = (ROOT / "discussion-body.md").read_text(encoding="utf-8")

payload = {
    "query": """
mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
  createDiscussion(
    input: {
      repositoryId: $repositoryId
      categoryId: $categoryId
      title: $title
      body: $body
    }
  ) {
    discussion {
      id
      number
      url
    }
  }
}
""",
    "variables": {
        "repositoryId": "R_kgDOSq9j5g",
        "categoryId": "DIC_kwDOSq9j5s4C-uUU",
        "title": "Stage 18 — Call for Co-Builders (Specific Roles Open)",
        "body": body,
    },
}

result = subprocess.run(
    ["gh", "api", "graphql", "--input", "-"],
    input=json.dumps(payload),
    capture_output=True,
    text=True,
    check=False,
)
print(result.stdout)
if result.stderr:
    print(result.stderr, end="")
raise SystemExit(result.returncode)
