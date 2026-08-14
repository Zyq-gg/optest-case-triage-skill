from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "collect_pytorch_env.py"
SPEC = importlib.util.spec_from_file_location("collect_pytorch_env", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CollectPyTorchEnvTest(unittest.TestCase):
    def test_no_torch_result_is_structured(self) -> None:
        result = MODULE.collect_environment(
            torch_module=None,
            torch_import_error="ImportError: missing",
        )
        self.assertIn("python", result)
        self.assertIn("platform", result)
        self.assertEqual(
            result["torch"],
            {"imported": False, "import_error": "ImportError: missing"},
        )
        self.assertIn("PyTorch import: FAILED", MODULE.format_text(result))

    def test_json_cli_is_parseable(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["python"]["executable"], sys.executable)
        self.assertIsInstance(result["torch"]["imported"], bool)
        self.assertNotIn("environment", result)

    def test_fake_torch_reports_validation_repo_and_device(self) -> None:
        class FakeCuda:
            @staticmethod
            def is_available() -> bool:
                return True

            @staticmethod
            def device_count() -> int:
                return 1

            @staticmethod
            def get_device_name(index: int) -> str:
                return f"fake-{index}"

            @staticmethod
            def get_device_capability(index: int) -> tuple[int, int]:
                return (9, index)

            @staticmethod
            def get_device_properties(index: int) -> SimpleNamespace:
                return SimpleNamespace(total_memory=1024 + index)

        fake_torch = SimpleNamespace(
            __file__="/opt/fake/torch/__init__.py",
            __version__="9.9.9",
            version=SimpleNamespace(git_version="abc", cuda="99", hip=None),
            cuda=FakeCuda(),
            backends=SimpleNamespace(
                cudnn=SimpleNamespace(version=lambda: 123),
                mps=SimpleNamespace(is_available=lambda: False),
            ),
        )
        result = MODULE.collect_environment(torch_module=fake_torch)["torch"]
        self.assertEqual(result["installed_validation_repo"], "/opt/fake/torch")
        self.assertEqual(result["device_count"], 1)
        self.assertEqual(result["devices"][0]["name"], "fake-0")

    def test_help_describes_safe_scope(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("without dumping credentials", completed.stdout)


if __name__ == "__main__":
    unittest.main()
