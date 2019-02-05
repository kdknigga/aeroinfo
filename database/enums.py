#!/usr/bin/env python

import enum

class OwnershipTypeEnum(enum.Enum):
    PU = "PUBLICLY OWNED"
    PR = "PRIVATELY OWNED"
    MA = "AIR FORCE OWNED"
    MN = "NAVY OWNED"
    MR = "ARMY OWNED"
    CG = "COAST GUARD OWNED"

class FacilityUseEnum(enum.Enum):
    PU = "OPEN TO THE PUBLIC"
    PR = "PRIVATE"

class DeterminationMethodEnum(enum.Enum):
    E = "ESTIMATED"
    S = "SURVEYED"

class RunwayMarkingsTypeEnum(enum.Enum):
    PIR = "PRECISION INSTRUMENT"
    NPI = "NONPRECISION INSTRUMENT"
    BSC = "BASIC"
    NRS = "NUMBERS ONLY"
    NSTD = "NONSTANDARD (OTHER THAN NUMBERS ONLY)"
    BUOY = "BUOYS (SEAPLANE BASE)"
    STOL = "SHORT TAKEOFF AND LANDING"
    NONE = "NONE"

class RunwayMarkingsConditionEnum(enum.Enum):
    G = "GOOD"
    F = "FAIR"
    P = "POOR"

class VisualGlideSlopeIndicatorEnum(enum.Enum):
    S2L = "2-BOX SAVASI ON LEFT SIDE OF RUNWAY"
    S2R = "2-BOX SAVASI ON RIGHT SIDE OF RUNWAY"
    V2L = "2-BOX VASI ON LEFT SIDE OF RUNWAY"
    V2R = "2-BOX VASI ON RIGHT SIDE OF RUNWAY"
    V4L = "4-BOX VASI ON LEFT SIDE OF RUNWAY"
    V4R = "4-BOX VASI ON RIGHT SIDE OF RUNWAY"
    V6L = "6-BOX VASI ON LEFT SIDE OF RUNWAY"
    V6R = "6-BOX VASI ON RIGHT SIDE OF RUNWAY"
    V12 = "12-BOX VASI ON BOTH SIDES OF RUNWAY"
    V16 = "16-BOX VASI ON BOTH SIDES OF RUNWAY"
    P2L = "2-LGT PAPI ON LEFT SIDE OF RUNWAY"
    P2R = "2-LGT PAPI ON RIGHT SIDE OF RUNWAY"
    P4L = "4-LGT PAPI ON LEFT SIDE OF RUNWAY"
    P4R = "4-LGT PAPI ON RIGHT SIDE OF RUNWAY"
    NSTD = "NONSTANDARD VASI SYSTEM"
    PVT = "PRIVATELY OWNED APPROACH SLOPE"
    VAS = "NON-SPECIFIC VASI SYSTEM"
    NONE = "NO APPROACH SLOPE LIGHT SYSTEM"
    N = "NO APPROACH SLOPE LIGHT SYSTEM"
    TRIL = "TRI-COLOR VASI ON LEFT SIDE OF RUNWAY"
    TRIR = "TRI-COLOR VASI ON RIGHT SIDE OF RUNWAY"
    PSIL = "PULSATING/STEADY BURNING VASI ON LEFT SIDE OF RUNWAY"
    PSIR = "PULSATING/STEADY BURNING VASI ON RIGHT SIDE OF RUNWAY"
    PNIL = "SYSTEM OF PANELS ON LEFT SIDE OF RUNWAY THAT MAY OR MAY NOT BE LIGHTED"
    PNIR = "SYSTEM OF PANELS ON RIGHT SIDE OF RUNWAY THAT MAY OR MAY NOT BE LIGHTED"

class RVREquipmentEnum(enum.Enum):
    T = "TOUCHDOWN"
    M = "MIDFIELD"
    R = "ROLLOUT"
    N = "NO RVR AVAILABLE"
    TM = "TOUCHDOWN AND MIDFIELD"
    TR = "TOUCHDOWN AND ROLLOUT"
    MR = "MIDFIELD AND ROLLOUT"
    TMR = "TOUCHDOWN, MIDFIELD, AND ROLLOUT"

class ControllingObjectMarkingEnum(enum.Enum):
    M = "MARKED"
    L = "LIGHTED"
    ML = "MARKED AND LIGHTED"
    LM = "MARKED AND LIGHTED"

class AirportStatusEnum(enum.Enum):
    CI = "CLOSED INDEFINITELY"
    CP = "CLOSED PERMANENTLY"
    O = "OPERATIONAL"
