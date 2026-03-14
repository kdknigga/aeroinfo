"""
Unit tests for CSV coercion utilities in aeroinfo.parsers.utils.

Tests cover:
- csv_field(): empty/missing handling, type coercion, enum normalization (UTIL-01)
- build_dms_string(): DMS coordinate reconstruction (UTIL-02)
- build_total_secs_string(): total-seconds string (UTIL-02)
- reconstruct_attendance_schedule(): attendance schedule join (UTIL-03)
- reconstruct_fuel(): fuel code space-padding (UTIL-01 multi-column)
- reconstruct_mag_variation(): mag variation formatting (UTIL-01 multi-column)
- reconstruct_transient_storage(): comma-joined storage flags (UTIL-01 multi-column)
- reconstruct_arff(): ARFF certification assembly (UTIL-01 multi-column)
"""

from __future__ import annotations

import datetime

import pytest

from aeroinfo.parsers.apt_csv import _reconstruct_surface_type_condition
from aeroinfo.parsers.utils import (
    build_dms_string,
    build_total_secs_string,
    csv_field,
    reconstruct_arff,
    reconstruct_attendance_schedule,
    reconstruct_fuel,
    reconstruct_mag_variation,
    reconstruct_transient_storage,
)

# ---------------------------------------------------------------------------
# csv_field() — UTIL-01
# ---------------------------------------------------------------------------


class TestCsvFieldEmptyAndMissing:
    """csv_field() returns None for empty strings and missing keys."""

    def test_empty_string_returns_none(self) -> None:
        """Empty string returns None."""
        assert csv_field({"COL": ""}, "COL") is None

    def test_whitespace_only_returns_none(self) -> None:
        """Whitespace-only string returns None."""
        assert csv_field({"COL": "   "}, "COL") is None

    def test_missing_key_returns_none(self) -> None:
        """Missing column key returns None."""
        assert csv_field({}, "COL") is None

    def test_strips_whitespace_from_str(self) -> None:
        """Leading/trailing whitespace is stripped from str values."""
        assert csv_field({"COL": "  value  "}, "COL") == "value"


class TestCsvFieldNumericCoercion:
    """csv_field() coerces int and float types, raises ValueError on bad input."""

    def test_int_coercion(self) -> None:
        """Integer string coerces to int."""
        assert csv_field({"COL": "42"}, "COL", "int") == 42

    def test_int_coercion_negative(self) -> None:
        """Negative integer string coerces to int."""
        assert csv_field({"COL": "-7"}, "COL", "int") == -7

    def test_float_coercion(self) -> None:
        """Float string coerces to float."""
        assert csv_field({"COL": "18.9"}, "COL", "float") == 18.9

    def test_float_coercion_integer_string(self) -> None:
        """Integer string with float type coerces to float."""
        assert csv_field({"COL": "100"}, "COL", "float") == 100.0

    def test_bad_int_raises_value_error(self) -> None:
        """Non-numeric string with int type raises ValueError."""
        with pytest.raises(ValueError):
            csv_field({"COL": "abc"}, "COL", "int")

    def test_bad_float_raises_value_error(self) -> None:
        """Non-numeric string with float type raises ValueError."""
        with pytest.raises(ValueError):
            csv_field({"COL": "abc"}, "COL", "float")

    def test_float_with_extra_whitespace_coerces(self) -> None:
        """Float string with surrounding whitespace is stripped then coerced."""
        assert csv_field({"COL": "  3.14  "}, "COL", "float") == 3.14


class TestCsvFieldBoolCoercion:
    """csv_field() coerces Y/T to True, N/F to False, unknown to None."""

    def test_y_returns_true(self) -> None:
        """'Y' coerces to True."""
        assert csv_field({"COL": "Y"}, "COL", "bool") is True

    def test_t_returns_true(self) -> None:
        """'T' coerces to True."""
        assert csv_field({"COL": "T"}, "COL", "bool") is True

    def test_n_returns_false(self) -> None:
        """'N' coerces to False."""
        assert csv_field({"COL": "N"}, "COL", "bool") is False

    def test_f_returns_false(self) -> None:
        """'F' coerces to False."""
        assert csv_field({"COL": "F"}, "COL", "bool") is False

    def test_empty_returns_none(self) -> None:
        """Empty string with bool type returns None."""
        assert csv_field({"COL": ""}, "COL", "bool") is None

    def test_unknown_value_returns_none(self) -> None:
        """Unknown bool value returns None (not a failure)."""
        assert csv_field({"COL": "X"}, "COL", "bool") is None


class TestCsvFieldDateCoercion:
    """csv_field() coerces date and date_ymd types to date objects."""

    def test_date_mdy_coerces(self) -> None:
        """MM/DD/YYYY date string coerces to date object."""
        result = csv_field({"COL": "01/01/2020"}, "COL", "date")
        assert result == datetime.date(2020, 1, 1)

    def test_date_returns_date_not_datetime(self) -> None:
        """Date type returns datetime.date, not datetime.datetime."""
        result = csv_field({"COL": "01/01/2020"}, "COL", "date")
        assert type(result) is datetime.date

    def test_date_ymd_coerces(self) -> None:
        """YYYY/MM/DD date string coerces to date object."""
        result = csv_field({"COL": "2020/01/01"}, "COL", "date_ymd")
        assert result == datetime.date(2020, 1, 1)

    def test_date_ymd_returns_date_not_datetime(self) -> None:
        """date_ymd type returns datetime.date, not datetime.datetime."""
        result = csv_field({"COL": "2020/01/01"}, "COL", "date_ymd")
        assert type(result) is datetime.date

    def test_date_yyyymm_normalizes_to_first_of_month(self) -> None:
        """YYYY/MM partial date always produces day=01 regardless of execution date."""
        result = csv_field({"COL": "1966/04"}, "COL", "date")
        assert result == datetime.date(1966, 4, 1)

    def test_date_yyyymm_day_is_one_deterministic(self) -> None:
        """YYYY/MM day=01 is deterministic (not today's day)."""
        result = csv_field({"COL": "1939/01"}, "COL", "date")
        assert result.day == 1


class TestCsvFieldEnumCoercion:
    """csv_field() normalizes enum codes per type-specific rules."""

    def test_airport_inspection_method_1_maps_to_O(self) -> None:
        """Inspection method code '1' maps to 'O'."""
        assert csv_field({"COL": "1"}, "COL", "AirportInspectionMethodEnum") == "O"

    def test_airport_inspection_method_2_maps_to_T(self) -> None:
        """Inspection method code '2' maps to 'T'."""
        assert csv_field({"COL": "2"}, "COL", "AirportInspectionMethodEnum") == "T"

    def test_airport_inspection_method_passthrough(self) -> None:
        """Unknown inspection method codes pass through unchanged."""
        assert csv_field({"COL": "F"}, "COL", "AirportInspectionMethodEnum") == "F"

    def test_segmented_circle_yl_maps(self) -> None:
        """'Y-L' segmented circle code maps to 'YL'."""
        assert csv_field({"COL": "Y-L"}, "COL", "SegmentedCircleEnum") == "YL"

    def test_segmented_circle_n_passthrough(self) -> None:
        """'N' segmented circle code passes through unchanged."""
        assert csv_field({"COL": "N"}, "COL", "SegmentedCircleEnum") == "N"

    def test_navaid_position_survey_0_maps_to_ZERO(self) -> None:
        """Navaid position survey accuracy '0' maps to 'ZERO'."""
        assert (
            csv_field({"COL": "0"}, "COL", "NavaidPositionSurveyAccuracyEnum") == "ZERO"
        )

    def test_navaid_position_survey_7_maps_to_SEVEN(self) -> None:
        """Navaid position survey accuracy '7' maps to 'SEVEN'."""
        assert (
            csv_field({"COL": "7"}, "COL", "NavaidPositionSurveyAccuracyEnum")
            == "SEVEN"
        )

    def test_navaid_monitoring_category_0_maps_to_ZERO(self) -> None:
        """Navaid monitoring category '0' maps to 'ZERO'."""
        assert csv_field({"COL": "0"}, "COL", "NavaidMonitoringCategoryEnum") == "ZERO"

    def test_navaid_monitoring_category_passthrough(self) -> None:
        """Unknown navaid enum values pass through unchanged."""
        assert csv_field({"COL": "X"}, "COL", "NavaidPositionSurveyAccuracyEnum") == "X"


# ---------------------------------------------------------------------------
# build_dms_string() — UTIL-02
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("deg", "min_", "sec", "hemis", "is_lon", "expected"),
    [
        # Latitude (no degree zero-padding)
        (41, 46, 18.9, "N", False, "41-46-18.9000N"),
        (41, 47, 8.3153, "N", False, "41-47-08.3153N"),
        (61, 15, 4.8715, "N", False, "61-15-04.8715N"),
        # Longitude (3-digit zero-padded degrees)
        (88, 28, 32.4, "W", True, "088-28-32.4000W"),
        (87, 45, 9.823, "W", True, "087-45-09.8230W"),
        (149, 48, 23.4924, "W", True, "149-48-23.4924W"),
    ],
)
def test_build_dms_string(
    deg: int,
    min_: int,
    sec: float,
    hemis: str,
    is_lon: bool,  # noqa: FBT001
    expected: str,
) -> None:
    """build_dms_string() produces byte-identical DMS strings for lat and lon."""
    result = build_dms_string(deg, min_, sec, hemis, is_longitude=is_lon)
    assert result == expected


def test_build_dms_string_default_is_latitude() -> None:
    """build_dms_string() defaults to latitude (no degree zero-padding)."""
    result = build_dms_string(41, 46, 18.9, "N")
    assert result == "41-46-18.9000N"


def test_build_dms_string_hemis_lowercase_normalized() -> None:
    """build_dms_string() uppercases the hemisphere character."""
    result = build_dms_string(41, 46, 18.9, "n", is_longitude=False)
    assert result == "41-46-18.9000N"


# ---------------------------------------------------------------------------
# build_total_secs_string() — UTIL-02
# ---------------------------------------------------------------------------


def test_build_total_secs_string_arithmetic() -> None:
    """build_total_secs_string() computes total seconds correctly."""
    # 41*3600 + 46*60 + 18.9 = 147600 + 2760 + 18.9 = 150378.9
    result = build_total_secs_string(41, 46, 18.9, "N")
    assert result == "150378.9000N"


def test_build_total_secs_string_ends_with_hemis() -> None:
    """build_total_secs_string() appends uppercase hemisphere."""
    result = build_total_secs_string(41, 46, 18.9, "n")
    assert result.endswith("N")


def test_build_total_secs_string_four_decimal_places() -> None:
    """build_total_secs_string() formats total seconds to 4 decimal places."""
    result = build_total_secs_string(41, 46, 18.9, "N")
    numeric_part = result[:-1]  # strip hemisphere
    assert "." in numeric_part
    assert len(numeric_part.split(".")[1]) == 4


# ---------------------------------------------------------------------------
# reconstruct_attendance_schedule() — UTIL-03
# ---------------------------------------------------------------------------


def test_attendance_unatndd_returned_unchanged() -> None:
    """reconstruct_attendance_schedule() returns 'UNATNDD' when month is UNATNDD."""
    assert reconstruct_attendance_schedule("UNATNDD", "", "") == "UNATNDD"


def test_attendance_unatndd_case_insensitive() -> None:
    """reconstruct_attendance_schedule() handles lowercase UNATNDD."""
    assert reconstruct_attendance_schedule("unatndd", "", "") == "UNATNDD"


def test_attendance_normal_join() -> None:
    """reconstruct_attendance_schedule() joins MONTH/DAY/HOUR with /."""
    assert (
        reconstruct_attendance_schedule("ALL", "ALL", "0600-2400")
        == "ALL/ALL/0600-2400"
    )


def test_attendance_all_all_all() -> None:
    """reconstruct_attendance_schedule() handles ALL/ALL/ALL case."""
    assert reconstruct_attendance_schedule("ALL", "ALL", "ALL") == "ALL/ALL/ALL"


def test_attendance_all_empty_returns_none() -> None:
    """reconstruct_attendance_schedule() returns None when all inputs are empty."""
    assert reconstruct_attendance_schedule("", "", "") is None


def test_attendance_empty_month_returns_none() -> None:
    """reconstruct_attendance_schedule() returns None when month is empty."""
    assert reconstruct_attendance_schedule("", "ALL", "0600-2400") is None


# ---------------------------------------------------------------------------
# reconstruct_fuel() — UTIL-01 multi-column
# ---------------------------------------------------------------------------


def test_fuel_two_codes_space_padded() -> None:
    """reconstruct_fuel() pads each code to 5 chars and joins."""
    # "100" -> "100  " (5 chars), "A1" -> "A1   " (5 chars)
    # joined -> "100  A1   ".rstrip() -> "100  A1"
    assert reconstruct_fuel("100,A1") == "100  A1"


def test_fuel_full_width_codes_adjacent() -> None:
    """reconstruct_fuel() handles 5-char codes that become adjacent."""
    # "100LL" -> "100LL" (5), "A1+" -> "A1+  " (5)
    # joined -> "100LLA1+  ".rstrip() -> "100LLA1+"
    assert reconstruct_fuel("100LL,A1+") == "100LLA1+"


def test_fuel_single_code() -> None:
    """reconstruct_fuel() handles a single fuel code."""
    assert reconstruct_fuel("100") == "100"


def test_fuel_single_short_code() -> None:
    """reconstruct_fuel() handles short single-char codes."""
    assert reconstruct_fuel("J8") == "J8"


def test_fuel_none_returns_none() -> None:
    """reconstruct_fuel() returns None for None input."""
    assert reconstruct_fuel(None) is None


def test_fuel_empty_string_returns_none() -> None:
    """reconstruct_fuel() returns None for empty string input."""
    assert reconstruct_fuel("") is None


# ---------------------------------------------------------------------------
# reconstruct_mag_variation() — UTIL-01 multi-column
# ---------------------------------------------------------------------------


def test_mag_variation_single_digit_west() -> None:
    """reconstruct_mag_variation() zero-pads single-digit degrees."""
    assert reconstruct_mag_variation("1", "W") == "01W"


def test_mag_variation_two_digit_east() -> None:
    """reconstruct_mag_variation() handles two-digit degrees."""
    assert reconstruct_mag_variation("18", "E") == "18E"


def test_mag_variation_empty_varn_returns_none() -> None:
    """reconstruct_mag_variation() returns None when varn is empty."""
    assert reconstruct_mag_variation("", "") is None


def test_mag_variation_none_varn_returns_none() -> None:
    """reconstruct_mag_variation() returns None when varn is None."""
    assert reconstruct_mag_variation(None, None) is None


def test_mag_variation_hemis_uppercased() -> None:
    """reconstruct_mag_variation() uppercases the hemisphere."""
    assert reconstruct_mag_variation("5", "w") == "05W"


# ---------------------------------------------------------------------------
# reconstruct_transient_storage() — UTIL-01 multi-column
# ---------------------------------------------------------------------------


def test_transient_storage_hgr_and_tie() -> None:
    """reconstruct_transient_storage() joins present flags with comma."""
    assert reconstruct_transient_storage("", "Y", "Y") == "HGR,TIE"


def test_transient_storage_all_three() -> None:
    """reconstruct_transient_storage() includes BUOY when set."""
    assert reconstruct_transient_storage("Y", "Y", "Y") == "BUOY,HGR,TIE"


def test_transient_storage_all_empty_returns_none() -> None:
    """reconstruct_transient_storage() returns None when all flags are empty."""
    assert reconstruct_transient_storage("", "", "") is None


def test_transient_storage_buoy_only() -> None:
    """reconstruct_transient_storage() handles single flag."""
    assert reconstruct_transient_storage("Y", "", "") == "BUOY"


def test_transient_storage_uses_comma_not_pipe() -> None:
    """reconstruct_transient_storage() uses comma separator, not pipe."""
    result = reconstruct_transient_storage("Y", "Y", "")
    assert result is not None
    assert "|" not in result
    assert result == "BUOY,HGR"


# ---------------------------------------------------------------------------
# reconstruct_arff() — UTIL-01 multi-column
# ---------------------------------------------------------------------------


def test_arff_full_reconstruction() -> None:
    """reconstruct_arff() assembles type, carrier, and flipped date."""
    # MDW: "I C", "S", "1973/05" -> "I C S 05/1973"
    assert reconstruct_arff("I C", "S", "1973/05") == "I C S 05/1973"


def test_arff_no_date() -> None:
    """reconstruct_arff() works without cert_date."""
    assert reconstruct_arff("I C", "S", "") == "I C S"


def test_arff_all_empty_returns_none() -> None:
    """reconstruct_arff() returns None when all inputs are empty."""
    assert reconstruct_arff("", "", "") is None


def test_arff_date_flip_yyyy_mm_to_mm_yyyy() -> None:
    """reconstruct_arff() flips date from YYYY/MM to MM/YYYY."""
    result = reconstruct_arff("I", "", "2005/12")
    assert result is not None
    assert "12/2005" in result


def test_arff_type_only() -> None:
    """reconstruct_arff() handles type_code only."""
    result = reconstruct_arff("I A", "", "")
    assert result == "I A"


# ---------------------------------------------------------------------------
# FIX-02: reconstruct_attendance_schedule() trailing slash stripping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("month", "day", "hour", "expected"),
    [
        # Empty day+hour should NOT produce trailing //
        ("ON CALL", "", "", "ON CALL"),
        ("UNATTND", "", "", "UNATTND"),
        # Empty hour should NOT produce trailing /
        ("JAN", "1-15", "", "JAN/1-15"),
        # Normal three-part schedule unchanged
        ("ALL", "ALL", "0600-2400", "ALL/ALL/0600-2400"),
    ],
)
def test_attendance_trailing_slash_stripping(
    month: str, day: str, hour: str, expected: str
) -> None:
    """reconstruct_attendance_schedule() strips trailing / characters."""
    assert reconstruct_attendance_schedule(month, day, hour) == expected


# ---------------------------------------------------------------------------
# FIX-04: build_dms_string() single-digit latitude zero-padding
# ---------------------------------------------------------------------------


def test_build_dms_string_single_digit_latitude_padded() -> None:
    """build_dms_string() zero-pads single-digit latitude degrees to 2 digits."""
    result = build_dms_string(7, 18, 47.643, "S")
    assert result == "07-18-47.6430S"


# ---------------------------------------------------------------------------
# FIX-07: _reconstruct_surface_type_condition() explicit mapping
# ---------------------------------------------------------------------------


class TestReconstructSurfaceTypeCondition:
    """Tests for explicit condition-to-letter mapping in surface type."""

    def test_excellent_maps_to_E(self) -> None:
        """EXCELLENT condition abbreviates to E."""
        assert _reconstruct_surface_type_condition("ASPH", "EXCELLENT") == "ASPH-E"

    def test_good_maps_to_G(self) -> None:
        """GOOD condition abbreviates to G."""
        assert _reconstruct_surface_type_condition("CONC", "GOOD") == "CONC-G"

    def test_poor_maps_to_P(self) -> None:
        """POOR condition abbreviates to P."""
        assert _reconstruct_surface_type_condition("ASPH", "POOR") == "ASPH-P"

    def test_fair_maps_to_F(self) -> None:
        """FAIR maps to 'F' (first letter); some TXT records use 'L' but that's a source inconsistency."""
        assert _reconstruct_surface_type_condition("ASPH", "FAIR") == "ASPH-F"

    def test_none_none_returns_none(self) -> None:
        """None inputs return None."""
        assert _reconstruct_surface_type_condition(None, None) is None

    def test_surface_only_no_condition(self) -> None:
        """Surface without condition returns surface only."""
        assert _reconstruct_surface_type_condition("ASPH", None) == "ASPH"

    def test_compound_surface_with_fair(self) -> None:
        """Compound surfaces like ASPH-GRVL also get correct FAIR->F mapping."""
        assert _reconstruct_surface_type_condition("ASPH-GRVL", "FAIR") == "ASPH-GRVL-F"
