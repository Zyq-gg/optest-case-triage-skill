#!/usr/bin/env python3
"""Safely collect a small, reproducible PyTorch environment summary."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any


_AUTO_IMPORT = object()


def _safe_call(fn: Any, default: Any = None) -> Any:
    try:
        return fn()
    except Exception:
        return default


def _stringify_version(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _collect_devices(torch_module: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "cuda_available": False,
        "device_count": 0,
        "devices": [],
    }
    cuda = getattr(torch_module, "cuda", None)
    if cuda is None:
        return result

    available = bool(_safe_call(cuda.is_available, False))
    count = int(_safe_call(cuda.device_count, 0) or 0)
    result["cuda_available"] = available
    result["device_count"] = count

    devices: list[dict[str, Any]] = []
    for index in range(count):
        item: dict[str, Any] = {"index": index}
        name = _safe_call(lambda: cuda.get_device_name(index))
        if name is not None:
            item["name"] = str(name)
        capability = _safe_call(lambda: cuda.get_device_capability(index))
        if capability is not None:
            item["capability"] = list(capability)
        properties = _safe_call(lambda: cuda.get_device_properties(index))
        total_memory = getattr(properties, "total_memory", None)
        if total_memory is not None:
            item["total_memory_bytes"] = int(total_memory)
        devices.append(item)
    result["devices"] = devices
    return result


def _collect_torch(torch_module: Any, include_config: bool) -> dict[str, Any]:
    raw_torch_file = getattr(torch_module, "__file__", None)
    torch_file = Path(raw_torch_file).resolve() if raw_torch_file else None
    version_module = getattr(torch_module, "version", None)
    backends = getattr(torch_module, "backends", None)
    cudnn = getattr(backends, "cudnn", None)
    mps = getattr(backends, "mps", None)

    result: dict[str, Any] = {
        "imported": True,
        "version": str(getattr(torch_module, "__version__", "unknown")),
        "file": str(torch_file) if torch_file else None,
        "installed_validation_repo": str(torch_file.parent) if torch_file else None,
        "git_version": _stringify_version(getattr(version_module, "git_version", None)),
        "cuda_runtime": _stringify_version(getattr(version_module, "cuda", None)),
        "hip_runtime": _stringify_version(getattr(version_module, "hip", None)),
        "cudnn_version": _safe_call(cudnn.version) if cudnn is not None else None,
        "mps_available": bool(_safe_call(mps.is_available, False)) if mps is not None else False,
    }
    result.update(_collect_devices(torch_module))

    if include_config:
        config = getattr(torch_module, "__config__", None)
        result["build_config"] = _safe_call(config.show) if config is not None else None
    return result


def collect_environment(
    *,
    include_config: bool = False,
    torch_module: Any = _AUTO_IMPORT,
    torch_import_error: str | None = None,
) -> dict[str, Any]:
    """Collect environment data; dependency injection keeps no-torch tests deterministic."""

    result: dict[str, Any] = {
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    }

    if torch_module is _AUTO_IMPORT:
        try:
            import torch as imported_torch

            torch_module = imported_torch
        except Exception as exc:  # pragma: no cover - depends on host installation
            torch_module = None
            torch_import_error = f"{type(exc).__name__}: {exc}"

    if torch_module is None:
        result["torch"] = {
            "imported": False,
            "import_error": torch_import_error or "torch is unavailable",
        }
    else:
        result["torch"] = _collect_torch(torch_module, include_config)
    return result


def format_text(data: dict[str, Any]) -> str:
    python_data = data["python"]
    platform_data = data["platform"]
    torch_data = data["torch"]
    lines = [
        f"Python executable: {python_data['executable']}",
        f"Python version: {python_data['version']} ({python_data['implementation']})",
        f"Platform: {platform_data['system']} {platform_data['release']} {platform_data['machine']}",
    ]
    if not torch_data["imported"]:
        lines.append(f"PyTorch import: FAILED ({torch_data['import_error']})")
        return "\n".join(lines)

    lines.extend(
        [
            "PyTorch import: OK",
            f"PyTorch version: {torch_data['version']}",
            f"PyTorch file: {torch_data['file']}",
            f"Installed validation repo: {torch_data['installed_validation_repo']}",
            f"PyTorch git version: {torch_data['git_version']}",
            f"CUDA runtime: {torch_data['cuda_runtime']}",
            f"HIP runtime: {torch_data['hip_runtime']}",
            f"cuDNN version: {torch_data['cudnn_version']}",
            f"MPS available: {torch_data['mps_available']}",
            f"CUDA/HIP device available: {torch_data['cuda_available']}",
            f"Device count: {torch_data['device_count']}",
        ]
    )
    for device in torch_data["devices"]:
        details = [f"index={device['index']}"]
        for key in ("name", "capability", "total_memory_bytes"):
            if key in device:
                details.append(f"{key}={device[key]}")
        lines.append("Device: " + ", ".join(details))
    if "build_config" in torch_data:
        lines.append("Build config:")
        lines.append(str(torch_data["build_config"]))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect a safe PyTorch environment summary without dumping credentials or all environment variables."
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    parser.add_argument(
        "--include-config",
        action="store_true",
        help="Include torch.__config__.show(); this can be long and may contain build paths.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data = collect_environment(include_config=args.include_config)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_text(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
