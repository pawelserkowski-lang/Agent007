"""
Convenience launcher for DebugDruid.

This wrapper ensures the repository root is on PYTHONPATH and invokes
``main.py`` with the current Python interpreter.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


def _build_pythonpath(resolved_root: Path, existing_pythonpath: str | None) -> str:
    """Return a PYTHONPATH that prefixes the repo root without duplicates."""

    parts = [str(resolved_root)]
    if existing_pythonpath:
        for entry in existing_pythonpath.split(os.pathsep):
            if entry and entry not in parts:
                parts.append(entry)
    return os.pathsep.join(parts)


def build_launch_command(repo_root: Path, python_executable: str | None = None) -> list[str]:
    """Return the command that launches the app.

    Args:
        repo_root: Directory containing ``main.py``.
        python_executable: Optional Python interpreter to use. Defaults to ``sys.executable``.

    Raises:
        FileNotFoundError: If ``main.py`` is missing.
    """

    executable = python_executable or sys.executable
    main_path = repo_root / "main.py"
    if not main_path.exists():
        raise FileNotFoundError(f"main.py not found in {repo_root}")
    return [executable, str(main_path)]


def launch_app(command: Iterable[str] | None = None, *, repo_root: Path | None = None) -> None:
    """Launch the DebugDruid app and exit with an informative message on failure."""

    resolved_root = repo_root or Path(__file__).resolve().parent
    env = os.environ.copy()
    env["PYTHONPATH"] = _build_pythonpath(resolved_root, env.get("PYTHONPATH"))
    cmd: List[str] = list(command or build_launch_command(resolved_root))

    try:
        subprocess.run(cmd, cwd=resolved_root, env=env, check=True)
    except FileNotFoundError as exc:  # Missing interpreter or main.py
        raise SystemExit(f"Launcher failed: {exc}") from exc
    except subprocess.CalledProcessError as exc:  # main.py failed
        raise SystemExit(exc.returncode) from exc


if __name__ == "__main__":
    launch_app()
