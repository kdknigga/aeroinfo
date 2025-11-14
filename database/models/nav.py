#!/usr/bin/env python
"""Database models for navigation aids (navaids)."""

import datetime
import logging

from sqlalchemy import Date, Enum, Float, Integer, String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.schema import ForeignKeyConstraint

from database import enums
from database.base import Base

logger = logging.getLogger(__name__)


class Navaid(Base):
    """Model for a navigation aid (NAV1 record)."""

    __tablename__ = "navaids"

    ########
    # 'NAV1' RECORD TYPE - BASE DATA
    ########
    # ****************NOTE:  Current unique key for this file is: 3 letter id + type + city
    ## NOTE: NOTE: Despite the above note, every other record type only seems to link back to NAV1 via facility ID and facility type.
    ##             And postgres doesn't seem to like navaids having 3 primary key columns but other tables only using 2 for foreign keys
    ##             (though, sqlite3 doesn't seem to care).  As such, we'll only be using facility_id and facility_type as primary keys.

    # L AN 0004 00005  DLID    NAVAID FACILITY IDENTIFIER
    facility_id: Mapped[str] = mapped_column(String(4), primary_key=True)
    # L AN 0020 00009  DLID    NAVAID FACILITY TYPE
    facility_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    # L AN 0004 00029  DLID    OFFICIAL NAVAID FACILITY IDENTIFIER
    official_facility_id: Mapped[str | None] = mapped_column(String(4))

    # ADMINISTRATIVE   DATA
    # L AN 0010 00033  N/A     EFFECTIVE DATE
    effective_date: Mapped[datetime.date | None] = mapped_column(Date)
    # L AN 0030 00043  N8      NAME OF NAVAID.
    name: Mapped[str | None] = mapped_column(String(30))
    # L AN 0040 00073  N1      CITY ASSOCIATED WITH THE NAVAID.
    city: Mapped[str | None] = mapped_column(String(40))
    # L AN 0030 00113  N2      STATE NAME WHERE ASSOCIATED CITY IS LOCATED
    state_name: Mapped[str | None] = mapped_column(String(30))
    # L AN 0002 00143  N2S     STATE POST OFFICE CODE WHERE ASSOCIATED CITY IS LOCATED.
    state_code: Mapped[str | None] = mapped_column(String(2))
    # L AN 0003 00145  N20     FAA REGION RESPONSIBLE FOR NAVAID
    region: Mapped[enums.FAARegionEnum | None] = mapped_column(
        Enum(enums.FAARegionEnum)
    )
    # L AN 0030 00148  N3      COUNTRY NAVAID LOCATED IF OTHER THAN U.S
    country: Mapped[str | None] = mapped_column(String(30))
    # L AN 0002 00178  N3S     COUNTRY POST OFFICE CODE NAVAID LOCATED IF OTHER THAN U.S.
    country_code: Mapped[str | None] = mapped_column(String(2))
    # L AN 0050 00180  N10     NAVAID OWNER NAME
    owners_name: Mapped[str | None] = mapped_column(String(50))
    # L AN 0050 00230  N12     NAVAID OPERATOR NAME
    operators_name: Mapped[str | None] = mapped_column(String(50))
    # L AN 0001 00280  N47     COMMON SYSTEM USAGE (Y OR N)
    common_system_usage: Mapped[str | None] = mapped_column(String(1))
    # L AN 0001 00281  N48     NAVAID PUBLIC USE
    public_use: Mapped[str | None] = mapped_column(String(1))
    # L AN 0011 00282  N28     CLASS OF NAVAID.
    navaid_class: Mapped[str | None] = mapped_column(String(11))
    # L AN 0011 00293  N52     HOURS OF OPERATION OF NAVAID (EX:  0800-2400)
    hours_of_operation: Mapped[str | None] = mapped_column(String(11))
    # L AN 0004 00304  N91     IDENTIFIER OF ARTCC WITH HIGH ALTITUDE BOUNDARY THAT THE NAVAID FALLS WITHIN.
    high_altitude_artcc_id: Mapped[str | None] = mapped_column(String(4))
    # L AN 0030 00308  N91     NAME OF ARTCC WITH HIGH ALTITUDE BOUNDARY THAT THE NAVAID FALLS WITHIN.
    high_altitude_artcc_name: Mapped[str | None] = mapped_column(String(30))
    # L AN 0004 00338  N94     IDENTIFIER OF ARTCC WITH LOW ALTITUDE BOUNDARY THAT THE NAVAID FALLS WITHIN.
    low_altitude_artcc_id: Mapped[str | None] = mapped_column(String(4))
    # L AN 0030 00342  N94     NAME OF ARTCC WITH LOW ALTITUDE BOUNDARY THAT THE NAVAID FALLS WITHIN.
    low_altitude_artcc_name: Mapped[str | None] = mapped_column(String(30))

    # GEOGRAPHICAL POSITION DATA
    # L AN 0014 00372  N4      NAVAID LATITUDE (FORMATTED)
    latitude_dms: Mapped[str | None] = mapped_column(String(14))
    # L AN 0011 00386  N4S     NAVAID LATITUDE (ALL SECONDS)
    latitude_secs: Mapped[str | None] = mapped_column(String(11))
    # L AN 0014 00397  N5      NAVAID LONGITUDE (FORMATTED)
    longitude_dms: Mapped[str | None] = mapped_column(String(14))
    # L AN 0011 00411  N5S     NAVAID LONGITUDE (ALL SECONDS)
    longitude_secs: Mapped[str | None] = mapped_column(String(11))
    # L AN 0001 00422  N38     LATITUDE/LONGITUDE SURVERY ACCURACY
    coords_survey_accuracy: Mapped[enums.NavaidPositionSurveyAccuracyEnum | None] = (
        mapped_column(Enum(enums.NavaidPositionSurveyAccuracyEnum))
    )
    # L AN 0014 00423  N21     LATITUDE OF TACAN PORTION OF VORTAC WHEN TACAN IS NOT SITED WITH VOR (FORMATTED)
    tacan_only_latitude_dms: Mapped[str | None] = mapped_column(String(14))
    # L AN 0011 00437  N21S    LATITUDE OF TACAN PORTION OF VORTAC WHEN TACAN IS NOT SITED WITH VOR (ALL SECONDS)
    tacan_only_latitude_secs: Mapped[str | None] = mapped_column(String(11))
    # L AN 0014 00448  N22     LONGITUDE OF TACAN PORTION OF VORTAC WHEN TACAN IS NOT SITED WITH VOR (FORMATTED)
    tacan_only_longitude_dms: Mapped[str | None] = mapped_column(String(14))
    # L AN 0011 00462  N22S    LONGITUDE OF TACAN PORTION OF VORTAC WHEN TACAN IS NOT SITED WITH VOR (ALL SECONDS)
    tacan_only_longitude_secs: Mapped[str | None] = mapped_column(String(11))
    # R AN 0007 00473  N37     ELEVATION IN TENTH OF A FOOT (MSL)
    elevation: Mapped[float | None] = mapped_column(Float(1))
    # R AN 0005 00480  N45      MAGNETIC VARIATION DEGREES   (00-99) FOLLOWED BY MAGNETIC VARIATION DIRECTION (E,W) (EX: 8080W)
    mag_variation: Mapped[str | None] = mapped_column(String(5))
    # R AN 0004 00485  N45S     MAGNETIC VARIATION EPOCH YEAR  (00-99)
    mag_variation_year: Mapped[int | None] = mapped_column(Integer)

    # FACILITIES/FEATURES OF NAVAID
    # L AN 0003 00489 N33     SIMULTANEOUS VOICE FEATURE (Y,N, OR NULL)
    simultaneous_voice: Mapped[enums.YesNoNullEnum | None] = mapped_column(
        Enum(enums.YesNoNullEnum)
    )
    # R  N 0004 00492 N34     POWER OUTPUT (IN WATTS)
    power_output_watts: Mapped[int | None] = mapped_column(Integer)
    # L AN 0003 00496 N35     AUTOMATIC VOICE IDENTIFICATION FEATURE (Y, N, OR NULL)
    automatic_voice_id: Mapped[enums.YesNoNullEnum | None] = mapped_column(
        Enum(enums.YesNoNullEnum)
    )
    # L AN 0001 00499  N36     MONITORING CATEGORY
    monitoring_category: Mapped[enums.NavaidMonitoringCategoryEnum | None] = (
        mapped_column(Enum(enums.NavaidMonitoringCategoryEnum))
    )
    # L AN 0030 00500 N23     RADIO VOICE CALL (NAME) (EX: WASHINGTON RADIO)
    radio_voice_call_name: Mapped[str | None] = mapped_column(String(30))
    # L AN 0004 00530 N24     CHANNEL (TACAN)  NAVAID TRANSMITS ON (EX : 51X)
    tacan_channel: Mapped[str | None] = mapped_column(String(4))
    # R  N 0006 00534 N25     FREQUENCY THE NAVAID TRANSMITS ON (EXCEPT TACAN) (EX:  110.60 298)
    frequency: Mapped[str | None] = mapped_column(String(6))
    # R  N 0024 00540 N75     TRANSMITTED FAN MARKER/MARINE RADIO BEACON IDENTIFIER  EX: (DOT,DASH SEQUENCE USED)
    transmitted_id: Mapped[str | None] = mapped_column(String(24))
    # L AN 0010 00564 N76     FAN MARKER TYPE (BONE OR ELLIPTICAL)
    fan_marker_type: Mapped[enums.FanMarkerTypeEnum | None] = mapped_column(
        Enum(enums.FanMarkerTypeEnum)
    )
    # L AN 0003 00574 N77     TRUE BEARING OF MAJOR AXIS OF FAN MARKER EX: IN WHOLE DEGREES (001-360)
    fan_marker_true_bearing: Mapped[int | None] = mapped_column(Integer)
    # L AN 0002 00577 N29     VOR STANDARD SERVICE VOLUME
    vor_service_volume: Mapped[enums.StandardServiceVolumeEnum | None] = mapped_column(
        Enum(enums.StandardServiceVolumeEnum)
    )
    # L AN 0002 00579 NA      DME STANDARD SERVICE VOLUME
    dme_service_volume: Mapped[enums.StandardServiceVolumeEnum | None] = mapped_column(
        Enum(enums.StandardServiceVolumeEnum)
    )
    # L AN 0003 00581 N30     LOW ALTITUDE FACILITY USED IN HIGH STRUCTURE (Y, N, OR NULL)
    low_altitude_facility_used_in_high_structure: Mapped[enums.YesNoNullEnum | None] = (
        mapped_column(Enum(enums.YesNoNullEnum))
    )
    # L AN 0003 00584 N31     NAVAID Z MARKER AVAILABLE (Y, N, OR NULL)
    z_marker_available: Mapped[enums.YesNoNullEnum | None] = mapped_column(
        Enum(enums.YesNoNullEnum)
    )
    # L AN 0009 00587 N32     TRANSCRIBED WEATHER BROADCAST HOURS (TWEB) (EX: 0500-2200)
    tweb_hours: Mapped[str | None] = mapped_column(String(9))
    # L AN 0020 00596 N95     TRANSCRIBED WEATHER BROADCAST PHONE NUMBER
    tweb_phone_number: Mapped[str | None] = mapped_column(String(20))
    # L AN 0004 00616 N49S    ASSOCIATED/CONTROLLING FSS (IDENT)
    fss_id: Mapped[str | None] = mapped_column(String(4))
    # L AN 0030 00620 N49     ASSOCIATED/CONTROLLING FSS (NAME)
    fss_name: Mapped[str | None] = mapped_column(String(30))
    # L AN 0100 00650 F15     HOURS OF OPERATION OF CONTROLLING FSS (EX: 0800-2400)
    fss_hours_of_operation: Mapped[str | None] = mapped_column(String(100))
    # L AN 0004 00750 N49B    NOTAM ACCOUNTABILITY CODE (IDENT)
    notam_accountability_code: Mapped[str | None] = mapped_column(String(4))

    # CHARTING  DATA
    # L AN 0016 00754 N80     QUADRANT IDENTIFICATION AND RANGE LEG BEARING (LFR ONLY) (EX: 151N190A311N036A)
    quadrant_id_and_range_leg_bearing: Mapped[str | None] = mapped_column(String(16))

    # NAVAID STATUS
    # L AN 0030 00770  N41,N42    NAVIGATION AID STATUS
    navaid_status: Mapped[str | None] = mapped_column(String(30))

    # PITCH, CATCH, AND SUA/ATCAA FLAGS
    # L AN 0001 00800  N/A    PITCH FLAG (Y OR N)
    pitch: Mapped[enums.YesNoNullEnum | None] = mapped_column(Enum(enums.YesNoNullEnum))
    # L AN 0001 00801  N/A    CATCH FLAG (Y OR N)
    catch: Mapped[enums.YesNoNullEnum | None] = mapped_column(Enum(enums.YesNoNullEnum))
    # L AN 0001 00802  N/A    SUA/ATCAA FLAG (Y OR N)
    sua_atcaa: Mapped[enums.YesNoNullEnum | None] = mapped_column(
        Enum(enums.YesNoNullEnum)
    )
    # L AN 0001 00803  N/A    NAVAID RESTRICTION FLAG (Y, N, OR NULL)
    navaid_restriction: Mapped[enums.YesNoNullEnum | None] = mapped_column(
        Enum(enums.YesNoNullEnum)
    )
    # L AN 0001 00804  N/A    HIWAS FLAG (Y, N, OR NULL)
    hiwas: Mapped[enums.YesNoNullEnum | None] = mapped_column(Enum(enums.YesNoNullEnum))
    # L AN 0001 00805  N/A    TRANSCRIBED WEATHER BROADCAST (TWEB) RESTRICTION (Y, N, OR NULL)
    tweb: Mapped[enums.YesNoNullEnum | None] = mapped_column(Enum(enums.YesNoNullEnum))

    remarks = relationship("Remark", back_populates="navaid")
    airspace_fixes = relationship("AirspaceFix", back_populates="navaid")
    holding_patterns = relationship("HoldingPattern", back_populates="navaid")
    fan_markers = relationship("FanMarker", back_populates="navaid")
    vor_receiver_checkpoints = relationship(
        "VORReceiverCheckpoint", back_populates="navaid"
    )

    def __repr__(self) -> str:
        """Return a short representation of the Navaid."""
        return f"<Navaid(name={self.name}, id={self.facility_id}, type={self.facility_type})>"


class Remark(Base):
    """Remark lines associated with a Navaid (NAV2)."""

    __tablename__ = "navaid_remarks"

    ########
    # 'NAV2' RECORD TYPE - NAVAID REMARKS
    ########

    # L AN 0004 00005  DLID    NAVAID FACILITY IDENTIFIER
    facility_id: Mapped[str] = mapped_column(String(4), primary_key=True)
    # L AN 0020 00009  DLID    NAVAID FACITITY TYPE (EX: VOR/DME) (SEE NAV1 RECORD FOR DESCRIPTION)
    facility_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    # L AN 0600 00029  RMRKS   NAVAID REMARKS. FREE FORM TEXT
    remark: Mapped[str] = mapped_column(String(600), primary_key=True)
    # L AN 0177 00629  N/A     FILLER.

    __table_args__ = (
        ForeignKeyConstraint(
            [facility_id, facility_type], [Navaid.facility_id, Navaid.facility_type]
        ),
        {},
    )

    navaid = relationship("Navaid", back_populates="remarks")

    def __repr__(self) -> str:
        """Return a short representation of the Remark."""
        return f'<Remark(id={self.facility_id}, type={self.facility_type}, remark="{self.remark[:16]}")>'


class AirspaceFix(Base):
    """Airspace fixes associated with a Navaid (NAV3)."""

    __tablename__ = "navaid_airspace_fixes"

    ########
    # 'NAV3' RECORD TYPE - COMPULSORY AND NON-COMPULSORY AIRSPACE FIXES ASSOCIATED WITH NAVAID
    ########

    # L AN 0004 00005  DLID    NAVAID FACILITY IDENTIFIER
    facility_id: Mapped[str] = mapped_column(String(4), primary_key=True)
    # L AN 0020 00009  DLID    NAVAID FACITITY TYPE (EX: VOR/DME) (SEE NAV1 RECORD FOR NAVAID FACILITY TYPE)
    facility_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    # L AN 0036 00029  N83     NAME(S) OF FIXES (FIX-FILE), THE ID'(S) OF THE STATE IN WHICH THE FIX IS LOCATED, AND THE ASSOCIATED ICAO REGION CODE.  (EX: FIX NAME*FIX STATE*ICAO REGION CODE - WHITE*TX*K1; ORICH*LA*K2)
    fix: Mapped[str] = mapped_column(String(36), primary_key=True)
    # TODO?: Break this into multiple rows?
    # L AN 0720 00065  N/A     SPACE ALLOCATED FOR 20 MORE FIXES (NOTE:  THIS RECORD MAY CONTAIN UP TO 21 FIX DATA)
    more_fixes: Mapped[str | None] = mapped_column(String(720))
    # L AN 0021 00785  N/A     BLANKS.

    __table_args__ = (
        ForeignKeyConstraint(
            [facility_id, facility_type], [Navaid.facility_id, Navaid.facility_type]
        ),
        {},
    )

    navaid = relationship("Navaid", back_populates="airspace_fixes")

    def __repr__(self) -> str:
        """Return a short representation of the AirspaceFix."""
        return f'<AirspaceFix(id={self.facility_id}, type={self.facility_type}, fix="{self.fix[:16]}")>'


class HoldingPattern(Base):
    """Holding pattern records associated with a Navaid (NAV4)."""

    __tablename__ = "navaid_holding_patterns"

    ########
    # 'NAV4' RECORD TYPE - HOLDING PATTERNs (HPF) ASSOCIATED WITH NAVAID
    ########

    # L AN 0004 00005  DLID    NAVAID FACILITY IDENTIFIER
    facility_id: Mapped[str] = mapped_column(String(4), primary_key=True)
    # L AN 0020 00009  DLID    NAVAID FACITITY TYPE (EX: VOR/DME) (SEE 'NAV1' RECORD FOR DESCRIPTION)
    facility_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    # L AN 0080 00029  N84     NAME(S) OF HOLDING PATTERN(S) AND THE STATE IN WHICH THE HOLDING PATTERN(S) IS (ARE) LOCATED.  (EX: NAVAID NAME & FAC TYPE*NAV STATE- GEORGETOWN NDB*TX)
    holding_pattern: Mapped[str] = mapped_column(String(80), primary_key=True)
    # R  N 0003 00109          PATTERN (NUMBER) OF THE HOLDING PATTERN
    holding_pattern_pattern: Mapped[str | None] = mapped_column(String(3))
    # TODO?: Break this into multiple rows?
    # L AN 0664 00112          SPACE ALLOCATED FOR 8 MORE HOLDING PATTERNS.  EACH HOLDING PATTERN HAS 80 CHARACTER NAME AND 3 FOR PATTERN (NUMBER).
    more_holding_patterns: Mapped[str | None] = mapped_column(String(664))
    # L AN 0030 00776  N/A     BLANKS.

    __table_args__ = (
        ForeignKeyConstraint(
            [facility_id, facility_type], [Navaid.facility_id, Navaid.facility_type]
        ),
        {},
    )

    navaid = relationship("Navaid", back_populates="holding_patterns")

    def __repr__(self) -> str:
        """Return a short representation of the HoldingPattern."""
        return f'<HoldingPattern(id={self.facility_id}, type={self.facility_type}, holding_pattern="{self.holding_pattern[:16]}")>'


class FanMarker(Base):
    """Fan marker records associated with a Navaid (NAV5)."""

    __tablename__ = "navaid_fan_markers"

    ########
    # 'NAV5' RECORD TYPE - FAN MARKERS ASSOCIATED WITH NAVAID
    ########

    # L AN 0004 00005  DLID    NAVAID FACILITY IDENTIFIER
    facility_id: Mapped[str] = mapped_column(String(4), primary_key=True)
    # L AN 0020 00009  DLID    NAVAID FACITITY TYPE (EX: VOR/DME) (SEE NAV1 RECORD DESCRIPTION)
    facility_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    # L AN 0030 00029  N81     NAME(S) OF FAN MARKER(S)
    fan_marker: Mapped[str] = mapped_column(String(30), primary_key=True)
    # Break this into multiple rows?  Nope!  There are only 6 (currently) and none use more_fan_markers at all.
    # L AN 0690 00059  N/A     SPACE ALLOCATED FOR 23 MORE FAN MARKERS (NOTE:  THIS RECORD MAY CONTAIN UP TO 24 FAN MARKERS)
    more_fan_markers: Mapped[str | None] = mapped_column(String(690))
    # L AN 0057 00749  N/A     BLANKS

    __table_args__ = (
        ForeignKeyConstraint(
            [facility_id, facility_type], [Navaid.facility_id, Navaid.facility_type]
        ),
        {},
    )

    navaid = relationship("Navaid", back_populates="fan_markers")

    def __repr__(self) -> str:
        """Return a short representation of the FanMarker."""
        return f'<FanMarker(id={self.facility_id}, type={self.facility_type}, fan_marker="{self.fan_marker[:16]}")>'


class VORReceiverCheckpoint(Base):
    """VOR receiver checkpoint records (NAV6)."""

    __tablename__ = "navaid_vor_receiver_checkpoints"

    ########
    # 'NAV6' RECORD TYPE - VOR RECEIVER CHECKPOINTS ASSOCIATED WITH NAVAID
    ########

    # L AN 0004 00005  DLID    NAVAID FACILITY IDENTIFIER
    facility_id: Mapped[str] = mapped_column(String(4), primary_key=True)
    # L AN 0020 00009  DLID    NAVAID FACITITY TYPE (EX: VOR/DME) (SEE NAV1 RECORD DESCRIPTION)
    facility_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    # L AN 0002 00029  N/A     AIR/GROUND CODE A=AIR, G=GROUND, G1=GROUND ONE
    air_ground: Mapped[enums.VORReceiverCheckpointAirGroundCodeEnum] = mapped_column(
        Enum(enums.VORReceiverCheckpointAirGroundCodeEnum), primary_key=True
    )
    # R  N 0003 00031  N/A     BEARING OF CHECKPOINT
    bearing: Mapped[int] = mapped_column(Integer, primary_key=True)
    # R  N 0005 00034  N/A     ALTITUDE ONLY WHEN CHECKPOINT IS IN AIR
    altitude: Mapped[int | None] = mapped_column(Integer)
    # L AN 0004 00039  N/A     AIRPORT ID
    airport_id: Mapped[str | None] = mapped_column(String(4))
    # L AN 0002 00043  N/A     STATE CODE IN WHICH ASSOCIATED CITY IS LOCATED
    state: Mapped[str | None] = mapped_column(String(2))
    # L AN 0075 00045  N/A     NARRATIVE DESCRIPTION ASSOCIATED WITH THE CHECKPOINT IN AIR
    air_narrative: Mapped[str | None] = mapped_column(String(75))
    # L AN 0075 00120  N/A     NARRATIVE DESCRIPTION ASSOCIATED WITH THE CHECKPOINT ON GROUND
    ground_narrative: Mapped[str | None] = mapped_column(String(75))
    # L AN 0611 00195  N/A     BLANKS

    __table_args__ = (
        ForeignKeyConstraint(
            [facility_id, facility_type], [Navaid.facility_id, Navaid.facility_type]
        ),
        {},
    )

    navaid = relationship("Navaid", back_populates="vor_receiver_checkpoints")

    def __repr__(self) -> str:
        """Return a short representation of the VORReceiverCheckpoint."""
        return f"<VORReceiverCheckpoint(id={self.facility_id}, type={self.facility_type}, air_ground={self.air_ground}, bearing={self.bearing})>"
