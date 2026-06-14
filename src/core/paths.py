from __future__ import annotations

import sys
from pathlib import Path


def app_dir() -> Path:
    """Directory for user-writable runtime files."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    """Path to bundled read-only resources."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*parts)
    return Path(__file__).resolve().parents[1].joinpath(*parts)


def bundled_default_path(*parts: str) -> Path:
    """Path to files bundled as defaults, falling back to the repo root in dev."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*parts)
    return app_dir().joinpath(*parts)


def resolve_runtime_path(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return app_dir() / path
