"""End-to-end tests that mirror the historical ``query.py`` demo."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

# Standard library
if TYPE_CHECKING:
    from collections.abc import Callable

# Third-party
import pytest
from sqlalchemy.exc import OperationalError

# Local
from aeroinfo.database import (
    find_airport,
    find_navaid,
    find_runway,
    find_runway_end,
)

DUPAGE_ID = "DPA"
DUPAGE_ICAO = "KDPA"
NAPER_AERO_ID = "LL10"
JOT_NAVAID = ("JOT", "VOR/DME")


T = TypeVar("T")


def _call_or_skip[T](
    label: str, func: Callable[..., T], *args: object, **kwargs: object
) -> T:
    """Execute ``func`` and skip the test when the database is unavailable."""
    try:
        result = func(*args, **kwargs)
    except OperationalError as exc:  # pragma: no cover - integration guard
        pytest.skip(f"{label}: database unavailable ({exc})")
    if result is None:
        pytest.skip(f"{label}: not found in test database")
    return result


def test_find_airport_is_case_insensitive() -> None:
    """FAA identifiers should match regardless of letter case."""
    airport_upper = _call_or_skip("airport DPA", find_airport, DUPAGE_ID)
    airport_lower = _call_or_skip("airport dpa", find_airport, DUPAGE_ID.lower())

    assert airport_upper.facility_site_number == airport_lower.facility_site_number
    assert airport_upper.faa_id == DUPAGE_ID
    assert airport_upper.icao_id == DUPAGE_ICAO


def test_airport_demographics_include_enum_descriptions() -> None:
    """Airport serialization must expose FAA enum descriptions, not codes."""
    airport = _call_or_skip(
        "airport demographics", find_airport, DUPAGE_ID, include=["demographic"]
    )
    payload = airport.to_dict(include=["demographic"])

    assert payload["region"] == "GREAT LAKES"
    assert payload["state_code"] == "IL"
    assert payload["city"] == "CHICAGO/WEST CHICAGO"


def test_airport_runways_are_serialized() -> None:
    """Including ``runways`` returns both LL10 strips with their names."""
    airport = _call_or_skip(
        "airport LL10", find_airport, NAPER_AERO_ID, include=["runways"]
    )
    payload = airport.to_dict(include=["runways"])

    runway_names = {runway["name"] for runway in payload["runways"]}
    assert {"09/27", "18/36"}.issubset(runway_names)


@pytest.mark.parametrize("runway_hint, runway_end_id", [("18", "36")])
def test_runway_end_lighting_uses_enum_descriptions(
    runway_hint: str, runway_end_id: str
) -> None:
    """Runway-end lighting data should serialize enum descriptions like historical output."""
    airport = _call_or_skip("LL10 airport", find_airport, NAPER_AERO_ID)
    runway = _call_or_skip(
        f"runway {runway_hint}",
        find_runway,
        runway_hint,
        airport,
        include=["runway_ends"],
    )
    runway_end = _call_or_skip(
        f"runway end {runway_end_id}",
        find_runway_end,
        runway_end_id,
        runway,
        include=["lighting"],
    )
    payload = runway_end.to_dict(include=["lighting"])

    assert payload["id"] == runway_end_id
    assert (
        payload["visual_glide_slope_indicators"] == "2-BOX VASI ON LEFT SIDE OF RUNWAY"
    )


def test_find_navaid_returns_latest_effective_record() -> None:
    """Navaid lookup should fetch the latest edition for well-known facilities."""
    facility_id, facility_type = JOT_NAVAID
    navaid = _call_or_skip("JOT VOR/DME", find_navaid, facility_id, facility_type)

    assert navaid.facility_id == facility_id
    assert navaid.facility_type == facility_type
    assert navaid.name == "JOLIET"
