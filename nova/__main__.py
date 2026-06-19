"""Allow `python -m nova` to invoke the lawful Nova CLI."""

from nova.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
