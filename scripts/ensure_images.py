#!/usr/bin/env python3
"""
Run the full image asset pipeline in one command:
1) backfill images
2) regenerate thumbnails
3) audit coverage
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path) -> int:
    print(f"\n$ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd))
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill images, regenerate thumbnails, and audit coverage.")
    parser.add_argument(
        "--data-dir",
        default="exports/frontend",
        help="Directory containing YAML files for download step (default: exports/frontend).",
    )
    parser.add_argument(
        "--dimension",
        action="append",
        default=[],
        help="Only run downloader for this dimension slug (repeatable).",
    )
    parser.add_argument("--skip-download", action="store_true", help="Skip image backfill step.")
    parser.add_argument("--skip-thumbnails", action="store_true", help="Skip thumbnail generation step.")
    parser.add_argument("--allow-placeholders", action="store_true", help="Pass through to download_images.py.")
    parser.add_argument("--show", type=int, default=60, help="How many missing records to print in final audit.")
    parser.add_argument("--no-validate", action="store_true", help="Final audit checks only file existence.")
    parser.add_argument("--by-dimension", action="store_true", help="Print missing counts by dimension in final audit.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent

    if not args.skip_download:
        if args.dimension:
            for dim in args.dimension:
                cmd = ["python3", "scripts/download_images.py", "--dimension", dim]
                cmd.extend(["--data-dir", args.data_dir])
                if args.allow_placeholders:
                    cmd.append("--allow-placeholders")
                code = run_cmd(cmd, root)
                if code != 0:
                    return code
        else:
            cmd = ["python3", "scripts/download_images.py"]
            cmd.extend(["--data-dir", args.data_dir])
            if args.allow_placeholders:
                cmd.append("--allow-placeholders")
            code = run_cmd(cmd, root)
            if code != 0:
                return code

    if not args.skip_thumbnails:
        code = run_cmd(["python3", "scripts/generate_thumbnails.py"], root)
        if code != 0:
            return code

    check_cmd = ["python3", "scripts/check_images.py", "--show", str(args.show)]
    if args.no_validate:
        check_cmd.append("--no-validate")
    if args.by_dimension:
        check_cmd.append("--by-dimension")
    return run_cmd(check_cmd, root)


if __name__ == "__main__":
    raise SystemExit(main())
