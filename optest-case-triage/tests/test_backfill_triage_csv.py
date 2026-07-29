from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "backfill_triage_csv.py"
TARGET_HEADERS = ("测试目的", "解决方案", "最终状态", "遗留原因")


class BackfillTriageCsvTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.csv_path = self.root / "input.csv"
        self.plan_path = self.root / "plan.json"
        self.output_path = self.root / "output.csv"
        self.headers = [
            "test_file",
            "class_name",
            "case_name",
            "错误结果",
            *TARGET_HEADERS,
            "问题结论",
            "",
            "",
        ]
        self.rows = [
            self.headers,
            [
                "test/a.py",
                "TestA",
                "test_one",
                "old, error",
                "old purpose",
                "old solution",
                "old status",
                "old residual",
                "historical\nnote",
                "",
                "",
            ],
            [
                "test/b.py",
                "TestB",
                "test_two",
                "",
                "keep purpose",
                "keep solution",
                "keep status",
                "keep residual",
                "",
                "",
                "",
            ],
        ]
        with self.csv_path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as handle:
            csv.writer(handle, lineterminator="\r\n").writerows(self.rows)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_plan(self, identity_case: str = "test_one") -> None:
        plan = {
            "source_markdown": "/workspace/report.md",
            "reference_columns": ["问题结论"],
            "updates": [
                {
                    "row": 2,
                    "identity": {
                        "test_file": "test/a.py",
                        "class_name": "TestA",
                        "case_name": identity_case,
                    },
                    "values": {
                        "测试目的": "验证算子结果。",
                        "解决方案": "当前环境实测通过，无需源码修改。",
                        "最终状态": "pass",
                        "遗留原因": "无；历史错误未复现。",
                    },
                }
            ],
        }
        self.plan_path.write_text(
            json.dumps(plan, ensure_ascii=False), encoding="utf-8"
        )

    def run_script(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--csv",
                str(self.csv_path),
                "--plan",
                str(self.plan_path),
                *extra,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def read_rows(self, path: Path) -> list[list[str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))

    def test_updates_only_planned_target_cells_and_preserves_bom(self) -> None:
        self.write_plan()
        result = self.run_script("--output", str(self.output_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.output_path.read_bytes().startswith(b"\xef\xbb\xbf"))

        actual = self.read_rows(self.output_path)
        target_indexes = [self.headers.index(header) for header in TARGET_HEADERS]
        non_target_indexes = [
            index for index in range(len(self.headers)) if index not in target_indexes
        ]
        for index in non_target_indexes:
            self.assertEqual(actual[1][index], self.rows[1][index])
        self.assertEqual(
            [actual[1][index] for index in target_indexes],
            [
                "验证算子结果。",
                "当前环境实测通过，无需源码修改。",
                "pass",
                "无；历史错误未复现。",
            ],
        )
        self.assertEqual(actual[2], self.rows[2])

    def test_identity_mismatch_fails_without_output(self) -> None:
        self.write_plan(identity_case="wrong_case")
        result = self.run_script("--output", str(self.output_path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("identity mismatch", result.stderr)
        self.assertFalse(self.output_path.exists())

    def test_dry_run_does_not_write(self) -> None:
        self.write_plan()
        result = self.run_script("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validated 1 updates", result.stdout)
        self.assertFalse(self.output_path.exists())


if __name__ == "__main__":
    unittest.main()
