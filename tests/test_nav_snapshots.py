"""
Parametrized snapshot regression tests for the NAV TXT parser.

Covers all fields of Navaid (NAV1) and all 5 sub-record types:
  - Remark (NAV2)
  - AirspaceFix (NAV3)
  - HoldingPattern (NAV4)
  - FanMarker (NAV5)
  - VORReceiverCheckpoint (NAV6)

Navaids selected (all verified in references/NAV.txt):
- AST VOR/DME: ASTORIA — 3 remarks, 1 fix, 1 pattern, 1 fan_marker, 1 checkpoint
  (covers ALL 5 sub-record types)
- BER TACAN:   ADAK — 1 remark, 1 fix, 1 pattern, 0 markers, 0 checkpoints
- CZF NDB:     CAPE ROMANZOF — 1 remark, 1 fix, 1 pattern, 0 markers, 0 checkpoints
- FAI VORTAC:  FAIRBANKS — 1 remark, 3 fixes, 1 pattern, 0 markers, 1 checkpoint
- EDN VOR:     ENTERPRISE — 1 remark, 1 fix, 1 pattern, 0 markers, 0 checkpoints
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import sessionmaker

from tests.conftest import _REFERENCES_DIR, CURATED_NAVAIDS
from tests.snapshot_helpers import extract_record

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine
    from syrupy.assertion import SnapshotAssertion

    from aeroinfo.database.models.nav import Navaid

_NAV_FILE = _REFERENCES_DIR / "NAV.txt"


@pytest.fixture(scope="module")
def nav_engine() -> Generator[Engine]:
    """Parse references/NAV.txt into in-memory SQLite once for all snapshot tests."""
    import aeroinfo.database as db
    from aeroinfo.database.base import Base

    engine = create_engine("sqlite:///:memory:")
    original_inner = db.Engine._engine
    db.Engine._engine = engine

    Base.metadata.create_all(engine)

    import aeroinfo.parsers.nav as nav_parser

    importlib.reload(nav_parser)
    nav_parser.parse(str(_NAV_FILE))

    yield engine

    db.Engine._engine = original_inner


@pytest.mark.parametrize(
    ("navaid_id", "facility_type"),
    CURATED_NAVAIDS,
    ids=[f"{fid}-{ftype.replace('/', '_')}" for fid, ftype in CURATED_NAVAIDS],
)
def test_nav_snapshot(
    navaid_id: str,
    facility_type: str,
    nav_engine: Engine,
    snapshot: SnapshotAssertion,
) -> None:
    """
    Snapshot all fields for a curated navaid.

    Asserts:
    1. Field-count equality for all models (set-difference error message on failure)
    2. Snapshot equality via syrupy (field-level diff on value regressions)
    """
    from aeroinfo.database.models.nav import Navaid

    Session = sessionmaker(bind=nav_engine)
    with Session() as session:
        navaid = (
            session.query(Navaid)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .first()
        )
        assert navaid is not None, (
            f"Navaid {navaid_id!r} (type={facility_type!r}) not found in references/NAV.txt — "
            "verify the facility_id and facility_type exist in the reference file"
        )

        # Field-count assertions (before snapshot to get actionable error first)
        _assert_navaid_field_coverage(navaid)

        # Build nested snapshot dict while session is open (avoids DetachedInstanceError)
        navaid_data = _build_navaid_snapshot(navaid)

    # Session closed — syrupy diff assertion
    assert navaid_data == snapshot


def _assert_navaid_field_coverage(navaid: Navaid) -> None:
    """
    Assert extract_record covers exactly the Navaid model's mapped columns.

    Also validates all 5 sub-record types (Remark, AirspaceFix, HoldingPattern,
    FanMarker, VORReceiverCheckpoint) for all child records of the navaid.
    """
    from aeroinfo.database.models.nav import (
        AirspaceFix,
        FanMarker,
        HoldingPattern,
        Navaid,
        Remark,
        VORReceiverCheckpoint,
    )

    # Navaid (NAV1)
    expected = {col.key for col in sa_inspect(Navaid).columns}
    actual = set(extract_record(navaid).keys())
    assert actual == expected, (
        f"Navaid field coverage mismatch — "
        f"missing: {sorted(expected - actual)}, "
        f"extra: {sorted(actual - expected)}"
    )

    # Sub-records
    _check_sub_record_coverage(navaid.remarks, Remark, "remarks")
    _check_sub_record_coverage(navaid.airspace_fixes, AirspaceFix, "airspace_fixes")
    _check_sub_record_coverage(
        navaid.holding_patterns, HoldingPattern, "holding_patterns"
    )
    _check_sub_record_coverage(navaid.fan_markers, FanMarker, "fan_markers")
    _check_sub_record_coverage(
        navaid.vor_receiver_checkpoints,
        VORReceiverCheckpoint,
        "vor_receiver_checkpoints",
    )


def _check_sub_record_coverage(records: list, model_cls: type, name: str) -> None:
    """Assert extract_record covers exactly the sub-record model's mapped columns."""
    expected = {col.key for col in sa_inspect(model_cls).columns}
    for rec in records:
        actual = set(extract_record(rec).keys())
        assert actual == expected, (
            f"{name} field coverage mismatch — "
            f"missing: {sorted(expected - actual)}, "
            f"extra: {sorted(actual - expected)}"
        )


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
