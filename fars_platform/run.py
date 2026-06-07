#!/usr/bin/env python3
"""
FARS Production Simulation — single entry point.

Usage (from project root):
    python fars_platform/run.py
    python fars_platform/run.py --no-3d
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fars_platform.orchestrator import run_platform  # noqa: E402

if __name__ == "__main__":
    try:
        run_platform(with_3d="--no-3d" not in sys.argv)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
        sys.exit(0)
    except Exception as exc:
        print(f"\nFATAL: {exc}", flush=True)
        import traceback

        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
