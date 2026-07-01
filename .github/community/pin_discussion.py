#!/usr/bin/env python3
"""Document pin state for co-builder discussion #9.

GitHub GraphQL exposes pinIssue / pinIssueComment but NOT pinDiscussion.
Pinning must be done in the web UI (see docs/community/HELP_WANTED_HUB.md).
"""
from __future__ import annotations

import json
import subprocess
import sys

OWNER = "warheart1984-ctrl"
REPO = "Project-Infinity1"
DISCUSSION_NUMBER = 9

QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pinnedDiscussions(first: 10) {
      nodes {
        discussion {
          number
          title
          url
        }
      }
    }
    discussion(number: %d) {
      title
      url
    }
  }
}
""" % DISCUSSION_NUMBER


def main() -> int:
    proc = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"owner={OWNER}", "-f", f"name={REPO}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return proc.returncode

    data = json.loads(proc.stdout)
    repo = data["data"]["repository"]
    target = repo["discussion"]
    pinned = [n["discussion"] for n in repo["pinnedDiscussions"]["nodes"]]

    print(f"Target: #{DISCUSSION_NUMBER} {target['title']}")
    print(target["url"])
    print()
    if any(d["number"] == DISCUSSION_NUMBER for d in pinned):
        print("Status: PINNED")
        return 0

    print("Status: NOT PINNED")
    print("Action: open the URL above -> Pin discussion (UI only)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
