#!/usr/bin/env python3
"""Verify that a code-record file and a runtime mirror have identical bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _file_info(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    data = resolved.read_bytes()
    return {
        "path": str(resolved),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def compare_files(source: Path, runtime: Path) -> dict[str, Any]:
    """Return reproducible metadata and a byte-for-byte comparison result."""

    source_info = _file_info(source)
    runtime_info = _file_info(runtime)
    return {
        "source": source_info,
        "runtime": runtime_info,
        "matches": (
            source_info["size_bytes"] == runtime_info["size_bytes"]
            and source_info["sha256"] == runtime_info["sha256"]
        ),
    }


def format_text(result: dict[str, Any]) -> str:
    source = result["source"]
    runtime = result["runtime"]
    return "\n".join(
        (
            f"Code-record file: {source['path']}",
            f"Code-record SHA256: {source['sha256']}",
            f"Runtime file: {runtime['path']}",
            f"Runtime SHA256: {runtime['sha256']}",
            f"Byte-for-byte match: {'yes' if result['matches'] else 'no'}",
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare one code-record source file with its installed runtime mirror "
            "using size and SHA256 without modifying either file."
        )
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = compare_files(args.source, args.runtime)
    except OSError as exc:
        print(f"verify_runtime_sync: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_text(result))
    return 0 if result["matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
