#!/usr/bin/env python
"""Helpers for parsing fixed-width NASR records."""

from __future__ import annotations

import datetime
import logging
import struct
from typing import TYPE_CHECKING, NamedTuple

from dateutil import parser as dateparser

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class FieldSpec(NamedTuple):
    """Specification for a single field in a fixed-width record."""

    name: str
    start: int
    length: int
    var_type: str = "str"


class StructParser:
    """
    Efficient fixed-width record parser using struct.Struct.

    This class pre-compiles field extraction using struct.Struct for better
    performance when parsing many records with the same field layout.

    Example usage:
        fields = [
            FieldSpec("facility_id", 5, 4),
            FieldSpec("facility_type", 9, 20),
            FieldSpec("elevation", 473, 7, "float"),
        ]
        parser = StructParser(fields)
        result = parser.parse(line)
        # result is {"facility_id": "BER", "facility_type": "TACAN", "elevation": 408.0}

    """

    def __init__(self, fields: Sequence[FieldSpec], record_length: int = 0) -> None:
        """
        Initialize the parser with field specifications.

        Parameters
        ----------
        fields:
            Sequence of FieldSpec tuples defining each field.
        record_length:
            Expected total record length. If 0, computed from field specs.

        """
        self.fields = fields
        self._record_length = record_length or self._compute_record_length()
        self._struct, self._field_indices = self._build_struct()

    def _compute_record_length(self) -> int:
        """Compute the minimum record length needed to extract all fields."""
        if not self.fields:
            return 0
        return max(f.start + f.length - 1 for f in self.fields)

    def _build_struct(self) -> tuple[struct.Struct, list[tuple[int, FieldSpec]]]:
        """
        Build the struct format string and field index mapping.

        Returns a tuple of (struct.Struct, field_indices) where field_indices
        maps struct output positions to FieldSpec objects.
        """
        # Sort fields by start position for efficient struct unpacking
        sorted_fields = sorted(self.fields, key=lambda f: f.start)

        # Build format string: we need to handle gaps between fields
        fmt_parts: list[str] = []
        field_indices: list[tuple[int, FieldSpec]] = []
        current_pos = 1  # 1-based position (matches get_field convention)

        for field_idx, field in enumerate(sorted_fields):
            # Add padding for gap before this field
            gap = field.start - current_pos
            if gap > 0:
                fmt_parts.append(f"{gap}x")  # skip bytes

            # Add this field
            fmt_parts.append(f"{field.length}s")
            field_indices.append((field_idx, field))
            current_pos = field.start + field.length

        fmt_string = "".join(fmt_parts)
        return struct.Struct(fmt_string), field_indices

    def parse(self, record: str) -> dict[str, object]:
        """
        Parse a fixed-width record and return a dictionary of field values.

        Parameters
        ----------
        record:
            The fixed-width record string to parse.

        Returns
        -------
        dict:
            Dictionary mapping field names to their converted values.

        """
        # Use latin-1 encoding because NASR files use ASCII with possible
        # extended characters. Latin-1 is a superset of ASCII that preserves
        # all byte values (0-255) and allows round-trip encoding/decoding.
        record_bytes = record.encode("latin-1", errors="replace")
        if len(record_bytes) < self._struct.size:
            record_bytes = record_bytes.ljust(self._struct.size)

        # Unpack all fields at once using the pre-compiled struct
        raw_values = self._struct.unpack_from(record_bytes)

        # Convert each field to its target type
        result: dict[str, object] = {}
        for idx, field_spec in self._field_indices:
            raw_bytes = raw_values[idx]
            raw_str = raw_bytes.decode("latin-1").strip()
            result[field_spec.name] = _convert_field(raw_str, field_spec.var_type)

        return result


def _convert_field(field: str, var_type: str) -> object:
    """
    Convert a field string to the requested type.

    This is the same conversion logic used by get_field, extracted for reuse.

    Parameters
    ----------
    field:
        The stripped field string value.
    var_type:
        The target type for conversion.

    Returns
    -------
    object:
        The converted value, or None if field is empty.

    """
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


def get_field(record: str, start: int, length: int, var_type: str = "str") -> object:
    """
    Extract a slice from a fixed-width record and coerce to the requested type.

    Returns None when the extracted field is empty.

    """
    s = start - 1
    e = start + length - 1
    field = record[s:e].strip()
    logger.debug("start: %s, length: %s, field: %s", start, length, field)
    return _convert_field(field, var_type)
