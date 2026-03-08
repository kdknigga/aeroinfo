"""
Snapshot regression tests for the NAV CSV parser.

Mirrors tests/test_nav_snapshots.py structure but uses CSV-sourced data.
Function names use 'test_csv_nav_' prefix to isolate baselines
from TXT snapshots — this prevents --snapshot-update contamination.

Fields expected to be None in CSV snapshots (no NAV CSV equivalent):
  - tweb_hours, tweb_phone_number, tweb (TWEB fields)

Sub-record collections expected to be empty in CSV snapshots:
  - airspace_fixes (NAV3 — no CSV equivalent)
  - holding_patterns (NAV4 — no CSV equivalent)
  - fan_markers (NAV5 — no CSV equivalent)

Populated sub-records from CSV:
  - remarks (from NAV_RMK.csv)
  - vor_receiver_checkpoints (from NAV_CKPT.csv)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy.orm import sessionmaker

from tests.conftest import CURATED_NAVAIDS
from tests.snapshot_helpers import extract_record

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from syrupy.assertion import SnapshotAssertion

    from aeroinfo.database.models.nav import Navaid


@pytest.mark.csv
@pytest.mark.parametrize(
    ("navaid_id", "facility_type"),
    CURATED_NAVAIDS,
    ids=[f"{fid}-{ftype.replace('/', '_')}" for fid, ftype in CURATED_NAVAIDS],
)
def test_csv_nav_snapshot(
    navaid_id: str,
    facility_type: str,
    csv_nav_engine: Engine,
    snapshot: SnapshotAssertion,
) -> None:
    """
    Snapshot all CSV-sourced fields for a curated navaid.

    Captures Navaid with all sub-records (remarks, checkpoints, and the three
    empty collections for NAV3/4/5) as a nested JSON snapshot.  Run with
    --snapshot-update to regenerate baselines after intentional parser changes.
    """
    from aeroinfo.database.models.nav import Navaid

    Session = sessionmaker(bind=csv_nav_engine)
    with Session() as session:
        navaid = (
            session.query(Navaid)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .first()
        )
        assert navaid is not None, (
            f"Navaid {navaid_id!r} (type={facility_type!r}) not found in CSV data"
        )
        navaid_data = _build_navaid_snapshot(navaid)

    assert navaid_data == snapshot


def _build_navaid_snapshot(navaid: Navaid) -> dict[str, Any]:
    """Serialize navaid and all nested sub-records to a plain dict."""
    data = extract_record(navaid)
    data["remarks"] = [extract_record(r) for r in navaid.remarks]
    data["airspace_fixes"] = [extract_record(f) for f in navaid.airspace_fixes]
    data["holding_patterns"] = [extract_record(h) for h in navaid.holding_patterns]
    data["fan_markers"] = [extract_record(m) for m in navaid.fan_markers]
    data["vor_receiver_checkpoints"] = [
        extract_record(v) for v in navaid.vor_receiver_checkpoints
    ]
    return data
