#!/usr/bin/env python3
"""Extract qemu-smoke.sh from agent transcript Write tool call."""
import json
import sys
from pathlib import Path

transcript = Path(
    "/mnt/c/Users/randj/.cursor/projects/e/agent-transcripts"
    "/3637969d-f634-46d3-873c-382fe92adfd0/3637969d-f634-46d3-873c-382fe92adfd0.jsonl"
)
if not transcript.is_file():
    transcript = Path(__file__).resolve().parents[2].parent / (
        "agent-transcripts/3637969d-f634-46d3-873c-382fe92adfd0/"
        "3637969d-f634-46d3-873c-382fe92adfd0.jsonl"
    )
out = Path(__file__).resolve().parents[1] / "cog-os" / "scripts" / "test" / "qemu-smoke.sh"

best = ""
for line in transcript.read_text(encoding="utf-8").splitlines():
    o = json.loads(line)
    for part in o.get("message", {}).get("content", []):
        if part.get("type") != "tool_use" or part.get("name") != "Write":
            continue
        inp = part.get("input", {})
        p = inp.get("path", "").replace("\\", "/")
        if not p.endswith("qemu-smoke.sh"):
            continue
        contents = inp.get("contents", "")
        if len(contents) > len(best):
            best = contents

if not best:
    print("not found", file=sys.stderr)
    sys.exit(1)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(best.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(best)} bytes)")
