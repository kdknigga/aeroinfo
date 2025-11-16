"""Pytest configuration for Aeroinfo integration tests."""

from __future__ import annotations

import os
from pathlib import Path


def _load_env_file() -> None:
    """Populate os.environ from the repository's .env file if present."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        line = line.removeprefix("export ")

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if value.startswith(("'", '"')) and value.endswith(("'", '"')):
            value = value[1:-1]

        os.environ.setdefault(key, value)


_load_env_file()
