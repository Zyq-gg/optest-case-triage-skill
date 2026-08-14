from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_runtime_sync.py"
SPEC = importlib.util.spec_from_file_location("verify_runtime_sync", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerifyRuntimeSyncTest(unittest.TestCase):
    def test_compare_matching_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.py"
            runtime = root / "runtime.py"
            source.write_bytes(b"same bytes\n")
            runtime.write_bytes(b"same bytes\n")

            result = MODULE.compare_files(source, runtime)

        self.assertTrue(result["matches"])
        self.assertEqual(result["source"]["sha256"], result["runtime"]["sha256"])

    def test_cli_mismatch_returns_one_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.py"
            runtime = root / "runtime.py"
            source.write_bytes(b"source\n")
            runtime.write_bytes(b"runtime\n")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source",
                    str(source),
                    "--runtime",
                    str(runtime),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertFalse(json.loads(completed.stdout)["matches"])

    def test_cli_missing_file_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source",
                    str(root / "missing-source.py"),
                    "--runtime",
                    str(root / "missing-runtime.py"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("FileNotFoundError", completed.stderr)

    def test_text_output_labels_both_roles(self) -> None:
        result = {
            "source": {"path": "/code/a.py", "size_bytes": 1, "sha256": "a"},
            "runtime": {"path": "/runtime/a.py", "size_bytes": 1, "sha256": "a"},
            "matches": True,
        }
        output = MODULE.format_text(result)
        self.assertIn("Code-record file: /code/a.py", output)
        self.assertIn("Runtime file: /runtime/a.py", output)
        self.assertIn("Byte-for-byte match: yes", output)


if __name__ == "__main__":
    unittest.main()
