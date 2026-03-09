"""
Parametrized snapshot regression tests for the APT TXT parser.

Covers all fields of Airport, Runway, RunwayEnd, AirportRemark, and
AttendanceSchedule for a curated set of airports parsed from the
fixed-width references/APT.txt file.

Coverage spans 107 airports across diverse types (all verified in references/APT.txt):
- GA/private: LL10, 1R8, 52F, 8I3, S50, and many more
- Military: EDF (Elmendorf AFB), and others
- Large commercial hubs: ORD, JFK, LAX, ATL, DFW, DEN, CLT, LAS, IAH, SFO, SEA, etc.
- Medium commercial: MDW, ARR, RFD, AUS, BNA, PDX, SAN, STL, TPA, and many more
- Towered/untowered, geographically diverse (AK, HI, PR, and all contiguous states)
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import sessionmaker

from tests.conftest import _APT_TXT_FILE, CURATED_AIRPORTS
from tests.snapshot_helpers import extract_record

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine
    from syrupy.assertion import SnapshotAssertion

    from aeroinfo.database.models.apt import Airport

_APT_FILE = _APT_TXT_FILE


@pytest.fixture(scope="module")
def apt_engine() -> Generator[Engine]:
    """Parse the reference APT.txt into in-memory SQLite once for all snapshot tests."""
    import aeroinfo.database as db
    from aeroinfo.database.base import Base

    engine = create_engine("sqlite:///:memory:")
    original_inner = db.Engine._engine
    db.Engine._engine = engine

    Base.metadata.create_all(engine)

    import aeroinfo.parsers.apt as apt_parser

    importlib.reload(apt_parser)
    apt_parser.parse(str(_APT_FILE))

    yield engine

    db.Engine._engine = original_inner


@pytest.mark.parametrize("airport_id", CURATED_AIRPORTS)
def test_apt_snapshot(
    airport_id: str,
    apt_engine: Engine,
    snapshot: SnapshotAssertion,
) -> None:
    """
    Snapshot all fields for a curated airport.

    Asserts:
    1. Field-count equality for all models (set-difference error message on failure)
    2. Snapshot equality via syrupy (field-level diff on value regressions)
    """
    from aeroinfo.database.models.apt import Airport

    Session = sessionmaker(bind=apt_engine)
    with Session() as session:
        airport = session.query(Airport).filter_by(faa_id=airport_id).first()
        assert airport is not None, (
            f"Airport {airport_id!r} not found in references/APT.txt — "
            "verify the airport ID exists in the reference file"
        )

        # Field-count assertions (before snapshot to get actionable error first)
        _assert_airport_field_coverage(airport)

        # Build nested snapshot dict while session is open (avoids DetachedInstanceError)
        airport_data = _build_airport_snapshot(airport)

    # Session closed — syrupy diff assertion
    assert airport_data == snapshot


def _assert_airport_field_coverage(airport: Airport) -> None:
    """
    Assert extract_record covers exactly the Airport model's mapped columns.

    Also validates Runway, RunwayEnd, AirportRemark, and AttendanceSchedule
    field coverage for all child records of the airport.
    """
    from aeroinfo.database.models.apt import (
        Airport,
        AirportRemark,
        AttendanceSchedule,
        Runway,
        RunwayEnd,
    )

    # Airport
    expected = {col.key for col in sa_inspect(Airport).columns}
    actual = set(extract_record(airport).keys())
    assert actual == expected, (
        f"Airport field coverage mismatch — "
        f"missing: {sorted(expected - actual)}, "
        f"extra: {sorted(actual - expected)}"
    )

    # Runway and RunwayEnd
    expected_rwy = {col.key for col in sa_inspect(Runway).columns}
    expected_rwy_end = {col.key for col in sa_inspect(RunwayEnd).columns}
    for rwy in airport.runways:
        actual_rwy = set(extract_record(rwy).keys())
        assert actual_rwy == expected_rwy, (
            f"Runway field coverage mismatch — "
            f"missing: {sorted(expected_rwy - actual_rwy)}, "
            f"extra: {sorted(actual_rwy - expected_rwy)}"
        )
        for end in rwy.runway_ends:
            actual_end = set(extract_record(end).keys())
            assert actual_end == expected_rwy_end, (
                f"RunwayEnd field coverage mismatch — "
                f"missing: {sorted(expected_rwy_end - actual_end)}, "
                f"extra: {sorted(actual_end - expected_rwy_end)}"
            )

    # AirportRemark
    expected_rmk = {col.key for col in sa_inspect(AirportRemark).columns}
    for rmk in airport.remarks:
        actual_rmk = set(extract_record(rmk).keys())
        assert actual_rmk == expected_rmk, (
            f"AirportRemark field coverage mismatch — "
            f"missing: {sorted(expected_rmk - actual_rmk)}, "
            f"extra: {sorted(actual_rmk - expected_rmk)}"
        )

    # AttendanceSchedule
    expected_att = {col.key for col in sa_inspect(AttendanceSchedule).columns}
    for att in airport.attendance_schedules:
        actual_att = set(extract_record(att).keys())
        assert actual_att == expected_att, (
            f"AttendanceSchedule field coverage mismatch — "
            f"missing: {sorted(expected_att - actual_att)}, "
            f"extra: {sorted(actual_att - expected_att)}"
        )


def _build_airport_snapshot(airport: Airport) -> dict[str, Any]:
    """Serialize airport and all nested records to a plain dict."""
    data = extract_record(airport)
    data["runways"] = _build_runways(airport)
    data["remarks"] = [extract_record(r) for r in airport.remarks]
    data["attendance_schedules"] = [
        extract_record(a) for a in airport.attendance_schedules
    ]
    return data


def _build_runways(airport: Airport) -> list[dict[str, Any]]:
    """Serialize each runway (sorted by name) with nested runway_ends."""
    result = []
    for rwy in sorted(airport.runways, key=lambda r: r.name):
        rwy_data = extract_record(rwy)
        rwy_data["runway_ends"] = [extract_record(end) for end in rwy.runway_ends]
        result.append(rwy_data)
    return result
