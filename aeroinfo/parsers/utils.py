#!/usr/bin/env python
"""Helpers for parsing fixed-width NASR records and CSV coercion utilities."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any

from charset_normalizer import from_path
from dateutil import parser as dateparser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

_DATE_DEFAULT = datetime.datetime(2000, 1, 1)


def get_field(record: str, start: int, length: int, var_type: str = "str") -> Any:  # noqa: ANN401
    """
    Extract a slice from a fixed-width record and coerce to the requested type.

    Returns None when the extracted field is empty.

    """
    s = start - 1
    e = start + length - 1
    field = record[s:e].strip()
    logger.debug("start: %s, length: %s, field: %s", start, length, field)
    if field == "":
        return None
    if var_type == "int":
        return int(field)
    if var_type == "float":
        return float(field)
    if var_type == "bool":
        return field in ["Y", "y", "T", "t"]
    if var_type == "date":
        return dateparser.parse(field, default=_DATE_DEFAULT)
    if var_type == "mdydate":
        return datetime.datetime.strptime(field, "%m%d%Y").date()
    if var_type == "AirportInspectionMethodEnum":
        # Literals like 1 or 2 can't be members of an enum, so translate them
        if field == "1":
            return "O"
        if field == "2":
            return "T"
        return field
    if var_type == "SegmentedCircleEnum":
        # Y-L is an invalid member of an enum, so translate to YL
        if field == "Y-L":
            return "YL"
        return field
    if var_type in (
        "NavaidPositionSurveyAccuracyEnum",
        "NavaidMonitoringCategoryEnum",
    ):
        mapping = {
            "0": "ZERO",
            "1": "ONE",
            "2": "TWO",
            "3": "THREE",
            "4": "FOUR",
            "5": "FIVE",
            "6": "SIX",
            "7": "SEVEN",
        }
        return mapping.get(field, field)
    return field


# ---------------------------------------------------------------------------
# CSV coercion utilities (UTIL-01, UTIL-02, UTIL-03)
# ---------------------------------------------------------------------------


def csv_field(row: dict[str, str], col: str, var_type: str = "str") -> Any:  # noqa: ANN401
    """
    Extract and coerce a CSV column value.

    Returns None for empty strings or missing columns.
    Raises ValueError on coercion failure (int/float/date types) — per project
    policy, bad data should fail the entire import, not be silently dropped.

    Args:
        row:      A dict row from csv.DictReader.
        col:      Column name to extract.
        var_type: Coercion type: "str" (default), "int", "float", "bool",
                  "date", "date_ymd", "AirportInspectionMethodEnum",
                  "SegmentedCircleEnum", "NavaidPositionSurveyAccuracyEnum",
                  "NavaidMonitoringCategoryEnum".

    Returns:
        Coerced value, or None for empty/missing.

    """
    field = row.get(col, "").strip()
    if field == "":
        return None
    if var_type == "int":
        return int(field)  # raises ValueError on failure (intentional)
    if var_type == "float":
        return float(field)  # raises ValueError on failure (intentional)
    if var_type == "bool":
        if field.upper() in ("Y", "T"):
            return True
        if field.upper() in ("N", "F"):
            return False
        return None  # unknown bool value -> None
    if var_type == "date":
        return dateparser.parse(
            field, default=_DATE_DEFAULT
        ).date()  # raises on failure
    if var_type == "date_ymd":
        return datetime.datetime.strptime(field, "%Y/%m/%d").date()
    if var_type == "AirportInspectionMethodEnum":
        if field == "1":
            return "O"
        if field == "2":
            return "T"
        return field
    if var_type == "SegmentedCircleEnum":
        if field == "Y-L":
            return "YL"
        return field
    if var_type in ("NavaidPositionSurveyAccuracyEnum", "NavaidMonitoringCategoryEnum"):
        mapping = {
            "0": "ZERO",
            "1": "ONE",
            "2": "TWO",
            "3": "THREE",
            "4": "FOUR",
            "5": "FIVE",
            "6": "SIX",
            "7": "SEVEN",
        }
        return mapping.get(field, field)
    return field  # default: stripped string


def build_dms_string(
    deg: int,
    min_: int,
    sec: float,
    hemis: str,
    *,
    is_longitude: bool = False,
) -> str:
    """
    Reconstruct a DMS coordinate string byte-identical to TXT parser output.

    Latitude degrees are NOT zero-padded (e.g., "41" not "041").
    Longitude degrees are zero-padded to 3 digits (e.g., "088").
    Minutes are zero-padded to 2 digits.
    Seconds are formatted to 4 decimal places with 2-digit integer part.

    Args:
        deg:          Degrees (integer).
        min_:         Minutes (integer).
        sec:          Seconds (float).
        hemis:        Hemisphere character ("N", "S", "E", "W").
        is_longitude: True for longitude (3-digit degree padding), False for latitude.

    Returns:
        DMS string, e.g., "41-46-18.9000N" or "088-28-32.4000W".

    """
    deg_str = f"{deg:03d}" if is_longitude else f"{deg:02d}"
    min_str = f"{min_:02d}"
    sec_str = f"{sec:07.4f}"
    return f"{deg_str}-{min_str}-{sec_str}{hemis.upper()}"


def build_total_secs_string(deg: int, min_: int, sec: float, hemis: str) -> str:
    """
    Compute the total-seconds coordinate field (e.g., "150378.9000N").

    The TXT parser reads a 14-character fixed-width field: 11 characters
    for the numeric value (6 integer digits + dot + 4 decimal places)
    followed by 3 blanks.  Low-latitude airports (e.g., HNL at ~21 deg N)
    produce totals < 100000 which require leading-zero padding to match
    the TXT format.

    Args:
        deg:   Degrees (integer).
        min_:  Minutes (integer).
        sec:   Seconds (float).
        hemis: Hemisphere character.

    Returns:
        Total-seconds string zero-padded to 11 characters with uppercase
        hemisphere appended (e.g., "076744.1690N").

    """
    total = deg * 3600 + min_ * 60 + sec
    return f"{total:011.4f}{hemis.upper()}"


def reconstruct_attendance_schedule(
    month: str,
    day: str,
    hour: str,
) -> str | None:
    """
    Reconstruct the TXT attendance_schedule string from three CSV columns.

    Rules (verified against LL10, EDF, MDW, ARR):
    - All empty -> None
    - MONTH == "UNATNDD" (case-insensitive) -> "UNATNDD"
    - Otherwise -> "MONTH/DAY/HOUR"

    Args:
        month: MONTH column value (may be empty or "UNATNDD").
        day:   DAY column value.
        hour:  HOUR column value.

    Returns:
        Reconstructed schedule string, or None if all inputs are empty.

    """
    month = (month or "").strip()
    day = (day or "").strip()
    hour = (hour or "").strip()

    if not month:
        return None
    if month.upper() == "UNATNDD":
        return "UNATNDD"
    return f"{month}/{day}/{hour}".rstrip("/")


def reconstruct_fuel(csv_fuel: str | None) -> str | None:
    """
    Reconstruct the TXT fuel_available string from CSV FUEL_TYPES column.

    Each comma-separated fuel code is left-justified in a 5-character slot.
    Codes are concatenated and trailing spaces stripped.

    Examples:
        "100,A1"   -> "100  A1"   (100 padded to 5, A1 padded to 5, trailing stripped)
        "100LL,A1+" -> "100LLA1+"  (100LL fills 5, A1+ padded, trailing stripped)
        "100"       -> "100"
        None        -> None

    Args:
        csv_fuel: Comma-separated fuel type codes, or None/empty.

    Returns:
        Reconstructed TXT-compatible fuel string, or None.

    """
    if not csv_fuel:
        return None
    codes = csv_fuel.split(",")
    return "".join(code.ljust(5) for code in codes).rstrip() or None


def reconstruct_mag_variation(
    varn: str | None,
    hemis: str | None,
) -> str | None:
    """
    Reconstruct the TXT mag_variation string from split CSV columns.

    Degrees are zero-padded to 2 digits; hemisphere is uppercased.
    Returns None when varn is empty or None.

    Examples:
        "1", "W" -> "01W"
        "18", "E" -> "18E"
        "", ""    -> None

    Args:
        varn:  MAG_VARN column value (integer degrees as string).
        hemis: MAG_HEMIS column value.

    Returns:
        Reconstructed variation string, or None.

    """
    varn = (varn or "").strip()
    if not varn:
        return None
    deg = int(varn)
    return f"{deg:02d}{(hemis or '').strip().upper()}"


def reconstruct_transient_storage(
    buoy: str,
    hgr: str,
    tie: str,
) -> str | None:
    """
    Reconstruct the TXT transient_storage_facilities string from 3 boolean CSV columns.

    Present flags ("Y") are joined with comma (NOT pipe).
    Returns None when all flags are empty/absent.

    Examples:
        "", "Y", "Y"  -> "HGR,TIE"
        "Y", "Y", "Y" -> "BUOY,HGR,TIE"
        "", "", ""    -> None

    Args:
        buoy: TRNS_STRG_BUOY_FLAG value.
        hgr:  TRNS_STRG_HGR_FLAG value.
        tie:  TRNS_STRG_TIE_FLAG value.

    Returns:
        Comma-joined storage type string, or None.

    """
    parts = []
    if (buoy or "").strip().upper() == "Y":
        parts.append("BUOY")
    if (hgr or "").strip().upper() == "Y":
        parts.append("HGR")
    if (tie or "").strip().upper() == "Y":
        parts.append("TIE")
    return ",".join(parts) or None


def reconstruct_arff(
    type_code: str,
    carrier_code: str,
    cert_date: str,
) -> str | None:
    """
    Reconstruct the TXT arff_certification string from 3 CSV columns.

    Assembles: [type_code] [carrier_code] [MM/YYYY] (date flipped from YYYY/MM).
    Returns None when all inputs are empty.

    Examples:
        "I C", "S", "1973/05" -> "I C S 05/1973"
        "I C", "S", ""        -> "I C S"
        "", "", ""            -> None

    Args:
        type_code:    FAR_139_TYPE_CODE value.
        carrier_code: FAR_139_CARRIER_SER_CODE value.
        cert_date:    ARFF_CERT_TYPE_DATE value in "YYYY/MM" format.

    Returns:
        Reconstructed ARFF certification string, or None.

    """
    type_code = (type_code or "").strip()
    carrier_code = (carrier_code or "").strip()
    cert_date = (cert_date or "").strip()

    if not any((type_code, carrier_code, cert_date)):
        return None

    parts = [p for p in [type_code, carrier_code] if p]
    if cert_date:
        yyyy, mm = cert_date.split("/")
        parts.append(f"{mm}/{yyyy}")
    return " ".join(parts)


def detect_encoding(path: Path) -> str:
    """
    Detect the character encoding of a file using charset-normalizer.

    Falls back to "utf-8" if detection yields no result.  Logs at INFO
    level when a non-UTF-8 encoding is found.

    Args:
        path: Path to the file to inspect.

    Returns:
        Encoding name string (e.g., "cp1250", "utf-8").

    """
    result = from_path(path)
    best = result.best()
    encoding = (best.encoding or "utf-8") if best else "utf-8"
    if encoding != "utf-8":
        logger.info("%s: detected encoding %s", path.name, encoding)
    return encoding
