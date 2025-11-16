"""
Tests for the NASR file parsers (APT/NAV) using an in-memory DB.

These tests patch the module-level Engine to a sqlite:///:memory: engine,
create the ORM tables, run the parser against the sample files in
`references/` and then assert that a few known records were merged.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if TYPE_CHECKING:
    import pytest


def _make_engine_and_create_schema(monkeypatch: pytest.MonkeyPatch) -> object:
    """
    Create an in-memory SQLite engine and patch the package Engine.

    Returns the created Engine object.
    """
    import aeroinfo.database as db

    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(db, "Engine", engine)

    # Import model modules so they register with Base.metadata
    import aeroinfo.database.models.apt as apt_models  # noqa: F401
    import aeroinfo.database.models.nav as nav_models  # noqa: F401
    from aeroinfo.database.base import Base

    Base.metadata.create_all(engine)
    return engine


def test_apt_parser_merges_airports(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the APT parser against sample data and assert airports were merged."""
    engine = _make_engine_and_create_schema(monkeypatch)

    # Import parser after Engine has been patched so it uses the in-memory DB
    apt_parser = import_module("aeroinfo.parsers.apt")
    # Ensure the parser module picks up the patched Engine (reload to rebind module-level Engine)
    import importlib

    importlib.reload(apt_parser)

    data_path = Path(__file__).resolve().parents[1] / "references" / "APT.txt"
    apt_parser.parse(str(data_path))

    Session = sessionmaker(bind=engine)
    session = Session()

    from aeroinfo.database.models.apt import Airport

    # ADK is present in the sample APT.txt; assert it was merged
    airport = session.query(Airport).filter_by(faa_id="ADK").first()
    assert airport is not None
    assert airport.name is not None

    # Additional deterministic field checks to guard parser regressions
    # ICAO is present in the sample file as PADK
    assert airport.icao_id == "PADK"

    # Elevation parsed as float (nearest tenth) in the APT sample is 19.5
    assert isinstance(airport.elevation, float)
    assert abs(airport.elevation - 19.5) < 0.01

    # Beacon color is stored as an Enum member with value 'WG' (white-green)
    from aeroinfo.database import enums as _enums

    assert airport.beacon_color is not None
    # SQLAlchemy maps Enum fields to the Enum member; check value and description
    assert airport.beacon_color.value == _enums.BeaconColorEnum.WG.value
    assert _enums.BeaconColorEnum.WG.description.upper().startswith("WHITE")

    # Effective date parsed from APT source (10/30/2025)
    assert airport.effective_date is not None
    # Check exact date components (10/30/2025)
    assert getattr(airport.effective_date, "year", None) == 2025
    assert getattr(airport.effective_date, "month", None) == 10
    assert getattr(airport.effective_date, "day", None) == 30

    # Check runway and runway_end parsing for ADK: there is a RWY record for 05/23
    from aeroinfo.database.models.apt import Runway, RunwayEnd

    runway = (
        session.query(Runway)
        .filter_by(facility_site_number=airport.facility_site_number, name="05/23")
        .first()
    )
    assert runway is not None
    # Check parsed numeric runway fields (from the sample: length 7790, width 200)
    assert isinstance(runway.length, int)
    assert runway.length == 7790
    assert isinstance(runway.width, int)
    assert runway.width == 200
    # Surface type should include 'ASPH' from the sample
    assert isinstance(runway.surface_type_condition, str)
    assert "ASPH" in runway.surface_type_condition.upper()
    # Surface treatment like 'GRVD' should be present
    assert runway.surface_treatment is not None

    # Base end (05) should be present and have numeric elevation and lighting info
    rw_end = (
        session.query(RunwayEnd)
        .filter_by(
            facility_site_number=airport.facility_site_number,
            runway_name=runway.name,
            id="05",
        )
        .first()
    )
    assert rw_end is not None
    assert isinstance(rw_end.elevation, float)
    # visual_glide_slope_indicators may be absent in some records; if present it should be an Enum
    if rw_end.visual_glide_slope_indicators is not None:
        import enum as _pyenum

        assert isinstance(rw_end.visual_glide_slope_indicators, _pyenum.Enum)
        # description property should exist on NASREnum-derived members
        assert hasattr(rw_end.visual_glide_slope_indicators, "description")
    # Threshold crossing height and visual glide path angle should be parsed
    if rw_end.threshold_crossing_height is not None:
        assert isinstance(rw_end.threshold_crossing_height, int)
        # sample RWY shows 600 for threshold crossing height
        assert rw_end.threshold_crossing_height == 600
    if rw_end.visual_glide_path_angle is not None:
        assert isinstance(rw_end.visual_glide_path_angle, float)
        # sample has ~17.4 as the visual glide path angle
        assert abs(rw_end.visual_glide_path_angle - 17.4) < 0.2
    # Displaced threshold length may be present; ensure type if exists
    if rw_end.displaced_threshold_length is not None:
        assert isinstance(rw_end.displaced_threshold_length, int)
    # Touchdown zone elevation should be a float when present
    if rw_end.touchdown_zone_elevation is not None:
        assert isinstance(rw_end.touchdown_zone_elevation, float)

    session.close()


def test_parsers_broad_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Broader assertions: counts and presence checks across parsed tables."""
    engine = _make_engine_and_create_schema(monkeypatch)

    # Run both parsers to populate DB
    apt_parser = import_module("aeroinfo.parsers.apt")
    nav_parser = import_module("aeroinfo.parsers.nav")
    # Reload both parser modules so their module-level Engine references are refreshed
    import importlib as _importlib

    _importlib.reload(apt_parser)
    _importlib.reload(nav_parser)

    apt_data = Path(__file__).resolve().parents[1] / "references" / "APT.txt"
    nav_data = Path(__file__).resolve().parents[1] / "references" / "NAV.txt"
    apt_parser.parse(str(apt_data))
    nav_parser.parse(str(nav_data))

    Session = sessionmaker(bind=engine)
    session = Session()

    from aeroinfo.database.models.apt import Airport, RunwayEnd
    from aeroinfo.database.models.nav import Navaid

    # There should be many airports parsed from the sample; assert a reasonable lower bound
    airport_count = session.query(Airport).count()
    assert airport_count > 100

    # At least one runway exists for ADK and overall
    adk_airport = session.query(Airport).filter_by(faa_id="ADK").first()
    assert adk_airport is not None
    runways_for_adk = list(adk_airport.runways)
    assert len(runways_for_adk) >= 1

    # At least one runway end across DB should have an elevation
    # Use SQLAlchemy 'is not' expression to filter non-null elevations
    runway_end_with_elev = (
        session.query(RunwayEnd).filter(RunwayEnd.elevation.isnot(None)).first()
    )
    assert runway_end_with_elev is not None

    # Navaids: assert a reasonable lower bound and that some have monitoring category set
    navaid_count = session.query(Navaid).count()
    assert navaid_count > 50
    some_monitored = (
        session.query(Navaid).filter(Navaid.monitoring_category.isnot(None)).first()
    )
    assert some_monitored is not None

    # And at least one navaid has a frequency string parsed
    some_with_freq = session.query(Navaid).filter(Navaid.frequency.isnot(None)).first()
    assert some_with_freq is not None

    session.close()


def test_nav_parser_merges_navaids(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the NAV parser against sample data and assert navaids were merged."""
    engine = _make_engine_and_create_schema(monkeypatch)

    nav_parser = import_module("aeroinfo.parsers.nav")
    # Reload nav parser so its module-level Engine reference is the patched one
    import importlib as _importlib

    _importlib.reload(nav_parser)

    data_path = Path(__file__).resolve().parents[1] / "references" / "NAV.txt"
    nav_parser.parse(str(data_path))

    Session = sessionmaker(bind=engine)
    session = Session()

    from aeroinfo.database.models.nav import Navaid

    # The sample NAV.txt includes BER (TACAN); assert it exists
    n = session.query(Navaid).filter_by(facility_id="BER").first()
    assert n is not None
    assert n.name is not None

    # Additional deterministic checks for NAV record
    # facility_type field contains 'TACAN'
    assert isinstance(n.facility_type, str)
    assert n.facility_type.strip().upper().startswith("TACAN")

    # Elevation for BER in the sample is 408.0
    assert isinstance(n.elevation, float)
    assert abs(n.elevation - 408.0) < 0.1

    # Frequency parsed (string) is present and equals 113.00 in sample
    assert isinstance(n.frequency, str)
    assert n.frequency.strip() == "113.00"

    # NAV parser only populated navaid tables; don't assert APT data here.
    session.close()
