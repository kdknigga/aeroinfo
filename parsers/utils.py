#!/usr/bin/env python
"""Helpers for parsing fixed-width NASR records."""

from __future__ import annotations

import datetime
import logging

from dateutil import parser as dateparser

logger = logging.getLogger(__name__)


def get_field(record: str, start: int, length: int, var_type: str = "str") -> object:
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
        return dateparser.parse(field)
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
