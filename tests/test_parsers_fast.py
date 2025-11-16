"""
Fast, minimal parser smoke test using in-memory SQLite.

This test parses tiny APT/NAV fixtures and asserts a couple of
deterministic fields so it runs quickly in CI.
"""

import importlib
from pathlib import Path

import pytest
from pytest import MonkeyPatch
from sqlalchemy import create_engine


@pytest.mark.fast
def test_parsers_minimal(monkeypatch: MonkeyPatch) -> None:
    """
    Run minimal parsers using an in-memory DB and assert a couple fields.

    Parameters
    ----------
    monkeypatch:
        Pytest monkeypatch fixture for patching the package Engine.

    """
    # Use in-memory SQLite and patch the package Engine before importing parsers
    db_uri = "sqlite:///:memory:"
    engine = create_engine(db_uri)

    # Patch the package-level Engine symbol so parsers use the in-memory DB
    import aeroinfo.database as dbmod

    monkeypatch.setattr(dbmod, "Engine", engine)

    # Create schema
    from aeroinfo.database.base import Base

    Base.metadata.create_all(engine)

    # Now import parsers (reload to ensure they pick up the patched Engine)
    import aeroinfo.parsers.apt as apt_parser
    import aeroinfo.parsers.nav as nav_parser

    importlib.reload(apt_parser)
    importlib.reload(nav_parser)

    fixtures = Path(__file__).parent / "fixtures"
    apt_file = fixtures / "APT_min.txt"
    nav_file = fixtures / "NAV_min.txt"

    # Run parsers
    apt_parser.parse(str(apt_file))
    nav_parser.parse(str(nav_file))

    # Query via package helpers to assert parsed results
    # `query.py` is a top-level module in the repo root (not `aeroinfo.query`),
    # import it directly so tests can call its helpers.
    query = importlib.import_module("query")

    adk = query.find_airport("ADK")
    assert adk is not None
    assert adk.icao_id == "PADK" or adk.facility_id == "ADK"
    adk_elev = adk.elevation
    assert adk_elev is not None
    assert round(adk_elev, 1) == 19.5

    ber = query.find_navaid("BER", "TACAN")
    assert ber is not None
    assert ber.facility_type.upper().startswith("TACAN")
    ber_elev = ber.elevation
    assert ber_elev is not None
    assert round(ber_elev, 1) == 408.0
