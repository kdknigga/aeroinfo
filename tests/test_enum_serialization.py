"""Unit tests ensuring NASREnum-derived enums serialize as descriptions."""

from __future__ import annotations

from aeroinfo.database import enums
from aeroinfo.database.models.apt import Airport, RunwayEnd


def test_nasr_enum_str_and_description() -> None:
    """NASREnum should stringify to the code and expose a human description."""
    # The NASREnum __str__ returns the code/value
    assert str(enums.FAARegionEnum.AGL) == "AGL"
    # The description property returns the human-readable text
    assert enums.FAARegionEnum.AGL.description == "GREAT LAKES"


def test_airport_to_dict_uses_description() -> None:
    """Airport.to_dict should emit enum descriptions for demographic fields."""
    airport = Airport(
        facility_site_number="1", facility_type="AIRPORT", faa_id="TST", name="Test"
    )
    airport.region = enums.FAARegionEnum.AGL
    payload = airport.to_dict(include=["demographic"])
    assert payload["region"] == "GREAT LAKES"


def test_runway_end_to_dict_uses_description() -> None:
    """RunwayEnd.to_dict should emit enum descriptions for lighting fields."""
    rwend = RunwayEnd(facility_site_number="1", runway_name="09/27", id="09")
    rwend.visual_glide_slope_indicators = enums.VisualGlideSlopeIndicatorEnum.V2L
    payload = rwend.to_dict(include=["lighting"])
    assert (
        payload["visual_glide_slope_indicators"] == "2-BOX VASI ON LEFT SIDE OF RUNWAY"
    )
