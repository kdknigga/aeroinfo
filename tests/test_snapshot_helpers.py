"""Smoke tests for tests/snapshot_helpers.extract_record()."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import inspect

from tests.snapshot_helpers import extract_record

if TYPE_CHECKING:
    from aeroinfo.database.models.apt import Airport, RunwayEnd


@pytest.mark.fast
def test_extract_record_nasr_enum(sample_runway_end: RunwayEnd) -> None:
    """NASREnum fields serialize to {"code": ..., "description": ...}."""
    record = extract_record(sample_runway_end)
    vgsi = record["visual_glide_slope_indicators"]
    assert isinstance(vgsi, dict)
    assert vgsi["code"] == "V2L"
    assert vgsi["description"] == "2-BOX VASI ON LEFT SIDE OF RUNWAY"


@pytest.mark.fast
def test_extract_record_date_field(sample_airport: Airport) -> None:
    """datetime.date fields serialize to ISO 8601 strings."""
    sample_airport.effective_date = datetime.date(2024, 1, 15)
    record = extract_record(sample_airport)
    assert record["effective_date"] == "2024-01-15"


@pytest.mark.fast
def test_extract_record_null_passthrough(sample_runway_end: RunwayEnd) -> None:
    """None values pass through as None."""
    record = extract_record(sample_runway_end)
    # position_date is not set on sample_runway_end in conftest
    assert record["position_date"] is None


@pytest.mark.fast
def test_extract_record_covers_all_columns(sample_runway_end: RunwayEnd) -> None:
    """extract_record() returns a key for every mapped ORM column."""
    from aeroinfo.database.models.apt import RunwayEnd

    mapper = inspect(RunwayEnd)
    record = extract_record(sample_runway_end)
    assert set(record.keys()) == {col.key for col in mapper.columns}
