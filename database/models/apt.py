#!/usr/bin/env python

import datetime
import enum
import logging

from sqlalchemy import Boolean, Column, Date, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKeyConstraint

from .. import enums
from ..base import Base

logger = logging.getLogger(__name__)


class Airport(Base):
    __tablename__ = "airports"

    # L A N D I N G   F A C I L I T Y   D A T A
    # L AN 0011 00004  DLID    LANDING FACILITY SITE NUMBER
    facility_site_number = Column(String(11), primary_key=True)
    # L AN 0013 00015  DLID    LANDING FACILITY TYPE
    facility_type = Column(String(13))
    # L AN 0004 00028  E7      LOCATION IDENTIFIER
    faa_id = Column(String(4), index=True)
    # L AN 0010 00032  N/A     INFORMATION EFFECTIVE DATE (MM/DD/YYYY)
    effective_date = Column(Date)

    # DEMOGRAPHIC DATA
    # L AN 0003 00042  A6      FAA REGION CODE
    region = Column(Enum(enums.FAARegionEnum))
    # L AN 0004 00045  A6A     FAA DISTRICT OR FIELD OFFICE CODE
    field_office = Column(String(4))
    # L AN 0002 00049  A4      ASSOCIATED STATE POST OFFICE CODE
    state_code = Column(String(2))
    # L AN 0020 00051  A4      ASSOCIATED STATE NAME
    state_name = Column(String(20))
    # L AN 0021 00071  A5      ASSOCIATED COUNTY (OR PARISH) NAME
    county = Column(String(21))
    county_remark = Column(String(1500))
    # L AN 0002 00092  A5      ASSOCIATED COUNTY'S STATE (POST OFFICE CODE)
    countys_state = Column(String(2))
    # L AN 0040 00094  A1      ASSOCIATED CITY NAME
    city = Column(String(40))
    city_remark = Column(String(1500))
    # L AN 0050 00134  A2      OFFICIAL FACILITY NAME
    name = Column(String(50))
    name_remark = Column(String(1500))

    # OWNERSHIP DATA
    # L AN 0002 00184  A10     AIRPORT OWNERSHIP TYPE
    ownership_type = Column(Enum(enums.OwnershipTypeEnum))
    ownership_type_remark = Column(String(1500))
    # L AN 0002 00186  A18     FACILITY USE
    facility_use = Column(Enum(enums.FacilityUseEnum))
    facility_use_remark = Column(String(1500))
    # L AN 0035 00188  A11     FACILITY OWNER'S NAME
    owners_name = Column(String(35))
    owners_name_remark = Column(String(1500))
    # L AN 0072 00223  A12     OWNER'S ADDRESS
    owners_address = Column(String(72))
    owners_address_remark = Column(String(1500))
    # L AN 0045 00295  A12A    OWNER'S CITY, STATE AND ZIP CODE
    owners_city_state_zip = Column(String(45))
    owners_city_state_zip_remark = Column(String(1500))
    # R AN 0016 00340  A13     OWNER'S PHONE NUMBER
    owners_phone = Column(String(16))
    owners_phone_remark = Column(String(1500))
    # L AN 0035 00356  A14     FACILITY MANAGER'S NAME
    managers_name = Column(String(35))
    managers_name_remark = Column(String(1500))
    # L AN 0072 00391  A15     MANAGER'S ADDRESS
    managers_address = Column(String(72))
    managers_address_remark = Column(String(1500))
    # L AN 0045 00463  A15A    MANAGER'S CITY, STATE AND ZIP CODE
    managers_city_state_zip = Column(String(45))
    managers_city_state_zip_remark = Column(String(1500))
    # R AN 0016 00508  A16     MANAGER'S PHONE NUMBER
    managers_phone = Column(String(16))
    managers_phone_remark = Column(String(1500))

    # GEOGRAPHIC DATA
    # L AN 0015 00524  A19     AIRPORT REFERENCE POINT LATITUDE (FORMATTED)
    latitude_dms = Column(String(15))
    latitude_dms_remark = Column(String(1500))
    # L AN 0012 00539  A19S    AIRPORT REFERENCE POINT LATITUDE (SECONDS)
    latitude_secs = Column(String(12))
    # L AN 0015 00551  A20     AIRPORT REFERENCE POINT LONGITUDE (FORMATTED)
    longitude_dms = Column(String(15))
    longitude_dms_remark = Column(String(1500))
    # L AN 0012 00566  A20S    AIRPORT REFERENCE POINT LONGITUDE (SECONDS)
    longitude_secs = Column(String(12))
    # L AN 0001 00578  A19A    AIRPORT REFERENCE POINT DETERMINATION METHOD
    coords_method = Column(Enum(enums.DeterminationMethodEnum))
    coords_method_remark = Column(String(1500))
    # R AN 0007 00579  A21     AIRPORT ELEVATION  (NEAREST TENTH OF A FOOT MSL)
    elevation = Column(Float(1))
    elevation_remark = Column(String(1500))
    # L AN 0001 00586  A21     AIRPORT ELEVATION DETERMINATION METHOD
    elevation_method = Column(Enum(enums.DeterminationMethodEnum))
    # L AN 0003 00587  E28     MAGNETIC VARIATION AND DIRECTION
    mag_variation = Column(String(3))
    # L AN 0004 00590  E28     MAGNETIC VARIATION EPOCH YEAR
    mag_variation_year = Column(Integer)
    # R AN 0004 00594  E147    TRAFFIC PATTERN ALTITUDE  (WHOLE FEET AGL)
    pattern_alt = Column(Integer)
    pattern_alt_remark = Column(String(1500))
    # L AN 0030 00598  A7      AERONAUTICAL SECTIONAL CHART ON WHICH FACILITY APPEARS
    sectional = Column(String(30))
    sectional_remark = Column(String(1500))
    # L AN 0002 00628  A3      DISTANCE FROM CENTRAL BUSINESS DISTRICT OF THE ASSOCIATED CITY TO THE AIRPORT
    distance_from_city = Column(Integer)
    distance_from_city_remark = Column(String(1500))
    # L AN 0003 00630  A3      DIRECTION OF AIRPORT FROM CENTRAL BUSINESS
    direction_from_city = Column(String(3))
    # R AN 0005 00633  A22     LAND AREA COVERED BY AIRPORT (ACRES)
    land_area = Column(Integer)
    land_area_remark = Column(String(1500))

    # FAA SERVICES
    # L AN 0004 00638  E146A   BOUNDARY ARTCC IDENTIFIER
    boundary_artcc_id = Column(String(4))
    # L AN 0003 00642  E146B   BOUNDARY ARTCC (FAA) COMPUTER IDENTIFIER
    boundary_artcc_computer_id = Column(String(3))
    # L AN 0030 00645  E146C   BOUNDARY ARTCC NAME
    boundary_artcc_name = Column(String(30))
    # L AN 0004 00675  E156A   RESPONSIBLE ARTCC IDENTIFIER
    responsible_artcc_id = Column(String(4))
    responsible_artcc_id_remark = Column(String(1500))
    # L AN 0003 00679  E156B   RESPONSIBLE ARTCC (FAA) COMPUTER IDENTIFIER
    responsible_artcc_computer_id = Column(String(3))
    # L AN 0030 00682  E156C   RESPONSIBLE ARTCC NAME
    responsible_artcc_name = Column(String(30))
    # L AN 0001 00712  A87     TIE-IN FSS PHYSICALLY LOCATED ON FACILITY
    tie_in_fss_local = Column(Boolean)
    # L AN 0004 00713  A86     TIE-IN FLIGHT SERVICE STATION (FSS) IDENTIFIER
    tie_in_fss_id = Column(String(4))
    tie_in_fss_remark = Column(String(1500))
    # L AN 0030 00717  A86     TIE-IN FSS NAME
    tie_in_fss_name = Column(String(30))
    # L AN 0016 00747  A88     LOCAL PHONE NUMBER FROM AIRPORT TO FSS
    fss_local_phone = Column(String(16))
    # L AN 0016 00763  A89     TOLL FREE PHONE NUMBER FROM AIRPORT TO FSS
    fss_toll_free_phone = Column(String(16))
    # L AN 0004 00779  A86A    ALTERNATE FSS IDENTIFIER
    alternate_fss_id = Column(String(4))
    # L AN 0030 00783  A86A    ALTERNATE FSS NAME
    alternate_fss_name = Column(String(30))
    # L AN 0016 00813  E3A     TOLL FREE PHONE NUMBER FROM AIRPORT TO ALTERNATE FSS
    alternate_fss_toll_free_phone = Column(String(16))
    # L AN 0004 00829  E2B     IDENTIFIER OF THE FACILITY RESPONSIBLE FOR ISSUING NOTICES TO AIRMEN
    notam_facility = Column(String(4))
    # L AN 0001 00833  E139    AVAILABILITY OF NOTAM 'D' SERVICE AT AIRPORT
    notam_d_available = Column(Boolean)

    # FEDERAL STATUS
    # L AN 0007 00834  E157    AIRPORT ACTIVATION DATE (MM/YYYY)
    activation_date = Column(Date)
    # L AN 0002 00841  N/A     AIRPORT STATUS CODE
    status = Column(Enum(enums.AirportStatusEnum))
    # L AN 0015 00843  A26     AIRPORT ARFF CERTIFICATION TYPE AND DATE
    arff_certification = Column(
        String(15)
    )  # Candidate for parsing and breaking into multiple columns
    arff_certification_remark = Column(
        String(1500)
    )  # Candidate for parsing and breaking into multiple columns
    # L AN 0007 00858  A25     NPIAS/FEDERAL AGREEMENTS CODE
    npias_federal_agreements = Column(
        String(7)
    )  # Candidate for parsing and breaking into multiple columns
    npias_federal_agreements_remark = Column(String(1500))
    # L AN 0013 00865  E111    AIRPORT AIRSPACE ANALYSIS DETERMINATION
    airspace_analysis = Column(String(13))
    airspace_analysis_remark = Column(String(1500))
    # L AN 0001 00878  E79     FACILITY HAS BEEN DESIGNATED BY THE U.S. TREASURY AS AN INTERNATIONAL AIRPORT OF ENTRY FOR CUSTOMS
    airport_of_entry = Column(Boolean)
    airport_of_entry_remark = Column(String(1500))
    # L AN 0001 00879  E80     FACILITY HAS BEEN DESIGNATED BY THE U.S. TREASURY AS A CUSTOMS LANDING RIGHTS AIRPORT
    customs_landing_rights = Column(Boolean)
    customs_landing_rights_remark = Column(String(1500))
    # L AN 0001 00880  E115    FACILITY HAS MILITARY/CIVIL JOINT USE AGREEMENT THAT ALLOWS CIVIL OPERATIONS AT A MILITARY AIRPORT
    military_civil_join_use = Column(Boolean)
    military_civil_join_use_remark = Column(String(1500))
    # L AN 0001 00881  E116    AIRPORT HAS ENTERED INTO AN AGREEMENT THAT GRANTS LANDING RIGHTS TO THE MILITARY
    military_landing_rights = Column(Boolean)
    military_landing_rights_remark = Column(String(1500))

    # AIRPORT INSPECTION DATA
    # L AN 0002 00882  E155    AIRPORT INSPECTION METHOD
    inspection_method = Column(Enum(enums.AirportInspectionMethodEnum))
    # L AN 0001 00884  A111    AGENCY/GROUP PERFORMING PHYSICAL INSPECTION
    agency_performing_inspection = Column(Enum(enums.AgencyPerformingInspectionEnum))
    agency_performing_inspection_remark = Column(String(1500))
    # L AN 0008 00885  A112    LAST PHYSICAL INSPECTION DATE (MMDDYYYY)
    last_inspection_date = Column(Date)
    last_inspection_date_remark = Column(String(1500))
    # L AN 0008 00893  A113    LAST DATE INFORMATION REQUEST WAS COMPLETED
    last_information_request_complete_date = Column(Date)

    # AIRPORT SERVICES
    # L AN 0040 00901  A70     FUEL TYPES AVAILABLE FOR PUBLIC USE
    fuel_available = Column(
        String(40)
    )  # Candidate for parsing and breaking into multiple columns
    fuel_available_remark = Column(String(1500))
    # L AN 0005 00941  A71     AIRFRAME REPAIR SERVICE AVAILABILITY/TYPE
    airframe_repair_service = Column(String(5))  # Could be an enum?
    airframe_repair_service_remark = Column(String(1500))
    # L AN 0005 00946  A72     POWER PLANT (ENGINE) REPAIR AVAILABILITY/TYPE
    power_plant_repair_service = Column(String(5))  # Could be an enum?
    power_plant_repair_service_remark = Column(String(1500))
    # L AN 0008 00951  A73     TYPE OF BOTTLED OXYGEN AVAILABLE
    bottled_oxygen = Column(String(8))  # Could be an enum?
    bottled_oxygen_remark = Column(String(1500))
    # L AN 0008 00959  A74     TYPE OF BULK OXYGEN AVAILABLE
    bulk_oxygen = Column(String(8))  # Could be an enum?
    bulk_oxygen_remark = Column(String(1500))

    # AIRPORT FACILITIES
    # L AN 0007 00967  A81     AIRPORT LIGHTING SCHEDULE
    lighting_schedule = Column(String(7))
    lighting_schedule_remark = Column(String(1500))
    # L AN 0007 00974  A81     BEACON LIGHTING SCHEDULE
    beacon_schedule = Column(String(7))
    beacon_schedule_remark = Column(String(1500))
    # L AN 0001 00981  A85     AIR TRAFFIC CONTROL TOWER LOCATED ON AIRPORT
    towered_airport = Column(Boolean)
    # L AN 0007 00982  A82     UNICOM FREQUENCY AVAILABLE AT THE AIRPORT
    unicom = Column(String(7))
    unicom_remark = Column(String(1500))
    # L AN 0007 00989  E100    COMMON TRAFFIC ADVISORY FREQUENCY (CTAF)
    ctaf = Column(String(7))
    ctaf_remark = Column(String(1500))
    # L AN 0004 00996  A84     SEGMENTED CIRCLE AIRPORT MARKER SYSTEM ON THE AIRPORT
    segmented_circle_available = Column(Enum(enums.SegmentedCircleEnum))
    segmented_circle_available_remark = Column(String(1500))
    # L AN 0003 01000  A80     LENS COLOR OF OPERABLE BEACON LOCATED ON THE AIRPORT
    beacon_color = Column(Enum(enums.BeaconColorEnum))
    beacon_color_remark = Column(String(1500))
    # L AN 0001 01003  A24     LANDING FEE CHARGED TO NON-COMMERCIAL USERS
    noncommerical_landing_fee = Column(Boolean)
    noncommerical_landing_fee_remark = Column(String(1500))
    # L AN 0001 01004  NONE    A "Y" IN THIS FIELD INDICATES THAT THE LANDING FACILITY IS USED FOR MEDICAL PURPOSES
    landing_facility_used_for_medical_purposes = Column(Boolean)

    # BASED AIRCRAFT
    # R  N 0003 01005  A90     SINGLE ENGINE GENERAL AVIATION AIRCRAFT
    based_general_aviation_single_engine_airplanes = Column(Integer)
    based_general_aviation_single_engine_airplanes_remark = Column(String(1500))
    # R  N 0003 01008  A91     MULTI ENGINE GENERAL AVIATION AIRCRAFT
    based_general_aviation_multi_engine_airplanes = Column(Integer)
    based_general_aviation_multi_engine_airplanes_remark = Column(String(1500))
    # R  N 0003 01011  A92     JET ENGINE GENERAL AVIATION AIRCRAFT
    based_general_aviation_jet_engine_airplanes = Column(Integer)
    based_general_aviation_jet_engine_airplanes_remark = Column(String(1500))
    # R  N 0003 01014  A93     GENERAL AVIATION HELICOPTER
    based_general_aviation_helicopters = Column(Integer)
    based_general_aviation_helicopters_remark = Column(String(1500))
    # R  N 0003 01017  A94     OPERATIONAL GLIDERS
    based_gliders = Column(Integer)
    based_gliders_remark = Column(String(1500))
    # R  N 0003 01020  A95     OPERATIONAL MILITARY AIRCRAFT (INCLUDING HELICOPTERS)
    based_military_aircraft = Column(Integer)
    based_military_aircraft_remark = Column(String(1500))
    # R  N 0003 01023  A96     ULTRALIGHT AIRCRAFT
    based_ultralight_aircraft = Column(Integer)
    based_ultralight_aircraft_remark = Column(String(1500))

    # ANNUAL OPERATIONS
    # R  N 0006 01026  A100    COMMERCIAL SERVICES
    annual_ops_commercial = Column(Integer)
    annual_ops_commercial_remark = Column(String(1500))
    # R  N 0006 01032  A101    COMMUTER SERVICES
    annual_ops_commuter = Column(Integer)
    annual_ops_commuter_remark = Column(String(1500))
    # R  N 0006 01038  A102    AIR TAXI
    annual_ops_air_taxi = Column(Integer)
    annual_ops_air_taxi_remark = Column(String(1500))
    # R  N 0006 01044  A103    GENERAL AVIATION LOCAL OPERATIONS
    annual_ops_general_aviation_local = Column(Integer)
    annual_ops_general_aviation_local_remark = Column(String(1500))
    # R  N 0006 01050  A104    GENERAL AVIATION ITINERANT OPERATIONS
    annual_ops_general_aviation_itinerant = Column(Integer)
    annual_ops_general_aviation_itinerant_remark = Column(String(1500))
    # R  N 0006 01056  A105    MILITARY AIRCRAFT OPERATIONS
    annual_ops_military = Column(Integer)
    annual_ops_military_remark = Column(String(1500))
    # L AN 0010 01062  NONE    12-MONTH ENDING DATE ON WHICH ANNUAL OPERATIONS DATA IN ABOVE SIX FIELDS IS BASED (MM/DD/YYYY)
    annual_ops_end_of_measurement_period = Column(Date)

    # ADDITIONAL AIRPORT DATA
    # L AN 0016 01072  NONE    AIRPORT POSITION SOURCE
    position_source = Column(String(16))
    # L AN 0010 01088  NONE    AIRPORT POSITION SOURCE DATE (MM/DD/YYYY)
    position_date = Column(Date)
    # L AN 0016 01098  NONE    AIRPORT ELEVATION SOURCE
    elevation_source = Column(String(16))
    # L AN 0010 01114  NONE    AIRPORT ELEVATION SOURCE DATE (MM/DD/YYYY)
    elevation_date = Column(Date)
    # L AN 0001 01124  NONE    CONTRACT FUEL AVAILABLE
    contract_fuel_available = Column(Boolean)
    # L AN 0012 01125  A75     TRANSIENT STORAGE FACILITIES
    transient_storage_facilities = Column(String(12))  # Candidate for further parsing
    transient_storage_facilities_remark = Column(String(1500))
    # L AN 0071 01137  A76     OTHER AIRPORT SERVICES AVAILABLE
    other_services_available = Column(String(71))  # Candidate for further parsing
    other_services_available_remark = Column(String(1500))
    # L AN 0003 01208  A83     WIND INDICATOR
    wind_indicator = Column(Enum(enums.SegmentedCircleEnum))
    wind_indicator_remark = Column(String(1500))
    # L AN 0007 01211  NONE    ICAO IDENTIFIER
    icao_id = Column(String(7), index=True)
    # L AN 0001 01218  NONE    MINIMUM OPERATIONAL NETWORK(MON)
    minimum_operational_network = Column(String(1))
    # L AN 0311 01219  NONE    AIRPORT RECORD FILLER (BLANK)

    runways = relationship("Runway", back_populates="airport")
    remarks = relationship("AirportRemark", back_populates="airport")
    attendance_schedules = relationship("AttendanceSchedule", back_populates="airport")

    def __repr__(self):
        return "<Airport(name='%s', faa='%s', icao='%s')>" % (
            self.name,
            self.faa_id,
            self.icao_id,
        )

    def to_dict(self, include=None):
        _include = include or []

        base_attrs = [
            "facility_type",
            "faa_id",
            "icao_id",
            "name",
            "name_remark",
            "effective_date",
        ]

        demo_attrs = [
            "region",
            "field_office",
            "state_code",
            "state_name",
            "county",
            "county_remark",
            "countys_state",
            "city",
            "city_remark",
        ]

        ownership_attrs = [
            "ownership_type",
            "ownership_type_remark",
            "facility_use",
            "facility_use_remark",
            "owners_name",
            "owners_name_remark",
            "owners_address",
            "owners_address_remark",
            "owners_city_state_zip",
            "owners_city_state_zip_remark",
            "owners_phone",
            "owners_phone_remark",
            "managers_name",
            "managers_name_remark",
            "managers_address",
            "managers_address_remark",
            "managers_city_state_zip",
            "managers_city_state_zip_remark",
            "managers_phone",
            "managers_phone_remark",
        ]

        geo_attrs = [
            "latitude_dms",
            "latitude_dms_remark",
            "latitude_secs",
            "longitude_dms",
            "longitude_dms_remark",
            "longitude_secs",
            "coords_method",
            "coords_method_remark",
            "elevation",
            "elevation_remark",
            "elevation_method",
            "mag_variation",
            "mag_variation_year",
            "pattern_alt",
            "pattern_alt_remark",
            "sectional",
            "sectional_remark",
            "distance_from_city",
            "distance_from_city_remark",
            "direction_from_city",
            "land_area",
            "land_area_remark",
        ]

        faasrv_attrs = [
            "boundary_artcc_id",
            "boundary_artcc_computer_id",
            "boundary_artcc_name",
            "responsible_artcc_id",
            "responsible_artcc_id_remark",
            "responsible_artcc_computer_id",
            "responsible_artcc_name",
            "tie_in_fss_local",
            "tie_in_fss_id",
            "tie_in_fss_remark",
            "tie_in_fss_name",
            "fss_local_phone",
            "fss_toll_free_phone",
            "alternate_fss_id",
            "alternate_fss_name",
            "alternate_fss_toll_free_phone",
            "notam_facility",
            "notam_d_available",
        ]

        fedstatus_attrs = [
            "activation_date",
            "status",
            "arff_certification",
            "arff_certification_remark",
            "npias_federal_agreements",
            "npias_federal_agreements_remark",
            "airspace_analysis",
            "airspace_analysis_remark",
            "airport_of_entry",
            "airport_of_entry_remark",
            "customs_landing_rights",
            "customs_landing_rights_remark",
            "military_civil_join_use",
            "military_civil_join_use_remark",
            "military_landing_rights",
            "military_landing_rights_remark",
        ]

        inspect_attrs = [
            "inspection_method",
            "agency_performing_inspection",
            "agency_performing_inspection_remark",
            "last_inspection_date",
            "last_inspection_date_remark",
            "last_information_request_complete_date",
        ]

        aptsrv_attrs = [
            "fuel_available",
            "fuel_available_remark",
            "airframe_repair_service",
            "airframe_repair_service_remark",
            "power_plant_repair_service",
            "power_plant_repair_service_remark",
            "bottled_oxygen",
            "bottled_oxygen_remark",
            "bulk_oxygen",
            "bulk_oxygen_remark",
        ]

        facilities_attrs = [
            "lighting_schedule",
            "lighting_schedule_remark",
            "beacon_schedule",
            "beacon_schedule_remark",
            "towered_airport",
            "unicom",
            "unicom_remark",
            "ctaf",
            "ctaf_remark",
            "segmented_circle_available",
            "segmented_circle_available_remark",
            "beacon_color",
            "beacon_color_remark",
            "noncommerical_landing_fee",
            "noncommerical_landing_fee_remark",
            "landing_facility_used_for_medical_purposes",
        ]

        basedacft_attrs = [
            "based_general_aviation_single_engine_airplanes",
            "based_general_aviation_single_engine_airplanes_remark",
            "based_general_aviation_multi_engine_airplanes",
            "based_general_aviation_multi_engine_airplanes_remark",
            "based_general_aviation_jet_engine_airplanes",
            "based_general_aviation_jet_engine_airplanes_remark",
            "based_general_aviation_helicopters",
            "based_general_aviation_helicopters_remark",
            "based_gliders",
            "based_gliders_remark",
            "based_military_aircraft",
            "based_military_aircraft_remark",
            "based_ultralight_aircraft",
            "based_ultralight_aircraft_remark",
        ]

        annops_attrs = [
            "annual_ops_commercial",
            "annual_ops_commercial_remark",
            "annual_ops_commuter",
            "annual_ops_air_taxi",
            "annual_ops_general_aviation_local",
            "annual_ops_general_aviation_local_remark",
            "annual_ops_general_aviation_itinerant",
            "annual_ops_general_aviation_itinerant_remark",
            "annual_ops_military",
            "annual_ops_military_remark",
            "annual_ops_end_of_measurement_period",
        ]

        addl_attrs = [
            "position_source",
            "position_date",
            "elevation_source",
            "elevation_date",
            "contract_fuel_available",
            "transient_storage_facilities",
            "transient_storage_facilities_remark",
            "other_services_available",
            "other_services_available_remark",
            "wind_indicator",
            "wind_indicator_remark",
            "minimum_operational_network",
        ]

        if "demographic" in _include or "all" in _include:
            base_attrs += demo_attrs

        if "ownership" in _include or "all" in _include:
            base_attrs += ownership_attrs

        if "geographic" in _include or "all" in _include:
            base_attrs += geo_attrs

        if "faaservices" in _include or "all" in _include:
            base_attrs += faasrv_attrs

        if "fedstatus" in _include or "all" in _include:
            base_attrs += fedstatus_attrs

        if "inspection" in _include or "all" in _include:
            base_attrs += inspect_attrs

        if "aptservices" in _include or "all" in _include:
            base_attrs += aptsrv_attrs

        if "facilities" in _include or "all" in _include:
            base_attrs += facilities_attrs

        if "basedaircraft" in _include or "all" in _include:
            base_attrs += basedacft_attrs

        if "annualops" in _include or "all" in _include:
            base_attrs += annops_attrs

        if "additional" in _include or "all" in _include:
            base_attrs += addl_attrs

        result = dict()

        for attr in base_attrs:
            value = getattr(self, attr)

            if isinstance(value, enum.Enum):
                result[attr] = value.value
            elif isinstance(value, (datetime.date, datetime.datetime)):
                result[attr] = value.isoformat()
            else:
                result[attr] = value

        if "runways" in _include:
            result["runways"] = [runway.to_dict() for runway in self.runways]

        if "remarks" in _include:
            result["remarks"] = [remark.remark for remark in self.remarks]

        if "attendance" in _include:
            result["attendance"] = [
                attsched.attendance_schedule for attsched in self.attendance_schedules
            ]

        return result


class Runway(Base):
    __tablename__ = "runways"

    # F A C I L I T Y   R U N W A Y   D A T A
    # L AN 0011 00004  DLID    LANDING FACILITY SITE NUMBER
    facility_site_number = Column(
        String(11), ForeignKey("airports.facility_site_number"), primary_key=True
    )
    # L AN 0007 00017  A30     RUNWAY IDENTIFICATION
    name = Column(String(7), primary_key=True)
    name_remark = Column(String(1500))

    # COMMON RUNWAY DATA
    # R AN 0005 00024  A31     PHYSICAL RUNWAY LENGTH (NEAREST FOOT)
    length = Column(Integer)
    length_remark = Column(String(1500))
    # R AN 0004 00029  A32     PHYSICAL RUNWAY WIDTH (NEAREST FOOT)
    width = Column(Integer)
    width_remark = Column(String(1500))
    # L AN 0012 00033  A33     RUNWAY SURFACE TYPE AND CONDITION
    surface_type_condition = Column(String(12))
    surface_type_condition_remark = Column(String(1500))
    # L AN 0005 00045  A34     RUNWAY SURFACE TREATMENT
    surface_treatment = Column(String(5))
    surface_treatment_remark = Column(String(1500))
    # L AN 0011 00050  A39     PAVEMENT CLASSIFICATION NUMBER (PCN)
    pavement_classification_number = Column(String(11))
    pavement_classification_number_remark = Column(String(1500))
    # L AN 0005 00061  A40     RUNWAY LIGHTS EDGE INTENSITY
    edge_light_intensity = Column(String(5))
    edge_light_intensity_remark = Column(String(1500))

    # ADDITIONAL COMMON RUNWAY DATA
    # L AN 0016 00510  NONE    RUNWAY LENGTH SOURCE
    length_source = Column(String(16))
    # L AN 0010 00526  NONE    RUNWAY LENGTH SOURCE DATE (MM/DD/YYYY)
    length_source_date = Column(Date)
    # R AN 0006 00536  A35     RUNWAY WEIGHT-BEARING CAPACITY FOR Single wheel type landing gear
    weight_bearing_capacity_single_wheel = Column(String(6))
    weight_bearing_capacity_single_wheel_remark = Column(String(1500))
    # R AN 0006 00542  A36     RUNWAY WEIGHT-BEARING CAPACITY FOR Dual wheel type landing gear
    weight_bearing_capacity_dual_wheels = Column(String(6))
    weight_bearing_capacity_dual_wheels_remark = Column(String(1500))
    # R AN 0006 00548  A37     RUNWAY WEIGHT-BEARING CAPACITY FOR Two dual wheels in tandem type landing gear
    weight_bearing_capacity_two_dual_wheels_tandem = Column(String(6))
    weight_bearing_capacity_two_dual_wheels_tandem_remark = Column(String(1500))
    # R AN 0006 00554  A38     RUNWAY WEIGHT-BEARING CAPACITY FOR Two dual wheels in tandem/two dual wheels in double tandem body gear type landing gear
    weight_bearing_capacity_two_dual_wheels_double_tandem = Column(String(6))
    weight_bearing_capacity_two_dual_wheels_double_tandem_remark = Column(String(1500))

    airport = relationship("Airport", back_populates="runways")
    runway_ends = relationship("RunwayEnd", back_populates="runway")
    remarks = relationship("RunwayRemark", back_populates="runway")

    def __repr__(self):
        return "<Runway(name='%s', airport='%s')>" % (self.name, self.airport)

    def to_dict(self, include=None):
        _include = include or []

        base_attrs = [
            "name",
            "name_remark",
            "length",
            "length_remark",
            "width",
            "width_remark",
            "surface_type_condition",
            "surface_type_condition_remark",
            "surface_treatment",
            "surface_treatment_remark",
            "pavement_classification_number",
            "pavement_classification_number_remark",
            "edge_light_intensity",
            "edge_light_intensity_remark",
        ]

        addl_attrs = [
            "length_source",
            "length_source_date",
            "weight_bearing_capacity_single_wheel",
            "weight_bearing_capacity_single_wheel_remark",
            "weight_bearing_capacity_dual_wheels",
            "weight_bearing_capacity_dual_wheels_remark",
            "weight_bearing_capacity_two_dual_wheels_tandem",
            "weight_bearing_capacity_two_dual_wheels_tandem_remark",
            "weight_bearing_capacity_two_dual_wheels_double_tandem",
            "weight_bearing_capacity_two_dual_wheels_double_tandem_remark",
        ]

        if "additional" in _include or "all" in _include:
            base_attrs += addl_attrs

        result = dict()

        for attr in base_attrs:
            value = getattr(self, attr)

            if isinstance(value, enum.Enum):
                result[attr] = value.value
            elif isinstance(value, (datetime.date, datetime.datetime)):
                result[attr] = value.isoformat()
            else:
                result[attr] = value

        if "runway_ends" in _include:
            result["runway_ends"] = [end.to_dict() for end in self.runway_ends]

        return result


class RunwayEnd(Base):
    __tablename__ = "runway_ends"

    facility_site_number = Column(String(11), primary_key=True)
    runway_name = Column(String(7), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            [facility_site_number, runway_name],
            [Runway.facility_site_number, Runway.name],
        ),
        {},
    )

    # RUNWAY END INFORMATION
    # L AN 0003 00066  A30A    BASE END IDENTIFIER
    # L AN 0003 00288  A30A    RECIPROCAL END IDENTIFIER
    id = Column(String(3), primary_key=True)
    id_remark = Column(String(1500))
    # L AN 0003 00069  E46     RUNWAY END TRUE ALIGNMENT
    # L AN 0003 00291  E46     RUNWAY END TRUE ALIGNMENT
    true_alignment = Column(Integer)
    true_alignment_remark = Column(String(1500))
    # L AN 0010 00072  I22     INSTRUMENT LANDING SYSTEM (ILS) TYPE
    # L AN 0010 00294  I22     INSTRUMENT LANDING SYSTEM (ILS) TYPE
    approach_type = Column(String(10))
    # L AN 0001 00082  A23     RIGHT HAND TRAFFIC PATTERN FOR LANDING AIRCRAFT
    # L AN 0001 00304  A23     RIGHT HAND TRAFFIC PATTERN FOR LANDING AIRCRAFT
    right_traffic = Column(Boolean)
    right_traffic_remark = Column(String(1500))
    # L AN 0005 00083  A42     RUNWAY MARKINGS  (TYPE)
    # L AN 0005 00305  A42     RUNWAY MARKINGS  (TYPE)
    markings_type = Column(Enum(enums.RunwayMarkingsTypeEnum))
    markings_remark = Column(String(1500))
    # L AN 0001 00088  A42     RUNWAY MARKINGS  (CONDITION)
    # L AN 0001 00310  A42     RUNWAY MARKINGS  (CONDITION)
    markings_condition = Column(Enum(enums.RunwayMarkingsConditionEnum))

    # RUNWAY END GEOGRAPHIC DATA
    # L AN 0015 00089  E68     LATITUDE OF PHYSICAL RUNWAY END (FORMATTED)
    # L AN 0015 00311  E68     LATITUDE OF PHYSICAL RUNWAY END (FORMATTED)
    latitude_dms = Column(String(15))
    latitude_dms_remark = Column(String(1500))
    # L AN 0012 00104  E68S    LATITUDE OF PHYSICAL RUNWAY END (SECONDS)
    # L AN 0012 00326  E68S    LATITUDE OF PHYSICAL RUNWAY END (SECONDS)
    latitude_secs = Column(String(12))
    # L AN 0015 00116  E69     LONGITUDE OF PHYSICAL RUNWAY END (FORMATTED)
    # L AN 0015 00338  E69     LONGITUDE OF PHYSICAL RUNWAY END (FORMATTED)
    longitude_dms = Column(String(15))
    longitude_dms_remark = Column(String(1500))
    # L AN 0012 00131  E69S    LONGITUDE OF PHYSICAL RUNWAY END (SECONDS)
    # L AN 0012 00353  E69S    LONGITUDE OF PHYSICAL RUNWAY END (SECONDS)
    longitude_secs = Column(String(12))
    # R AN 0007 00143  E70     ELEVATION (FEET MSL) AT PHYSICAL RUNWAY END
    # R AN 0007 00365  E70     ELEVATION (FEET MSL) AT PHYSICAL RUNWAY END
    elevation = Column(Float(1))
    elevation_remark = Column(String(1500))
    # R AN 0003 00150  A44     THRESHOLD CROSSING HEIGHT (FEET AGL)
    # R AN 0003 00372  A44     THRESHOLD CROSSING HEIGHT (FEET AGL)
    threshold_crossing_height = Column(Integer)
    threshold_crossing_height_remark = Column(String(1500))
    # L AN 0004 00153  A45     VISUAL GLIDE PATH ANGLE (HUNDREDTHS OF DEGREES)
    # L AN 0004 00375  A45     VISUAL GLIDE PATH ANGLE (HUNDREDTHS OF DEGREES)
    visual_glide_path_angle = Column(Float(2))
    visual_glide_path_angle_remark = Column(String(1500))
    # L AN 0015 00157  E161    LATITUDE  AT DISPLACED THRESHOLD (FORMATTED)
    # L AN 0015 00379  E161    LATITUDE  AT DISPLACED THRESHOLD (FORMATTED)
    displaced_threshold_latitude_dms = Column(String(15))
    displaced_threshold_latitude_dms_remark = Column(String(1500))
    # L AN 0012 00172  E161S   LATITUDE  AT DISPLACED THRESHOLD (SECONDS)
    # L AN 0012 00394  E161S   LATITUDE  AT DISPLACED THRESHOLD (SECONDS)
    displaced_threshold_latitude_secs = Column(String(12))
    # L AN 0015 00184  E162    LONGITUDE AT DISPLACED THRESHOLD (FORMATTED)
    # L AN 0015 00406  E162    LONGITUDE AT DISPLACED THRESHOLD (FORMATTED)
    displaced_threshold_longitude_dms = Column(String(15))
    displaced_threshold_longitude_dms_remark = Column(String(1500))
    # L AN 0012 00199  E162S   LONGITUDE AT DISPLACED THRESHOLD (SECONDS)
    # L AN 0012 00421  E162S   LONGITUDE AT DISPLACED THRESHOLD (SECONDS)
    displaced_threshold_longitude_secs = Column(String(12))
    # R AN 0007 00211  E160    ELEVATION AT DISPLACED THRESHOLD (FEET MSL)
    # R AN 0007 00433  E160    ELEVATION AT DISPLACED THRESHOLD (FEET MSL)
    displaced_threshold_elevation = Column(Float(1))
    # R AN 0004 00218  A51     DISPLACED THRESHOLD - LENGTH IN FEET FROM RUNWAY END
    # R AN 0004 00440  A51     DISPLACED THRESHOLD - LENGTH IN FEET FROM RUNWAY END
    displaced_threshold_length = Column(Integer)
    displaced_threshold_length_remark = Column(String(1500))
    # R AN 0007 00222  E163    ELEVATION AT TOUCHDOWN ZONE (FEET MSL)
    # R AN 0007 00444  E163    ELEVATION AT TOUCHDOWN ZONE (FEET MSL)
    touchdown_zone_elevation = Column(Float(1))

    # RUNWAY END LIGHTING DATA
    # L AN 0005 00229  A43     VISUAL GLIDE SLOPE INDICATORS
    # L AN 0005 00451  A43     APPROACH SLOPE INDICATOR EQUIPMENT
    visual_glide_slope_indicators = Column(Enum(enums.VisualGlideSlopeIndicatorEnum))
    visual_glide_slope_indicators_remark = Column(String(1500))
    # L AN 0003 00234  A47     RUNWAY VISUAL RANGE EQUIPMENT (RVR)
    # L AN 0003 00456  A47     RUNWAY VISUAL RANGE EQUIPMENT (RVR)
    rvr_equipment = Column(Enum(enums.RVREquipmentEnum))
    rvr_equipment_remark = Column(String(1500))
    # L AN 0001 00237  A47A    RUNWAY VISIBILITY VALUE EQUIPMENT (RVV)
    # L AN 0001 00459  A47A    RUNWAY VISIBILITY VALUE EQUIPMENT (RVV)
    rvv_equipment = Column(Boolean)
    # L AN 0008 00238  A49     APPROACH LIGHT SYSTEM
    # L AN 0008 00460  A49     APPROACH LIGHT SYSTEM
    approach_light_system = Column(String(8))
    approach_light_system_remark = Column(String(1500))
    # L AN 0001 00246  A48     RUNWAY END IDENTIFIER LIGHTS (REIL) AVAILABILITY
    # L AN 0001 00468  A48     RUNWAY END IDENTIFIER LIGHTS (REIL) AVAILABILITY
    reil_availability = Column(Boolean)
    reil_availability_remark = Column(String(1500))
    # L AN 0001 00247  A46     RUNWAY CENTERLINE LIGHTS AVAILABILITY
    # L AN 0001 00469  A46     RUNWAY CENTERLINE LIGHTS AVAILABILITY
    centerline_light_availability = Column(Boolean)
    centerline_light_availability_remark = Column(String(1500))
    # L AN 0001 00248  A46A    RUNWAY END TOUCHDOWN LIGHTS AVAILABILITY
    # L AN 0001 00470  A46A    RUNWAY END TOUCHDOWN LIGHTS AVAILABILITY
    touchdown_lights_availability = Column(Boolean)
    touchdown_lights_availability_remark = Column(String(1500))

    # RUNWAY END OBJECT DATA
    # L AN 0011 00249  A52     CONTROLLING OBJECT DESCRIPTION
    # L AN 0011 00471  A52     CONTROLLING OBJECT DESCRIPTION
    controlling_object_description = Column(String(11))
    controlling_object_description_remark = Column(String(1500))
    # L AN 0004 00260  A53     CONTROLLING OBJECT MARKED/LIGHTED
    # L AN 0004 00482  A53     CONTROLLING OBJECT MARKED/LIGHTED
    controlling_object_marking = Column(Enum(enums.ControllingObjectMarkingEnum))
    controlling_object_marking_remark = Column(String(1500))
    # L AN 0005 00264  A50     FAA CFR PART 77 (OBJECTS AFFECTING NAVIGABLE AIRSPACE) RUNWAY CATEGORY
    # L AN 0005 00486  A50     FAA CFR PART 77 (OBJECTS AFFECTING NAVIGABLE AIRSPACE) RUNWAY CATEGORY
    part77_category = Column(String(5))  # Might be able to turn into an enum
    part77_category_remark = Column(String(1500))
    # R AN 0002 00269  A57     CONTROLLING OBJECT CLEARANCE SLOPE
    # R AN 0002 00491  A57     CONTROLLING OBJECT CLEARANCE SLOPE
    controlling_object_clearance_slope = Column(Integer)
    controlling_object_clearance_slope_remark = Column(String(1500))
    # R AN 0005 00271  A54     CONTROLLING OBJECT HEIGHT ABOVE RUNWAY
    # R AN 0005 00493  A54     CONTROLLING OBJECT HEIGHT ABOVE RUNWAY
    controlling_object_height_above_runway = Column(Integer)
    controlling_object_height_above_runway_remark = Column(String(1500))
    # R AN 0005 00276  A55     CONTROLLING OBJECT DISTANCE FROM RUNWAY END
    # R AN 0005 00498  A55     CONTROLLING OBJECT DISTANCE FROM RUNWAY END
    controlling_object_distance_from_runway = Column(Integer)
    controlling_object_distance_from_runway_remark = Column(String(1500))
    # L AN 0007 00281  A56     CONTROLLING OBJECT CENTERLINE OFFSET
    # L AN 0007 00503  A56     CONTROLLING OBJECT CENTERLINE OFFSET
    controlling_object_centerline_offset = Column(String(7))
    controlling_object_centerline_offset_remark = Column(String(1500))

    # ADDITIONAL RUNWAY END DATA
    # R AN 0005 00560  E40     RUNWAY END GRADIENT
    # R AN 0005 00851  E40     RUNWAY END GRADIENT
    gradient = Column(String(5))
    gradient_remark = Column(String(1500))
    # L AN 0004 00565  E40     RUNWAY END GRADIENT DIRECTION (UP OR DOWN)
    # L AN 0004 00856  E40     RUNWAY END GRADIENT DIRECTION (UP OR DOWN)
    gradient_direction = Column(String(4))
    # L AN 0016 00569  NONE    RUNWAY END POSITION SOURCE
    # L AN 0016 00860  NONE    RUNWAY END POSITION SOURCE
    position_source = Column(String(16))
    # L AN 0010 00585  NONE    RUNWAY END POSITION SOURCE DATE (MM/DD/YYYY)
    # L AN 0010 00876  NONE    RUNWAY END POSITION SOURCE DATE (MM/DD/YYYY)
    position_date = Column(Date)
    # L AN 0016 00595  NONE    RUNWAY END ELEVATION SOURCE
    # L AN 0016 00886  NONE    RUNWAY END ELEVATION SOURCE
    elevation_source = Column(String(16))
    # L AN 0010 00611  NONE    RUNWAY END ELEVATION SOURCE DATE (MM/DD/YYYY)
    # L AN 0010 00902  NONE    RUNWAY END ELEVATION SOURCE DATE (MM/DD/YYYY)
    elevation_date = Column(Date)
    # L AN 0016 00621  NONE    DISPLACED THESHOLD POSITION SOURCE
    # L AN 0016 00912  NONE    DISPLACED THESHOLD POSITION SOURCE
    displaced_threshold_position_source = Column(String(16))
    # L AN 0010 00637  NONE    DISPLACED THESHOLD POSITION SOURCE DATE (MM/DD/YYYY)
    # L AN 0010 00928  NONE    DISPLACED THESHOLD POSITION SOURCE DATE (MM/DD/YYYY)
    displaced_threshold_position_date = Column(Date)
    # L AN 0016 00647  NONE    DISPLACED THESHOLD ELEVATION SOURCE
    # L AN 0016 00938  NONE    DISPLACED THESHOLD ELEVATION SOURCE
    displaced_threshold_elevation_source = Column(String(16))
    # L AN 0010 00663  NONE    DISPLACED THESHOLD ELEVATION SOURCE DATE (MM/DD/YYYY)
    # L AN 0010 00954  NONE    DISPLACED THESHOLD ELEVATION SOURCE DATE (MM/DD/YYYY)
    displaced_threshold_elevation_date = Column(Date)
    # L AN 0016 00673  NONE    TOUCHDOWN ZONE ELEVATION SOURCE
    # L AN 0016 00964  NONE    TOUCHDOWN ZONE ELEVATION SOURCE
    touchdown_zone_elevation_source = Column(String(16))
    # L AN 0010 00689  NONE    TOUCHDOWN ZONE ELEVATION SOURCE DATE (MM/DD/YYYY)
    # L AN 0010 00980  NONE    TOUCHDOWN ZONE ELEVATION SOURCE DATE (MM/DD/YYYY)
    touchdown_zone_elevation_date = Column(Date)
    # R AN 0005 00699  A60     TAKEOFF RUN AVAILABLE (TORA), IN FEET
    # R AN 0005 00990  A60     TAKEOFF RUN AVAILABLE (TORA), IN FEET
    takeoff_run_available = Column(Integer)
    takeoff_run_available_remark = Column(String(1500))
    # R AN 0005 00704  A61     TAKEOFF DISTANCE AVAILABLE (TODA), IN FEET
    # R AN 0005 00995  A61     TAKEOFF DISTANCE AVAILABLE (TODA), IN FEET
    takeoff_distance_available = Column(Integer)
    # R AN 0005 00709  A62     ACLT STOP DISTANCE AVAILABLE (ASDA), IN FEET
    # R AN 0005 01000  A62     ACLT STOP DISTANCE AVAILABLE (ASDA), IN FEET
    accelerate_stop_distance_available = Column(Integer)
    # R AN 0005 00714  A63     LANDING DISTANCE AVAILABLE (LDA), IN FEET
    # R AN 0005 01005  A63     LANDING DISTANCE AVAILABLE (LDA), IN FEET
    landing_distance_available = Column(Integer)
    # R AN 0005 00719  NONE    AVAILABLE LANDING DISTANCE FOR LAND AND HOLD SHORT OPERATIONS
    # R AN 0005 01010  NONE    AVAILABLE LANDING DISTANCE FOR LAND AND HOLD SHORT OPERATIONS
    lahso_distance_available = Column(Integer)
    # L AN 0007 00724  NONE    ID OF INTERSECTING RUNWAY DEFINING HOLD SHORT POINT
    # L AN 0007 01015  NONE    ID OF INTERSECTING RUNWAY DEFINING HOLD SHORT POINT
    id_of_lahso_intersecting_runway = Column(String(7))
    # L AN 0040 00731  NONE    DESCRIPTION OF ENTITY DEFINING HOLD SHORT POINT IF NOT AN INTERSECTING RUNWAY
    # L AN 0040 01022  NONE    DESCRIPTION OF ENTITY DEFINING HOLD SHORT POINT IF NOT AN INTERSECTING RUNWAY
    description_of_lahso_entity = Column(String(40))
    # L AN 0015 00771  NONE    LATITUDE OF LAHSO HOLD SHORT POINT (FORMATTED)
    # L AN 0015 01062  NONE    LATITUDE OF LAHSO HOLD SHORT POINT (FORMATTED)
    lahso_latitude_dms = Column(String(15))
    # L AN 0012 00786  NONE    LATITUDE OF LAHSO HOLD SHORT POINT (SECONDS)
    # L AN 0012 01077  NONE    LATITUDE OF LAHSO HOLD SHORT POINT (SECONDS)
    lahso_latitude_secs = Column(String(12))
    # L AN 0015 00798  NONE    LONGITUDE OF LAHSO HOLD SHORT POINT (FORMATTED)
    # L AN 0015 01089  NONE    LONGITUDE OF LAHSO HOLD SHORT POINT (FORMATTED)
    lahso_longitude_dms = Column(String(15))
    # L AN 0012 00813  NONE    LONGITUDE OF LAHSO HOLD SHORT POINT (SECONDS)
    # L AN 0012 01104  NONE    LONGITUDE OF LAHSO HOLD SHORT POINT (SECONDS)
    lahso_longitude_secs = Column(String(12))
    # L AN 0016 00825  NONE    LAHSO HOLD SHORT POINT LAT/LONG SOURCE
    # L AN 0016 01116  NONE    LAHSO HOLD SHORT POINT LAT/LONG SOURCE
    lahso_coords_source = Column(String(16))
    # L AN 0010 00841  NONE    HOLD SHORT POINT LAT/LONG SOURCE DATE (MM/DD/YYYY)
    # L AN 0010 01132  NONE    HOLD SHORT POINT LAT/LONG SOURCE DATE (MM/DD/YYYY)
    lahso_coords_date = Column(Date)
    # L AN 0388 01142  NONE    RUNWAY RECORD FILLER (BLANK)

    # R U N W A Y   A R R E S T I N G   S Y S T E M   D A T A
    # L AN 0009 00027  E60     TYPE OF AIRCRAFT ARRESTING DEVICE
    arresting_gear = Column(String(9))

    runway = relationship("Runway", back_populates="runway_ends")
    remarks = relationship("RunwayEndRemark", back_populates="runway_end")

    def __repr__(self):
        return "<Runway End(id='%s', runway='%s')>" % (self.id, self.runway)

    def to_dict(self, include=None):
        _include = include or []

        base_attrs = [
            "id",
            "id_remark",
            "true_alignment",
            "true_alignment_remark",
            "approach_type",
            "right_traffic",
            "right_traffic_remark",
            "markings_type",
            "markings_remark",
            "markings_condition",
        ]

        geo_attrs = [
            "latitude_dms",
            "latitude_dms_remark",
            "latitude_secs",
            "longitude_dms",
            "longitude_dms_remark",
            "longitude_secs",
            "elevation",
            "elevation_remark",
            "threshold_crossing_height",
            "threshold_crossing_height_remark",
            "visual_glide_path_angle",
            "visual_glide_path_angle_remark",
            "displaced_threshold_latitude_dms",
            "displaced_threshold_latitude_dms_remark",
            "displaced_threshold_latitude_secs",
            "displaced_threshold_longitude_dms",
            "displaced_threshold_longitude_dms_remark",
            "displaced_threshold_longitude_secs",
            "displaced_threshold_elevation",
            "displaced_threshold_length",
            "displaced_threshold_length_remark",
            "touchdown_zone_elevation",
        ]

        lighting_attrs = [
            "visual_glide_slope_indicators",
            "visual_glide_slope_indicators_remark",
            "rvr_equipment",
            "rvr_equipment_remark",
            "rvv_equipment",
            "approach_light_system",
            "approach_light_system_remark",
            "reil_availability",
            "reil_availability_remark",
            "centerline_light_availability",
            "centerline_light_availability_remark",
            "touchdown_lights_availability",
            "touchdown_lights_availability_remark",
        ]

        obj_attrs = [
            "controlling_object_description",
            "controlling_object_description_remark",
            "controlling_object_marking",
            "controlling_object_marking_remark",
            "part77_category",
            "part77_category_remark",
            "controlling_object_clearance_slope",
            "controlling_object_clearance_slope_remark",
            "controlling_object_height_above_runway",
            "controlling_object_height_above_runway_remark",
            "controlling_object_distance_from_runway",
            "controlling_object_distance_from_runway_remark",
            "controlling_object_centerline_offset",
            "controlling_object_centerline_offset_remark",
        ]

        addl_attrs = [
            "gradient",
            "gradient_remark",
            "gradient_direction",
            "position_source",
            "position_date",
            "elevation_source",
            "elevation_date",
            "displaced_threshold_position_source",
            "displaced_threshold_position_date",
            "displaced_threshold_elevation_source",
            "displaced_threshold_elevation_date",
            "touchdown_zone_elevation_source",
            "touchdown_zone_elevation_date",
            "takeoff_run_available",
            "takeoff_run_available_remark",
            "takeoff_distance_available",
            "accelerate_stop_distance_available",
            "landing_distance_available",
            "lahso_distance_available",
            "id_of_lahso_intersecting_runway",
            "description_of_lahso_entity",
            "lahso_latitude_dms",
            "lahso_latitude_secs",
            "lahso_longitude_dms",
            "lahso_longitude_secs",
            "lahso_coords_source",
            "lahso_coords_date",
            "arresting_gear",
        ]

        if "geographic" in _include or "all" in _include:
            base_attrs += geo_attrs

        if "lighting" in _include or "all" in _include:
            base_attrs += lighting_attrs

        if "object" in _include or "all" in _include:
            base_attrs += obj_attrs

        if "additional" in _include or "all" in _include:
            base_attrs += addl_attrs

        result = dict()

        for attr in base_attrs:
            value = getattr(self, attr)

            if isinstance(value, enum.Enum):
                result[attr] = value.value
            elif isinstance(value, (datetime.date, datetime.datetime)):
                result[attr] = value.isoformat()
            else:
                result[attr] = value

        return result


class AirportRemark(Base):
    __tablename__ = "airport_remarks"

    facility_site_number = Column(
        String(11), ForeignKey("airports.facility_site_number"), primary_key=True
    )
    remark_element_name = Column(String(13), primary_key=True)
    remark = Column(String(1500))

    airport = relationship("Airport", back_populates="remarks")

    def __repr__(self):
        return "<Airport Remark(airport='%s', element_name='%s', remark='%s...')>" % (
            self.airport,
            self.remark_element_name,
            self.remark[:13],
        )


class RunwayRemark(Base):
    __tablename__ = "runway_remarks"

    facility_site_number = Column(String(11), primary_key=True)
    runway_name = Column(String(7), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            [facility_site_number, runway_name],
            [Runway.facility_site_number, Runway.name],
        ),
        {},
    )

    remark_element_name = Column(String(13), primary_key=True)
    remark = Column(String(1500))

    runway = relationship("Runway", back_populates="remarks")

    def __repr__(self):
        return "<Runway Remark(runway='%s', element_name='%s', remark='%s...')>" % (
            self.runway,
            self.remark_element_name,
            self.remark[:13],
        )


class RunwayEndRemark(Base):
    __tablename__ = "runway_end_remarks"

    facility_site_number = Column(String(11), primary_key=True)
    runway_name = Column(String(7), primary_key=True)
    id = Column(String(3), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            [facility_site_number, runway_name, id],
            [RunwayEnd.facility_site_number, RunwayEnd.runway_name, RunwayEnd.id],
        ),
        {},
    )

    remark_element_name = Column(String(13), primary_key=True)
    remark = Column(String(1500))

    runway_end = relationship("RunwayEnd", back_populates="remarks")

    def __repr__(self):
        return (
            "<RunwayEnd Remark(runway_end='%s', element_name='%s', remark='%s...')>"
            % (self.runway_end, self.remark_element_name, self.remark[:13])
        )


class AttendanceSchedule(Base):
    __tablename__ = "attendance_schedules"

    # F A C I L I T Y   A T T E N D A N C E   S C H E D U L E   D A T A
    # L AN 0011 00004  N/A     LANDING FACILITY SITE NUMBER
    facility_site_number = Column(
        String(11), ForeignKey("airports.facility_site_number"), primary_key=True
    )
    # R AN 0002 00017  N/A     ATTENDANCE SCHEDULE SEQUENCE NUMBER
    sequence_number = Column(Integer, primary_key=True)
    # L AN 0108 00019  A17     AIRPORT ATTENDANCE SCHEDULE
    attendance_schedule = Column(String(108))
    # L AN 1403 00127  NONE    ATTENDANCE SCHEDULE RECORD FILLER (BLANK)

    airport = relationship("Airport", back_populates="attendance_schedules")

    def __repr__(self):
        return (
            "<Attendance Schedule(airport='%s', sequence_number='%d', attendance_schedule='%s')>"
            % (self.airport, self.sequence_number, self.attendance_schedule[:13])
        )
