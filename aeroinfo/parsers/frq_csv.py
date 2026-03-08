#!/usr/bin/env python

"""
Parser for NASR FRQ CSV records.

Reads FRQ.csv and populates unicom and ctaf fields on existing Airport records.
FRQ.csv uses FACILITY (= Airport.faa_id) as the join key, unlike the APT_* files
which use SITE_NO + SITE_TYPE_CODE.

FRQ.csv may use non-UTF-8 encoding (cp1250 detected for 2026-02-19).
charset-normalizer is used for runtime encoding detection.

Frequency types populated:
  UNICOM -> Airport.unicom (first-match-wins)
  CTAF   -> Airport.ctaf   (first-match-wins)

Structured for future expansion: the FREQ_USE guard makes it straightforward to
add tower, ATIS, AWOS, RCAG, and RCO frequency types without restructuring the
module.
"""

import csv
import logging
from pathlib import Path

from sqlalchemy.orm import Session as SASession

from aeroinfo.database.models.apt import Airport
from aeroinfo.parsers.utils import detect_encoding

logger = logging.getLogger(__name__)

# Required columns — parser fails immediately if any are absent.
_REQUIRED_FRQ_COLS = frozenset({"FACILITY", "FREQ", "FREQ_USE"})


def parse(frq_path: Path, session: SASession) -> None:
    """
    Parse FRQ.csv and populate unicom/ctaf on existing Airport records.

    Uses charset-normalizer to detect encoding at runtime (FRQ.csv uses cp1250
    for the 2026-02-19 data cycle).  Frequencies are formatted to 3 decimal
    places to match TXT snapshot values (e.g., "120.6" -> "120.600").

    First-match-wins semantics: only the first UNICOM and CTAF row encountered
    for each airport is applied; subsequent rows for the same airport and
    FREQ_USE are silently skipped.

    Raises:
        RuntimeError: if FRQ.csv is missing or required columns are absent.

    """
    if not frq_path.exists():
        msg = f"FRQ.csv not found at {frq_path!s} — required for CSV imports"
        raise RuntimeError(msg)

    encoding = detect_encoding(frq_path)

    with frq_path.open(newline="", encoding=encoding, errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing = _REQUIRED_FRQ_COLS - fieldnames
        if missing:
            msg = f"FRQ.csv is missing required columns: {sorted(missing)}"
            raise RuntimeError(msg)

        for row in reader:
            freq_use = row["FREQ_USE"].strip()
            if freq_use not in ("UNICOM", "CTAF"):
                continue

            faa_id = row["FACILITY"].strip()
            if not faa_id:
                continue

            airport = session.query(Airport).filter_by(faa_id=faa_id).first()
            if airport is None:
                continue

            freq = _format_freq(row["FREQ"].strip())
            if freq is None:
                continue

            if freq_use == "UNICOM" and airport.unicom is None:
                airport.unicom = freq
                session.merge(airport)
            elif freq_use == "CTAF" and airport.ctaf is None:
                airport.ctaf = freq
                session.merge(airport)


def _format_freq(raw: str) -> str | None:
    """
    Format a frequency string to 3 decimal places.

    Converts variable-precision strings from FRQ.csv (e.g., "120.6", "122.95",
    "122.725") to fixed 3-decimal-place format matching TXT snapshot values
    (e.g., "120.600", "122.950", "122.725").

    Args:
        raw: Raw frequency string from FRQ.csv FREQ column.

    Returns:
        Formatted frequency string, or None if ``raw`` is empty.

    """
    if not raw:
        return None
    return f"{float(raw):.3f}"
