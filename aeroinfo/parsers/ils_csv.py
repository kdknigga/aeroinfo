#!/usr/bin/env python

"""
Parser for NASR ILS_BASE CSV records.

Reads ILS_BASE.csv and builds a lookup dictionary mapping
(site_no, rwy_end_id) to approach_type strings.  Used by apt_csv.py
to enrich RunwayEnd.approach_type when APT_RWY_END.csv ILS_TYPE is empty.

ILS_BASE.csv SYSTEM_TYPE_CODE values are mapped to the full approach_type
strings that the TXT parser (apt.py) produces from fixed-width fields, so
that CSV and TXT imports yield identical RunwayEnd.approach_type values.

First-match-wins semantics: when multiple ILS records exist for the same
(site_no, rwy_end_id), only the first record's approach_type is kept.  This
matches TXT behavior, which stores one approach_type per runway end.
"""

import csv
import logging
from pathlib import Path

from aeroinfo.parsers.utils import detect_encoding

logger = logging.getLogger(__name__)

# Required columns -- parser fails immediately if any are absent.
_REQUIRED_ILS_COLS = frozenset({"SITE_NO", "RWY_END_ID", "SYSTEM_TYPE_CODE"})

# SYSTEM_TYPE_CODE -> approach_type string mapping.
# Source: ILS DATA LAYOUT.txt lines 73-91.
# Values are adjusted to match APT.txt fixed-width output exactly:
#   - LC -> "LOCALIZER" (not "LOC") per APT DATA LAYOUT ILS_TYPE definition
#     and verified against TXT snapshot baselines.
_SYSTEM_TYPE_MAP: dict[str, str] = {
    "LS": "ILS",
    "SF": "SDF",
    "LC": "LOCALIZER",
    "LA": "LDA",
    "LD": "ILS/DME",
    "SD": "SDF/DME",
    "LE": "LOC/DME",
    "LG": "LOC/GS",
    "DD": "LDA/DME",
}


def build_approach_type_lookup(
    ils_path: Path,
) -> dict[tuple[str, str], str]:
    """
    Build (site_no, rwy_end_id) -> approach_type string lookup from ILS_BASE.csv.

    Uses charset-normalizer to detect encoding at runtime.  First-match-wins
    semantics for duplicate (site_no, rwy_end_id) keys.

    Args:
        ils_path: Path to ILS_BASE.csv.

    Returns:
        Dictionary mapping (site_no, rwy_end_id) tuples to approach_type strings.

    Raises:
        RuntimeError: if ILS_BASE.csv is missing or required columns are absent.
        ValueError: if an unknown SYSTEM_TYPE_CODE is encountered.

    """
    if not ils_path.exists():
        msg = f"ILS_BASE.csv not found at {ils_path!s} -- required for CSV imports"
        raise RuntimeError(msg)

    encoding = detect_encoding(ils_path)
    lookup: dict[tuple[str, str], str] = {}

    with ils_path.open(newline="", encoding=encoding, errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing = _REQUIRED_ILS_COLS - fieldnames
        if missing:
            msg = f"ILS_BASE.csv is missing required columns: {sorted(missing)}"
            raise RuntimeError(msg)

        for row in reader:
            site_no = row["SITE_NO"].strip()
            rwy_end_id = row["RWY_END_ID"].strip()
            key = (site_no, rwy_end_id)
            if key in lookup:
                continue  # first-match-wins

            code = row["SYSTEM_TYPE_CODE"].strip()
            if not code:
                continue  # skip empty SYSTEM_TYPE_CODE

            if code not in _SYSTEM_TYPE_MAP:
                msg = (
                    f"Unknown SYSTEM_TYPE_CODE {code!r} for "
                    f"SITE_NO={site_no!r}, RWY_END_ID={rwy_end_id!r}"
                )
                raise ValueError(msg)

            lookup[key] = _SYSTEM_TYPE_MAP[code]

    logger.info("ILS lookup: %d approach_type entries from %s", len(lookup), ils_path)
    return lookup
