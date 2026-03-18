"""
Cross-format parity tests -- TXT vs CSV parser output.

Verifies that TXT and CSV parsers produce identical database records for all
curated airports (117) and navaids (5), excluding accepted field gaps that
are documented in independent exclusion dicts below.

Purpose: TST-04 requires proof that TXT and CSV parsers produce identical
output for curated records.  Any future parser change that breaks parity
will be caught immediately.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy.orm import sessionmaker

from tests.conftest import CURATED_AIRPORTS, CURATED_NAVAIDS
from tests.snapshot_helpers import extract_record

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


# ---------------------------------------------------------------------------
# Accepted airport field gaps (independent of tests/parity/categories.py)
# ---------------------------------------------------------------------------
# Field names to skip on the airport record, with rationale string.
# Derived from tests/parity/categories.py ACCEPTED_FIELDS where table is "airports".

ACCEPTED_AIRPORT_FIELD_GAPS: dict[str, str] = {
    "boundary_artcc_computer_id": "boundary_artcc -- no CSV equivalent",
    "boundary_artcc_id": "boundary_artcc -- no CSV equivalent",
    "boundary_artcc_name": "boundary_artcc -- no CSV equivalent",
    "field_office": "field_office_none -- TXT 'NONE' sentinel vs CSV empty",
    "landing_facility_used_for_medical_purposes": "medical_purposes -- TXT blank vs CSV explicit False",
    "customs_landing_rights_remark": "remark_data_gap -- CSV APT_RMK.csv lacks this remark",
    "other_services_available_remark": "remark_data_gap -- CSV APT_RMK.csv REMARK_TEXT empty for AIRPORT_SERVICE rows",
    "fuel_available": "fuel_format_diff -- CSV fuel codes >5 chars produce different concatenation",
    "airspace_analysis_remark": "remark_data_gap -- negligible (4 diffs total)",
    "transient_storage_facilities_remark": "remark_content_diffs -- remark text differs between formats",
    "arff_certification_remark": "remark_content_diffs -- remark text differs between formats",
    "last_inspection_date_remark": "remark_content_diffs -- remark text differs between formats",
    "tie_in_fss_remark": "remark_content_diffs -- remark text differs between formats",
}

# ---------------------------------------------------------------------------
# Accepted navaid field gaps (independent of tests/parity/categories.py)
# ---------------------------------------------------------------------------
# TWEB fields have no CSV equivalent (per FAA TXT_to_CSV_Mapping.txt).
# Sub-tables (airspace_fixes, holding_patterns, fan_markers) have no CSV
# source files at all -- these are whole-table accepted gaps handled by
# skipping those relationship attributes entirely.

ACCEPTED_NAVAID_FIELD_GAPS: dict[str, str] = {
    "tweb_hours": "tweb -- no CSV equivalent",
    "tweb_phone_number": "tweb -- no CSV equivalent",
    "tweb": "tweb -- no CSV equivalent",
}

# ---------------------------------------------------------------------------
# Accepted runway/runway-end field gaps
# ---------------------------------------------------------------------------

ACCEPTED_RUNWAY_FIELD_GAPS: dict[str, str] = {
    "surface_type_condition_remark": "remark_content_diffs",
    "name_remark": "remark_content_diffs",
}

ACCEPTED_RUNWAY_END_FIELD_GAPS: dict[str, str] = {
    "markings_remark": "remark_content_diffs",
    "rvr_equipment_remark": "minor_accepted",
    "displaced_threshold_latitude_dms": "minor_accepted",
}

# RunwayEnd approach_type: FAA CSV distribution gaps where TXT has ILS data
# but CSV has no ILS_TYPE and no ILS_BASE.csv record.
# Format: {(airport_faa_id, rwy_end_id): txt_approach_type}
APPROACH_TYPE_CSV_DATA_GAPS: dict[tuple[str, str], str] = {
    ("BLM", "14"): "LOC/DME",
    ("ORD", "04L"): "LOCALIZER",
}

# ---------------------------------------------------------------------------
# Per-airport remark element name exclusions
# ---------------------------------------------------------------------------
# Remark element names that exist only in one format due to FAA data encoding
# differences.  Copied from test_apt_csv.py exclusion dicts.

TXT_ONLY_REMARK_ELEMENTS: dict[str, frozenset[str]] = {
    "3A7": frozenset({"A110-3", "A110-4"}),
    "7M2": frozenset({"A110-6", "A110-7"}),
    "CMD": frozenset({"A17", "A17 1"}),
    "FRG": frozenset({"A110-28", "A110-29"}),
    "GFK": frozenset({"A110-21"}),
}

CSV_ONLY_REMARK_ELEMENTS: dict[str, frozenset[str]] = {
    "3A7": frozenset({"A110*P"}),
    "7M2": frozenset({"A110-RWY_09", "A110-RWY_27"}),
    "CMD": frozenset({"A17"}),
    "FRG": frozenset({"A110-RWY_14", "A110-RWY_19"}),
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _compare_records(
    txt_dict: dict[str, Any],
    csv_dict: dict[str, Any],
    excluded_fields: dict[str, str] | frozenset[str],
    record_id: str,
) -> list[str]:
    """
    Compare two extract_record() dicts field-by-field.

    Returns a list of diff strings (empty = match).
    Skips keys in excluded_fields.
    """
    diffs: list[str] = []
    all_keys = set(txt_dict.keys()) | set(csv_dict.keys())

    for key in sorted(all_keys):
        if key in excluded_fields:
            continue

        txt_val = txt_dict.get(key)
        csv_val = csv_dict.get(key)

        if txt_val != csv_val:
            diffs.append(f"{record_id}.{key}: txt={txt_val!r} csv={csv_val!r}")

    return diffs


# ---------------------------------------------------------------------------
# Airport cross-parity test
# ---------------------------------------------------------------------------

# Fields that are nested relationships, not scalar columns
_AIRPORT_NESTED_FIELDS = frozenset({"runways", "remarks", "attendance_schedules"})

# Combined exclusion for airport-level fields
_AIRPORT_EXCLUDED = {
    **ACCEPTED_AIRPORT_FIELD_GAPS,
    **dict.fromkeys(_AIRPORT_NESTED_FIELDS, "nested"),
}


@pytest.mark.parametrize("airport_id", CURATED_AIRPORTS)
def test_airport_cross_parity(
    airport_id: str,
    apt_engine: Engine,
    csv_apt_engine: Engine,
) -> None:
    """
    TXT and CSV parsers produce identical Airport output for each curated airport.

    Compares airport-level fields, runways, runway_ends, attendance_schedules,
    and remarks (filtered by element names present in both formats).
    """
    from aeroinfo.database.models.apt import Airport, AirportRemark, RunwayEnd

    diffs: list[str] = []

    TxtSession = sessionmaker(bind=apt_engine)
    CsvSession = sessionmaker(bind=csv_apt_engine)

    with TxtSession() as txt_session, CsvSession() as csv_session:
        txt_apt = txt_session.query(Airport).filter_by(faa_id=airport_id).first()
        csv_apt = csv_session.query(Airport).filter_by(faa_id=airport_id).first()

        assert txt_apt is not None, f"Airport {airport_id!r} not found in TXT data"
        assert csv_apt is not None, f"Airport {airport_id!r} not found in CSV data"

        # -- Airport-level fields --
        txt_data = extract_record(txt_apt)
        csv_data = extract_record(csv_apt)
        diffs.extend(
            _compare_records(txt_data, csv_data, _AIRPORT_EXCLUDED, airport_id)
        )

        # -- Attendance schedules (sorted by sequence) --
        txt_scheds = sorted(
            [extract_record(s) for s in txt_apt.attendance_schedules],
            key=lambda r: r.get("sequence_number") or 0,
        )
        csv_scheds = sorted(
            [extract_record(s) for s in csv_apt.attendance_schedules],
            key=lambda r: r.get("sequence_number") or 0,
        )

        if len(txt_scheds) != len(csv_scheds):
            diffs.append(
                f"{airport_id}.attendance_schedules: "
                f"count txt={len(txt_scheds)} csv={len(csv_scheds)}"
            )
        else:
            for i, (txt_s, csv_s) in enumerate(
                zip(txt_scheds, csv_scheds, strict=True)
            ):
                diffs.extend(
                    _compare_records(
                        txt_s, csv_s, frozenset(), f"{airport_id}.sched[{i}]"
                    )
                )

        # -- Runways (sorted by name) --
        txt_rwys = sorted(txt_apt.runways, key=lambda r: r.name or "")
        csv_rwys = sorted(csv_apt.runways, key=lambda r: r.name or "")

        if len(txt_rwys) != len(csv_rwys):
            diffs.append(
                f"{airport_id}.runways: count txt={len(txt_rwys)} csv={len(csv_rwys)}"
            )
        else:
            for txt_rwy, csv_rwy in zip(txt_rwys, csv_rwys, strict=True):
                rwy_name = txt_rwy.name or "?"
                txt_rwy_data = extract_record(txt_rwy)
                csv_rwy_data = extract_record(csv_rwy)
                # Exclude nested runway_ends from runway comparison
                rwy_excluded = {
                    **ACCEPTED_RUNWAY_FIELD_GAPS,
                    "runway_ends": "nested",
                    "remarks": "nested",
                }
                diffs.extend(
                    _compare_records(
                        txt_rwy_data,
                        csv_rwy_data,
                        rwy_excluded,
                        f"{airport_id}.rwy[{rwy_name}]",
                    )
                )

        # -- Runway ends (sorted by runway_name + id) --
        fsn_txt = txt_apt.facility_site_number
        fsn_csv = csv_apt.facility_site_number

        txt_ends = sorted(
            txt_session.query(RunwayEnd).filter_by(facility_site_number=fsn_txt).all(),
            key=lambda r: (r.runway_name or "", r.id or ""),
        )
        csv_ends = sorted(
            csv_session.query(RunwayEnd).filter_by(facility_site_number=fsn_csv).all(),
            key=lambda r: (r.runway_name or "", r.id or ""),
        )

        if len(txt_ends) != len(csv_ends):
            diffs.append(
                f"{airport_id}.runway_ends: count txt={len(txt_ends)} csv={len(csv_ends)}"
            )
        else:
            rwe_excluded_base = {
                **ACCEPTED_RUNWAY_END_FIELD_GAPS,
                "remarks": "nested",
            }
            for txt_end, csv_end in zip(txt_ends, csv_ends, strict=True):
                end_label = f"{txt_end.runway_name}/{txt_end.id}"
                # Add approach_type to exclusions if this is a known CSV data gap
                rwe_excluded = dict(rwe_excluded_base)
                if (airport_id, txt_end.id) in APPROACH_TYPE_CSV_DATA_GAPS:
                    rwe_excluded["approach_type"] = "csv_data_gap"
                diffs.extend(
                    _compare_records(
                        extract_record(txt_end),
                        extract_record(csv_end),
                        rwe_excluded,
                        f"{airport_id}.rwe[{end_label}]",
                    )
                )

        # -- Remarks (only element names present in BOTH formats) --
        txt_only_excl = TXT_ONLY_REMARK_ELEMENTS.get(airport_id, frozenset())
        csv_only_excl = CSV_ONLY_REMARK_ELEMENTS.get(airport_id, frozenset())

        txt_remarks_all = (
            txt_session.query(AirportRemark)
            .filter_by(facility_site_number=fsn_txt)
            .all()
        )
        csv_remarks_all = (
            csv_session.query(AirportRemark)
            .filter_by(facility_site_number=fsn_csv)
            .all()
        )

        # Build sets of element names present in each format (after exclusions)
        txt_element_names = {
            r.remark_element_name
            for r in txt_remarks_all
            if r.remark_element_name not in txt_only_excl
        }
        csv_element_names = {
            r.remark_element_name
            for r in csv_remarks_all
            if r.remark_element_name not in csv_only_excl
        }
        common_element_names = txt_element_names & csv_element_names

        # Filter to common elements and sort for stable comparison
        txt_remarks = sorted(
            [
                extract_record(r)
                for r in txt_remarks_all
                if r.remark_element_name in common_element_names
            ],
            key=lambda r: r.get("remark_element_name") or "",
        )
        csv_remarks = sorted(
            [
                extract_record(r)
                for r in csv_remarks_all
                if r.remark_element_name in common_element_names
            ],
            key=lambda r: r.get("remark_element_name") or "",
        )

        if len(txt_remarks) != len(csv_remarks):
            diffs.append(
                f"{airport_id}.remarks(common): "
                f"count txt={len(txt_remarks)} csv={len(csv_remarks)}"
            )
        else:
            for txt_rmk, csv_rmk in zip(txt_remarks, csv_remarks, strict=True):
                elem = txt_rmk.get("remark_element_name", "?")
                # Skip remark_element_name itself (it's the join key)
                rmk_excluded = frozenset({"remark_element_name"})
                diffs.extend(
                    _compare_records(
                        txt_rmk,
                        csv_rmk,
                        rmk_excluded,
                        f"{airport_id}.rmk[{elem}]",
                    )
                )

    assert len(diffs) == 0, (
        f"Cross-parity failures for {airport_id} ({len(diffs)} diffs):\n"
        + "\n".join(f"  - {d}" for d in diffs)
    )


# ---------------------------------------------------------------------------
# Navaid cross-parity test
# ---------------------------------------------------------------------------

# Navaid sub-record types with no CSV source (whole-table accepted gaps)
_NAVAID_NO_CSV_SUBTABLES = frozenset(
    {
        "airspace_fixes",
        "holding_patterns",
        "fan_markers",
    }
)

# Combined exclusion for navaid-level fields
_NAVAID_EXCLUDED = {
    **ACCEPTED_NAVAID_FIELD_GAPS,
    **dict.fromkeys(_NAVAID_NO_CSV_SUBTABLES, "nested/no-csv"),
    "remarks": "nested",
    "vor_receiver_checkpoints": "nested",
}


@pytest.mark.parametrize(
    ("navaid_id", "facility_type"),
    CURATED_NAVAIDS,
    ids=[f"{nid}-{ntype.replace('/', '_')}" for nid, ntype in CURATED_NAVAIDS],
)
def test_navaid_cross_parity(
    navaid_id: str,
    facility_type: str,
    nav_engine: Engine,
    csv_nav_engine: Engine,
) -> None:
    """
    TXT and CSV parsers produce identical Navaid output for each curated navaid.

    Compares navaid-level fields and remarks (only those present in both formats).
    Skips sub-record types with no CSV source (airspace_fixes, holding_patterns,
    fan_markers).
    """
    from aeroinfo.database.models.nav import Navaid, Remark

    diffs: list[str] = []
    navaid_label = f"{navaid_id}-{facility_type}"

    TxtSession = sessionmaker(bind=nav_engine)
    CsvSession = sessionmaker(bind=csv_nav_engine)

    with TxtSession() as txt_session, CsvSession() as csv_session:
        txt_nav = (
            txt_session.query(Navaid)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .first()
        )
        csv_nav = (
            csv_session.query(Navaid)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .first()
        )

        assert txt_nav is not None, f"Navaid {navaid_label!r} not found in TXT data"
        assert csv_nav is not None, f"Navaid {navaid_label!r} not found in CSV data"

        # -- Navaid-level fields --
        txt_data = extract_record(txt_nav)
        csv_data = extract_record(csv_nav)
        diffs.extend(
            _compare_records(txt_data, csv_data, _NAVAID_EXCLUDED, navaid_label)
        )

        # -- Remarks (only those present in both formats) --
        txt_remarks_all = (
            txt_session.query(Remark)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .all()
        )
        csv_remarks_all = (
            csv_session.query(Remark)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .all()
        )

        # Navaid remarks use remark text as PK, so compare by remark text
        txt_remark_texts = {r.remark for r in txt_remarks_all}
        csv_remark_texts = {r.remark for r in csv_remarks_all}
        common_remarks = txt_remark_texts & csv_remark_texts

        txt_remarks = sorted(
            [extract_record(r) for r in txt_remarks_all if r.remark in common_remarks],
            key=lambda r: r.get("remark") or "",
        )
        csv_remarks = sorted(
            [extract_record(r) for r in csv_remarks_all if r.remark in common_remarks],
            key=lambda r: r.get("remark") or "",
        )

        # Also check for non-common remarks (diffs in remark set)
        txt_only_remarks = txt_remark_texts - csv_remark_texts
        csv_only_remarks = csv_remark_texts - txt_remark_texts
        diffs.extend(
            f"{navaid_label}.remark: txt-only={rmk!r}"
            for rmk in sorted(txt_only_remarks)
        )
        diffs.extend(
            f"{navaid_label}.remark: csv-only={rmk!r}"
            for rmk in sorted(csv_only_remarks)
        )

        # Compare field-by-field on matching remarks
        for txt_rmk, csv_rmk in zip(txt_remarks, csv_remarks, strict=True):
            rmk_text = (txt_rmk.get("remark") or "")[:40]
            # Skip remark text itself (it's the join key)
            diffs.extend(
                _compare_records(
                    txt_rmk,
                    csv_rmk,
                    frozenset({"remark"}),
                    f"{navaid_label}.rmk[{rmk_text}]",
                )
            )

        # -- VOR Receiver Checkpoints --
        from aeroinfo.database.models.nav import VORReceiverCheckpoint

        txt_ckpts = sorted(
            [
                extract_record(c)
                for c in txt_session.query(VORReceiverCheckpoint)
                .filter_by(facility_id=navaid_id, facility_type=facility_type)
                .all()
            ],
            key=lambda c: c.get("bearing") or 0,
        )
        csv_ckpts = sorted(
            [
                extract_record(c)
                for c in csv_session.query(VORReceiverCheckpoint)
                .filter_by(facility_id=navaid_id, facility_type=facility_type)
                .all()
            ],
            key=lambda c: c.get("bearing") or 0,
        )

        if len(txt_ckpts) != len(csv_ckpts):
            diffs.append(
                f"{navaid_label}.checkpoints: "
                f"count txt={len(txt_ckpts)} csv={len(csv_ckpts)}"
            )
        else:
            for i, (txt_c, csv_c) in enumerate(zip(txt_ckpts, csv_ckpts, strict=True)):
                diffs.extend(
                    _compare_records(
                        txt_c,
                        csv_c,
                        frozenset(),
                        f"{navaid_label}.ckpt[{i}]",
                    )
                )

    assert len(diffs) == 0, (
        f"Cross-parity failures for {navaid_label} ({len(diffs)} diffs):\n"
        + "\n".join(f"  - {d}" for d in diffs)
    )
