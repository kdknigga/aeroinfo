#!/usr/bin/env python

# ruff: noqa: E741

"""
Enumerations used by the database models.

These enums model the various coded fields found in NASR/Aeronautical
datasets and are intentionally literal mappings to source values.
"""

import enum
import logging

logger = logging.getLogger(__name__)


class NASREnum(str, enum.Enum):
    """Enum that stores the FAA code as the value with a human description."""

    def __new__(cls, code: str, description: str) -> "NASREnum":  # type: ignore[override]
        """Create the enum member storing the code as the value and description."""
        obj = str.__new__(cls, code)
        obj._value_ = code  # type: ignore[attr-defined]
        obj._description_: str = description
        return obj

    @property
    def description(self) -> str:
        """Return the FAA description for this enum entry."""
        return self._description_

    def __str__(self) -> str:
        """Return the stored FAA code when coerced to a string."""
        return self.value


class OwnershipTypeEnum(NASREnum):
    """Ownership type of an airport."""

    PU = ("PU", "PUBLICLY OWNED")
    PR = ("PR", "PRIVATELY OWNED")
    MA = ("MA", "AIR FORCE OWNED")
    MN = ("MN", "NAVY OWNED")
    MR = ("MR", "ARMY OWNED")
    CG = ("CG", "COAST GUARD OWNED")


class FacilityUseEnum(NASREnum):
    """Public/private use classification for a facility."""

    PU = ("PU", "OPEN TO THE PUBLIC")
    PR = ("PR", "PRIVATE")


class DeterminationMethodEnum(NASREnum):
    """Method used to determine a measurement (surveyed vs estimated)."""

    E = ("E", "ESTIMATED")
    S = ("S", "SURVEYED")


class RunwayMarkingsTypeEnum(NASREnum):
    """Type of markings present on a runway."""

    PIR = ("PIR", "PRECISION INSTRUMENT")
    NPI = ("NPI", "NONPRECISION INSTRUMENT")
    BSC = ("BSC", "BASIC")
    NRS = ("NRS", "NUMBERS ONLY")
    NSTD = ("NSTD", "NONSTANDARD (OTHER THAN NUMBERS ONLY)")
    BUOY = ("BUOY", "BUOYS (SEAPLANE BASE)")
    STOL = ("STOL", "SHORT TAKEOFF AND LANDING")
    NONE = ("NONE", "NONE")


class RunwayMarkingsConditionEnum(NASREnum):
    """Condition of runway markings."""

    G = ("G", "GOOD")
    F = ("F", "FAIR")
    P = ("P", "POOR")


class VisualGlideSlopeIndicatorEnum(NASREnum):
    """Visual glide slope / approach slope light systems."""

    S2L = ("S2L", "2-BOX SAVASI ON LEFT SIDE OF RUNWAY")
    S2R = ("S2R", "2-BOX SAVASI ON RIGHT SIDE OF RUNWAY")
    V2L = ("V2L", "2-BOX VASI ON LEFT SIDE OF RUNWAY")
    V2R = ("V2R", "2-BOX VASI ON RIGHT SIDE OF RUNWAY")
    V4L = ("V4L", "4-BOX VASI ON LEFT SIDE OF RUNWAY")
    V4R = ("V4R", "4-BOX VASI ON RIGHT SIDE OF RUNWAY")
    V6L = ("V6L", "6-BOX VASI ON LEFT SIDE OF RUNWAY")
    V6R = ("V6R", "6-BOX VASI ON RIGHT SIDE OF RUNWAY")
    V12 = ("V12", "12-BOX VASI ON BOTH SIDES OF RUNWAY")
    V16 = ("V16", "16-BOX VASI ON BOTH SIDES OF RUNWAY")
    P2L = ("P2L", "2-LGT PAPI ON LEFT SIDE OF RUNWAY")
    P2R = ("P2R", "2-LGT PAPI ON RIGHT SIDE OF RUNWAY")
    P4L = ("P4L", "4-LGT PAPI ON LEFT SIDE OF RUNWAY")
    P4R = ("P4R", "4-LGT PAPI ON RIGHT SIDE OF RUNWAY")
    NSTD = ("NSTD", "NONSTANDARD VASI SYSTEM")
    PVT = ("PVT", "PRIVATELY OWNED APPROACH SLOPE")
    VAS = ("VAS", "NON-SPECIFIC VASI SYSTEM")
    NONE = ("NONE", "NO APPROACH SLOPE LIGHT SYSTEM")
    N = ("N", "NO APPROACH SLOPE LIGHT SYSTEM")
    TRIL = ("TRIL", "TRI-COLOR VASI ON LEFT SIDE OF RUNWAY")
    TRIR = ("TRIR", "TRI-COLOR VASI ON RIGHT SIDE OF RUNWAY")
    PSIL = ("PSIL", "PULSATING/STEADY BURNING VASI ON LEFT SIDE OF RUNWAY")
    PSIR = ("PSIR", "PULSATING/STEADY BURNING VASI ON RIGHT SIDE OF RUNWAY")
    PNIL = (
        "PNIL",
        "SYSTEM OF PANELS ON LEFT SIDE OF RUNWAY THAT MAY OR MAY NOT BE LIGHTED",
    )
    PNIR = (
        "PNIR",
        "SYSTEM OF PANELS ON RIGHT SIDE OF RUNWAY THAT MAY OR MAY NOT BE LIGHTED",
    )


class RVREquipmentEnum(NASREnum):
    """Runway visual range (RVR) equipment locations."""

    T = ("T", "TOUCHDOWN")
    M = ("M", "MIDFIELD")
    R = ("R", "ROLLOUT")
    N = ("N", "NO RVR AVAILABLE")
    TM = ("TM", "TOUCHDOWN AND MIDFIELD")
    TR = ("TR", "TOUCHDOWN AND ROLLOUT")
    MR = ("MR", "MIDFIELD AND ROLLOUT")
    TMR = ("TMR", "TOUCHDOWN, MIDFIELD, AND ROLLOUT")


class ControllingObjectMarkingEnum(NASREnum):
    """Marking and lighting status for a controlling object."""

    M = ("M", "MARKED")
    L = ("L", "LIGHTED")
    ML = ("ML", "MARKED AND LIGHTED")
    LM = ("LM", "MARKED AND LIGHTED")


class AirportStatusEnum(NASREnum):
    """Operational or closed status of an airport."""

    CI = ("CI", "CLOSED INDEFINITELY")
    CP = ("CP", "CLOSED PERMANENTLY")
    O = ("O", "OPERATIONAL")


class AirportInspectionMethodEnum(NASREnum):
    """Method used to inspect the airport."""

    F = ("F", "FEDERAL")
    S = ("S", "STATE")
    C = ("C", "CONTRACTOR")
    O = ("O", "5010-1 PUBLIC USE MAILOUT PROGRAM")  # Source data uses 1
    T = ("T", "5010-2 PRIVATE USE MAILOUT PROGRAM")  # Source data uses 2


class AgencyPerformingInspectionEnum(NASREnum):
    """Agency or organization performing an inspection."""

    F = ("F", "FAA AIRPORTS FIELD PERSONNEL")
    S = ("S", "STATE AERONAUTICAL PERSONNEL")
    C = ("C", "PRIVATE CONTRACT PERSONNEL")
    N = ("N", "OWNER")


class SegmentedCircleEnum(NASREnum):
    """Segmented circle presence / lighting."""

    Y = ("Y", "YES")
    N = ("N", "NO")
    NONE = ("NONE", "NONE")
    YL = ("YL", "YES, LIGHTED (Y-L)")


# CLEAR changed to WHITE starting Dec 1, 2022
class BeaconColorEnum(NASREnum):
    """Color coding for airport beacons."""

    WG = ("WG", "WHITE-GREEN (LIGHTED LAND AIRPORT)")
    WY = ("WY", "WHITE-YELLOW (LIGHTED SEAPLANE BASE)")
    WGY = ("WGY", "WHITE-GREEN-YELLOW (HELIPORT)")
    SWG = ("SWG", "SPLIT-WHITE-GREEN (LIGHTED MILITARY AIRPORT)")
    W = ("W", "WHITE (UNLIGHTED LAND AIRPORT)")
    Y = ("Y", "YELLOW (UNLIGHTED SEAPLANE BASE)")
    G = ("G", "GREEN (LIGHTED LAND AIRPORT)")
    N = ("N", "NONE")


class FAARegionEnum(NASREnum):
    """FAA region codes."""

    AAL = ("AAL", "ALASKA")
    ACE = ("ACE", "CENTRAL")
    AEA = ("AEA", "EASTERN")
    AGL = ("AGL", "GREAT LAKES")
    AIN = ("AIN", "INTERNATIONAL")
    ANE = ("ANE", "NEW ENGLAND")
    ANM = ("ANM", "NORTHWEST MOUNTAIN")
    ASO = ("ASO", "SOUTHERN")
    ASW = ("ASW", "SOUTHWEST")
    AWP = ("AWP", "WESTERN-PACIFIC")


class NavaidPositionSurveyAccuracyEnum(NASREnum):
    """Position survey accuracy categories for navaids."""

    ZERO = ("ZERO", "UNKNOWN")
    ONE = ("ONE", "DEGREE")
    TWO = ("TWO", "10 MINUTES")
    THREE = ("THREE", "1 MINUTE")
    FOUR = ("FOUR", "10 SECONDS")
    FIVE = ("FIVE", "1 SECOND OR BETTER")
    SIX = ("SIX", "NOS")
    SEVEN = ("SEVEN", "3RD ORDER TRIANGULATION")


class NavaidMonitoringCategoryEnum(NASREnum):
    """Monitoring category descriptions for navaids."""

    ONE = (
        "ONE",
        "1 - INTERNAL MONITORING PLUS A STATUS INDICATOR INSTALLED AT CONTROL POINT. (REVERTS TO A TEMPORARY CATEGORY 3 STATUS WHEN THE CONTROL POINT IS NOT MANNED.)",
    )
    TWO = (
        "TWO",
        "2 - INTERNAL MONITORING WITH STATUS INDICATOR AT CONTROL POINT INOPERATIVE BUT PILOT REPORTS INDICATE FACILITY IS OPERATING NORMALLY.  (THIS IS A TEMPORARY SITUATION THAT REQUIRES NO PROCEDURAL ACTION.)",
    )
    THREE = (
        "THREE",
        "3 - INTERNAL MONITORING ONLY. STATUS INDICATOR NON INSTALLED AT CONTROL POINT.",
    )
    FOUR = (
        "FOUR",
        "4 - INTERNAL MONITOR NOT INSTALLED. REMOTE STATUS INDICATOR PROVIDED AT CONTROL POINT.  THIS CATEGORY IS APPLICABLE ONLY TO NON-DIRECTIONAL BEACONS.",
    )


class StandardServiceVolumeEnum(NASREnum):
    """Service volume categories for navigation aids."""

    T = ("T", "TERMINAL")
    L = ("L", "LOW ALTITUDE")
    H = ("H", "HIGH ALTITUDE")
    VH = ("VH", "VOR HIGH")
    VL = ("VL", "VOR LOW")
    DH = ("DH", "DME HIGH")
    DL = ("DL", "DME LOW")


class YesNoNullEnum(NASREnum):
    """Simple yes/no/null tri-state enum."""

    Y = ("Y", "YES")
    N = ("N", "NO")
    NULL = ("NULL", "NULL")


class FanMarkerTypeEnum(NASREnum):
    """Types of fan marker beacons."""

    BONE = ("BONE", "BONE")
    ELLIPTICAL = ("ELLIPTICAL", "ELLIPTICAL")


class VORReceiverCheckpointAirGroundCodeEnum(NASREnum):
    """Air/ground code for VOR receiver checkpoints."""

    A = ("A", "AIR")
    G = ("G", "GROUND")
    G1 = ("G1", "GROUND ONE")
