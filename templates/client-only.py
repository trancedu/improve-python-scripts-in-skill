#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27",
#   "rich>=13.0",
# ]
# ///
"""One-line description of what this script does.

Usage:
    uv run client-only.py --input FILE [--output FILE]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--output", default="output.csv", help="Output file path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: {input_path} does not exist", file=sys.stderr)
        sys.exit(1)

    # --- replace this block with your actual logic ---
    output_path = Path(args.output)
    output_path.write_text(input_path.read_text())  # TODO: real processing here
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
