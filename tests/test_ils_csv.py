"""Unit tests for ILS_BASE.csv parser (approach_type lookup builder)."""

from __future__ import annotations

from pathlib import Path

import pytest


def _write_csv(tmp_path: Path, rows: list[str], filename: str = "ILS_BASE.csv") -> Path:
    """Write a minimal ILS_BASE.csv with given rows (first row is header)."""
    p = tmp_path / filename
    p.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return p


class TestBuildApproachTypeLookup:
    """Tests for ils_csv.build_approach_type_lookup."""

    def test_all_nine_system_type_codes(self, tmp_path: Path) -> None:
        """All 9 SYSTEM_TYPE_CODE values map to correct approach_type strings."""
        from aeroinfo.parsers.ils_csv import build_approach_type_lookup

        header = '"SITE_NO","RWY_END_ID","SYSTEM_TYPE_CODE"'
        rows = [
            header,
            '"S01","01","LS"',
            '"S02","02","SF"',
            '"S03","03","LC"',
            '"S04","04","LA"',
            '"S05","05","LD"',
            '"S06","06","SD"',
            '"S07","07","LE"',
            '"S08","08","LG"',
            '"S09","09","DD"',
        ]
        p = _write_csv(tmp_path, rows)
        lookup = build_approach_type_lookup(p)

        assert lookup[("S01", "01")] == "ILS"
        assert lookup[("S02", "02")] == "SDF"
        assert lookup[("S03", "03")] == "LOCALIZER"
        assert lookup[("S04", "04")] == "LDA"
        assert lookup[("S05", "05")] == "ILS/DME"
        assert lookup[("S06", "06")] == "SDF/DME"
        assert lookup[("S07", "07")] == "LOC/DME"
        assert lookup[("S08", "08")] == "LOC/GS"
        assert lookup[("S09", "09")] == "LDA/DME"

    def test_unknown_system_type_code_raises(self, tmp_path: Path) -> None:
        """Unknown SYSTEM_TYPE_CODE raises ValueError."""
        from aeroinfo.parsers.ils_csv import build_approach_type_lookup

        rows = [
            '"SITE_NO","RWY_END_ID","SYSTEM_TYPE_CODE"',
            '"S01","01","ZZ"',
        ]
        p = _write_csv(tmp_path, rows)
        with pytest.raises(ValueError, match="Unknown SYSTEM_TYPE_CODE"):
            build_approach_type_lookup(p)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """Missing ILS_BASE.csv raises RuntimeError."""
        from aeroinfo.parsers.ils_csv import build_approach_type_lookup

        p = tmp_path / "ILS_BASE.csv"
        with pytest.raises(RuntimeError, match=r"ILS_BASE\.csv not found"):
            build_approach_type_lookup(p)

    def test_first_match_wins(self, tmp_path: Path) -> None:
        """When multiple records exist for same key, first match wins."""
        from aeroinfo.parsers.ils_csv import build_approach_type_lookup

        rows = [
            '"SITE_NO","RWY_END_ID","SYSTEM_TYPE_CODE"',
            '"S01","01","LS"',
            '"S01","01","LD"',
        ]
        p = _write_csv(tmp_path, rows)
        lookup = build_approach_type_lookup(p)
        assert lookup[("S01", "01")] == "ILS"  # first: LS->ILS, not LD->ILS/DME

    def test_missing_columns_raises(self, tmp_path: Path) -> None:
        """Missing required columns raises RuntimeError."""
        from aeroinfo.parsers.ils_csv import build_approach_type_lookup

        rows = [
            '"SITE_NO","RWY_END_ID"',
            '"S01","01"',
        ]
        p = _write_csv(tmp_path, rows)
        with pytest.raises(RuntimeError, match="missing required columns"):
            build_approach_type_lookup(p)

    def test_empty_system_type_code_skipped(self, tmp_path: Path) -> None:
        """Rows with empty SYSTEM_TYPE_CODE are skipped gracefully."""
        from aeroinfo.parsers.ils_csv import build_approach_type_lookup

        rows = [
            '"SITE_NO","RWY_END_ID","SYSTEM_TYPE_CODE"',
            '"S01","01",""',
            '"S02","02","LS"',
        ]
        p = _write_csv(tmp_path, rows)
        lookup = build_approach_type_lookup(p)
        assert ("S01", "01") not in lookup
        assert lookup[("S02", "02")] == "ILS"

    def test_real_ils_base_csv(self) -> None:
        """Actual ILS_BASE.csv parses without error."""
        from aeroinfo.parsers.ils_csv import build_approach_type_lookup

        real_path = Path("references/2026-02-19/CSV_Data/ILS_BASE.csv")
        if not real_path.exists():
            pytest.skip("ILS_BASE.csv not available")
        lookup = build_approach_type_lookup(real_path)
        assert len(lookup) > 0
