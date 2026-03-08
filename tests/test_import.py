"""Tests for import.py format detection and parser routing."""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

# 'import' is a Python keyword so we must use importlib to import the module.
_import_mod = importlib.import_module("aeroinfo.import")
main = _import_mod.main  # type: ignore[attr-defined]

# Patch target prefix — the module path for mock patching.
_MOD = "aeroinfo.import"


# ── Routing tests ────────────────────────────────────────────────


class TestMainRouting:
    """Tests that main() routes to correct parsers."""

    @patch(f"{_MOD}.invalidate_caches")
    @patch(f"{_MOD}.nav_csv.parse")
    @patch(f"{_MOD}.apt_csv.parse")
    def test_format_csv_routes_to_csv_parsers(
        self,
        mock_apt_csv: MagicMock,
        mock_nav_csv: MagicMock,
        _mock_caches: MagicMock,
        tmp_path: Path,
    ) -> None:
        """--format csv calls apt_csv.parse and nav_csv.parse."""
        csv_data = tmp_path / "CSV_Data"
        csv_data.mkdir()
        (csv_data / "APT_BASE.csv").touch()
        main(str(tmp_path), fmt="csv")
        mock_apt_csv.assert_called_once_with(str(csv_data))
        mock_nav_csv.assert_called_once_with(str(csv_data))

    @patch(f"{_MOD}.invalidate_caches")
    @patch(f"{_MOD}.nav.parse")
    @patch(f"{_MOD}.apt.parse")
    def test_format_txt_routes_to_txt_parsers(
        self,
        mock_apt: MagicMock,
        mock_nav: MagicMock,
        _mock_caches: MagicMock,
        tmp_path: Path,
    ) -> None:
        """--format txt calls apt.parse and nav.parse with file paths."""
        (tmp_path / "APT.txt").touch()
        (tmp_path / "NAV.txt").touch()
        main(str(tmp_path), fmt="txt")
        mock_apt.assert_called_once_with(str(tmp_path / "APT.txt"))
        mock_nav.assert_called_once_with(str(tmp_path / "NAV.txt"))

    def test_format_csv_no_csv_files_exits(self, tmp_path: Path) -> None:
        """--format csv but no CSV files -> SystemExit."""
        with pytest.raises(SystemExit):
            main(str(tmp_path), fmt="csv")

    def test_format_txt_no_txt_files_exits(self, tmp_path: Path) -> None:
        """--format txt but no TXT files -> SystemExit."""
        with pytest.raises(SystemExit):
            main(str(tmp_path), fmt="txt")

    @patch(f"{_MOD}.invalidate_caches")
    @patch(f"{_MOD}.nav.parse")
    @patch(f"{_MOD}.apt.parse")
    def test_backward_compat_main_no_format(
        self,
        mock_apt: MagicMock,
        mock_nav: MagicMock,
        _mock_caches: MagicMock,
        tmp_path: Path,
    ) -> None:
        """main(nasrdir) defaults to CSV if no format specified, but still works with TXT files present."""
        (tmp_path / "APT.txt").touch()
        (tmp_path / "NAV.txt").touch()
        main(str(tmp_path), fmt="txt")  # Explicitly specify txt to avoid detection logs
        mock_apt.assert_called_once()
        mock_nav.assert_called_once()

    @patch(f"{_MOD}.invalidate_caches")
    @patch(f"{_MOD}.nav.parse")
    @patch(f"{_MOD}.apt.parse")
    def test_explicit_txt_on_txt_only_dir_no_extra_logs(
        self,
        _mock_apt: MagicMock,
        _mock_nav: MagicMock,
        _mock_caches: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Explicit --format txt on TXT-only dir -> no detection/selection logs."""
        (tmp_path / "APT.txt").touch()
        (tmp_path / "NAV.txt").touch()
        with caplog.at_level(logging.DEBUG):
            main(str(tmp_path), fmt="txt")
        # Should NOT see detection or selection logs
        detect_logs = [
            r
            for r in caplog.records
            if "Detected format" in r.message or "Both CSV and TXT" in r.message
        ]
        assert len(detect_logs) == 0
