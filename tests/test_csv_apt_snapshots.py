"""
Snapshot regression tests for the APT CSV parser.

Mirrors tests/test_apt_snapshots.py structure but uses CSV-sourced data.
Function names use 'test_csv_apt_' prefix to isolate baselines
from TXT snapshots -- this prevents --snapshot-update contamination.

Fields expected to be None in CSV snapshots (no APT CSV equivalent):
  - boundary_artcc_id, boundary_artcc_computer_id, boundary_artcc_name
  - based_general_aviation_*, annual_ops_*, npias_federal_agreements
  See tests/test_apt_csv.py CSV_EXPECTED_NONE_FIELDS for the complete list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy.orm import sessionmaker

from tests.conftest import CURATED_AIRPORTS
from tests.snapshot_helpers import extract_record

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from syrupy.assertion import SnapshotAssertion

    from aeroinfo.database.models.apt import Airport


@pytest.mark.csv
@pytest.mark.parametrize("airport_id", CURATED_AIRPORTS)
def test_csv_apt_snapshot(
    airport_id: str,
    csv_apt_engine: Engine,
    snapshot: SnapshotAssertion,
) -> None:
    """
    Snapshot all CSV-sourced fields for a curated airport.

    Captures Airport, Runway, RunwayEnd, AirportRemark, and AttendanceSchedule
    as a nested JSON snapshot.  Run with --snapshot-update to regenerate baselines
    after intentional parser changes.
    """
    from aeroinfo.database.models.apt import Airport

    Session = sessionmaker(bind=csv_apt_engine)
    with Session() as session:
        airport = session.query(Airport).filter_by(faa_id=airport_id).first()
        assert airport is not None, f"Airport {airport_id!r} not found in CSV data"
        airport_data = _build_airport_snapshot(airport)

    assert airport_data == snapshot


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
