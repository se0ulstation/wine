#!/usr/bin/env python3
"""Validate, then regenerate everything.

    python3 scripts/build.py

The check runs first and a failure stops the build, so a bad edit cannot reach
CELLAR.md, PRICES.md or the two copies of the dashboard. Use this rather than
the individual generators — running one of them alone is how the outputs drift
apart, which is the failure this layout exists to prevent.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["check.py", "build_cellar.py", "build_prices.py", "build_dashboard.py"]


def main():
    for step in STEPS:
        r = subprocess.run([sys.executable, str(HERE / step)])
        if r.returncode:
            print(f"\n{step} failed — nothing further was generated.", file=sys.stderr)
            return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
