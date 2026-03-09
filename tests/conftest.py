"""
Pytest configuration and shared fixtures for Aeroinfo integration tests.

Provides CURATED_AIRPORTS (107) and CURATED_NAVAIDS (5) lists used by
snapshot tests, plus csv_apt_engine and csv_nav_engine fixtures that parse
CSV data into in-memory SQLite databases.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine
from syrupy.extensions.json import JSONSnapshotExtension

# Register ORM models with Base.metadata (side-effect imports).
# These MUST run at module level, NOT inside TYPE_CHECKING.
import aeroinfo.database.models.apt
import aeroinfo.database.models.nav  # noqa: F401


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
    from collections.abc import Generator

    from sqlalchemy.engine import Engine
    from syrupy.assertion import SnapshotAssertion

    from aeroinfo.database.models.apt import Airport, Runway, RunwayEnd
    from aeroinfo.database.models.nav import Navaid


_REFERENCES_DIR = Path(__file__).resolve().parents[1] / "references"
_TXT_DATA_DIR = _REFERENCES_DIR / "2026-02-19"
_APT_TXT_FILE = _TXT_DATA_DIR / "APT.txt"
_NAV_TXT_FILE = _TXT_DATA_DIR / "NAV.txt"
_CSV_DATA_DIR = _REFERENCES_DIR / "2026-02-19" / "CSV_Data"

CURATED_AIRPORTS: list[str] = [
    "1R8",
    "52F",
    "8I3",
    "ANC",
    "APA",
    "ARR",
    "ATL",
    "AUS",
    "AWO",
    "BDN",
    "BFI",
    "BJC",
    "BNA",
    "BOS",
    "BWI",
    "CHD",
    "CLT",
    "CMA",
    "CNO",
    "CRG",
    "CRQ",
    "CVG",
    "DAB",
    "DAL",
    "DCA",
    "DCU",
    "DEN",
    "DFW",
    "DPA",
    "DTO",
    "DTW",
    "DVT",
    "EDF",
    "EUL",
    "EWR",
    "FFZ",
    "FIN",
    "FLL",
    "FPR",
    "FRG",
    "FXE",
    "GFK",
    "HIO",
    "HNL",
    "HOU",
    "HPN",
    "IAD",
    "IAH",
    "IND",
    "ISM",
    "IWA",
    "JFK",
    "LAL",
    "LAS",
    "LAX",
    "LGA",
    "LGB",
    "LL10",
    "LVK",
    "MCI",
    "MCO",
    "MDW",
    "MEM",
    "MIA",
    "MSP",
    "MSY",
    "MYF",
    "OAK",
    "OGG",
    "OKK",
    "ORD",
    "ORF",
    "OSH",
    "PAO",
    "PDK",
    "PDX",
    "PHL",
    "PHX",
    "PIT",
    "PMP",
    "PRC",
    "PVU",
    "RDU",
    "RFD",
    "RHV",
    "RVS",
    "S50",
    "SAN",
    "SDF",
    "SDL",
    "SEA",
    "SEE",
    "SFB",
    "SFO",
    "SGJ",
    "SJC",
    "SJU",
    "SLC",
    "SMF",
    "SMO",
    "SNA",
    "STL",
    "TMB",
    "TPA",
    "VGT",
    "VNY",
    "VRB",
]

CURATED_NAVAIDS: list[tuple[str, str]] = [
    ("AST", "VOR/DME"),
    ("BER", "TACAN"),
    ("CZF", "NDB"),
    ("FAI", "VORTAC"),
    ("EDN", "VOR"),
]


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


@pytest.fixture(scope="module")
def csv_apt_engine() -> Generator[Engine]:
    """Parse 2026-02-19 CSV APT data into in-memory SQLite once per module."""
    if not _CSV_DATA_DIR.is_dir():
        pytest.fail(
            f"CSV data directory not found: {_CSV_DATA_DIR}\n"
            "Cannot run CSV tests without reference CSV data."
        )
    import aeroinfo.database as db
    from aeroinfo.database.base import Base

    engine = create_engine("sqlite:///:memory:")
    original_inner = db.Engine._engine
    db.Engine._engine = engine

    Base.metadata.create_all(engine)

    import aeroinfo.parsers.apt_csv as csv_parser

    importlib.reload(csv_parser)
    csv_parser.parse(str(_CSV_DATA_DIR))

    yield engine
    db.Engine._engine = original_inner


@pytest.fixture(scope="module")
def csv_nav_engine() -> Generator[Engine]:
    """Parse 2026-02-19 CSV NAV data into in-memory SQLite once per module."""
    if not _CSV_DATA_DIR.is_dir():
        pytest.fail(
            f"CSV data directory not found: {_CSV_DATA_DIR}\n"
            "Cannot run CSV tests without reference CSV data."
        )
    import aeroinfo.database as db
    from aeroinfo.database.base import Base

    engine = create_engine("sqlite:///:memory:")
    original_inner = db.Engine._engine
    db.Engine._engine = engine

    Base.metadata.create_all(engine)

    import aeroinfo.parsers.nav_csv as nav_csv_parser

    importlib.reload(nav_csv_parser)
    nav_csv_parser.parse(str(_CSV_DATA_DIR))

    yield engine
    db.Engine._engine = original_inner


@pytest.fixture(scope="module")
def query_engine() -> Generator[Engine]:
    """Parse CSV APT+NAV data into in-memory SQLite for query behavior tests."""
    if not _CSV_DATA_DIR.is_dir():
        pytest.fail(
            f"CSV data directory not found: {_CSV_DATA_DIR}\n"
            "Cannot run CSV tests without reference CSV data."
        )
    import aeroinfo.database as db
    from aeroinfo.database.base import Base

    engine = create_engine("sqlite:///:memory:")
    original_inner = db.Engine._engine
    db.Engine._engine = engine

    Base.metadata.create_all(engine)

    import aeroinfo.parsers.apt_csv as apt_csv_parser
    import aeroinfo.parsers.nav_csv as nav_csv_parser

    importlib.reload(apt_csv_parser)
    importlib.reload(nav_csv_parser)
    apt_csv_parser.parse(str(_CSV_DATA_DIR))
    nav_csv_parser.parse(str(_CSV_DATA_DIR))

    db.invalidate_caches()

    yield engine

    db.invalidate_caches()
    db.Engine._engine = original_inner


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Override default syrupy snapshot extension to use JSON format globally."""
    return snapshot.use_extension(JSONSnapshotExtension)
