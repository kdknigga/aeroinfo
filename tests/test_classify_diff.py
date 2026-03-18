"""Tests for classify_diff() and is_excluded() in tests.parity.categories."""

from __future__ import annotations

import pytest

from tests.parity.categories import classify_diff, is_excluded

# (table, field, expected_category) tuples covering all 27 categories
CLASSIFY_CASES = [
    # boundary_artcc (accepted)
    ("airports", "boundary_artcc_computer_id", "boundary_artcc"),
    ("airports", "boundary_artcc_id", "boundary_artcc"),
    ("airports", "boundary_artcc_name", "boundary_artcc"),
    # field_office (accepted)
    ("airports", "field_office", "field_office_none"),
    # medical_purposes (accepted)
    ("airports", "landing_facility_used_for_medical_purposes", "medical_purposes"),
    # navaids PK dedup (accepted)
    ("navaids", "any_field", "navaids_pk_dedup"),
    # navaid sub-tables (accepted)
    ("navaid_airspace_fixes", "(row missing from B)", "navaid_sub_tables_no_csv"),
    ("navaid_holding_patterns", "(row missing from A)", "navaid_sub_tables_no_csv"),
    ("navaid_fan_markers", "any_field", "navaid_sub_tables_no_csv"),
    # navaid remarks (accepted)
    ("navaid_remarks", "any_field", "navaid_remarks_pk_dedup"),
    # airport_remarks (accepted - Phase 4: source data gaps)
    (
        "airport_remarks",
        "remark",
        "airport_remarks_text_diffs",
    ),  # default diff_type=value_diff
    # attendance_schedules (accepted - TXT/CSV format differences)
    ("attendance_schedules", "attendance_schedule", "attendance_trailing"),
    # city_state_whitespace (actionable - Phase 3)
    ("airports", "owners_city_state_zip", "city_state_whitespace"),
    ("airports", "managers_city_state_zip", "city_state_whitespace"),
    ("airports", "owners_address", "city_state_whitespace"),
    ("airports", "managers_address", "city_state_whitespace"),
    # latitude_dms_padding (actionable - Phase 3)
    ("airports", "latitude_dms", "latitude_dms_padding"),
    ("runway_ends", "latitude_dms", "latitude_dms_padding"),
    # remark_field_mapping (actionable - Phase 3)
    ("airports", "customs_landing_rights_remark", "remark_field_mapping"),
    ("airports", "other_services_available_remark", "remark_field_mapping"),
    # surface_type_condition (actionable - Phase 3)
    ("runways", "surface_type_condition", "surface_type_condition"),
    # approach_type (actionable - Phase 3)
    ("runway_ends", "approach_type", "approach_type"),
    # fuel_available and airspace_analysis_remark now accepted as negligible (minor_accepted)
    ("airports", "fuel_available", "minor_accepted"),
    ("airports", "airspace_analysis_remark", "minor_accepted"),
    # remark_content_diffs (accepted)
    ("airports", "transient_storage_facilities_remark", "remark_content_diffs"),
    ("airports", "arff_certification_remark", "remark_content_diffs"),
    ("airports", "last_inspection_date_remark", "remark_content_diffs"),
    ("airports", "tie_in_fss_remark", "remark_content_diffs"),
    ("runway_ends", "markings_remark", "remark_content_diffs"),
    ("runways", "surface_type_condition_remark", "remark_content_diffs"),
    ("runways", "name_remark", "remark_content_diffs"),
    # minor_accepted (accepted)
    ("runway_ends", "rvr_equipment_remark", "minor_accepted"),
    ("runway_ends", "displaced_threshold_latitude_dms", "minor_accepted"),
]

# (category, expected_excluded) tuples
EXCLUDED_CASES = [
    ("boundary_artcc", True),
    ("field_office_none", True),
    ("navaids_pk_dedup", True),
    ("navaid_sub_tables_no_csv", True),
    ("navaid_remarks_pk_dedup", True),
    ("medical_purposes", True),
    ("remark_content_diffs", True),
    ("minor_accepted", True),
    ("attendance_trailing", True),
    ("airport_remarks_text_diffs", True),
    ("airport_remarks_txt_only", True),
    ("airport_remarks_csv_only", True),
    ("airport_remarks_naming", True),
    ("city_state_whitespace", True),
    ("latitude_dms_padding", True),
    ("remark_field_mapping", True),
    ("surface_type_condition", True),
    ("approach_type", True),
    ("value_normalization", True),
    ("uncategorized", False),
]


@pytest.mark.parametrize(
    ("table", "field", "expected"),
    CLASSIFY_CASES,
    ids=[f"{t}.{f}" for t, f, _ in CLASSIFY_CASES],
)
def test_classify_diff(table: str, field: str, expected: str) -> None:
    """Verify classify_diff maps (table, field) to the correct category."""
    assert classify_diff(table, field) == expected


# (table, field, diff_type, expected_category) for diff_type-dependent routing
CLASSIFY_DIFF_TYPE_CASES = [
    (
        "airport_remarks",
        "(row missing from B)",
        "missing_from_b",
        "airport_remarks_txt_only",
    ),
    (
        "airport_remarks",
        "(row missing from A)",
        "missing_from_a",
        "airport_remarks_csv_only",
    ),
    ("airport_remarks", "remark", "value_diff", "airport_remarks_text_diffs"),
    ("airport_remarks", "remark", "unknown_type", "airport_remarks_naming"),  # fallback
]


@pytest.mark.parametrize(
    ("table", "field", "diff_type", "expected"),
    CLASSIFY_DIFF_TYPE_CASES,
    ids=[f"{t}.{f}.{d}" for t, f, d, _ in CLASSIFY_DIFF_TYPE_CASES],
)
def test_classify_diff_with_diff_type(
    table: str, field: str, diff_type: str, expected: str
) -> None:
    """Verify classify_diff routes airport_remarks by diff_type parameter."""
    assert classify_diff(table, field, diff_type=diff_type) == expected


@pytest.mark.parametrize(
    ("category", "expected"),
    EXCLUDED_CASES,
    ids=[f"{c}={'excl' if e else 'act'}" for c, e in EXCLUDED_CASES],
)
def test_is_excluded(category: str, *, expected: bool) -> None:
    """Verify is_excluded correctly identifies accepted vs actionable categories."""
    assert is_excluded(category) is expected
