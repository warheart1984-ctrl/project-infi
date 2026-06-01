"""Run the Mechanic hosted pilot API."""

from __future__ import annotations

import uvicorn


def main() -> int:
    uvicorn.run("mechanic.hosted.api:app", host="127.0.0.1", port=8765, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
