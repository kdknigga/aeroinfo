"""Classification logic for database comparison diffs."""

from __future__ import annotations

# -- Category definitions -----------------------------------------------------
# All 27 disposition categories from PROJECT.md Phase 1 triage.
# Each category has a disposition (accept/fix_phase4),
# a description, and an optional requirement ID.

CATEGORIES: dict[str, dict[str, str]] = {
    # Accepted gaps -- excluded from actionable count
    "boundary_artcc": {
        "disposition": "accept",
        "description": "CSV format omits boundary ARTCC fields",
    },
    "field_office_none": {
        "disposition": "accept",
        "description": "TXT='NONE' vs CSV=null",
    },
    "navaids_pk_dedup": {
        "disposition": "accept",
        "description": "PK collision: different merge winners",
    },
    "navaid_sub_tables_no_csv": {
        "disposition": "accept",
        "description": "No CSV source file for navaid sub-tables",
    },
    "navaid_remarks_pk_dedup": {
        "disposition": "accept",
        "description": "99.4% correlate with navaid PK dedup",
    },
    "medical_purposes": {
        "disposition": "accept",
        "description": "TXT=null vs CSV=False",
    },
    "remark_content_diffs": {
        "disposition": "accept",
        "description": "Source data genuinely differs between formats",
    },
    "minor_accepted": {
        "disposition": "accept",
        "description": "Single-case source data differences",
    },
    # Actionable -- Phase 3 fixes
    "attendance_trailing": {
        "disposition": "accept",
        "description": "TXT/CSV attendance format differences (trailing slashes, UNATNDD expansion, spaces)",
        "req_id": "FIX-02",
    },
    "city_state_whitespace": {
        "disposition": "accept",
        "description": "Whitespace around commas in city/state (fixed in Phase 3, zero remaining diffs)",
        "req_id": "FIX-03",
    },
    "latitude_dms_padding": {
        "disposition": "accept",
        "description": "Leading zero padding in DMS degrees (fixed in Phase 3, zero remaining diffs)",
        "req_id": "FIX-04",
    },
    "remark_field_mapping": {
        "disposition": "accept",
        "description": "CSV data gap: remark text only in TXT format (E80/A76 records)",
        "req_id": "FIX-06",
    },
    "surface_type_condition": {
        "disposition": "accept",
        "description": "35 FAA source inconsistencies: FAIR condition encoded as -L in TXT vs -F in CSV (not a parser bug)",
        "req_id": "FIX-07",
    },
    "approach_type": {
        "disposition": "accept",
        "description": "CSV data gap: ILS data absent from CSV files for 72 runway ends",
        "req_id": "FIX-08",
    },
    "value_normalization": {
        "disposition": "accept",
        "description": "Fuel/airspace parsing differences (fixed in Phase 3, zero remaining diffs)",
        "req_id": "FIX-03",
    },
    # Airport remarks -- sub-categorized by root cause (all accepted)
    "airport_remarks_text_diffs": {
        "disposition": "accept",
        "description": "Source data text differs between TXT and CSV remark content (A110, A17, E60, A70-FUEL)",
    },
    "airport_remarks_txt_only": {
        "disposition": "accept",
        "description": "TXT has remark rows not in CSV (A110 source gaps, sequence suffixes A17/A42/A33)",
    },
    "airport_remarks_csv_only": {
        "disposition": "accept",
        "description": "CSV has remark rows not in TXT (richer format: A110-MEDICAL, A110*P, E80A, E7)",
    },
    "airport_remarks_naming": {
        "disposition": "accept",
        "description": "Residual airport remark diffs (investigate if count > 0)",
        "req_id": "STR-02",
    },
    # Fallback
    "uncategorized": {
        "disposition": "fix_phase3",
        "description": "Unclassified diff (investigate)",
    },
}

# Tables where ALL diffs are accepted (entire table excluded)
ACCEPTED_TABLES: set[str] = {
    "navaid_airspace_fixes",  # No CSV source file
    "navaid_holding_patterns",  # No CSV source file
    "navaid_fan_markers",  # No CSV source file
}

# (table, field) -> category for field-level accepted diffs
ACCEPTED_FIELDS: dict[tuple[str, str], str] = {
    ("airports", "boundary_artcc_computer_id"): "boundary_artcc",
    ("airports", "boundary_artcc_id"): "boundary_artcc",
    ("airports", "boundary_artcc_name"): "boundary_artcc",
    ("airports", "field_office"): "field_office_none",
    ("airports", "landing_facility_used_for_medical_purposes"): "medical_purposes",
    ("airports", "transient_storage_facilities_remark"): "remark_content_diffs",
    ("airports", "arff_certification_remark"): "remark_content_diffs",
    ("airports", "last_inspection_date_remark"): "remark_content_diffs",
    ("airports", "tie_in_fss_remark"): "remark_content_diffs",
    ("runway_ends", "markings_remark"): "remark_content_diffs",
    ("runway_ends", "rvr_equipment_remark"): "minor_accepted",
    ("runway_ends", "displaced_threshold_latitude_dms"): "minor_accepted",
    ("runways", "surface_type_condition_remark"): "remark_content_diffs",
    ("runways", "name_remark"): "remark_content_diffs",
    ("airports", "fuel_available"): "minor_accepted",
    ("airports", "airspace_analysis_remark"): "minor_accepted",
}

# Categories with "accept" disposition -- excluded from actionable output
EXCLUDED_CATEGORIES: set[str] = {
    name for name, info in CATEGORIES.items() if info["disposition"] == "accept"
}


def classify_diff(table: str, field: str, diff_type: str = "value_diff") -> str:
    """Classify a diff into a disposition category."""
    # Entire tables accepted (no CSV source)
    if table in ACCEPTED_TABLES:
        return "navaid_sub_tables_no_csv"

    # Navaid row/field diffs -> PK dedup
    if table == "navaids":
        return "navaids_pk_dedup"

    # Navaid remarks: 99.4% correlate with PK dedup
    if table == "navaid_remarks":
        return "navaid_remarks_pk_dedup"

    # Field-level accepted diffs
    key = (table, field)
    if key in ACCEPTED_FIELDS:
        return ACCEPTED_FIELDS[key]

    # Actionable categories by table+field patterns
    if table == "airport_remarks":
        if diff_type == "value_diff":
            return "airport_remarks_text_diffs"
        if diff_type == "missing_from_b":  # In TXT but not CSV
            return "airport_remarks_txt_only"
        if diff_type == "missing_from_a":  # In CSV but not TXT
            return "airport_remarks_csv_only"
        return "airport_remarks_naming"  # Fallback

    if table == "attendance_schedules":
        return "attendance_trailing"  # FIX-02

    if table == "airports":
        if field in (
            "owners_city_state_zip",
            "managers_city_state_zip",
            "owners_address",
            "managers_address",
        ):
            return "city_state_whitespace"  # FIX-03
        if field == "latitude_dms":
            return "latitude_dms_padding"  # FIX-04
        if field in (
            "customs_landing_rights_remark",
            "other_services_available_remark",
        ):
            return "remark_field_mapping"  # FIX-06
        if field in ("fuel_available", "airspace_analysis_remark"):
            return "value_normalization"  # FIX-03

    if table == "runway_ends":
        if field == "approach_type":
            return "approach_type"  # FIX-08
        if field == "latitude_dms":
            return "latitude_dms_padding"  # FIX-04

    if table == "runways" and field == "surface_type_condition":
        return "surface_type_condition"  # FIX-07

    return "uncategorized"


def is_excluded(category: str) -> bool:
    """Check if a category is excluded (accepted gap, not actionable)."""
    return category in EXCLUDED_CATEGORIES
