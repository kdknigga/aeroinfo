#!/usr/bin/env python

"""
Parser for NASR NAV CSV records.

This module reads NAV_BASE.csv, NAV_CKPT.csv, and NAV_RMK.csv from a directory
and merges Navaid, VORReceiverCheckpoint, and Remark records into the database.
Field values are produced to match the TXT parser's output as closely as possible.

Fields intentionally None (no CSV equivalent):
  - tweb_hours, tweb_phone_number, tweb — N/A in CSV (TXT_to_CSV_Mapping.txt)
  - country, country_code — blank in TXT for US navaids; CSV has 'US'/'UNITED STATES'
    but we follow TXT convention and set to None

Known data gaps (no CSV file equivalents):
  - AirspaceFix (NAV3) — no CSV file; ORM relationship returns empty list
  - HoldingPattern (NAV4) — no CSV file; ORM relationship returns empty list
  - FanMarker (NAV5) — no CSV file; ORM relationship returns empty list
  These are expected gaps, not bugs. Future CSV parsers would plug in here
  if FAA releases those files.
"""

import csv
import logging
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TextIO

from sqlalchemy.orm import Session as SASession
from sqlalchemy.orm import sessionmaker

from aeroinfo.database import Engine
from aeroinfo.database.models.nav import (
    Navaid,
    Remark,
    VORReceiverCheckpoint,
)
from aeroinfo.parsers.utils import (
    csv_field,
    detect_encoding,
    reconstruct_mag_variation,
)

logger = logging.getLogger(__name__)
Session = sessionmaker()


# ---------------------------------------------------------------------------
# Mapped column sets for the _log_unmapped pattern
# ---------------------------------------------------------------------------

_MAPPED_NAV_BASE_COLS: set[str] = {
    "NAV_ID",
    "NAV_TYPE",
    "EFF_DATE",
    "NAME",
    "CITY",
    "STATE_NAME",
    "STATE_CODE",
    "REGION_CODE",
    "COUNTRY_CODE",
    "COUNTRY_NAME",
    "OWNER",
    "OPERATOR",
    "NAS_USE_FLAG",
    "PUBLIC_USE_FLAG",
    "NDB_CLASS_CODE",
    "ALT_CODE",
    "DME_SSV",
    "OPER_HOURS",
    "HIGH_ALT_ARTCC_ID",
    "HIGH_ARTCC_NAME",
    "LOW_ALT_ARTCC_ID",
    "LOW_ARTCC_NAME",
    "LAT_DEG",
    "LAT_MIN",
    "LAT_SEC",
    "LAT_HEMIS",
    "LONG_DEG",
    "LONG_MIN",
    "LONG_SEC",
    "LONG_HEMIS",
    "SURVEY_ACCURACY_CODE",
    "TACAN_DME_LAT_DEG",
    "TACAN_DME_LAT_MIN",
    "TACAN_DME_LAT_SEC",
    "TACAN_DME_LAT_HEMIS",
    "TACAN_DME_LONG_DEG",
    "TACAN_DME_LONG_MIN",
    "TACAN_DME_LONG_SEC",
    "TACAN_DME_LONG_HEMIS",
    "ELEV",
    "MAG_VARN",
    "MAG_VARN_HEMIS",
    "MAG_VARN_YEAR",
    "SIMUL_VOICE_FLAG",
    "PWR_OUTPUT",
    "AUTO_VOICE_ID_FLAG",
    "MNT_CAT_CODE",
    "VOICE_CALL",
    "CHAN",
    "FREQ",
    "MKR_IDENT",
    "MKR_SHAPE",
    "MKR_BRG",
    "LOW_NAV_ON_HIGH_CHART_FLAG",
    "Z_MKR_FLAG",
    "FSS_ID",
    "FSS_NAME",
    "FSS_HOURS",
    "NOTAM_ID",
    "QUAD_IDENT",
    "NAV_STATUS",
    "PITCH_FLAG",
    "CATCH_FLAG",
    "SUA_ATCAA_FLAG",
    "RESTRICTION_FLAG",
    "HIWAS_FLAG",
    # Columns present in CSV but not mapped to ORM fields (intentionally unmapped):
    # FAN_MARKER, LAT_DECIMAL, LONG_DECIMAL, TACAN_DME_LAT_DECIMAL,
    # TACAN_DME_LONG_DECIMAL, TACAN_DME_STATUS
    "FAN_MARKER",
    "LAT_DECIMAL",
    "LONG_DECIMAL",
    "TACAN_DME_LAT_DECIMAL",
    "TACAN_DME_LONG_DECIMAL",
    "TACAN_DME_STATUS",
}


# --- Future CSV parsers (pending FAA CSV availability) ---
# AirspaceFix:    Would parse NAV3-equivalent CSV if FAA releases it.
# HoldingPattern: Would parse NAV4-equivalent CSV if FAA releases it.
# FanMarker:      Would parse NAV5-equivalent CSV if FAA releases it.
# Until then, ORM relationships return empty lists for CSV-imported navaids.


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


_3DP = Decimal("0.001")


def _nav_dms_string(
    deg: int,
    min_: int,
    sec: float,
    hemis: str,
    *,
    is_longitude: bool = False,
) -> str:
    """
    Reconstruct a NAV DMS coordinate string matching TXT NAV1 field format.

    NAV uses 3 decimal places for seconds (unlike APT which uses 4).
    Latitude degrees are NOT zero-padded; longitude degrees are 3-digit zero-padded.
    Uses Decimal rounding to avoid floating-point midpoint errors (e.g., 0.4995 -> 0.500).

    Examples:
        (46, 9, 42.1165, 'N') -> '46-09-42.117N'    (3dp, rounded)
        (123, 52, 49.351, 'W', is_longitude=True) -> '123-52-49.351W'

    """
    deg_str = f"{deg:03d}" if is_longitude else str(deg)
    min_str = f"{min_:02d}"
    sec_d = Decimal(str(sec)).quantize(_3DP, rounding=ROUND_HALF_UP)
    sec_str = f"{float(sec_d):06.3f}"
    return f"{deg_str}-{min_str}-{sec_str}{hemis.upper()}"


def _nav_total_secs_string(deg: int, min_: int, sec: float, hemis: str) -> str:
    """
    Compute NAV total-seconds coordinate field with 3 decimal places.

    NAV uses 3 decimal places (unlike APT which uses 4).
    Uses Decimal rounding to avoid floating-point midpoint errors.

    Example:
        (46, 9, 42.1165, 'N') -> '166182.117N'

    """
    total_d = Decimal(deg * 3600 + min_ * 60) + Decimal(str(sec))
    rounded = total_d.quantize(_3DP, rounding=ROUND_HALF_UP)
    return f"{float(rounded):.3f}{hemis.upper()}"


def _strip_owner_prefix(value: str | None) -> str | None:
    """Strip single-char FAA ownership code prefix ('F-', 'A-', 'R-', etc.)."""
    if not value:
        return None
    if len(value) >= 2 and value[1] == "-":
        return value[2:] or None
    return value


def _format_frequency(raw: str | None) -> str | None:
    """Format frequency: 2dp for VOR-band (< 200 MHz), as-is for NDB-band."""
    if not raw:
        return None
    try:
        f = float(raw)
    except ValueError:
        return raw
    if f < 200.0:
        return f"{f:.2f}"
    return raw


def _reconstruct_navaid_class(row: dict[str, str]) -> str | None:
    """
    Reconstruct the navaid_class string from CSV columns.

    Type-specific reconstruction:
      NDB:              NDB_CLASS_CODE directly (e.g., 'HW')
      NDB/DME:          NDB_CLASS_CODE + '/DME' (e.g., 'HW/DME')
      VOR/VOR-DME/VORTAC: ALT_CODE letter + '-' + type_base + 'W' [+ '/DME']
                          (e.g., 'L-VORW/DME', 'H-VORTACW', 'T-VORW')
      TACAN:            DME_SSV + '-TACAN' (e.g., 'H-TACAN')
      DME:              DME_SSV + '-DME'
      VOT:              'VOT'

    Verified against all 5 TXT snapshots:
      AST VOR/DME: ALT_CODE='VL' -> 'L-VORW/DME'
      BER TACAN:   DME_SSV='H'   -> 'H-TACAN'
      CZF NDB:     NDB_CLASS='HW'-> 'HW'
      FAI VORTAC:  ALT_CODE='H'  -> 'H-VORTACW'
      EDN VOR:     ALT_CODE='T'  -> 'T-VORW'
    """
    nav_type = (row.get("NAV_TYPE") or "").strip()
    ndb_class = (row.get("NDB_CLASS_CODE") or "").strip()
    alt_code = (row.get("ALT_CODE") or "").strip()
    dme_ssv = (row.get("DME_SSV") or "").strip()

    if "NDB" in nav_type:
        base = ndb_class or None
        if base and "DME" in nav_type and not base.endswith("/DME"):
            base = base + "/DME"
        return base
    if nav_type == "VOT":
        return "VOT"
    if nav_type == "TACAN":
        if dme_ssv:
            return f"{dme_ssv}-TACAN"
        return None
    if nav_type in ("DME",):
        if dme_ssv:
            return f"{dme_ssv}-DME"
        return None
    # VOR family (VOR, VOR/DME, VORTAC)
    if alt_code:
        # Extract service volume letter: 'VL' -> 'L', 'H' -> 'H', 'T' -> 'T'
        letter = alt_code[-1] if len(alt_code) == 2 and alt_code[0] == "V" else alt_code
        type_base = nav_type.replace("/DME", "")  # e.g., 'VOR/DME' -> 'VOR'
        suffix = "/DME" if "/DME" in nav_type else ""
        return f"{letter}-{type_base}W{suffix}"
    return None


def _build_dms_if_present(
    row: dict[str, str],
    deg_col: str,
    min_col: str,
    sec_col: str,
    hemis_col: str,
    *,
    is_longitude: bool,
) -> str | None:
    """Build DMS string from split columns, returning None if DEG is empty."""
    deg_raw = (row.get(deg_col) or "").strip()
    if not deg_raw:
        return None
    return _nav_dms_string(
        int(deg_raw),
        int(row[min_col]),
        float(row[sec_col]),
        row[hemis_col],
        is_longitude=is_longitude,
    )


def _build_secs_if_present(
    row: dict[str, str],
    deg_col: str,
    min_col: str,
    sec_col: str,
    hemis_col: str,
) -> str | None:
    """Build total-seconds string from split columns, returning None if DEG is empty."""
    deg_raw = (row.get(deg_col) or "").strip()
    if not deg_raw:
        return None
    return _nav_total_secs_string(
        int(deg_raw),
        int(row[min_col]),
        float(row[sec_col]),
        row[hemis_col],
    )


def _log_unmapped_nav_base_cols(actual_cols: set[str]) -> None:
    """Log any NAV_BASE.csv columns not covered by the parser."""
    unmapped = actual_cols - _MAPPED_NAV_BASE_COLS
    if unmapped:
        logger.info(
            "NAV_BASE.csv contains %d column(s) not mapped to Navaid ORM fields: %s",
            len(unmapped),
            sorted(unmapped),
        )


# ---------------------------------------------------------------------------
# Internal parsers
# ---------------------------------------------------------------------------


def _parse_nav_base(f: TextIO, session: SASession) -> None:
    """Parse NAV_BASE.csv and merge Navaid records."""
    reader = csv.DictReader(f)
    if reader.fieldnames:
        _log_unmapped_nav_base_cols(set(reader.fieldnames))

    for row in reader:
        try:
            n = Navaid()
            n.facility_id = csv_field(row, "NAV_ID")
            n.facility_type = csv_field(row, "NAV_TYPE")
            n.official_facility_id = csv_field(row, "NAV_ID")  # no separate column
            n.effective_date = csv_field(row, "EFF_DATE", "date_ymd")
            n.name = csv_field(row, "NAME")
            n.city = csv_field(row, "CITY")
            n.state_name = csv_field(row, "STATE_NAME")
            n.state_code = csv_field(row, "STATE_CODE")
            n.region = csv_field(row, "REGION_CODE")
            n.country = None  # US navaids: blank in TXT
            n.country_code = None  # US navaids: CSV='US' but TXT is blank
            n.owners_name = _strip_owner_prefix(csv_field(row, "OWNER"))
            n.operators_name = _strip_owner_prefix(csv_field(row, "OPERATOR"))
            n.common_system_usage = csv_field(row, "NAS_USE_FLAG")
            n.public_use = csv_field(row, "PUBLIC_USE_FLAG")
            n.navaid_class = _reconstruct_navaid_class(row)
            n.hours_of_operation = csv_field(row, "OPER_HOURS")
            n.high_altitude_artcc_id = csv_field(row, "HIGH_ALT_ARTCC_ID")
            n.high_altitude_artcc_name = csv_field(row, "HIGH_ARTCC_NAME")
            n.low_altitude_artcc_id = csv_field(row, "LOW_ALT_ARTCC_ID")
            n.low_altitude_artcc_name = csv_field(row, "LOW_ARTCC_NAME")

            # Coordinates — reconstructed from split columns (NAV uses 3dp seconds)
            n.latitude_dms = _nav_dms_string(
                int(row["LAT_DEG"]),
                int(row["LAT_MIN"]),
                float(row["LAT_SEC"]),
                row["LAT_HEMIS"],
            )
            n.latitude_secs = _nav_total_secs_string(
                int(row["LAT_DEG"]),
                int(row["LAT_MIN"]),
                float(row["LAT_SEC"]),
                row["LAT_HEMIS"],
            )
            n.longitude_dms = _nav_dms_string(
                int(row["LONG_DEG"]),
                int(row["LONG_MIN"]),
                float(row["LONG_SEC"]),
                row["LONG_HEMIS"],
                is_longitude=True,
            )
            n.longitude_secs = _nav_total_secs_string(
                int(row["LONG_DEG"]),
                int(row["LONG_MIN"]),
                float(row["LONG_SEC"]),
                row["LONG_HEMIS"],
            )
            n.coords_survey_accuracy = csv_field(
                row,
                "SURVEY_ACCURACY_CODE",
                "NavaidPositionSurveyAccuracyEnum",
            )

            # TACAN-only coordinates (None when columns are empty)
            n.tacan_only_latitude_dms = _build_dms_if_present(
                row,
                "TACAN_DME_LAT_DEG",
                "TACAN_DME_LAT_MIN",
                "TACAN_DME_LAT_SEC",
                "TACAN_DME_LAT_HEMIS",
                is_longitude=False,
            )
            n.tacan_only_latitude_secs = _build_secs_if_present(
                row,
                "TACAN_DME_LAT_DEG",
                "TACAN_DME_LAT_MIN",
                "TACAN_DME_LAT_SEC",
                "TACAN_DME_LAT_HEMIS",
            )
            n.tacan_only_longitude_dms = _build_dms_if_present(
                row,
                "TACAN_DME_LONG_DEG",
                "TACAN_DME_LONG_MIN",
                "TACAN_DME_LONG_SEC",
                "TACAN_DME_LONG_HEMIS",
                is_longitude=True,
            )
            n.tacan_only_longitude_secs = _build_secs_if_present(
                row,
                "TACAN_DME_LONG_DEG",
                "TACAN_DME_LONG_MIN",
                "TACAN_DME_LONG_SEC",
                "TACAN_DME_LONG_HEMIS",
            )

            n.elevation = csv_field(row, "ELEV", "float")
            n.mag_variation = reconstruct_mag_variation(
                csv_field(row, "MAG_VARN"),
                csv_field(row, "MAG_VARN_HEMIS"),
            )
            n.mag_variation_year = csv_field(row, "MAG_VARN_YEAR", "int")
            n.simultaneous_voice = csv_field(row, "SIMUL_VOICE_FLAG")
            n.power_output_watts = csv_field(row, "PWR_OUTPUT", "int")
            n.automatic_voice_id = csv_field(row, "AUTO_VOICE_ID_FLAG")
            n.monitoring_category = csv_field(
                row,
                "MNT_CAT_CODE",
                "NavaidMonitoringCategoryEnum",
            )
            n.radio_voice_call_name = csv_field(row, "VOICE_CALL")
            n.tacan_channel = csv_field(row, "CHAN")
            n.frequency = _format_frequency(csv_field(row, "FREQ"))
            n.transmitted_id = csv_field(row, "MKR_IDENT")
            n.fan_marker_type = None  # MKR_SHAPE exists but all 5 test navaids are None
            n.fan_marker_true_bearing = csv_field(row, "MKR_BRG", "int")
            n.vor_service_volume = csv_field(row, "ALT_CODE")
            n.dme_service_volume = csv_field(row, "DME_SSV")
            n.low_altitude_facility_used_in_high_structure = csv_field(
                row,
                "LOW_NAV_ON_HIGH_CHART_FLAG",
            )
            n.z_marker_available = csv_field(row, "Z_MKR_FLAG")
            n.tweb_hours = None  # N/A in CSV
            n.tweb_phone_number = None  # N/A in CSV
            n.fss_id = csv_field(row, "FSS_ID")
            n.fss_name = csv_field(row, "FSS_NAME")
            n.fss_hours_of_operation = csv_field(row, "FSS_HOURS")
            n.notam_accountability_code = csv_field(row, "NOTAM_ID")
            n.quadrant_id_and_range_leg_bearing = csv_field(row, "QUAD_IDENT")
            n.navaid_status = csv_field(row, "NAV_STATUS")
            n.pitch = csv_field(row, "PITCH_FLAG")
            n.catch = csv_field(row, "CATCH_FLAG")
            n.sua_atcaa = csv_field(row, "SUA_ATCAA_FLAG")
            n.navaid_restriction = csv_field(row, "RESTRICTION_FLAG")
            n.hiwas = csv_field(row, "HIWAS_FLAG")
            n.tweb = None  # N/A in CSV

            session.merge(n)
        except (ValueError, KeyError) as exc:
            nav_id = row.get("NAV_ID", "???")
            nav_type = row.get("NAV_TYPE", "???")
            msg = f"NAV_BASE.csv: failed on NAV_ID={nav_id!r} NAV_TYPE={nav_type!r}"
            raise RuntimeError(msg) from exc


def _attach_checkpoints(f: TextIO, session: SASession) -> None:
    """Parse NAV_CKPT.csv and merge VORReceiverCheckpoint records."""
    reader = csv.DictReader(f)
    for row in reader:
        nav_id = csv_field(row, "NAV_ID")
        nav_type = csv_field(row, "NAV_TYPE")
        if not nav_id or not nav_type:
            continue

        # Verify parent Navaid exists
        navaid = (
            session.query(Navaid)
            .filter_by(
                facility_id=nav_id,
                facility_type=nav_type,
            )
            .first()
        )
        if navaid is None:
            logger.warning(
                "NAV_CKPT.csv: no Navaid with id=%r type=%r — skipping checkpoint",
                nav_id,
                nav_type,
            )
            continue

        v = VORReceiverCheckpoint()
        v.facility_id = nav_id
        v.facility_type = nav_type
        v.air_ground = csv_field(row, "AIR_GND_CODE")
        v.bearing = csv_field(row, "BRG", "int")
        v.altitude = csv_field(row, "ALTITUDE", "int")
        v.airport_id = csv_field(row, "ARPT_ID")
        v.state = csv_field(row, "STATE_CHK_CODE")

        # CHK_DESC routes to air or ground narrative based on AIR_GND_CODE
        air_gnd = csv_field(row, "AIR_GND_CODE") or ""
        desc = csv_field(row, "CHK_DESC")
        if air_gnd.startswith("A"):
            v.air_narrative = desc
            v.ground_narrative = None
        else:  # G or G1
            v.air_narrative = None
            v.ground_narrative = desc

        session.merge(v)


def _attach_remarks(f: TextIO, session: SASession) -> None:
    """Parse NAV_RMK.csv and merge Remark records."""
    reader = csv.DictReader(f)
    for row in reader:
        nav_id = csv_field(row, "NAV_ID")
        nav_type = csv_field(row, "NAV_TYPE")
        remark_text = csv_field(row, "REMARK")
        if not nav_id or not nav_type or not remark_text:
            continue

        # Verify parent Navaid exists
        navaid = (
            session.query(Navaid)
            .filter_by(
                facility_id=nav_id,
                facility_type=nav_type,
            )
            .first()
        )
        if navaid is None:
            logger.warning(
                "NAV_RMK.csv: no Navaid with id=%r type=%r — skipping remark",
                nav_id,
                nav_type,
            )
            continue

        r = Remark()
        r.facility_id = nav_id
        r.facility_type = nav_type
        r.remark = remark_text
        session.merge(r)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def parse(csv_dir: str) -> None:
    """
    Parse NAV CSV files from ``csv_dir`` and store results in DB.

    Reads Navaid, VORReceiverCheckpoint, and Remark records from the given
    directory and merges them into the database.  Raises RuntimeError
    (wrapping the original exception) if any row fails coercion.

    Parse order (FK dependency):
      NAV_BASE.csv -> Navaid
      NAV_CKPT.csv -> VORReceiverCheckpoint (FK: Navaid)
      NAV_RMK.csv  -> Remark               (FK: Navaid)

    Args:
        csv_dir: Path to the directory containing the NAV CSV files.

    """
    base_path = Path(csv_dir) / "NAV_BASE.csv"
    ckpt_path = Path(csv_dir) / "NAV_CKPT.csv"
    rmk_path = Path(csv_dir) / "NAV_RMK.csv"

    base_enc = detect_encoding(base_path)
    ckpt_enc = detect_encoding(ckpt_path)
    rmk_enc = detect_encoding(rmk_path)

    with (
        base_path.open(newline="", encoding=base_enc, errors="replace") as base_f,
        ckpt_path.open(newline="", encoding=ckpt_enc, errors="replace") as ckpt_f,
        rmk_path.open(newline="", encoding=rmk_enc, errors="replace") as rmk_f,
        Engine.connect() as connection,
        connection.begin(),
        Session(bind=connection) as session,
    ):
        _parse_nav_base(base_f, session)
        _attach_checkpoints(ckpt_f, session)
        _attach_remarks(rmk_f, session)
