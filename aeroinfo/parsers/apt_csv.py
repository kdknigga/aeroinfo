#!/usr/bin/env python

"""
Parser for NASR APT CSV records.

This module reads the following CSV files from a directory and merges them
into the database:

  APT_BASE.csv    -> Airport
  APT_ATT.csv     -> AttendanceSchedule
  APT_RWY.csv     -> Runway
  APT_RWY_END.csv -> RunwayEnd
  APT_ARS.csv     -> RunwayEnd.arresting_gear
  APT_RMK.csv     -> Remarks (Airport, Runway, RunwayEnd)
  APT_CON.csv     -> Airport owner/manager contacts
  FRQ.csv         -> Airport unicom/ctaf (via frq_csv module)
  ILS_BASE.csv    -> RunwayEnd.approach_type enrichment (via ils_csv module)

Field values are produced to match the TXT parser's output as closely as
possible given the available CSV columns.

Fields intentionally None (no APT_BASE.csv equivalent):
  - boundary_artcc_id, boundary_artcc_computer_id, boundary_artcc_name
      These three ARTCC fields have no column in APT_BASE.csv (confirmed N/A
      in TXT_to_CSV_Mapping.txt).  They will be None for CSV-imported airports.
  - based_general_aviation_single_engine_airplanes, ..._multi_engine_airplanes,
    ..._jet_engine_airplanes, ..._helicopters, based_gliders,
    based_military_aircraft, based_ultralight_aircraft
      The mapping document lists BASED_* columns but they are absent from the
      actual 2026-02-19 APT_BASE.csv (90 columns; none of those names exist).
  - annual_ops_commercial, annual_ops_commuter, annual_ops_air_taxi,
    annual_ops_general_aviation_local, annual_ops_general_aviation_itinerant,
    annual_ops_military, annual_ops_end_of_measurement_period
      Similarly absent from actual APT_BASE.csv despite mapping doc listing them.
  - unicom, ctaf
      These come from FRQ.csv, not APT_BASE.csv.
"""

import csv
import logging
from pathlib import Path
from typing import TextIO

from sqlalchemy.orm import Session as SASession
from sqlalchemy.orm import sessionmaker

from aeroinfo.database import Engine
from aeroinfo.database.models.apt import (
    Airport,
    AirportRemark,
    AttendanceSchedule,
    Runway,
    RunwayEnd,
)
from aeroinfo.parsers import frq_csv, ils_csv
from aeroinfo.parsers.utils import (
    build_dms_string,
    build_total_secs_string,
    csv_field,
    detect_encoding,
    reconstruct_arff,
    reconstruct_attendance_schedule,
    reconstruct_fuel,
    reconstruct_mag_variation,
    reconstruct_transient_storage,
)

logger = logging.getLogger(__name__)
Session = sessionmaker()

# ---------------------------------------------------------------------------
# ASP_ANLYS_DTRM_CODE -> airspace_analysis string
# ---------------------------------------------------------------------------
# CSV uses 'CONDL' where TXT stores 'CONDITIONAL'.  All other values are
# identical between CSV and TXT (verified against 2026-02-19 data cycle).
_AIRSPACE_ANALYSIS_MAP: dict[str, str] = {
    "CONDL": "CONDITIONAL",
}

# ---------------------------------------------------------------------------
# SITE_TYPE_CODE -> facility_type string
# ---------------------------------------------------------------------------
# From TXT data: the 13-char "LANDING FACILITY TYPE" field at position 15.
# In CSV, this is encoded as a single-char code in SITE_TYPE_CODE.
# Verified by comparing CSV code vs TXT field for 4 baseline airports (all 'A').
# Full mapping from TXT source (FAA NASR APT.txt layout document):
_SITE_TYPE_MAP: dict[str, str] = {
    "A": "AIRPORT",
    "B": "BALLOONPORT",
    "C": "SEAPLANE BASE",
    "G": "GLIDERPORT",
    "H": "HELIPORT",
    "U": "ULTRALIGHT",
}

# ---------------------------------------------------------------------------
# Required APT_BASE.csv columns — parser fails immediately if any are absent
# ---------------------------------------------------------------------------
_REQUIRED_APT_BASE_COLS = {
    "SITE_NO",
    "SITE_TYPE_CODE",
    "ARPT_ID",
    "EFF_DATE",
    "LAT_DEG",
    "LAT_MIN",
    "LAT_SEC",
    "LAT_HEMIS",
    "LONG_DEG",
    "LONG_MIN",
    "LONG_SEC",
    "LONG_HEMIS",
}

# Required APT_ATT.csv columns
_REQUIRED_APT_ATT_COLS = {
    "SITE_NO",
    "SITE_TYPE_CODE",
    "SKED_SEQ_NO",
    "MONTH",
    "DAY",
    "HOUR",
}


def parse(csv_dir: str) -> None:
    """
    Parse APT CSV files from ``csv_dir`` and store results in DB.

    Reads Airport, AttendanceSchedule, Runway, RunwayEnd, arresting gear,
    and remark records from the given directory and merges them into the
    database using the project's standard Engine/Session pattern.  Raises
    RuntimeError (wrapping the original exception) if any row fails coercion.

    Parse order (FK dependency):
      APT_BASE.csv    -> Airport
      APT_ATT.csv     -> AttendanceSchedule  (FK: Airport)
      APT_RWY.csv     -> Runway              (FK: Airport)
      APT_RWY_END.csv -> RunwayEnd           (FK: Runway)
      APT_ARS.csv     -> RunwayEnd.arresting_gear (FK: RunwayEnd)
      APT_RMK.csv     -> Remarks (MUST be last — updates Airport/Runway/RunwayEnd
                         attributes that must already exist)
      APT_CON.csv     -> Airport owner/manager contacts (FK: Airport)
      FRQ.csv         -> Airport unicom/ctaf frequencies (FK: Airport via faa_id)

    Args:
        csv_dir: Path to the directory containing the APT CSV files.

    """
    base_path = Path(csv_dir) / "APT_BASE.csv"
    att_path = Path(csv_dir) / "APT_ATT.csv"
    rwy_path = Path(csv_dir) / "APT_RWY.csv"
    rwy_end_path = Path(csv_dir) / "APT_RWY_END.csv"
    ars_path = Path(csv_dir) / "APT_ARS.csv"
    rmk_path = Path(csv_dir) / "APT_RMK.csv"
    con_path = Path(csv_dir) / "APT_CON.csv"
    frq_path = Path(csv_dir) / "FRQ.csv"
    ils_path = Path(csv_dir) / "ILS_BASE.csv"

    ils_lookup = ils_csv.build_approach_type_lookup(ils_path)

    base_enc = detect_encoding(base_path)
    att_enc = detect_encoding(att_path)
    rwy_enc = detect_encoding(rwy_path)
    rwy_end_enc = detect_encoding(rwy_end_path)
    ars_enc = detect_encoding(ars_path)
    rmk_enc = detect_encoding(rmk_path)
    con_enc = detect_encoding(con_path)

    with (
        base_path.open(newline="", encoding=base_enc, errors="replace") as base_f,
        att_path.open(newline="", encoding=att_enc, errors="replace") as att_f,
        rwy_path.open(newline="", encoding=rwy_enc, errors="replace") as rwy_f,
        rwy_end_path.open(
            newline="", encoding=rwy_end_enc, errors="replace"
        ) as rwy_end_f,
        ars_path.open(newline="", encoding=ars_enc, errors="replace") as ars_f,
        rmk_path.open(newline="", encoding=rmk_enc, errors="replace") as rmk_f,
        con_path.open(newline="", encoding=con_enc, errors="replace") as con_f,
        Engine.connect() as connection,
        connection.begin(),
        Session(bind=connection) as session,
    ):
        _parse_apt_base(base_f, session)
        _parse_apt_att(att_f, session)
        _parse_apt_rwy(rwy_f, session)
        _parse_apt_rwy_end(rwy_end_f, session, ils_lookup)
        _parse_apt_ars(ars_f, session)
        _parse_apt_rmk(rmk_f, session)
        _parse_apt_con(con_f, session)
        frq_csv.parse(frq_path, session)


def _parse_apt_base(f: TextIO, session: SASession) -> None:
    """Parse APT_BASE.csv rows and merge Airport ORM objects into session."""
    reader = csv.DictReader(f)

    # Fail-fast column presence check
    actual_cols = set(reader.fieldnames or [])
    missing = _REQUIRED_APT_BASE_COLS - actual_cols
    if missing:
        msg = (
            f"APT_BASE.csv is missing required columns: {sorted(missing)}.  "
            "Verify the CSV file is from the correct NASR data cycle."
        )
        raise RuntimeError(msg)

    # Log unmapped columns at module-load time (once, not per row)
    _log_unmapped_apt_base_cols(actual_cols)

    for row in reader:
        try:
            _process_apt_base_row(row, session)
        except (ValueError, KeyError) as exc:
            arpt_id = row.get("ARPT_ID", "<unknown>")
            msg = f"Coercion failure in APT_BASE row for airport {arpt_id!r}: {exc}"
            raise RuntimeError(msg) from exc


def _process_apt_base_row(row: dict[str, str], session: SASession) -> None:
    """Map a single APT_BASE.csv row to an Airport ORM instance and merge it."""
    # Reconstruct primary key
    site_no = csv_field(row, "SITE_NO")
    site_type_code = csv_field(row, "SITE_TYPE_CODE")
    if not site_no or not site_type_code:
        msg = f"Missing SITE_NO or SITE_TYPE_CODE in row: {row}"
        raise ValueError(msg)
    facility_site_number = f"{site_no}*{site_type_code}"

    # Coordinate reconstruction
    lat_deg = csv_field(row, "LAT_DEG", "int")
    lat_min = csv_field(row, "LAT_MIN", "int")
    lat_sec = csv_field(row, "LAT_SEC", "float")
    lat_hemis = csv_field(row, "LAT_HEMIS")
    lon_deg = csv_field(row, "LONG_DEG", "int")
    lon_min = csv_field(row, "LONG_MIN", "int")
    lon_sec = csv_field(row, "LONG_SEC", "float")
    lon_hemis = csv_field(row, "LONG_HEMIS")

    lat_dms = build_dms_string(lat_deg, lat_min, lat_sec, lat_hemis, is_longitude=False)
    lat_secs = build_total_secs_string(lat_deg, lat_min, lat_sec, lat_hemis)
    lon_dms = build_dms_string(lon_deg, lon_min, lon_sec, lon_hemis, is_longitude=True)
    lon_secs = build_total_secs_string(lon_deg, lon_min, lon_sec, lon_hemis)

    airport = Airport(
        # LANDING FACILITY DATA
        facility_site_number=facility_site_number,
        facility_type=_SITE_TYPE_MAP.get(site_type_code, site_type_code),
        faa_id=csv_field(row, "ARPT_ID"),
        effective_date=csv_field(row, "EFF_DATE", "date"),
        # DEMOGRAPHIC DATA
        region=csv_field(row, "REGION_CODE"),
        field_office=csv_field(row, "ADO_CODE"),
        state_code=csv_field(row, "STATE_CODE"),
        state_name=csv_field(row, "STATE_NAME"),
        county=csv_field(row, "COUNTY_NAME"),
        countys_state=csv_field(row, "COUNTY_ASSOC_STATE"),
        city=csv_field(row, "CITY"),
        name=csv_field(row, "ARPT_NAME"),
        # OWNERSHIP DATA
        ownership_type=csv_field(row, "OWNERSHIP_TYPE_CODE"),
        facility_use=csv_field(row, "FACILITY_USE_CODE"),
        # owners_name / owners_address / owners_city_state_zip / owners_phone — APT_CON.csv
        # managers_name / managers_address / managers_city_state_zip / managers_phone — APT_CON.csv
        # GEOGRAPHIC DATA
        latitude_dms=lat_dms,
        latitude_secs=lat_secs,
        longitude_dms=lon_dms,
        longitude_secs=lon_secs,
        coords_method=csv_field(row, "SURVEY_METHOD_CODE"),
        elevation=csv_field(row, "ELEV", "float"),
        elevation_method=csv_field(row, "ELEV_METHOD_CODE"),
        mag_variation=reconstruct_mag_variation(
            csv_field(row, "MAG_VARN"),
            csv_field(row, "MAG_HEMIS"),
        ),
        mag_variation_year=csv_field(row, "MAG_VARN_YEAR", "int"),
        pattern_alt=csv_field(row, "TPA", "int"),
        sectional=csv_field(row, "CHART_NAME"),
        distance_from_city=csv_field(row, "DIST_CITY_TO_AIRPORT", "int"),
        direction_from_city=csv_field(row, "DIRECTION_CODE"),
        land_area=csv_field(row, "ACREAGE", "int"),
        # FAA SERVICES
        # boundary_artcc_id — N/A in APT_BASE.csv
        # boundary_artcc_computer_id — N/A in APT_BASE.csv
        # boundary_artcc_name — N/A in APT_BASE.csv
        responsible_artcc_id=csv_field(row, "RESP_ARTCC_ID"),
        responsible_artcc_computer_id=csv_field(row, "COMPUTER_ID"),
        responsible_artcc_name=csv_field(row, "ARTCC_NAME"),
        tie_in_fss_local=csv_field(row, "FSS_ON_ARPT_FLAG", "bool"),
        tie_in_fss_id=csv_field(row, "FSS_ID"),
        tie_in_fss_name=csv_field(row, "FSS_NAME"),
        fss_local_phone=csv_field(row, "PHONE_NO"),
        fss_toll_free_phone=csv_field(row, "TOLL_FREE_NO"),
        alternate_fss_id=csv_field(row, "ALT_FSS_ID"),
        alternate_fss_name=csv_field(row, "ALT_FSS_NAME"),
        alternate_fss_toll_free_phone=csv_field(row, "ALT_TOLL_FREE_NO"),
        notam_facility=csv_field(row, "NOTAM_ID"),
        notam_d_available=csv_field(row, "NOTAM_FLAG", "bool"),
        # FEDERAL STATUS
        activation_date=csv_field(row, "ACTIVATION_DATE", "date"),
        status=csv_field(row, "ARPT_STATUS"),
        arff_certification=reconstruct_arff(
            csv_field(row, "FAR_139_TYPE_CODE"),
            csv_field(row, "FAR_139_CARRIER_SER_CODE"),
            csv_field(row, "ARFF_CERT_TYPE_DATE"),
        ),
        npias_federal_agreements=csv_field(row, "NASP_CODE"),
        airspace_analysis=_map_airspace_analysis(csv_field(row, "ASP_ANLYS_DTRM_CODE")),
        airport_of_entry=csv_field(row, "CUST_FLAG", "bool"),
        customs_landing_rights=csv_field(row, "LNDG_RIGHTS_FLAG", "bool"),
        military_civil_join_use=csv_field(row, "JOINT_USE_FLAG", "bool"),
        military_landing_rights=csv_field(row, "MIL_LNDG_FLAG", "bool"),
        # AIRPORT INSPECTION DATA
        inspection_method=csv_field(
            row, "INSPECT_METHOD_CODE", "AirportInspectionMethodEnum"
        ),
        agency_performing_inspection=csv_field(row, "INSPECTOR_CODE"),
        last_inspection_date=csv_field(row, "LAST_INSPECTION", "date"),
        last_information_request_complete_date=csv_field(
            row, "LAST_INFO_RESPONSE", "date"
        ),
        # AIRPORT SERVICES
        fuel_available=reconstruct_fuel(csv_field(row, "FUEL_TYPES")),
        airframe_repair_service=csv_field(row, "AIRFRAME_REPAIR_SER_CODE"),
        power_plant_repair_service=csv_field(row, "PWR_PLANT_REPAIR_SER"),
        bottled_oxygen=csv_field(row, "BOTTLED_OXY_TYPE"),
        bulk_oxygen=csv_field(row, "BULK_OXY_TYPE"),
        # AIRPORT FACILITIES
        lighting_schedule=csv_field(row, "LGT_SKED"),
        beacon_schedule=csv_field(row, "BCN_LGT_SKED"),
        towered_airport=_parse_towered(csv_field(row, "TWR_TYPE_CODE")),
        # unicom — FRQ.csv, not APT_BASE.csv
        # ctaf — FRQ.csv, not APT_BASE.csv
        segmented_circle_available=csv_field(
            row, "SEG_CIRCLE_MKR_FLAG", "SegmentedCircleEnum"
        ),
        beacon_color=csv_field(row, "BCN_LENS_COLOR"),
        noncommerical_landing_fee=csv_field(row, "LNDG_FEE_FLAG", "bool"),
        landing_facility_used_for_medical_purposes=csv_field(
            row, "MEDICAL_USE_FLAG", "bool"
        ),
        # BASED AIRCRAFT — columns absent from actual 2026-02-19 APT_BASE.csv
        # ANNUAL OPERATIONS — columns absent from actual 2026-02-19 APT_BASE.csv
        # ADDITIONAL AIRPORT DATA
        position_source=csv_field(row, "ARPT_PSN_SOURCE"),
        position_date=csv_field(row, "POSITION_SRC_DATE", "date"),
        elevation_source=csv_field(row, "ARPT_ELEV_SOURCE"),
        elevation_date=csv_field(row, "ELEVATION_SRC_DATE", "date"),
        contract_fuel_available=csv_field(row, "CONTR_FUEL_AVBL", "bool"),
        transient_storage_facilities=reconstruct_transient_storage(
            csv_field(row, "TRNS_STRG_BUOY_FLAG"),
            csv_field(row, "TRNS_STRG_HGR_FLAG"),
            csv_field(row, "TRNS_STRG_TIE_FLAG"),
        ),
        other_services_available=csv_field(row, "OTHER_SERVICES"),
        wind_indicator=csv_field(row, "WIND_INDCR_FLAG", "SegmentedCircleEnum"),
        icao_id=csv_field(row, "ICAO_ID"),
        minimum_operational_network=csv_field(row, "MIN_OP_NETWORK"),
    )
    session.merge(airport)


def _parse_towered(twr_code: str | None) -> bool | None:
    """
    Derive towered_airport bool from TWR_TYPE_CODE.

    Any code beginning with 'ATCT' (e.g. 'ATCT', 'ATCT-TRACON', 'ATCT-RAPCON',
    'ATCT-A/C') -> True (Airport Traffic Control Tower present).
    'NON-ATCT' or any other non-empty value -> False.
    Empty/None -> None.
    """
    if not twr_code:
        return None
    return twr_code.strip().upper().startswith("ATCT")


def _map_airspace_analysis(value: str | None) -> str | None:
    """
    Normalize CSV ASP_ANLYS_DTRM_CODE to TXT airspace_analysis string.

    CSV uses 'CONDL' where TXT stores 'CONDITIONAL'.  All other values are
    identical.  Returns None when value is None/empty.
    """
    if not value:
        return None
    return _AIRSPACE_ANALYSIS_MAP.get(value, value)


def _parse_apt_att(f: TextIO, session: SASession) -> None:
    """Parse APT_ATT.csv rows and merge AttendanceSchedule ORM objects."""
    reader = csv.DictReader(f)

    actual_cols = set(reader.fieldnames or [])
    missing = _REQUIRED_APT_ATT_COLS - actual_cols
    if missing:
        msg = (
            f"APT_ATT.csv is missing required columns: {sorted(missing)}.  "
            "Verify the CSV file is from the correct NASR data cycle."
        )
        raise RuntimeError(msg)

    for row in reader:
        try:
            site_no = csv_field(row, "SITE_NO")
            site_type = csv_field(row, "SITE_TYPE_CODE")
            if not site_no or not site_type:
                continue  # Skip rows without a valid site reference
            seq = csv_field(row, "SKED_SEQ_NO", "int")
            month = csv_field(row, "MONTH") or ""
            day = csv_field(row, "DAY") or ""
            hour = csv_field(row, "HOUR") or ""
            sched = reconstruct_attendance_schedule(month, day, hour)
            att = AttendanceSchedule(
                facility_site_number=f"{site_no}*{site_type}",
                sequence_number=seq,
                attendance_schedule=sched,
            )
            session.merge(att)
        except (ValueError, KeyError) as exc:
            arpt_id = row.get("ARPT_ID", "<unknown>")
            msg = f"Coercion failure in APT_ATT row for airport {arpt_id!r}: {exc}"
            raise RuntimeError(msg) from exc


# ---------------------------------------------------------------------------
# Column introspection helpers
# ---------------------------------------------------------------------------

# Columns in APT_BASE.csv that the parser explicitly maps to Airport fields.
_MAPPED_APT_BASE_COLS = frozenset(
    {
        "EFF_DATE",
        "SITE_NO",
        "SITE_TYPE_CODE",
        "STATE_CODE",
        "ARPT_ID",
        "CITY",
        "REGION_CODE",
        "ADO_CODE",
        "STATE_NAME",
        "COUNTY_NAME",
        "COUNTY_ASSOC_STATE",
        "ARPT_NAME",
        "OWNERSHIP_TYPE_CODE",
        "FACILITY_USE_CODE",
        "LAT_DEG",
        "LAT_MIN",
        "LAT_SEC",
        "LAT_HEMIS",
        "LAT_DECIMAL",  # Not used directly; covered by build_dms_string inputs
        "LONG_DEG",
        "LONG_MIN",
        "LONG_SEC",
        "LONG_HEMIS",
        "LONG_DECIMAL",  # Not used directly; covered by build_dms_string inputs
        "SURVEY_METHOD_CODE",
        "ELEV",
        "ELEV_METHOD_CODE",
        "MAG_VARN",
        "MAG_HEMIS",
        "MAG_VARN_YEAR",
        "TPA",
        "CHART_NAME",
        "DIST_CITY_TO_AIRPORT",
        "DIRECTION_CODE",
        "ACREAGE",
        "RESP_ARTCC_ID",
        "COMPUTER_ID",
        "ARTCC_NAME",
        "FSS_ON_ARPT_FLAG",
        "FSS_ID",
        "FSS_NAME",
        "PHONE_NO",
        "TOLL_FREE_NO",
        "ALT_FSS_ID",
        "ALT_FSS_NAME",
        "ALT_TOLL_FREE_NO",
        "NOTAM_ID",
        "NOTAM_FLAG",
        "ACTIVATION_DATE",
        "ARPT_STATUS",
        "FAR_139_TYPE_CODE",
        "FAR_139_CARRIER_SER_CODE",
        "ARFF_CERT_TYPE_DATE",
        "ASP_ANLYS_DTRM_CODE",
        "CUST_FLAG",
        "LNDG_RIGHTS_FLAG",
        "JOINT_USE_FLAG",
        "MIL_LNDG_FLAG",
        "INSPECT_METHOD_CODE",
        "INSPECTOR_CODE",
        "LAST_INSPECTION",
        "LAST_INFO_RESPONSE",
        "FUEL_TYPES",
        "AIRFRAME_REPAIR_SER_CODE",
        "PWR_PLANT_REPAIR_SER",
        "BOTTLED_OXY_TYPE",
        "BULK_OXY_TYPE",
        "LGT_SKED",
        "BCN_LGT_SKED",
        "TWR_TYPE_CODE",
        "SEG_CIRCLE_MKR_FLAG",
        "BCN_LENS_COLOR",
        "LNDG_FEE_FLAG",
        "MEDICAL_USE_FLAG",
        "ARPT_PSN_SOURCE",
        "POSITION_SRC_DATE",
        "ARPT_ELEV_SOURCE",
        "ELEVATION_SRC_DATE",
        "CONTR_FUEL_AVBL",
        "TRNS_STRG_BUOY_FLAG",
        "TRNS_STRG_HGR_FLAG",
        "TRNS_STRG_TIE_FLAG",
        "OTHER_SERVICES",
        "WIND_INDCR_FLAG",
        "ICAO_ID",
        "MIN_OP_NETWORK",
        # Explicitly known but intentionally not mapped to an ORM field:
        "COUNTRY_CODE",  # Not in Airport model (US-only dataset)
        "USER_FEE_FLAG",  # Not in Airport model
        "CTA",  # Not in Airport model
        "NASP_CODE",  # Mapped to npias_federal_agreements (was incorrectly labeled ASP_CODE)
    }
)


def _log_unmapped_apt_base_cols(actual_cols: set[str]) -> None:
    """Log any CSV columns not covered by the parser's field mapping."""
    unmapped = actual_cols - _MAPPED_APT_BASE_COLS
    if unmapped:
        logger.info(
            "APT_BASE.csv contains %d column(s) not mapped to Airport ORM fields: %s",
            len(unmapped),
            sorted(unmapped),
        )


# ---------------------------------------------------------------------------
# Helper functions for Runway / RunwayEnd field reconstruction
# ---------------------------------------------------------------------------


def _reconstruct_surface_type_condition(
    surface: str | None, cond: str | None
) -> str | None:
    """
    Reconstruct 'ASPH-CONC-E' from SURFACE_TYPE_CODE='ASPH-CONC' + COND='EXCELLENT'.

    Condition is abbreviated to its first character and appended with a dash.
    Returns None when surface is empty.
    """
    surface = (surface or "").strip()
    if not surface:
        return None
    cond = (cond or "").strip()
    if cond:
        return f"{surface}-{cond[0]}"
    return surface


def _reconstruct_pcn(
    pcn: str | None,
    pav: str | None,
    sub: str | None,
    tire: str | None,
    det: str | None,
) -> str | None:
    """
    Reconstruct '71 /F/A/W/T' from PCN sub-fields.

    The TXT format right-justifies the PCN number in a 3-character slot
    followed by ``/TYPE/SUB/TIRE/DET``.  Single-digit values like ``6``
    become ``6  /…``, two-digit values like ``21`` become ``21 /…``, and
    three-digit values like ``120`` become ``120/…``.

    Returns None when PCN is empty.
    """
    pcn = (pcn or "").strip()
    if not pcn:
        return None
    pav = (pav or "").strip()
    sub = (sub or "").strip()
    tire = (tire or "").strip()
    det = (det or "").strip()
    return f"{pcn:<3}/{pav}/{sub}/{tire}/{det}"


def _format_weight(raw: str | None) -> str | None:
    """
    Format weight-bearing capacity as float string: '60' -> '60.0'.

    TXT stores weights as float strings (e.g., '60.0', '250.0').
    CSV stores them as integer-like strings (e.g., '60', '250').
    """
    if not raw or not raw.strip():
        return None
    return str(float(raw.strip()))


def _reconstruct_centerline_offset(
    offset: str | None, direction: str | None
) -> str | None:
    """
    Reconstruct controlling object centerline offset as f'{offset}{direction}'.

    The TXT parser reads a single 7-character field that may contain just a
    direction code (e.g., 'B') with no numeric offset (SJU runway 10/28).
    Returns None only when both offset and direction are empty.
    """
    offset = (offset or "").strip()
    direction = (direction or "").strip()
    if not offset and not direction:
        return None
    return f"{offset}{direction}"


def _lahso_dms_to_secs(dms: str | None) -> str | None:
    """
    Parse a pre-formatted DMS string like '41-59-17.9165N' to total-seconds string.

    LAHSO_LAT and LAHSO_LONG in APT_RWY_END.csv are pre-formatted DMS strings
    (not split DEG/MIN/SEC/HEMIS columns).  This helper parses them to compute
    the total-seconds representation.
    """
    if not dms or not dms.strip():
        return None
    dms = dms.strip()
    hemis = dms[-1]
    parts = dms[:-1].split("-")
    deg = int(parts[0])
    min_ = int(parts[1])
    sec = float(parts[2])
    total = deg * 3600 + min_ * 60 + sec
    return f"{total:011.4f}{hemis}"


# Mapping from CSV full-word condition to single-letter ORM enum code
_MARKINGS_CONDITION_MAP: dict[str, str] = {
    "GOOD": "G",
    "FAIR": "F",
    "POOR": "P",
}

# ---------------------------------------------------------------------------
# Required columns for Runway and RunwayEnd parsers
# ---------------------------------------------------------------------------

_REQUIRED_APT_RWY_COLS = {
    "SITE_NO",
    "SITE_TYPE_CODE",
    "RWY_ID",
    "RWY_LEN",
    "RWY_WIDTH",
}

_REQUIRED_APT_RWY_END_COLS = {
    "SITE_NO",
    "SITE_TYPE_CODE",
    "RWY_ID",
    "RWY_END_ID",
}

_REQUIRED_APT_ARS_COLS = {
    "SITE_NO",
    "SITE_TYPE_CODE",
    "RWY_ID",
    "RWY_END_ID",
    "ARREST_DEVICE_CODE",
}

_REQUIRED_APT_CON_COLS = frozenset(
    {
        "SITE_NO",
        "SITE_TYPE_CODE",
        "TITLE",
        "NAME",
        "ADDRESS1",
        "ADDRESS2",
        "TITLE_CITY",
        "STATE",
        "ZIP_CODE",
        "ZIP_PLUS_FOUR",
        "PHONE_NO",
    }
)


# ---------------------------------------------------------------------------
# Runway parser
# ---------------------------------------------------------------------------


def _parse_apt_rwy(f: TextIO, session: SASession) -> None:
    """Parse APT_RWY.csv rows and merge Runway ORM objects into session."""
    reader = csv.DictReader(f)

    actual_cols = set(reader.fieldnames or [])
    missing = _REQUIRED_APT_RWY_COLS - actual_cols
    if missing:
        msg = (
            f"APT_RWY.csv is missing required columns: {sorted(missing)}.  "
            "Verify the CSV file is from the correct NASR data cycle."
        )
        raise RuntimeError(msg)

    for row in reader:
        try:
            site_no = csv_field(row, "SITE_NO")
            site_type = csv_field(row, "SITE_TYPE_CODE")
            if not site_no or not site_type:
                continue
            fsn = f"{site_no}*{site_type}"

            # Orphan check — Runway requires an existing Airport FK
            airport = session.query(Airport).filter_by(facility_site_number=fsn).first()
            if airport is None:
                logger.warning(
                    "APT_RWY.csv: no Airport with facility_site_number=%r — "
                    "skipping runway %r",
                    fsn,
                    csv_field(row, "RWY_ID"),
                )
                continue

            rwy_id = csv_field(row, "RWY_ID")

            runway = Runway(
                facility_site_number=fsn,
                name=rwy_id,
                length=csv_field(row, "RWY_LEN", "int"),
                width=csv_field(row, "RWY_WIDTH", "int"),
                surface_type_condition=_reconstruct_surface_type_condition(
                    csv_field(row, "SURFACE_TYPE_CODE"),
                    csv_field(row, "COND"),
                ),
                surface_treatment=csv_field(row, "TREATMENT_CODE"),
                pavement_classification_number=_reconstruct_pcn(
                    csv_field(row, "PCN"),
                    csv_field(row, "PAVEMENT_TYPE_CODE"),
                    csv_field(row, "SUBGRADE_STRENGTH_CODE"),
                    csv_field(row, "TIRE_PRES_CODE"),
                    csv_field(row, "DTRM_METHOD_CODE"),
                ),
                edge_light_intensity=csv_field(row, "RWY_LGT_CODE"),
                length_source=csv_field(row, "RWY_LEN_SOURCE"),
                length_source_date=csv_field(row, "LENGTH_SOURCE_DATE", "date"),
                weight_bearing_capacity_single_wheel=_format_weight(
                    csv_field(row, "GROSS_WT_SW")
                ),
                weight_bearing_capacity_dual_wheels=_format_weight(
                    csv_field(row, "GROSS_WT_DW")
                ),
                weight_bearing_capacity_two_dual_wheels_tandem=_format_weight(
                    csv_field(row, "GROSS_WT_DTW")
                ),
                weight_bearing_capacity_two_dual_wheels_double_tandem=_format_weight(
                    csv_field(row, "GROSS_WT_DDTW")
                ),
            )
            session.merge(runway)
        except (ValueError, KeyError) as exc:
            rwy_id = row.get("RWY_ID", "<unknown>")
            msg = f"Coercion failure in APT_RWY row for runway {rwy_id!r}: {exc}"
            raise RuntimeError(msg) from exc


# ---------------------------------------------------------------------------
# RunwayEnd parser
# ---------------------------------------------------------------------------


def _parse_apt_rwy_end(
    f: TextIO, session: SASession, ils_lookup: dict[tuple[str, str], str]
) -> None:
    """Parse APT_RWY_END.csv rows and merge RunwayEnd ORM objects into session."""
    reader = csv.DictReader(f)

    actual_cols = set(reader.fieldnames or [])
    missing = _REQUIRED_APT_RWY_END_COLS - actual_cols
    if missing:
        msg = (
            f"APT_RWY_END.csv is missing required columns: {sorted(missing)}.  "
            "Verify the CSV file is from the correct NASR data cycle."
        )
        raise RuntimeError(msg)

    for row in reader:
        try:
            site_no = csv_field(row, "SITE_NO")
            site_type = csv_field(row, "SITE_TYPE_CODE")
            if not site_no or not site_type:
                continue
            fsn = f"{site_no}*{site_type}"

            # Orphan check — RunwayEnd requires an existing Airport FK
            airport = session.query(Airport).filter_by(facility_site_number=fsn).first()
            if airport is None:
                logger.warning(
                    "APT_RWY_END.csv: no Airport with facility_site_number=%r — "
                    "skipping runway end %r/%r",
                    fsn,
                    csv_field(row, "RWY_ID"),
                    csv_field(row, "RWY_END_ID"),
                )
                continue

            rwy_id = csv_field(row, "RWY_ID")
            end_id = csv_field(row, "RWY_END_ID")

            # Coordinate reconstruction — runway end lat/lon
            lat_deg = csv_field(row, "RWY_END_LAT_DEG", "int")
            lat_min = csv_field(row, "RWY_END_LAT_MIN", "int")
            lat_sec = csv_field(row, "RWY_END_LAT_SEC", "float")
            lat_hemis = csv_field(row, "RWY_END_LAT_HEMIS")
            lon_deg = csv_field(row, "RWY_END_LONG_DEG", "int")
            lon_min = csv_field(row, "RWY_END_LONG_MIN", "int")
            lon_sec = csv_field(row, "RWY_END_LONG_SEC", "float")
            lon_hemis = csv_field(row, "RWY_END_LONG_HEMIS")

            if lat_deg is not None and lat_hemis:
                latitude_dms = build_dms_string(
                    lat_deg, lat_min, lat_sec, lat_hemis, is_longitude=False
                )
                latitude_secs = build_total_secs_string(
                    lat_deg, lat_min, lat_sec, lat_hemis
                )
            else:
                latitude_dms = None
                latitude_secs = None

            if lon_deg is not None and lon_hemis:
                longitude_dms = build_dms_string(
                    lon_deg, lon_min, lon_sec, lon_hemis, is_longitude=True
                )
                longitude_secs = build_total_secs_string(
                    lon_deg, lon_min, lon_sec, lon_hemis
                )
            else:
                longitude_dms = None
                longitude_secs = None

            # Displaced threshold coordinates (many runway ends have no displaced threshold)
            dspl_lat_deg = csv_field(row, "DISPLACED_THR_LAT_DEG", "int")
            dspl_lat_min = csv_field(row, "DISPLACED_THR_LAT_MIN", "int")
            dspl_lat_sec = csv_field(row, "DISPLACED_THR_LAT_SEC", "float")
            dspl_lat_hemis = csv_field(row, "DISPLACED_THR_LAT_HEMIS")
            dspl_lon_deg = csv_field(row, "DISPLACED_THR_LONG_DEG", "int")
            dspl_lon_min = csv_field(row, "DISPLACED_THR_LONG_MIN", "int")
            dspl_lon_sec = csv_field(row, "DISPLACED_THR_LONG_SEC", "float")
            dspl_lon_hemis = csv_field(row, "DISPLACED_THR_LONG_HEMIS")

            if dspl_lat_deg is not None and dspl_lat_hemis:
                displaced_threshold_latitude_dms = build_dms_string(
                    dspl_lat_deg,
                    dspl_lat_min,
                    dspl_lat_sec,
                    dspl_lat_hemis,
                    is_longitude=False,
                )
                displaced_threshold_latitude_secs = build_total_secs_string(
                    dspl_lat_deg, dspl_lat_min, dspl_lat_sec, dspl_lat_hemis
                )
            else:
                displaced_threshold_latitude_dms = None
                displaced_threshold_latitude_secs = None

            if dspl_lon_deg is not None and dspl_lon_hemis:
                displaced_threshold_longitude_dms = build_dms_string(
                    dspl_lon_deg,
                    dspl_lon_min,
                    dspl_lon_sec,
                    dspl_lon_hemis,
                    is_longitude=True,
                )
                displaced_threshold_longitude_secs = build_total_secs_string(
                    dspl_lon_deg, dspl_lon_min, dspl_lon_sec, dspl_lon_hemis
                )
            else:
                displaced_threshold_longitude_dms = None
                displaced_threshold_longitude_secs = None

            # Markings condition — map full word to single-letter code
            raw_cond = csv_field(row, "RWY_MARKING_COND")
            markings_condition_code = (
                _MARKINGS_CONDITION_MAP.get(raw_cond, raw_cond) if raw_cond else None
            )

            # LAHSO coordinates — pre-formatted DMS strings in CSV
            lahso_lat_dms = csv_field(row, "LAHSO_LAT")
            lahso_lon_dms = csv_field(row, "LAHSO_LONG")

            # ILS_TYPE from APT_RWY_END.csv wins; ILS_BASE.csv fills gaps
            approach_type = csv_field(row, "ILS_TYPE")
            if approach_type is None and site_no and end_id:
                approach_type = ils_lookup.get((site_no, end_id))

            rwy_end = RunwayEnd(
                facility_site_number=fsn,
                runway_name=rwy_id,
                id=end_id,
                true_alignment=csv_field(row, "TRUE_ALIGNMENT", "int"),
                approach_type=approach_type,
                right_traffic=csv_field(row, "RIGHT_HAND_TRAFFIC_PAT_FLAG", "bool"),
                markings_type=csv_field(row, "RWY_MARKING_TYPE_CODE"),
                markings_condition=markings_condition_code,
                latitude_dms=latitude_dms,
                latitude_secs=latitude_secs,
                longitude_dms=longitude_dms,
                longitude_secs=longitude_secs,
                elevation=csv_field(row, "RWY_END_ELEV", "float"),
                threshold_crossing_height=csv_field(row, "THR_CROSSING_HGT", "int"),
                visual_glide_path_angle=csv_field(
                    row, "VISUAL_GLIDE_PATH_ANGLE", "float"
                ),
                displaced_threshold_latitude_dms=displaced_threshold_latitude_dms,
                displaced_threshold_latitude_secs=displaced_threshold_latitude_secs,
                displaced_threshold_longitude_dms=displaced_threshold_longitude_dms,
                displaced_threshold_longitude_secs=displaced_threshold_longitude_secs,
                displaced_threshold_elevation=csv_field(
                    row, "DISPLACED_THR_ELEV", "float"
                ),
                displaced_threshold_length=csv_field(row, "DISPLACED_THR_LEN", "int"),
                touchdown_zone_elevation=csv_field(row, "TDZ_ELEV", "float"),
                visual_glide_slope_indicators=csv_field(row, "VGSI_CODE"),
                rvr_equipment=csv_field(row, "RWY_VISUAL_RANGE_EQUIP_CODE"),
                rvv_equipment=csv_field(row, "RWY_VSBY_VALUE_EQUIP_FLAG", "bool"),
                approach_light_system=csv_field(row, "APCH_LGT_SYSTEM_CODE"),
                reil_availability=csv_field(row, "RWY_END_LGTS_FLAG", "bool"),
                centerline_light_availability=csv_field(
                    row, "CNTRLN_LGTS_AVBL_FLAG", "bool"
                ),
                touchdown_lights_availability=csv_field(
                    row, "TDZ_LGT_AVBL_FLAG", "bool"
                ),
                controlling_object_description=csv_field(row, "OBSTN_TYPE"),
                controlling_object_marking=csv_field(row, "OBSTN_MRKD_CODE"),
                part77_category=csv_field(row, "FAR_PART_77_CODE"),
                controlling_object_clearance_slope=csv_field(
                    row, "OBSTN_CLNC_SLOPE", "int"
                ),
                controlling_object_height_above_runway=csv_field(
                    row, "OBSTN_HGT", "int"
                ),
                controlling_object_distance_from_runway=csv_field(
                    row, "DIST_FROM_THR", "int"
                ),
                controlling_object_centerline_offset=_reconstruct_centerline_offset(
                    csv_field(row, "CNTRLN_OFFSET"),
                    csv_field(row, "CNTRLN_DIR_CODE"),
                ),
                gradient=csv_field(row, "RWY_GRAD"),
                gradient_direction=csv_field(row, "RWY_GRAD_DIRECTION"),
                position_source=csv_field(row, "RWY_END_PSN_SOURCE"),
                position_date=csv_field(row, "RWY_END_PSN_DATE", "date"),
                elevation_source=csv_field(row, "RWY_END_ELEV_SOURCE"),
                elevation_date=csv_field(row, "RWY_END_ELEV_DATE", "date"),
                displaced_threshold_position_source=csv_field(
                    row, "DSPL_THR_PSN_SOURCE"
                ),
                displaced_threshold_position_date=csv_field(
                    row, "RWY_END_DSPL_THR_PSN_DATE", "date"
                ),
                displaced_threshold_elevation_source=csv_field(
                    row, "DSPL_THR_ELEV_SOURCE"
                ),
                displaced_threshold_elevation_date=csv_field(
                    row, "RWY_END_DSPL_THR_ELEV_DATE", "date"
                ),
                touchdown_zone_elevation_source=csv_field(row, "TDZ_ELEV_SOURCE"),
                touchdown_zone_elevation_date=csv_field(
                    row, "RWY_END_TDZ_ELEV_DATE", "date"
                ),
                takeoff_run_available=csv_field(row, "TKOF_RUN_AVBL", "int"),
                takeoff_distance_available=csv_field(row, "TKOF_DIST_AVBL", "int"),
                accelerate_stop_distance_available=csv_field(
                    row, "ACLT_STOP_DIST_AVBL", "int"
                ),
                landing_distance_available=csv_field(row, "LNDG_DIST_AVBL", "int"),
                lahso_distance_available=csv_field(row, "LAHSO_ALD", "int"),
                id_of_lahso_intersecting_runway=csv_field(
                    row, "RWY_END_INTERSECT_LAHSO"
                ),
                description_of_lahso_entity=csv_field(row, "LAHSO_DESC"),
                lahso_latitude_dms=lahso_lat_dms,
                lahso_latitude_secs=_lahso_dms_to_secs(lahso_lat_dms),
                lahso_longitude_dms=lahso_lon_dms,
                lahso_longitude_secs=_lahso_dms_to_secs(lahso_lon_dms),
                lahso_coords_source=csv_field(row, "LAHSO_PSN_SOURCE"),
                lahso_coords_date=csv_field(row, "RWY_END_LAHSO_PSN_DATE", "date"),
            )
            session.merge(rwy_end)
        except (ValueError, KeyError) as exc:
            end_id = row.get("RWY_END_ID", "<unknown>")
            rwy_id = row.get("RWY_ID", "<unknown>")
            msg = (
                f"Coercion failure in APT_RWY_END row for runway end "
                f"{rwy_id!r}/{end_id!r}: {exc}"
            )
            raise RuntimeError(msg) from exc


# ---------------------------------------------------------------------------
# Arresting gear parser
# ---------------------------------------------------------------------------


def _parse_apt_ars(f: TextIO, session: SASession) -> None:
    """
    Parse APT_ARS.csv rows and set RunwayEnd.arresting_gear.

    For each arresting gear record, looks up the RunwayEnd by
    facility_site_number + runway_name + id and sets arresting_gear.
    Orphaned records (RunwayEnd not found) are logged and skipped.
    """
    reader = csv.DictReader(f)

    actual_cols = set(reader.fieldnames or [])
    missing = _REQUIRED_APT_ARS_COLS - actual_cols
    if missing:
        msg = (
            f"APT_ARS.csv is missing required columns: {sorted(missing)}.  "
            "Verify the CSV file is from the correct NASR data cycle."
        )
        raise RuntimeError(msg)

    for row in reader:
        try:
            site_no = csv_field(row, "SITE_NO")
            site_type = csv_field(row, "SITE_TYPE_CODE")
            if not site_no or not site_type:
                continue
            fsn = f"{site_no}*{site_type}"

            rwy_id = csv_field(row, "RWY_ID")
            end_id = csv_field(row, "RWY_END_ID")
            device_code = csv_field(row, "ARREST_DEVICE_CODE")

            runway_end = (
                session.query(RunwayEnd)
                .filter_by(facility_site_number=fsn, runway_name=rwy_id, id=end_id)
                .first()
            )
            if runway_end is None:
                logger.warning(
                    "APT_ARS.csv: no RunwayEnd for %r runway=%r end=%r — "
                    "skipping arresting gear %r",
                    fsn,
                    rwy_id,
                    end_id,
                    device_code,
                )
                continue

            runway_end.arresting_gear = device_code
            session.merge(runway_end)
        except (ValueError, KeyError) as exc:
            end_id = row.get("RWY_END_ID", "<unknown>")
            rwy_id = row.get("RWY_ID", "<unknown>")
            msg = (
                f"Coercion failure in APT_ARS row for runway end "
                f"{rwy_id!r}/{end_id!r}: {exc}"
            )
            raise RuntimeError(msg) from exc


# ---------------------------------------------------------------------------
# Remark dispatch dictionaries
# ---------------------------------------------------------------------------

# TAB_NAME=AIRPORT: REF_COL_NAME -> Airport ORM attribute name
# Complete mapping derived from TXT parser legacy-code dispatch and CSV
# REF_COL_NAME-to-LEGACY_ELEMENT_NUMBER correspondence in APT_RMK.csv.
_AIRPORT_REMARK_DISPATCH: dict[str, str] = {
    "COUNTY_CODE": "county_remark",
    "COUNTY_ASSOC_STATE": "county_remark",
    "CITY": "city_remark",
    "ARPT_NAME": "name_remark",
    "OWNERSHIP_TYPE_CODE": "ownership_type_remark",
    "FACILITY_USE_CODE": "facility_use_remark",
    "LAT_DEG": "latitude_dms_remark",
    "LONG_DEG": "longitude_dms_remark",
    "SURVEY_METHOD_CODE": "coords_method_remark",
    "ELEV": "elevation_remark",
    "ELEV_METHOD_CODE": "elevation_remark",
    "TPA": "pattern_alt_remark",
    "CHART_NAME": "sectional_remark",
    "DIST": "distance_from_city_remark",
    "ACREAGE": "land_area_remark",
    "PRIMARY_FSS_SEQ_NO": "tie_in_fss_remark",
    "FSS_ON_ARPT_FLAG": "tie_in_fss_remark",
    "FAR_139_TYPE_CODE": "arff_certification_remark",
    "FAR_139_CARRIER_SER_CODE": "arff_certification_remark",
    "NASP_CODE": "npias_federal_agreements_remark",
    "ASP_ANLYS_DTRM_CODE": "airspace_analysis_remark",
    "CUST_FLAG": "airport_of_entry_remark",
    "LNDG_RIGHTS_FLAG": "customs_landing_rights_remark",
    "JOINT_USE_FLAG": "military_civil_join_use_remark",
    "MIL_LNDG_FLAG": "military_landing_rights_remark",
    "INSPECTOR_CODE": "agency_performing_inspection_remark",
    "INFO_REQ_DATE": "last_inspection_date_remark",
    "AIRFRAME_REPAIR_SER_CODE": "airframe_repair_service_remark",
    "PWR_PLANT_REPAIR_SER": "power_plant_repair_service_remark",
    "BOTTLED_OXY_TYPE": "bottled_oxygen_remark",
    "BULK_OXY_TYPE": "bulk_oxygen_remark",
    "LGT_SKED": "lighting_schedule_remark",
    "BCN_LGT_SKED": "beacon_schedule_remark",
    "UNICOM_FREQ": "unicom_remark",
    "CTAF_FREQ": "ctaf_remark",
    "SEG_CIRCLE_MKR_FLAG": "segmented_circle_available_remark",
    "BCN_LENS_COLOR": "beacon_color_remark",
    "LNDG_FEE_FLAG": "noncommerical_landing_fee_remark",
    "SINGLE_ENG_CNT": "based_general_aviation_single_engine_airplanes_remark",
    "MULTI_ENG_CNT": "based_general_aviation_multi_engine_airplanes_remark",
    "HEL_CNT": "based_general_aviation_helicopters_remark",
    "OPR_GLIDERS_CNT": "based_gliders_remark",
    "OPR_MIL_ACFT_CNT": "based_military_aircraft_remark",
    "ULTRALGT_ACFT_CNT": "based_ultralight_aircraft_remark",
    "COMMERCIAL_OPS_CNT": "annual_ops_commercial_remark",
    "ITNRNT_OPS_CNT": "annual_ops_general_aviation_itinerant_remark",
    "LOCAL_OPS_CNT": "annual_ops_general_aviation_local_remark",
    "MIL_ACFT_OPS_CNT": "annual_ops_military_remark",
    "TRNS_STRG_HGR_FLAG": "transient_storage_facilities_remark",
    "TRNS_STRG_TIE_FLAG": "transient_storage_facilities_remark",
    "TRNS_STRG_BUOY_FLAG": "transient_storage_facilities_remark",
    "WIND_INDCR_FLAG": "wind_indicator_remark",
}

# TAB_NAME=AIRPORT_CONTACT: LEGACY_ELEMENT_NUMBER -> Airport ORM attribute name
# Dispatch is by LEGACY because REF_COL_NAME only tells us NAME or PHONE_NO,
# not which contact (owner vs manager) or which field.
_AIRPORT_CONTACT_DISPATCH: dict[str, str] = {
    "A11": "owners_name_remark",
    "A12": "owners_address_remark",
    "A12A": "owners_city_state_zip_remark",
    "A13": "owners_phone_remark",
    "A14": "managers_name_remark",
    "A15": "managers_address_remark",
    "A15A": "managers_city_state_zip_remark",
    "A16": "managers_phone_remark",
}

# TAB_NAME=RUNWAY or RUNWAY_SURFACE_TYPE: REF_COL_NAME -> Runway ORM attribute name
# Complete mapping derived from TXT parser legacy-code dispatch.
_RUNWAY_REMARK_DISPATCH: dict[str, str] = {
    "RWY_ID": "name_remark",
    "RWY_LEN": "length_remark",
    "RWY_WIDTH": "width_remark",
    "SURFACE_TYPE_CODE": "surface_type_condition_remark",
    "COND": "surface_type_condition_remark",
    "TREATMENT_CODE": "surface_treatment_remark",
    "PCN": "pavement_classification_number_remark",
    "PAVEMENT_TYPE_CODE": "pavement_classification_number_remark",
    "DTRM_METHOD_CODE": "pavement_classification_number_remark",
    "RWY_LGT_CODE": "edge_light_intensity_remark",
    "GROSS_WT_SW": "weight_bearing_capacity_single_wheel_remark",
    "GROSS_WT_DW": "weight_bearing_capacity_dual_wheels_remark",
    "GROSS_WT_DTW": "weight_bearing_capacity_two_dual_wheels_tandem_remark",
    "GROSS_WT_DDTW": "weight_bearing_capacity_two_dual_wheels_double_tandem_remark",
}

# TAB_NAME=RUNWAY_END or RUNWAY_END_OBSTN: REF_COL_NAME -> RunwayEnd ORM attribute name
# CLOSE_IN_OBSTN and LNDG_DIST_AVBL are handled separately (AirportRemark rows).
# Complete mapping derived from TXT parser legacy-code dispatch.
_RUNWAY_END_REMARK_DISPATCH: dict[str, str] = {
    "RWY_END_ID": "id_remark",
    "TRUE_ALIGNMENT": "true_alignment_remark",
    "RIGHT_HAND_TRAFFIC_PAT_FLAG": "right_traffic_remark",
    "RWY_MARKING_TYPE_CODE": "markings_remark",
    "RWY_MARKING_COND": "markings_remark",
    "RWY_END_LAT_DEG": "latitude_dms_remark",
    "RWY_END_ELEV": "elevation_remark",
    "VISUAL_GLIDE_PATH_ANGLE": "visual_glide_path_angle_remark",
    "DISPLACED_THR_LAT_DEG": "displaced_threshold_latitude_dms_remark",
    "DISPLACED_THR_LEN": "displaced_threshold_length_remark",
    "VGSI_CODE": "visual_glide_slope_indicators_remark",
    "RWY_VISUAL_RANGE_EQUIP_CODE": "rvr_equipment_remark",
    "RWY_VSBY_RANGE_EQUIP_FLAG": "rvr_equipment_remark",
    "APCH_LGT_SYSTEM_CODE": "approach_light_system_remark",
    "RWY_END_LGTS_FLAG": "reil_availability_remark",
    "CNTRLN_LGTS_AVBL_FLAG": "centerline_light_availability_remark",
    "TDZ_LGT_AVBL_FLAG": "touchdown_lights_availability_remark",
    "OBSTN_TYPE": "controlling_object_description_remark",
    "OBSTN_MRKD_CODE": "controlling_object_marking_remark",
    "FAR_PART_77_CODE": "part77_category_remark",
    "OBSTN_CLNC_SLOPE": "controlling_object_clearance_slope_remark",
    "OBSTN_HGT": "controlling_object_height_above_runway_remark",
    "DIST_FROM_THR": "controlling_object_distance_from_runway_remark",
    "CNTRLN_OFFSET": "controlling_object_centerline_offset_remark",
    "CNTRLN_DIR_CODE": "controlling_object_centerline_offset_remark",
    "RWY_GRAD": "gradient_remark",
    "TKOF_RUN_AVBL": "takeoff_run_available_remark",
}


# ---------------------------------------------------------------------------
# Remark parser
# ---------------------------------------------------------------------------


def _parse_apt_rmk(f: TextIO, session: SASession) -> None:
    """
    Parse APT_RMK.csv and dispatch remarks to correct ORM attributes.

    Dispatches based on TAB_NAME using dictionary lookups (not if/elif chains
    on REF_COL_NAME).  Airport/Runway/RunwayEnd attribute remarks are stored
    directly on the ORM instances.  Narrative remarks (GENERAL_REMARK,
    ARPT_PSN_SOURCE, CLOSE_IN_OBSTN, ARRESTING_DEVICE, FUEL_TYPE,
    AIRPORT_ATTEND_SCHED) are stored in the AirportRemark table using
    LEGACY_ELEMENT_NUMBER as the element name.

    Must be called LAST in parse() so all Airport/Runway/RunwayEnd records
    already exist in the session.
    """
    reader = csv.DictReader(f)
    for row in reader:
        site_no = csv_field(row, "SITE_NO")
        site_type = csv_field(row, "SITE_TYPE_CODE")
        if not site_no or not site_type:
            continue
        fsn = f"{site_no}*{site_type}"
        tab = csv_field(row, "TAB_NAME") or ""
        ref_col = csv_field(row, "REF_COL_NAME") or ""
        element = csv_field(row, "ELEMENT") or ""
        legacy = csv_field(row, "LEGACY_ELEMENT_NUMBER") or ""
        remark = csv_field(row, "REMARK")

        if tab == "AIRPORT":
            _dispatch_airport_remark(session, fsn, ref_col, legacy, remark)
        elif tab == "AIRPORT_CONTACT":
            _dispatch_airport_contact_remark(session, fsn, legacy, remark)
        elif tab in ("RUNWAY", "RUNWAY_SURFACE_TYPE"):
            _dispatch_runway_remark(session, fsn, ref_col, element, legacy, remark)
        elif tab in ("RUNWAY_END", "RUNWAY_END_OBSTN"):
            _dispatch_runway_end_remark(session, fsn, ref_col, element, legacy, remark)
        elif tab == "ARRESTING_DEVICE":
            _dispatch_arresting_device_remark(session, fsn, legacy, remark)
        elif tab == "FUEL_TYPE":
            _dispatch_fuel_type_remark(session, fsn, element, remark)
        elif tab == "AIRPORT_ATTEND_SCHED":
            _dispatch_attend_sched_remark(session, fsn, remark)
        elif tab == "AIRPORT_SERVICE":
            # AIRPORT_SERVICE remarks are not present in the TXT format —
            # skip silently (no AirportRemark row to create).
            pass
        else:
            logger.warning("APT_RMK.csv: unknown TAB_NAME=%r for site %r", tab, fsn)


# ---------------------------------------------------------------------------
# Contact parser
# ---------------------------------------------------------------------------


def _parse_apt_con(f: TextIO, session: SASession) -> None:
    r"""
    Parse APT_CON.csv rows and populate owner/manager contact fields.

    Only TITLE values of 'OWNER' and 'MANAGER' are processed; all other
    contact types (e.g., 'ENGINEER', 'SECURITY') are skipped (deferred).

    Address reconstruction matches TXT format:
      city_state_zip = "CITY, ST ZIP" or "CITY, ST ZIP-PLUS4"
        (e.g., "AURORA, IL 60507" or "ROCKFORD, IL 61109-2902")
      address = ADDRESS1 when ADDRESS2 is empty; "ADDRESS1, ADDRESS2" otherwise
        (TXT uses ", " as the separator between address lines)
    """
    reader = csv.DictReader(f)

    actual_cols = set(reader.fieldnames or [])
    missing = _REQUIRED_APT_CON_COLS - actual_cols
    if missing:
        msg = (
            f"APT_CON.csv is missing required columns: {sorted(missing)}.  "
            "Verify the CSV file is from the correct NASR data cycle."
        )
        raise RuntimeError(msg)

    for row in reader:
        try:
            title = csv_field(row, "TITLE")
            if title not in ("OWNER", "MANAGER"):
                continue  # Only OWNER and MANAGER processed; others deferred

            site_no = csv_field(row, "SITE_NO")
            site_type = csv_field(row, "SITE_TYPE_CODE")
            if not site_no or not site_type:
                continue
            fsn = f"{site_no}*{site_type}"

            airport = session.query(Airport).filter_by(facility_site_number=fsn).first()
            if airport is None:
                continue

            name = csv_field(row, "NAME")
            address1 = csv_field(row, "ADDRESS1") or ""
            address2 = csv_field(row, "ADDRESS2") or ""
            city = csv_field(row, "TITLE_CITY") or ""
            state = csv_field(row, "STATE") or ""
            zip_code = csv_field(row, "ZIP_CODE") or ""
            zip_plus_four = csv_field(row, "ZIP_PLUS_FOUR") or ""
            phone = csv_field(row, "PHONE_NO")

            # Reconstruct address to match TXT format.
            # TXT uses ", " as the separator between ADDRESS1 and ADDRESS2.
            address = f"{address1}, {address2}" if address2 else address1 or None
            # Build ZIP string: include ZIP+4 suffix when present (e.g., "61109-2902")
            full_zip = f"{zip_code}-{zip_plus_four}" if zip_plus_four else zip_code
            city_state_zip = f"{city}, {state} {full_zip}".strip() if city else None

            if title == "OWNER":
                airport.owners_name = name
                airport.owners_address = address
                airport.owners_city_state_zip = city_state_zip
                airport.owners_phone = phone
            else:  # MANAGER
                airport.managers_name = name
                airport.managers_address = address
                airport.managers_city_state_zip = city_state_zip
                airport.managers_phone = phone

            session.merge(airport)
        except (ValueError, KeyError) as exc:
            site_ref = row.get("ARPT_ID", row.get("SITE_NO", "<unknown>"))
            msg = f"Coercion failure in APT_CON row for airport {site_ref!r}: {exc}"
            raise RuntimeError(msg) from exc


def _dispatch_airport_remark(
    session: SASession,
    fsn: str,
    ref_col: str,
    legacy: str,
    remark: str | None,
) -> None:
    """Dispatch a TAB_NAME=AIRPORT remark to the correct Airport attribute."""
    if ref_col in _AIRPORT_REMARK_DISPATCH:
        airport = session.query(Airport).filter_by(facility_site_number=fsn).first()
        if not airport:
            logger.warning(
                "APT_RMK.csv: no Airport with facility_site_number=%r for "
                "AIRPORT remark ref_col=%r — skipping",
                fsn,
                ref_col,
            )
            return
        setattr(airport, _AIRPORT_REMARK_DISPATCH[ref_col], remark)
        session.merge(airport)
    else:
        # Narrative / unmapped remarks — store in AirportRemark table keyed by
        # LEGACY_ELEMENT_NUMBER, matching the TXT parser's fallback behaviour.
        # Covers GENERAL_REMARK, ARPT_PSN_SOURCE, USER_FEE_FLAG,
        # MEDICAL_USE_FLAG, ARPT_ELEV_SOURCE, and any future additions.
        rmk_obj = AirportRemark(
            facility_site_number=fsn,
            remark_element_name=legacy,
            remark=remark,
        )
        session.merge(rmk_obj)


def _dispatch_airport_contact_remark(
    session: SASession,
    fsn: str,
    legacy: str,
    remark: str | None,
) -> None:
    """Dispatch a TAB_NAME=AIRPORT_CONTACT remark to an Airport _remark field."""
    if legacy in _AIRPORT_CONTACT_DISPATCH:
        airport = session.query(Airport).filter_by(facility_site_number=fsn).first()
        if not airport:
            logger.warning(
                "APT_RMK.csv: no Airport with facility_site_number=%r for "
                "AIRPORT_CONTACT remark legacy=%r — skipping",
                fsn,
                legacy,
            )
            return
        setattr(airport, _AIRPORT_CONTACT_DISPATCH[legacy], remark)
        session.merge(airport)
    else:
        # Non-standard contact remarks (e.g., A110-MANAGER, A110-OWNER,
        # A110-ASST_MGR-PHONE_NO) — contact types beyond OWNER/MANAGER.
        # These have no TXT equivalent and their LEGACY_ELEMENT_NUMBER
        # values often exceed the varchar(13) remark_element_name column
        # limit (up to 24 chars).  Skip silently; the TXT parser never
        # stored these either.
        pass


def _dispatch_runway_remark(
    session: SASession,
    fsn: str,
    ref_col: str,
    element: str,
    legacy: str,
    remark: str | None,
) -> None:
    """
    Dispatch a TAB_NAME=RUNWAY/RUNWAY_SURFACE_TYPE remark to a Runway attribute.

    ``element`` contains the runway name (e.g., '06/24').
    """
    if ref_col in _RUNWAY_REMARK_DISPATCH:
        runway = (
            session.query(Runway)
            .filter_by(facility_site_number=fsn, name=element)
            .first()
        )
        if not runway:
            logger.warning(
                "APT_RMK.csv: no Runway for site=%r name=%r (RUNWAY remark "
                "ref_col=%r) — skipping",
                fsn,
                element,
                ref_col,
            )
            return
        setattr(runway, _RUNWAY_REMARK_DISPATCH[ref_col], remark)
        session.merge(runway)
    else:
        # Narrative / unmapped runway remarks — store in AirportRemark table
        # keyed by LEGACY_ELEMENT_NUMBER (e.g., RWY_LEN_DATE -> A110-*).
        rmk_obj = AirportRemark(
            facility_site_number=fsn,
            remark_element_name=legacy,
            remark=remark,
        )
        session.merge(rmk_obj)


def _dispatch_runway_end_remark(
    session: SASession,
    fsn: str,
    ref_col: str,
    element: str,
    legacy: str,
    remark: str | None,
) -> None:
    """
    Dispatch a TAB_NAME=RUNWAY_END/RUNWAY_END_OBSTN remark.

    ``element`` contains the runway end ID (e.g., '06', '24').
    CLOSE_IN_OBSTN is a narrative remark stored in AirportRemark, not an
    attribute update.
    """
    if ref_col in ("CLOSE_IN_OBSTN", "LNDG_DIST_AVBL"):
        # Narrative remark — stored in AirportRemark table
        rmk_obj = AirportRemark(
            facility_site_number=fsn,
            remark_element_name=legacy,
            remark=remark,
        )
        session.merge(rmk_obj)
    elif ref_col in _RUNWAY_END_REMARK_DISPATCH:
        rwy_end = (
            session.query(RunwayEnd)
            .filter_by(facility_site_number=fsn, id=element)
            .first()
        )
        if not rwy_end:
            logger.warning(
                "APT_RMK.csv: no RunwayEnd for site=%r id=%r (RUNWAY_END remark "
                "ref_col=%r) — skipping",
                fsn,
                element,
                ref_col,
            )
            return
        setattr(rwy_end, _RUNWAY_END_REMARK_DISPATCH[ref_col], remark)
        session.merge(rwy_end)
    else:
        # Narrative / unmapped runway-end remarks — store in AirportRemark
        # table keyed by LEGACY_ELEMENT_NUMBER (e.g., OVERRUN_LEN, LAHSO_ALD,
        # DISPLACED_THR_APCH_RATIO, TDZ_ELEV_SOURCE -> A110-RWY_* codes).
        rmk_obj = AirportRemark(
            facility_site_number=fsn,
            remark_element_name=legacy,
            remark=remark,
        )
        session.merge(rmk_obj)


def _dispatch_arresting_device_remark(
    session: SASession,
    fsn: str,
    legacy: str,
    remark: str | None,
) -> None:
    """
    Dispatch a TAB_NAME=ARRESTING_DEVICE remark to AirportRemark.

    The remark_element_name is extracted by splitting LEGACY at the first
    underscore (e.g., 'E60-04R_BAK-12B' -> 'E60-04R').  This matches the
    element name format used by the TXT parser.
    """
    idx = legacy.find("_")
    element_name = legacy if idx == -1 else legacy[:idx]
    rmk_obj = AirportRemark(
        facility_site_number=fsn,
        remark_element_name=element_name,
        remark=remark,
    )
    session.merge(rmk_obj)


def _dispatch_fuel_type_remark(
    session: SASession,
    fsn: str,
    element: str,
    remark: str | None,
) -> None:
    """
    Dispatch a TAB_NAME=FUEL_TYPE remark to AirportRemark.

    The TXT parser reads remarks from a fixed-width format where the element
    name field is exactly 13 characters (positions 17-29) and the remark text
    starts at position 30.  When the full element name 'A70-FUEL-{element}'
    exceeds 13 characters, the overflow characters spill into the remark text
    field.  To match TXT snapshot remark text exactly, any overflow characters
    must be prepended to the remark.

    Example: element='100LL' -> 'A70-FUEL-100LL' (14 chars) -> element_name
    truncated to 'A70-FUEL-100L' (13 chars), overflow 'L' prepended to remark.
    """
    full_name = f"A70-FUEL-{element}"
    element_name = full_name[:13]
    # If full_name exceeds 13 chars, the TXT fixed-width format places the
    # overflow characters at the start of the remark field (position 30),
    # followed by a space and then the actual remark text.  Reproduce this
    # to match the TXT snapshot exactly.
    overflow = full_name[13:]
    if overflow and remark is not None:
        remark_text = overflow + " " + remark
    elif overflow:
        remark_text = overflow
    else:
        remark_text = remark
    rmk_obj = AirportRemark(
        facility_site_number=fsn,
        remark_element_name=element_name,
        remark=remark_text,
    )
    session.merge(rmk_obj)


def _dispatch_attend_sched_remark(
    session: SASession,
    fsn: str,
    remark: str | None,
) -> None:
    """
    Dispatch a TAB_NAME=AIRPORT_ATTEND_SCHED remark to AirportRemark.

    The TXT parser stores attendance schedule remarks as a single A17
    element.  If an airport has multiple AIRPORT_ATTEND_SCHED CSV rows,
    the last one wins (via session.merge on the composite PK).
    """
    rmk_obj = AirportRemark(
        facility_site_number=fsn,
        remark_element_name="A17",
        remark=remark,
    )
    session.merge(rmk_obj)
