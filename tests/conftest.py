"""Pytest configuration for Aeroinfo integration tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest


def _load_dotenv_file(env_path: Path) -> None:
    """
    Load simple KEY=VALUE pairs from an .env file into os.environ.

    This is intentionally small — it supports optional leading "export " and
    quoted values and ignores blank lines and comments. It's used to ensure
    tests can set DB-related environment variables before importing modules
    that may create a SQLAlchemy Engine at import time.
    """
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        line = line.removeprefix("export ")

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if value.startswith(("'", '"')) and value.endswith(("'", '"')):
            value = value[1:-1]

        os.environ.setdefault(key, value)


env_path = Path(__file__).resolve().parents[1] / ".env"
_load_dotenv_file(env_path)


if TYPE_CHECKING:
    from aeroinfo.database.models.apt import Airport, Runway, RunwayEnd
    from aeroinfo.database.models.nav import Navaid


# Note: env is already loaded above; avoid repeating the loader.


@pytest.fixture
def sample_airport() -> Airport:
    """In-memory Airport with a few demographic fields populated."""
    # Import at runtime after .env has been loaded to avoid creating the
    # Engine during module import when tests may not have DB env vars set.
    from aeroinfo.database import enums
    from aeroinfo.database.models.apt import Airport

    a = Airport(
        facility_site_number="SAMP00001",
        facility_type="AIRPORT",
        faa_id="SMP",
        name="Sample Field",
    )
    a.region = enums.FAARegionEnum.AGL
    a.state_code = "IL"
    a.city = "SAMPLE CITY"
    return a


@pytest.fixture
def sample_runway(sample_airport: Airport) -> Runway:
    """In-memory Runway attached to `sample_airport` with basic fields set."""
    from aeroinfo.database.models.apt import Runway

    rw = Runway(facility_site_number=sample_airport.facility_site_number, name="18/36")
    rw.length = 2500
    rw.width = 30
    rw.surface_type_condition = "ASPH"
    rw.airport = sample_airport
    return rw


@pytest.fixture
def sample_runway_end(sample_runway: Runway) -> RunwayEnd:
    """In-memory RunwayEnd with lighting enum set so serialization can be tested."""
    from aeroinfo.database import enums
    from aeroinfo.database.models.apt import RunwayEnd

    re = RunwayEnd(
        facility_site_number=sample_runway.facility_site_number,
        runway_name=sample_runway.name,
        id="36",
    )
    re.visual_glide_slope_indicators = enums.VisualGlideSlopeIndicatorEnum.V2L
    re.elevation = 700.0
    re.runway = sample_runway
    return re


@pytest.fixture
def sample_navaid() -> Navaid:
    """In-memory Navaid record useful for light-weight testing without DB."""
    from aeroinfo.database import enums
    from aeroinfo.database.models.nav import Navaid

    n = Navaid(facility_id="JOT", facility_type="VOR/DME", name="JOLIET")
    n.region = enums.FAARegionEnum.AGL
    n.frequency = "113.6"
    return n
