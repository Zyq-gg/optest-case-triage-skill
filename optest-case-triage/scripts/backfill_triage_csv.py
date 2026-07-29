#!/usr/bin/env python3
"""Safely apply Markdown-derived optest summaries to four CSV columns.

The semantic analysis belongs to the agent following csv_report_backfill.md.
This helper only validates and applies an explicit JSON update plan.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


TARGET_HEADERS = ("测试目的", "解决方案", "最终状态", "遗留原因")


def read_csv(path: Path) -> tuple[list[list[str]], csv.Dialect, bool, str]:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig" if has_bom else "utf-8")
    if not text:
        raise ValueError(f"CSV is empty: {path}")

    try:
        dialect = csv.Sniffer().sniff(text[:65536], delimiters=",;\t|")
    except csv.Error as exc:
        raise ValueError(f"could not detect CSV delimiter: {exc}") from exc

    rows = list(csv.reader(text.splitlines(keepends=True), dialect))
    if not rows:
        raise ValueError(f"CSV has no rows: {path}")
    width = len(rows[0])
    if width == 0:
        raise ValueError("CSV header is empty")
    for number, row in enumerate(rows, start=1):
        if len(row) != width:
            raise ValueError(
                f"CSV row {number} has {len(row)} fields; header has {width}"
            )

    line_ending = "\r\n" if b"\r\n" in raw else "\n"
    return rows, dialect, has_bom, line_ending


def validate_headers(headers: list[str]) -> dict[str, int]:
    missing = [header for header in TARGET_HEADERS if header not in headers]
    if missing:
        raise ValueError(f"missing target headers: {missing}")
    duplicates = [header for header in TARGET_HEADERS if headers.count(header) > 1]
    if duplicates:
        raise ValueError(f"duplicate target headers: {duplicates}")
    return {header: headers.index(header) for header in TARGET_HEADERS}


def load_plan(path: Path) -> dict[str, Any]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON plan: {exc}") from exc
    if not isinstance(plan, dict):
        raise ValueError("plan root must be a JSON object")
    if not str(plan.get("source_markdown", "")).strip():
        raise ValueError("plan must name its authoritative source_markdown")
    updates = plan.get("updates")
    if not isinstance(updates, list) or not updates:
        raise ValueError("plan updates must be a non-empty array")
    return plan


def apply_plan(rows: list[list[str]], plan: dict[str, Any]) -> list[int]:
    headers = rows[0]
    target_indexes = validate_headers(headers)
    header_indexes = {header: index for index, header in enumerate(headers)}
    updated_rows: list[int] = []
    seen_rows: set[int] = set()

    for item_number, update in enumerate(plan["updates"], start=1):
        if not isinstance(update, dict):
            raise ValueError(f"update {item_number} must be an object")
        row_number = update.get("row")
        if not isinstance(row_number, int) or isinstance(row_number, bool):
            raise ValueError(f"update {item_number} row must be an integer")
        if row_number < 2 or row_number > len(rows):
            raise ValueError(
                f"update {item_number} row {row_number} is outside 2..{len(rows)}"
            )
        if row_number in seen_rows:
            raise ValueError(f"CSV row {row_number} is updated more than once")
        seen_rows.add(row_number)

        identity = update.get("identity")
        if not isinstance(identity, dict) or not identity:
            raise ValueError(f"update {item_number} must include identity fields")
        for header, expected in identity.items():
            if header not in header_indexes:
                raise ValueError(
                    f"update {item_number} identity header {header!r} is absent"
                )
            if headers.count(header) != 1:
                raise ValueError(
                    f"update {item_number} identity header {header!r} is not unique"
                )
            actual = rows[row_number - 1][header_indexes[header]]
            if actual != str(expected):
                raise ValueError(
                    f"row {row_number} identity mismatch for {header!r}: "
                    f"expected {expected!r}, found {actual!r}"
                )

        values = update.get("values")
        if not isinstance(values, dict):
            raise ValueError(f"update {item_number} values must be an object")
        missing = [header for header in TARGET_HEADERS if header not in values]
        extra = sorted(set(values) - set(TARGET_HEADERS))
        if missing or extra:
            raise ValueError(
                f"update {item_number} values must contain exactly "
                f"{list(TARGET_HEADERS)}; missing={missing}, extra={extra}"
            )
        for header in TARGET_HEADERS:
            value = values[header]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"update {item_number} value for {header!r} must be non-empty text"
                )
            rows[row_number - 1][target_indexes[header]] = value
        updated_rows.append(row_number)

    return updated_rows


def write_csv(
    path: Path,
    rows: list[list[str]],
    dialect: csv.Dialect,
    has_bom: bool,
    line_ending: str,
    before: list[list[str]],
    updated_rows: list[int],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoding = "utf-8-sig" if has_bom else "utf-8"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            writer = csv.writer(handle, dialect=dialect, lineterminator=line_ending)
            writer.writerows(rows)
        written, _, written_bom, _ = read_csv(temporary)
        if written_bom != has_bom:
            raise ValueError("output BOM state changed")
        verify_output(before, written, updated_rows)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def verify_output(
    before: list[list[str]], after: list[list[str]], updated_rows: list[int]
) -> None:
    if len(before) != len(after):
        raise ValueError("output row count changed")
    if before[0] != after[0]:
        raise ValueError("output headers changed")

    target_indexes = set(validate_headers(before[0]).values())
    for row_number, (old_row, new_row) in enumerate(zip(before, after), start=1):
        if len(old_row) != len(new_row):
            raise ValueError(f"output width changed at row {row_number}")
        for index, (old_value, new_value) in enumerate(zip(old_row, new_row)):
            if index not in target_indexes and old_value != new_value:
                raise ValueError(
                    f"non-target column {before[0][index]!r} changed at row {row_number}"
                )
        if row_number not in updated_rows:
            for index in target_indexes:
                if old_row[index] != new_row[index]:
                    raise ValueError(
                        f"unplanned target cell changed at row {row_number}"
                    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply an explicit Markdown-derived JSON plan to the 测试目的、解决方案、"
            "最终状态、遗留原因 CSV columns."
        )
    )
    parser.add_argument("--csv", type=Path, required=True, help="Input CSV")
    parser.add_argument("--plan", type=Path, required=True, help="JSON update plan")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output", type=Path, help="Write a new CSV")
    destination.add_argument(
        "--in-place", action="store_true", help="Atomically replace the input CSV"
    )
    parser.add_argument(
        "--force", action="store_true", help="Allow overwriting an existing --output"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate the plan without writing"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not args.dry_run and not args.output and not args.in_place:
            raise ValueError("choose --output or --in-place, or use --dry-run")
        if args.output and args.output.resolve() == args.csv.resolve():
            raise ValueError("use --in-place when output is the input CSV")
        if args.output and args.output.exists() and not args.force and not args.dry_run:
            raise ValueError(f"output exists; pass --force to replace it: {args.output}")

        before, dialect, has_bom, line_ending = read_csv(args.csv)
        plan = load_plan(args.plan)
        after = [row.copy() for row in before]
        updated_rows = apply_plan(after, plan)

        if args.dry_run:
            print(
                f"validated {len(updated_rows)} updates from "
                f"{plan['source_markdown']}; no file written"
            )
            return 0

        output = args.csv if args.in_place else args.output
        assert output is not None
        write_csv(
            output,
            after,
            dialect,
            has_bom,
            line_ending,
            before,
            updated_rows,
        )
        written, _, written_bom, _ = read_csv(output)
        if written_bom != has_bom:
            raise ValueError("output BOM state changed")
        verify_output(before, written, updated_rows)
        print(
            f"updated {len(updated_rows)} rows in {output} from "
            f"{plan['source_markdown']}"
        )
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
