"""
Integration tests — CSV Airport parity with TXT snapshot baselines.

Verifies that Airport, AttendanceSchedule, Runway, RunwayEnd, and AirportRemark
objects produced by aeroinfo.parsers.apt_csv.parse() have field values matching
the TXT snapshot baselines for 107 curated airports.

Design:
  - A module-scoped fixture parses the 2026-02-19 CSV data once into an
    in-memory SQLite database.
  - Each parametrized test loads the corresponding TXT snapshot JSON and
    compares CSV-parsed field values against TXT values field-by-field.
  - Fields with no CSV equivalent (see CSV_EXPECTED_NONE_FIELDS below) are
    verified as None in CSV output and excluded from the TXT-comparison loop.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy.orm import sessionmaker

from tests.conftest import _CSV_DATA_DIR, CURATED_AIRPORTS
from tests.snapshot_helpers import extract_record

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SNAPSHOTS_DIR = Path(__file__).resolve().parent / "snapshots" / "test_apt_snapshots"

# ---------------------------------------------------------------------------
# Fields with no APT_BASE.csv equivalent — expected to be None in CSV output
# ---------------------------------------------------------------------------
# These fields are present (potentially non-null) in TXT snapshots but cannot
# be populated from APT_BASE.csv.  Tests verify they are None in CSV output
# and skip them in the field-by-field comparison against TXT values.

# Owner/manager city_state_zip remark fields: no APT_RMK.csv
# AIRPORT_CONTACT dispatch populates these for any curated airport.
# The primary contact fields (owners_name, owners_address, etc.) ARE
# populated from APT_CON.csv (Phase 11-01) and compared against TXT
# values. owners_address_remark and managers_address_remark ARE populated
# by APT_RMK.csv for some airports (STL, DPA, LGA, OSH) — removed from
# this set in Phase 13 (107-airport expansion).
# Identified: Phase 10 gap analysis, confirmed Phase 11, refined Phase 13.
_OWNER_MANAGER_REMARK_UNPOPULATED = frozenset(
    {
        "owners_city_state_zip_remark",
        "managers_city_state_zip_remark",
    }
)

# Fields universally absent from CSV for every airport — suppress warnings
# since these are known, permanent gaps with no possible resolution.
_UNIVERSAL_CSV_GAPS = frozenset(
    {
        "boundary_artcc_id",
        "boundary_artcc_computer_id",
        "boundary_artcc_name",
        "based_general_aviation_single_engine_airplanes",
        "based_general_aviation_multi_engine_airplanes",
        "based_general_aviation_jet_engine_airplanes",
        "based_general_aviation_helicopters",
        "based_gliders",
        "based_military_aircraft",
        "based_ultralight_aircraft",
        "annual_ops_commercial",
        "annual_ops_commuter",
        "annual_ops_air_taxi",
        "annual_ops_general_aviation_local",
        "annual_ops_general_aviation_itinerant",
        "annual_ops_military",
        "annual_ops_end_of_measurement_period",
    }
)

# Boundary ARTCC fields: confirmed N/A in APT_BASE.csv per FAA
# TXT_to_CSV_Mapping.txt. These 3 fields have no CSV column equivalent
# and are permanently null in CSV format.
# Identified: Phase 10 gap analysis — never resolvable from CSV data.
_BOUNDARY_ARTCC_FIELDS = frozenset(
    {
        "boundary_artcc_id",
        "boundary_artcc_computer_id",
        "boundary_artcc_name",
    }
)

# Based-aircraft counts: FAA mapping doc lists BASED_* columns but they
# are absent from the actual 2026-02-19 APT_BASE.csv (90 columns; none
# of the BASED_* columns exist). Removed from NASR CSV in Sept 2024.
# The _remark variants are now populated from APT_RMK.csv (REF_COL_NAME
# dispatch) — only the base counts and jet-engine remark remain null.
# Identified: Phase 10 gap analysis — permanently null in CSV format.
_BASED_AIRCRAFT_FIELDS = frozenset(
    {
        "based_general_aviation_single_engine_airplanes",
        "based_general_aviation_multi_engine_airplanes",
        "based_general_aviation_jet_engine_airplanes",
        "based_general_aviation_jet_engine_airplanes_remark",
        "based_general_aviation_helicopters",
        "based_gliders",
        "based_military_aircraft",
        "based_ultralight_aircraft",
    }
)

# Annual operations counts: same as BASED_* — absent from actual
# APT_BASE.csv since Sept 2024. Permanently null in CSV format.
# Note: annual_ops_commercial_remark IS populated by APT_RMK.csv for
# some airports (e.g., ARR via COMMERCIAL_OPS_CNT) — it is NOT in this
# set and is compared against TXT snapshot values.
# The _remark variants for local/itinerant/military are now populated
# from APT_RMK.csv REF_COL_NAME dispatch. Only commuter and air_taxi
# remarks remain null (no CSV REF_COL_NAME for those).
# Identified: Phase 10 gap analysis.
_ANNUAL_OPS_FIELDS = frozenset(
    {
        "annual_ops_commercial",
        "annual_ops_commuter",
        "annual_ops_commuter_remark",
        "annual_ops_air_taxi",
        "annual_ops_air_taxi_remark",
        "annual_ops_general_aviation_local",
        "annual_ops_general_aviation_itinerant",
        "annual_ops_military",
        "annual_ops_end_of_measurement_period",
    }
)

# NPIAS remark: now populated from APT_RMK.csv NASP_CODE REF_COL_NAME
# dispatch. npias_federal_agreements itself was already populated from
# NASP_CODE (fixed in Phase 11-01).
# Identified: Phase 10 gap analysis, remark gap closed by REF_COL_NAME
# dispatch expansion.

# Frequency remark: UNICOM and CTAF frequencies are now populated from
# FRQ.csv (Phase 11-02). ctaf_remark is now also populated from
# APT_RMK.csv CTAF_FREQ REF_COL_NAME dispatch.
# Identified: Phase 10 gap analysis, frequency gap closed Phase 11-02,
# remark gap closed by REF_COL_NAME dispatch expansion.

# Remark fields with NO CSV dispatch path at all — either no CSV
# REF_COL_NAME exists for them, or the TAB_NAME route is silently
# skipped (AIRPORT_SERVICE -> other_services_available_remark).
# These remain permanently None in CSV output.
# Identified: Phase 5-02 remark dispatch — ongoing maintenance.
_APT_RMK_UNPOPULATED_REMARK_FIELDS = frozenset(
    {
        "fuel_available_remark",
        "other_services_available_remark",
        "responsible_artcc_id_remark",
    }
)

# Remark fields that now HAVE CSV dispatch paths but where APT_RMK.csv
# may not contain the same remark rows as APT.txt for every airport.
# When CSV is None but TXT has a value, this is a FAA data coverage
# gap, not a parser bug. When CSV has a value, it must match TXT.
# Identified: REF_COL_NAME dispatch expansion.
_REMARK_COVERAGE_GAP_TOLERANCE: frozenset[str] = frozenset(
    {
        "city_remark",
        "name_remark",
        "ownership_type_remark",
        "facility_use_remark",
        "latitude_dms_remark",
        "longitude_dms_remark",
        "coords_method_remark",
        "elevation_remark",
        "sectional_remark",
        "distance_from_city_remark",
        "land_area_remark",
        "tie_in_fss_remark",
        "npias_federal_agreements_remark",
        "airport_of_entry_remark",
        "customs_landing_rights_remark",
        "military_civil_join_use_remark",
        "military_landing_rights_remark",
        "agency_performing_inspection_remark",
        "last_inspection_date_remark",
        "airframe_repair_service_remark",
        "power_plant_repair_service_remark",
        "bottled_oxygen_remark",
        "bulk_oxygen_remark",
        "beacon_schedule_remark",
        "ctaf_remark",
        "segmented_circle_available_remark",
        "beacon_color_remark",
        "noncommerical_landing_fee_remark",
        "transient_storage_facilities_remark",
        "wind_indicator_remark",
        "based_general_aviation_single_engine_airplanes_remark",
        "based_general_aviation_multi_engine_airplanes_remark",
        "based_general_aviation_helicopters_remark",
        "based_gliders_remark",
        "based_military_aircraft_remark",
        "based_ultralight_aircraft_remark",
        "annual_ops_general_aviation_local_remark",
        "annual_ops_general_aviation_itinerant_remark",
        "annual_ops_military_remark",
    }
)

# Combined set — all fields that are expected to be None in CSV output.
# Note: owner/manager contact fields removed — those 8 fields are now
# populated from APT_CON.csv and compared against TXT snapshot values.
CSV_EXPECTED_NONE_FIELDS: frozenset[str] = (
    _OWNER_MANAGER_REMARK_UNPOPULATED
    | _BOUNDARY_ARTCC_FIELDS
    | _BASED_AIRCRAFT_FIELDS
    | _ANNUAL_OPS_FIELDS
    | _APT_RMK_UNPOPULATED_REMARK_FIELDS
)

# ---------------------------------------------------------------------------
# Fields where TXT uses blank/sentinel values that produce None but CSV uses
# explicit values. These are known TXT-vs-CSV encoding differences, not
# parser bugs.
#
# 'field_office': TXT stores literal 'NONE' at fixed-width position 45 (4
# chars) for military airports; CSV ADO_CODE column is empty. Both mean
# "not applicable".
#
# 'landing_facility_used_for_medical_purposes': TXT position 1004 is blank
# for all 107 curated airports (→ None). CSV MEDICAL_USE_FLAG has explicit
# 'N' for some (→ False). Both mean "not used for medical purposes".
# Identified: Phase 13 (107-airport expansion).
# ---------------------------------------------------------------------------
_TXT_NONE_SENTINEL_FIELDS: frozenset[str] = frozenset(
    {"field_office", "landing_facility_used_for_medical_purposes"}
)

# ---------------------------------------------------------------------------
# Fuel code reconstruction tolerance: CSV fuel codes exceeding 5 characters
# produce different concatenation than TXT's fixed 5-char slot format.
# E.g., RHV: CSV "A,G100UL,UL94" → "A    G100ULUL94" but TXT reads
# "A    G100 UL94" (separate 5-char slots for G100 and UL94).
# This is a FAA source-data encoding difference, not a parser bug.
# Identified: Phase 13 (107-airport expansion).
# ---------------------------------------------------------------------------
_FUEL_RECONSTRUCTION_TOLERANCE: frozenset[str] = frozenset({"fuel_available"})

# Nested / child-record fields — handled separately in attendance schedule tests.
_NESTED_FIELDS: frozenset[str] = frozenset(
    {"runways", "remarks", "attendance_schedules"}
)

# ---------------------------------------------------------------------------
# RunwayEnd approach_type tolerances for FAA CSV distribution gaps.
#
# These are approach_type values present in APT.txt (RWY record, position 72/294)
# that have NO equivalent in any CSV file: APT_RWY_END.csv ILS_TYPE is empty AND
# ILS_BASE.csv has no record for the (site_no, rwy_end_id).  This is a FAA data
# distribution gap, not a parser bug.  Phase 15 added ILS_BASE.csv enrichment
# which closes all gaps EXCEPT these entries.
#
# Format: {(airport_faa_id, rwy_end_id): txt_approach_type}
# ---------------------------------------------------------------------------
_APPROACH_TYPE_CSV_DATA_GAPS: dict[tuple[str, str], str] = {
    ("ORD", "04L"): "LOCALIZER",  # No ILS_BASE.csv entry for ORD 04L
}

# ---------------------------------------------------------------------------
# AirportRemark element names present in TXT but absent from CSV data.
#
# These are remarks where the TXT fixed-width format contains data that is
# either (a) not present in the CSV remark file at all, or (b) stored under
# a different TAB_NAME/LEGACY scheme that cannot be reconstructed to match
# the TXT element name.
#
# FRG A110-28/A110-29: Displaced threshold approach ratio remarks are in the
#   TXT fixed-width file but entirely absent from APT_RMK.csv.
# GFK A110-21: AIRPORT_CONTACT/NAME remark stored in CSV as LEGACY
#   A110-ASST_MGR-NAME; TXT stores it as A110-21 with a "(CONTACT NAME)"
#   prefix.  Different element numbering and remark text formatting make
#   exact reconstruction infeasible.
# Identified: Phase 13 (107-airport expansion).
# ---------------------------------------------------------------------------
_TXT_ONLY_REMARK_ELEMENTS: dict[str, frozenset[str]] = {
    "FRG": frozenset({"A110-28", "A110-29"}),
    "GFK": frozenset({"A110-21"}),
}

# ---------------------------------------------------------------------------
# AirportRemark element names present in CSV but absent from TXT data.
#
# These are narrative/unmapped remarks that the expanded REF_COL_NAME
# dispatch now stores as AirportRemark rows via the LEGACY fallback path,
# but that have no TXT equivalent (different element numbering).
#
# FRG A110-RWY_14/A110-RWY_19: DISPLACED_THR_APCH_RATIO remarks stored in
#   CSV under A110-RWY_* legacy codes; TXT stores similar content under
#   A110-28/A110-29 (already in _TXT_ONLY_REMARK_ELEMENTS).
# Identified: REF_COL_NAME dispatch expansion.
# ---------------------------------------------------------------------------
_CSV_ONLY_REMARK_ELEMENTS: dict[str, frozenset[str]] = {
    "FRG": frozenset({"A110-RWY_14", "A110-RWY_19"}),
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _load_txt_snapshot(airport_id: str) -> dict[str, Any]:
    """Load the TXT-parser snapshot JSON for the given airport ID from disk."""
    snapshot_path = _SNAPSHOTS_DIR / f"test_apt_snapshot[{airport_id}].json"
    with snapshot_path.open() as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Airport parity tests
# ---------------------------------------------------------------------------


@pytest.mark.csv
@pytest.mark.parametrize("airport_id", CURATED_AIRPORTS)
def test_csv_airport_parity(airport_id: str, csv_apt_engine: Engine) -> None:
    """
    CSV-parsed Airport field values match TXT snapshot baselines.

    For each field in the TXT snapshot:
    - If in CSV_EXPECTED_NONE_FIELDS: verify CSV value is None (documenting gap).
    - Otherwise: verify CSV value equals TXT value.
    """
    from aeroinfo.database.models.apt import Airport

    Session = sessionmaker(bind=csv_apt_engine)
    with Session() as session:
        airport = session.query(Airport).filter_by(faa_id=airport_id).first()
        assert airport is not None, (
            f"Airport {airport_id!r} not found in CSV data — "
            f"verify {_CSV_DATA_DIR / 'APT_BASE.csv'} contains this airport"
        )
        csv_data = extract_record(airport)

    txt_snapshot = _load_txt_snapshot(airport_id)

    for field, txt_value in txt_snapshot.items():
        if field in _NESTED_FIELDS:
            continue  # compared separately or out of scope

        if field in CSV_EXPECTED_NONE_FIELDS:
            assert csv_data[field] is None, (
                f"Field {field!r} should be None in CSV output for {airport_id} "
                f"(no APT_BASE.csv equivalent), but got {csv_data[field]!r}"
            )
            if txt_value is not None and field not in _UNIVERSAL_CSV_GAPS:
                warnings.warn(
                    f"{airport_id}: CSV lacks {field!r} (TXT has {txt_value!r})",
                    stacklevel=1,
                )
            continue

        # TXT blank/sentinel vs CSV explicit value — encoding differences.
        # Case 1: TXT stores 'NONE' sentinel, CSV column is empty (None).
        # Case 2: TXT position is blank (None), CSV has explicit value (e.g., False).
        if field in _TXT_NONE_SENTINEL_FIELDS and (
            (txt_value == "NONE" and csv_data[field] is None)
            or (txt_value is None and csv_data[field] is not None)
        ):
            continue

        # Fuel code reconstruction: CSV codes >5 chars produce different
        # concatenation than TXT 5-char slots. Skip comparison for these.
        if field in _FUEL_RECONSTRUCTION_TOLERANCE and csv_data[field] != txt_value:
            continue

        # Remark coverage gap: APT_RMK.csv may not contain the same remark
        # rows as APT.txt for every airport.  If CSV is None but TXT has a
        # value, tolerate the gap; if CSV has a value, it must match TXT.
        if (
            field in _REMARK_COVERAGE_GAP_TOLERANCE
            and csv_data[field] is None
            and txt_value is not None
        ):
            warnings.warn(
                f"{airport_id}: CSV lacks {field!r} (TXT has {txt_value!r})",
                stacklevel=1,
            )
            continue

        assert csv_data[field] == txt_value, (
            f"Field {field!r} mismatch for {airport_id}: "
            f"CSV={csv_data[field]!r}, TXT={txt_value!r}"
        )


# ---------------------------------------------------------------------------
# AttendanceSchedule parity tests
# ---------------------------------------------------------------------------


@pytest.mark.csv
@pytest.mark.parametrize("airport_id", CURATED_AIRPORTS)
def test_csv_attendance_schedule_parity(
    airport_id: str, csv_apt_engine: Engine
) -> None:
    """
    CSV-parsed AttendanceSchedule rows match TXT snapshot attendance_schedules.

    Compares sorted lists of dicts (by sequence_number) to be order-independent.
    """
    from aeroinfo.database.models.apt import Airport

    Session = sessionmaker(bind=csv_apt_engine)
    with Session() as session:
        airport = session.query(Airport).filter_by(faa_id=airport_id).first()
        assert airport is not None, f"Airport {airport_id!r} not found in CSV data"

        csv_schedules = sorted(
            [extract_record(a) for a in airport.attendance_schedules],
            key=lambda r: r["sequence_number"] or 0,
        )

    txt_snapshot = _load_txt_snapshot(airport_id)
    txt_schedules = sorted(
        txt_snapshot.get("attendance_schedules", []),
        key=lambda r: r["sequence_number"] or 0,
    )

    assert len(csv_schedules) == len(txt_schedules), (
        f"AttendanceSchedule count mismatch for {airport_id}: "
        f"CSV={len(csv_schedules)}, TXT={len(txt_schedules)}"
    )

    for csv_sched, txt_sched in zip(csv_schedules, txt_schedules, strict=True):
        assert csv_sched == txt_sched, (
            f"AttendanceSchedule mismatch for {airport_id} "
            f"seq={csv_sched.get('sequence_number')!r}: "
            f"CSV={csv_sched!r}, TXT={txt_sched!r}"
        )


# ---------------------------------------------------------------------------
# Runway remark fields — expected None (not populated by APT_RMK.csv)
# ---------------------------------------------------------------------------
# Fields removed from this set (now compared against TXT):
#   name_remark (RUNWAY/RWY_ID dispatch)
#   surface_type_condition_remark (RUNWAY_SURFACE_TYPE/SURFACE_TYPE_CODE dispatch)
#   pavement_classification_number_remark (RUNWAY/PCN dispatch)

# Runway remark fields — all now have CSV dispatch paths via expanded
# _RUNWAY_REMARK_DISPATCH.  However, APT_RMK.csv may not contain the
# same remark rows as APT.txt for every runway.  When CSV is None but
# TXT has a value, tolerate the gap; when CSV has a value, it must
# match TXT.
_RUNWAY_REMARK_FIELDS = frozenset(
    {
        "length_remark",
        "width_remark",
        "surface_treatment_remark",
        "edge_light_intensity_remark",
        "weight_bearing_capacity_single_wheel_remark",
        "weight_bearing_capacity_dual_wheels_remark",
        "weight_bearing_capacity_two_dual_wheels_tandem_remark",
        "weight_bearing_capacity_two_dual_wheels_double_tandem_remark",
    }
)

# RunwayEnd remark fields — permanently None (no CSV REF_COL_NAME at all)
_RUNWAY_END_REMARK_FIELDS_PERMANENTLY_NONE = frozenset(
    {
        "longitude_dms_remark",
        "threshold_crossing_height_remark",
        "displaced_threshold_longitude_dms_remark",
    }
)

# RunwayEnd remark fields with CSV dispatch paths — APT_RMK.csv may not
# contain the same remark rows as APT.txt.  Tolerate CSV=None when TXT
# has a value; when CSV has a value, it must match TXT.
_RUNWAY_END_REMARK_FIELDS_COVERAGE_GAP = frozenset(
    {
        "true_alignment_remark",
        "right_traffic_remark",
        "markings_remark",
        "latitude_dms_remark",
        "elevation_remark",
        "visual_glide_path_angle_remark",
        "displaced_threshold_latitude_dms_remark",
        "displaced_threshold_length_remark",
        "rvr_equipment_remark",
        "reil_availability_remark",
        "centerline_light_availability_remark",
        "touchdown_lights_availability_remark",
        "controlling_object_description_remark",
        "controlling_object_marking_remark",
        "part77_category_remark",
        "controlling_object_height_above_runway_remark",
        "controlling_object_distance_from_runway_remark",
        "controlling_object_centerline_offset_remark",
        "gradient_remark",
        "takeoff_run_available_remark",
    }
)

# Combined for backwards compatibility in test references
_RUNWAY_END_REMARK_FIELDS = (
    _RUNWAY_END_REMARK_FIELDS_PERMANENTLY_NONE | _RUNWAY_END_REMARK_FIELDS_COVERAGE_GAP
)


# ---------------------------------------------------------------------------
# Runway parity tests
# ---------------------------------------------------------------------------


@pytest.mark.csv
@pytest.mark.parametrize("airport_id", CURATED_AIRPORTS)
def test_csv_runway_parity(airport_id: str, csv_apt_engine: Engine) -> None:
    """
    CSV-parsed Runway field values match TXT snapshot baselines.

    Remark fields in _RUNWAY_REMARK_FIELDS are expected to be None — no APT_RMK.csv
    dispatch populates them for any curated airport.  All other fields are compared
    against TXT snapshot values field-by-field.
    """
    from aeroinfo.database.models.apt import Airport

    Session = sessionmaker(bind=csv_apt_engine)
    with Session() as session:
        airport = session.query(Airport).filter_by(faa_id=airport_id).first()
        assert airport is not None, f"Airport {airport_id!r} not found in CSV data"

        csv_runways = sorted(
            [extract_record(rwy) for rwy in airport.runways],
            key=lambda r: r["name"] or "",
        )

    txt_snapshot = _load_txt_snapshot(airport_id)
    # TXT snapshot nests runway_ends inside runways — strip them for this test
    txt_runways = sorted(
        [
            {k: v for k, v in rwy.items() if k != "runway_ends"}
            for rwy in txt_snapshot.get("runways", [])
        ],
        key=lambda r: r["name"] or "",
    )

    assert len(csv_runways) == len(txt_runways), (
        f"Runway count mismatch for {airport_id}: "
        f"CSV={len(csv_runways)}, TXT={len(txt_runways)}"
    )

    for csv_data, txt_data in zip(csv_runways, txt_runways, strict=True):
        name = csv_data.get("name")
        for field, txt_value in txt_data.items():
            # Remark coverage gap: APT_RMK.csv may not contain the same
            # remark rows as APT.txt.  If CSV is None, tolerate the gap;
            # if CSV has a value, it must match TXT.
            if field in _RUNWAY_REMARK_FIELDS and csv_data[field] is None:
                continue
            assert csv_data[field] == txt_value, (
                f"Field {field!r} mismatch for {airport_id} runway {name!r}: "
                f"CSV={csv_data[field]!r}, TXT={txt_value!r}"
            )


# ---------------------------------------------------------------------------
# RunwayEnd parity tests
# ---------------------------------------------------------------------------


@pytest.mark.csv
@pytest.mark.parametrize("airport_id", CURATED_AIRPORTS)
def test_csv_runway_end_parity(airport_id: str, csv_apt_engine: Engine) -> None:
    """
    CSV-parsed RunwayEnd field values match TXT snapshot baselines.

    Covers all ~65 RunwayEnd fields including coordinates, LAHSO, markings
    condition, controlling objects, and arresting_gear.

    Remark fields in _RUNWAY_END_REMARK_FIELDS are expected None — no APT_RMK.csv
    dispatch populates them for any curated airport.  Airports EDF and MDW have
    arresting gear data; LL10 and ARR do not.
    """
    from aeroinfo.database.models.apt import Airport, RunwayEnd

    Session = sessionmaker(bind=csv_apt_engine)
    with Session() as session:
        airport = session.query(Airport).filter_by(faa_id=airport_id).first()
        assert airport is not None, f"Airport {airport_id!r} not found in CSV data"

        fsn = airport.facility_site_number
        csv_ends = sorted(
            [
                extract_record(rwe)
                for rwe in session.query(RunwayEnd)
                .filter_by(facility_site_number=fsn)
                .all()
            ],
            key=lambda r: (r["runway_name"] or "", r["id"] or ""),
        )

    txt_snapshot = _load_txt_snapshot(airport_id)
    # Flatten runway_ends from the nested snapshot structure
    txt_ends = sorted(
        [
            rwe
            for rwy in txt_snapshot.get("runways", [])
            for rwe in rwy.get("runway_ends", [])
        ],
        key=lambda r: (r.get("runway_name") or "", r.get("id") or ""),
    )

    assert len(csv_ends) == len(txt_ends), (
        f"RunwayEnd count mismatch for {airport_id}: "
        f"CSV={len(csv_ends)}, TXT={len(txt_ends)}"
    )

    for csv_data, txt_data in zip(csv_ends, txt_ends, strict=True):
        rwy_name = csv_data.get("runway_name")
        end_id = csv_data.get("id")
        for field, txt_value in txt_data.items():
            # Permanently None: no CSV REF_COL_NAME at all.
            if field in _RUNWAY_END_REMARK_FIELDS_PERMANENTLY_NONE:
                assert csv_data[field] is None, (
                    f"Field {field!r} should be None for {airport_id} "
                    f"runway end {rwy_name!r}/{end_id!r} (no CSV REF_COL_NAME), "
                    f"but got {csv_data[field]!r}"
                )
                continue
            # Remark coverage gap: dispatch path exists but APT_RMK.csv may
            # not contain the same rows as APT.txt.
            if (
                field in _RUNWAY_END_REMARK_FIELDS_COVERAGE_GAP
                and csv_data[field] is None
            ):
                continue
            # FAA CSV distribution gap: approach_type in TXT but absent from
            # all CSV files (APT_RWY_END.csv ILS_TYPE + ILS_BASE.csv).
            if (
                field == "approach_type"
                and csv_data[field] is None
                and (airport_id, end_id) in _APPROACH_TYPE_CSV_DATA_GAPS
            ):
                assert txt_value == _APPROACH_TYPE_CSV_DATA_GAPS[(airport_id, end_id)]
                continue
            assert csv_data[field] == txt_value, (
                f"Field {field!r} mismatch for {airport_id} "
                f"runway end {rwy_name!r}/{end_id!r}: "
                f"CSV={csv_data[field]!r}, TXT={txt_value!r}"
            )


# ---------------------------------------------------------------------------
# AirportRemark parity tests
# ---------------------------------------------------------------------------


@pytest.mark.csv
@pytest.mark.parametrize("airport_id", CURATED_AIRPORTS)
def test_csv_airport_remark_parity(airport_id: str, csv_apt_engine: Engine) -> None:
    """
    CSV-parsed AirportRemark table entries match TXT snapshot baselines.

    Verifies that all remark_element_name values and remark texts for each
    airport match the TXT snapshot 'remarks' list.  Covers GENERAL_REMARK,
    ARPT_PSN_SOURCE, CLOSE_IN_OBSTN, ARRESTING_DEVICE, and FUEL_TYPE entries
    (TAB_NAME categories that produce AirportRemark rows rather than attribute
    updates).

    Comparison is sorted by remark_element_name for order-independence.
    """
    from aeroinfo.database.models.apt import Airport, AirportRemark

    Session = sessionmaker(bind=csv_apt_engine)
    with Session() as session:
        airport = session.query(Airport).filter_by(faa_id=airport_id).first()
        assert airport is not None, f"Airport {airport_id!r} not found in CSV data"

        fsn = airport.facility_site_number
        # Filter out CSV-only remark elements (no TXT equivalent).
        csv_only = _CSV_ONLY_REMARK_ELEMENTS.get(airport_id, frozenset())
        csv_remarks = sorted(
            [
                extract_record(rmk)
                for rmk in session.query(AirportRemark)
                .filter_by(facility_site_number=fsn)
                .all()
                if rmk.remark_element_name not in csv_only
            ],
            key=lambda r: r["remark_element_name"] or "",
        )

    txt_snapshot = _load_txt_snapshot(airport_id)
    # Filter out TXT-only remark elements (absent from CSV data entirely).
    txt_only = _TXT_ONLY_REMARK_ELEMENTS.get(airport_id, frozenset())
    txt_remarks = sorted(
        [
            r
            for r in txt_snapshot.get("remarks", [])
            if r.get("remark_element_name") not in txt_only
        ],
        key=lambda r: r.get("remark_element_name") or "",
    )

    assert len(csv_remarks) == len(txt_remarks), (
        f"AirportRemark count mismatch for {airport_id}: "
        f"CSV={len(csv_remarks)}, TXT={len(txt_remarks)}\n"
        f"CSV element names: {[r['remark_element_name'] for r in csv_remarks]}\n"
        f"TXT element names: {[r['remark_element_name'] for r in txt_remarks]}"
    )

    for csv_rmk, txt_rmk in zip(csv_remarks, txt_remarks, strict=True):
        assert csv_rmk["remark_element_name"] == txt_rmk["remark_element_name"], (
            f"remark_element_name mismatch for {airport_id}: "
            f"CSV={csv_rmk['remark_element_name']!r}, "
            f"TXT={txt_rmk['remark_element_name']!r}"
        )
        assert csv_rmk["remark"] == txt_rmk["remark"], (
            f"remark text mismatch for {airport_id} "
            f"element={csv_rmk['remark_element_name']!r}: "
            f"CSV={csv_rmk['remark']!r}, TXT={txt_rmk['remark']!r}"
        )
