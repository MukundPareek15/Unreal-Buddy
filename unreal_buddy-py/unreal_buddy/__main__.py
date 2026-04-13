"""UnrealBuddy entry point: `python -m unreal_buddy`."""

from __future__ import annotations

from unreal_buddy.app import run


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
