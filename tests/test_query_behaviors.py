"""Query behavior tests using in-memory SQLite populated by CSV parsers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aeroinfo.database import (
    find_airport,
    find_navaid,
    find_runway,
    find_runway_end,
    get_session,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine

DUPAGE_ID = "DPA"
DUPAGE_ICAO = "KDPA"
NAPER_AERO_ID = "LL10"
JOT_NAVAID = ("JOT", "VOR/DME")


def test_find_airport_is_case_insensitive(query_engine: Engine) -> None:
    """FAA identifiers should match regardless of letter case."""
    airport_upper = find_airport(DUPAGE_ID)
    assert airport_upper is not None
    airport_lower = find_airport(DUPAGE_ID.lower())
    assert airport_lower is not None

    assert airport_upper.facility_site_number == airport_lower.facility_site_number
    assert airport_upper.faa_id == DUPAGE_ID
    assert airport_upper.icao_id == DUPAGE_ICAO


def test_airport_demographics_include_enum_descriptions(query_engine: Engine) -> None:
    """Airport serialization must expose FAA enum descriptions, not codes."""
    airport = find_airport(DUPAGE_ID, include=["demographic"])
    assert airport is not None
    payload = airport.to_dict(include=["demographic"])

    assert payload["region"] == "GREAT LAKES"
    assert payload["state_code"] == "IL"
    assert payload["city"] == "CHICAGO/WEST CHICAGO"


def test_airport_runways_are_serialized(query_engine: Engine) -> None:
    """Including ``runways`` returns both LL10 strips with their names."""
    airport = find_airport(NAPER_AERO_ID, include=["runways"])
    assert airport is not None
    payload = airport.to_dict(include=["runways"])

    runway_names = {runway["name"] for runway in payload["runways"]}
    assert {"09/27", "18/36"}.issubset(runway_names)


@pytest.mark.parametrize("runway_hint, runway_end_id", [("18", "36")])
def test_runway_end_lighting_uses_enum_descriptions(
    query_engine: Engine, runway_hint: str, runway_end_id: str
) -> None:
    """Runway-end lighting data should serialize enum descriptions like historical output."""
    airport = find_airport(NAPER_AERO_ID)
    assert airport is not None
    runway = find_runway(runway_hint, airport, include=["runway_ends"])
    assert runway is not None
    runway_end = find_runway_end(runway_end_id, runway, include=["lighting"])
    assert runway_end is not None
    payload = runway_end.to_dict(include=["lighting"])

    assert payload["id"] == runway_end_id
    assert (
        payload["visual_glide_slope_indicators"] == "2-BOX VASI ON LEFT SIDE OF RUNWAY"
    )


def test_find_navaid_returns_latest_effective_record(query_engine: Engine) -> None:
    """Navaid lookup should fetch the latest edition for well-known facilities."""
    facility_id, facility_type = JOT_NAVAID
    navaid = find_navaid(facility_id, facility_type)
    assert navaid is not None

    assert navaid.facility_id == facility_id
    assert navaid.facility_type == facility_type
    assert navaid.name == "JOLIET"


def test_lookup_helpers_can_share_sessions(query_engine: Engine) -> None:
    """Sharing a single Session should work for chained lookups."""
    session = get_session()
    try:
        airport = find_airport(NAPER_AERO_ID, session=session)
        assert airport is not None
        runway = find_runway("18", airport, session=session)
        assert runway is not None
    finally:
        session.close()
