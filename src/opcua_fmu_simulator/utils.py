# src/mypackage/utils.py
from __future__ import annotations
from pathlib import Path

# Absolute path to the repo root (…/mypackage/..)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def resolve_path(path: str | Path, base: Path | None = None) -> Path:
    """
    Resolve a relative or absolute path.
    - If `path` is absolute, return it unchanged.
    - If `path` is relative, resolve it against `base` (defaults to PROJECT_ROOT).
    """
    base = base or PROJECT_ROOT
    p = Path(path)
    return p if p.is_absolute() else base / p
