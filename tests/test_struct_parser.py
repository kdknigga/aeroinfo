"""Tests for the StructParser class in utils.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from aeroinfo.parsers.utils import FieldSpec, StructParser, get_field

# Load test data from fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture_line(filename: str, line_num: int = 0) -> str:
    """Load a specific line from a fixture file."""
    with (FIXTURES_DIR / filename).open() as f:
        lines = f.readlines()
        return lines[line_num].rstrip("\n")


class TestFieldSpec:
    """Tests for the FieldSpec named tuple."""

    def test_field_spec_defaults(self) -> None:
        """Test that FieldSpec has correct default values."""
        spec = FieldSpec("test", 1, 5)
        assert spec.name == "test"
        assert spec.start == 1
        assert spec.length == 5
        assert spec.var_type == "str"

    def test_field_spec_with_type(self) -> None:
        """Test FieldSpec with explicit var_type."""
        spec = FieldSpec("elevation", 10, 7, "float")
        assert spec.var_type == "float"


class TestStructParser:
    """Tests for the StructParser class."""

    @pytest.fixture
    def nav1_line(self) -> str:
        """Load NAV1 record from fixture."""
        return _load_fixture_line("NAV_min.txt", 0)

    @pytest.fixture
    def apt_line(self) -> str:
        """Load APT record from fixture."""
        return _load_fixture_line("APT_min.txt", 0)

    def test_basic_string_field_extraction(self, nav1_line: str) -> None:
        """Test basic string field extraction."""
        fields = [
            FieldSpec("record_type", 1, 4),
            FieldSpec("facility_id", 5, 4),
        ]
        parser = StructParser(fields)
        result = parser.parse(nav1_line)

        assert result["record_type"] == "NAV1"
        assert result["facility_id"] == "BER"

    def test_float_field_extraction(self, nav1_line: str) -> None:
        """Test float field extraction and conversion."""
        fields = [FieldSpec("elevation", 473, 7, "float")]
        parser = StructParser(fields)
        result = parser.parse(nav1_line)

        assert isinstance(result["elevation"], float)
        assert abs(result["elevation"] - 408.0) < 0.01

    def test_int_field_extraction(self, nav1_line: str) -> None:
        """Test integer field extraction and conversion."""
        fields = [FieldSpec("mag_variation_year", 485, 4, "int")]
        parser = StructParser(fields)
        result = parser.parse(nav1_line)

        assert isinstance(result["mag_variation_year"], int)
        assert result["mag_variation_year"] == 2000

    def test_date_field_extraction(self, nav1_line: str) -> None:
        """Test date field extraction and conversion."""
        fields = [FieldSpec("effective_date", 33, 10, "date")]
        parser = StructParser(fields)
        result = parser.parse(nav1_line)

        assert result["effective_date"] is not None
        assert result["effective_date"].year == 2025
        assert result["effective_date"].month == 10
        assert result["effective_date"].day == 30

    def test_empty_field_returns_none(self) -> None:
        """Test that empty (whitespace-only) fields return None."""
        # Create a line with spaces in a specific position
        line = "    " + " " * 100  # All spaces
        fields = [FieldSpec("empty_field", 5, 10)]
        parser = StructParser(fields)
        result = parser.parse(line)

        assert result["empty_field"] is None

    def test_multiple_fields_extraction(self, nav1_line: str) -> None:
        """Test extracting multiple fields at once."""
        fields = [
            FieldSpec("record_type", 1, 4),
            FieldSpec("facility_id", 5, 4),
            FieldSpec("facility_type", 9, 20),
            FieldSpec("official_facility_id", 29, 4),
            FieldSpec("elevation", 473, 7, "float"),
            FieldSpec("frequency", 534, 6),
        ]
        parser = StructParser(fields)
        result = parser.parse(nav1_line)

        assert result["record_type"] == "NAV1"
        assert result["facility_id"] == "BER"
        assert result["facility_type"] == "TACAN"
        assert result["official_facility_id"] == "BER"
        assert abs(result["elevation"] - 408.0) < 0.01
        assert result["frequency"] == "113.00"

    def test_consistency_with_get_field(self, nav1_line: str) -> None:
        """Test that StructParser produces the same results as get_field."""
        fields = [
            FieldSpec("record_type", 1, 4),
            FieldSpec("facility_id", 5, 4),
            FieldSpec("facility_type", 9, 20),
            FieldSpec("elevation", 473, 7, "float"),
            FieldSpec("frequency", 534, 6),
        ]
        parser = StructParser(fields)
        result = parser.parse(nav1_line)

        assert result["record_type"] == get_field(nav1_line, 1, 4)
        assert result["facility_id"] == get_field(nav1_line, 5, 4)
        assert result["facility_type"] == get_field(nav1_line, 9, 20)
        assert result["elevation"] == get_field(nav1_line, 473, 7, "float")
        assert result["frequency"] == get_field(nav1_line, 534, 6)

    def test_apt_record_parsing(self, apt_line: str) -> None:
        """Test parsing an APT record format."""
        fields = [
            FieldSpec("record_type", 1, 3),
            FieldSpec("facility_site_number", 4, 11),
            FieldSpec("faa_id", 28, 4),
            FieldSpec("elevation", 579, 7, "float"),
            FieldSpec("icao_id", 1211, 7),
        ]
        parser = StructParser(fields)
        result = parser.parse(apt_line)

        assert result["record_type"] == "APT"
        assert result["facility_site_number"] == "50009.*A"
        assert result["faa_id"] == "ADK"
        assert abs(result["elevation"] - 19.5) < 0.01
        assert result["icao_id"] == "PADK"

    def test_apt_consistency_with_get_field(self, apt_line: str) -> None:
        """Test APT record parsing is consistent with get_field."""
        fields = [
            FieldSpec("record_type", 1, 3),
            FieldSpec("facility_site_number", 4, 11),
            FieldSpec("faa_id", 28, 4),
            FieldSpec("elevation", 579, 7, "float"),
            FieldSpec("icao_id", 1211, 7),
        ]
        parser = StructParser(fields)
        result = parser.parse(apt_line)

        assert result["record_type"] == get_field(apt_line, 1, 3)
        assert result["facility_site_number"] == get_field(apt_line, 4, 11)
        assert result["faa_id"] == get_field(apt_line, 28, 4)
        assert result["elevation"] == get_field(apt_line, 579, 7, "float")
        assert result["icao_id"] == get_field(apt_line, 1211, 7)

    def test_short_record_padding(self) -> None:
        """Test that short records are padded correctly."""
        short_line = "NAV1BER "  # Very short line
        fields = [
            FieldSpec("record_type", 1, 4),
            FieldSpec("facility_id", 5, 4),
            FieldSpec("missing_field", 100, 10),  # Beyond line length
        ]
        parser = StructParser(fields)
        result = parser.parse(short_line)

        assert result["record_type"] == "NAV1"
        assert result["facility_id"] == "BER"
        assert result["missing_field"] is None  # Padded with spaces, returns None

    def test_non_contiguous_fields(self) -> None:
        """Test extraction of fields with gaps between them."""
        fields = [
            FieldSpec("first", 1, 4),
            FieldSpec("third", 50, 5),  # Large gap
            FieldSpec("second", 10, 5),  # Out of order in definition
        ]
        parser = StructParser(fields)
        # Parser should handle gaps and out-of-order field definitions
        assert parser._struct is not None

    def test_empty_fields_list(self) -> None:
        """Test parser with no fields."""
        parser = StructParser([])
        result = parser.parse("some data")
        assert result == {}


@pytest.mark.fast
class TestStructParserFast:
    """Fast tests that don't require DB fixtures."""

    def test_field_spec_creation(self) -> None:
        """Test FieldSpec can be created with all parameters."""
        spec = FieldSpec("test_field", 1, 10, "int")
        assert spec.name == "test_field"
        assert spec.start == 1
        assert spec.length == 10
        assert spec.var_type == "int"

    def test_struct_parser_initialization(self) -> None:
        """Test StructParser can be initialized with field specs."""
        fields = [
            FieldSpec("f1", 1, 5),
            FieldSpec("f2", 10, 5),
        ]
        parser = StructParser(fields)
        assert parser.fields == fields
        assert parser._struct is not None
        assert len(parser._field_indices) == 2
