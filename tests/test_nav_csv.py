"""
Integration tests — CSV NAV parity with TXT snapshot baselines.

Verifies that Navaid, VORReceiverCheckpoint, and Remark objects produced by
aeroinfo.parsers.nav_csv.parse() have field values matching the TXT snapshot
baselines for 5 curated navaids.

Design:
  - A module-scoped fixture (csv_nav_engine) parses the 2026-02-19 CSV data
    once into an in-memory SQLite database (defined in conftest.py).
  - Each parametrized test loads the corresponding TXT snapshot JSON and
    compares CSV-parsed field values against TXT values field-by-field.
  - Fields with no CSV equivalent (see NAV_CSV_EXPECTED_NONE_FIELDS below)
    are verified as None in CSV output and excluded from the TXT-comparison loop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy.orm import sessionmaker

from tests.conftest import _CSV_DATA_DIR, CURATED_NAVAIDS
from tests.snapshot_helpers import extract_record

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SNAPSHOTS_DIR = Path(__file__).resolve().parent / "snapshots" / "test_nav_snapshots"

# ---------------------------------------------------------------------------
# Fields with no CSV equivalent — expected to be None in CSV output
# ---------------------------------------------------------------------------

# TWEB fields — N/A in CSV (TXT_to_CSV_Mapping.txt)
_TWEB_FIELDS = frozenset(
    {
        "tweb_hours",
        "tweb_phone_number",
        "tweb",
    }
)

# Sub-record lists — compared separately, not in the main field loop
_NESTED_FIELDS = frozenset(
    {
        "remarks",
        "airspace_fixes",
        "holding_patterns",
        "fan_markers",
        "vor_receiver_checkpoints",
    }
)

# Combined set for easy checking
NAV_CSV_EXPECTED_NONE_FIELDS = _TWEB_FIELDS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_txt_snapshot(navaid_id: str, facility_type: str) -> dict[str, Any]:
    """Load the TXT-parser snapshot JSON for the given navaid from disk."""
    type_slug = facility_type.replace("/", "_")
    snapshot_path = _SNAPSHOTS_DIR / f"test_nav_snapshot[{navaid_id}-{type_slug}].json"
    with snapshot_path.open() as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.csv
@pytest.mark.parametrize(
    ("navaid_id", "facility_type"),
    CURATED_NAVAIDS,
    ids=[f"{nid}-{ntype.replace('/', '_')}" for nid, ntype in CURATED_NAVAIDS],
)
def test_csv_navaid_parity(
    navaid_id: str,
    facility_type: str,
    csv_nav_engine: Engine,
) -> None:
    """
    CSV-parsed Navaid field values match TXT snapshot baselines.

    For each field in the TXT snapshot:
    - If in NAV_CSV_EXPECTED_NONE_FIELDS (TWEB fields): verify CSV value is None.
    - Otherwise: verify CSV value equals TXT value.
    """
    from aeroinfo.database.models.nav import Navaid

    _Session = sessionmaker(bind=csv_nav_engine)
    with _Session() as session:
        navaid = (
            session.query(Navaid)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .first()
        )
        assert navaid is not None, (
            f"Navaid {navaid_id!r} (type={facility_type!r}) not found in CSV data — "
            f"verify {_CSV_DATA_DIR / 'NAV_BASE.csv'} contains this navaid"
        )
        csv_data = extract_record(navaid)

    txt_snapshot = _load_txt_snapshot(navaid_id, facility_type)

    for field, txt_value in txt_snapshot.items():
        if field in _NESTED_FIELDS:
            continue  # compared in separate tests

        if field in NAV_CSV_EXPECTED_NONE_FIELDS:
            assert csv_data[field] is None, (
                f"Field {field!r} should be None in CSV output for "
                f"{navaid_id} {facility_type} (no CSV equivalent), "
                f"but got {csv_data[field]!r}"
            )
            continue

        assert csv_data[field] == txt_value, (
            f"Field {field!r} mismatch for {navaid_id} {facility_type}: "
            f"CSV={csv_data[field]!r}, TXT={txt_value!r}"
        )


@pytest.mark.csv
@pytest.mark.parametrize(
    ("navaid_id", "facility_type"),
    CURATED_NAVAIDS,
    ids=[f"{nid}-{ntype.replace('/', '_')}" for nid, ntype in CURATED_NAVAIDS],
)
def test_csv_checkpoint_parity(
    navaid_id: str,
    facility_type: str,
    csv_nav_engine: Engine,
) -> None:
    """
    CSV-parsed VORReceiverCheckpoint records match TXT snapshot baselines.

    Compares sorted lists of checkpoints (by bearing) to be order-independent.
    """
    from aeroinfo.database.models.nav import VORReceiverCheckpoint

    _Session = sessionmaker(bind=csv_nav_engine)
    with _Session() as session:
        checkpoints = (
            session.query(VORReceiverCheckpoint)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .all()
        )
        csv_list = [extract_record(v) for v in checkpoints]

    txt_snapshot = _load_txt_snapshot(navaid_id, facility_type)
    txt_list = txt_snapshot.get("vor_receiver_checkpoints", [])

    assert len(csv_list) == len(txt_list), (
        f"Checkpoint count mismatch for {navaid_id} {facility_type}: "
        f"CSV={len(csv_list)}, TXT={len(txt_list)}"
    )

    # Sort both by (bearing) for stable comparison
    csv_sorted = sorted(csv_list, key=lambda c: c.get("bearing") or 0)
    txt_sorted = sorted(txt_list, key=lambda c: c.get("bearing") or 0)

    for i, (csv_ckpt, txt_ckpt) in enumerate(zip(csv_sorted, txt_sorted, strict=True)):
        for field, txt_value in txt_ckpt.items():
            assert csv_ckpt[field] == txt_value, (
                f"Checkpoint[{i}] field {field!r} mismatch for "
                f"{navaid_id} {facility_type}: "
                f"CSV={csv_ckpt[field]!r}, TXT={txt_value!r}"
            )


@pytest.mark.csv
@pytest.mark.parametrize(
    ("navaid_id", "facility_type"),
    CURATED_NAVAIDS,
    ids=[f"{nid}-{ntype.replace('/', '_')}" for nid, ntype in CURATED_NAVAIDS],
)
def test_csv_remark_parity(
    navaid_id: str,
    facility_type: str,
    csv_nav_engine: Engine,
) -> None:
    """
    CSV-parsed Remark records match TXT snapshot baselines.

    Compares sorted lists of remarks (by remark text) to be order-independent.
    """
    from aeroinfo.database.models.nav import Remark

    _Session = sessionmaker(bind=csv_nav_engine)
    with _Session() as session:
        remarks = (
            session.query(Remark)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .all()
        )
        csv_list = [extract_record(r) for r in remarks]

    txt_snapshot = _load_txt_snapshot(navaid_id, facility_type)
    txt_list = txt_snapshot.get("remarks", [])

    assert len(csv_list) == len(txt_list), (
        f"Remark count mismatch for {navaid_id} {facility_type}: "
        f"CSV={len(csv_list)}, TXT={len(txt_list)}"
    )

    # Sort both by remark text for stable comparison
    csv_sorted = sorted(csv_list, key=lambda r: r.get("remark") or "")
    txt_sorted = sorted(txt_list, key=lambda r: r.get("remark") or "")

    for i, (csv_rmk, txt_rmk) in enumerate(zip(csv_sorted, txt_sorted, strict=True)):
        for field, txt_value in txt_rmk.items():
            assert csv_rmk[field] == txt_value, (
                f"Remark[{i}] field {field!r} mismatch for "
                f"{navaid_id} {facility_type}: "
                f"CSV={csv_rmk[field]!r}, TXT={txt_value!r}"
            )


@pytest.mark.csv
@pytest.mark.parametrize(
    ("navaid_id", "facility_type"),
    CURATED_NAVAIDS,
    ids=[f"{nid}-{ntype.replace('/', '_')}" for nid, ntype in CURATED_NAVAIDS],
)
def test_csv_empty_sub_records(
    navaid_id: str,
    facility_type: str,
    csv_nav_engine: Engine,
) -> None:
    """
    CSV-parsed navaids have empty AirspaceFix, HoldingPattern, and FanMarker lists.

    NAV3/NAV4/NAV5 CSV files are absent from the 2026-02-19 dataset — empty lists
    are the expected correct output, not a parser error.
    """
    from aeroinfo.database.models.nav import Navaid

    _Session = sessionmaker(bind=csv_nav_engine)
    with _Session() as session:
        navaid = (
            session.query(Navaid)
            .filter_by(facility_id=navaid_id, facility_type=facility_type)
            .first()
        )
        assert navaid is not None

        # These sub-records have no CSV equivalents
        assert navaid.airspace_fixes == [], (
            f"{navaid_id} {facility_type}: airspace_fixes should be empty list "
            f"(no CSV equivalent), got {len(navaid.airspace_fixes)} records"
        )
        assert navaid.holding_patterns == [], (
            f"{navaid_id} {facility_type}: holding_patterns should be empty list "
            f"(no CSV equivalent), got {len(navaid.holding_patterns)} records"
        )
        assert navaid.fan_markers == [], (
            f"{navaid_id} {facility_type}: fan_markers should be empty list "
            f"(no CSV equivalent), got {len(navaid.fan_markers)} records"
        )
