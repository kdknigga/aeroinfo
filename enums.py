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
