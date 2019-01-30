#!/usr/bin/env python

import datetime
import enum
from . import enums
from .base import Base
from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy import Enum, ForeignKey, Boolean
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.orm import relationship

class Airport(Base):
    __tablename__ = "airports"

    # L A N D I N G   F A C I L I T Y   D A T A
    facility_site_number = Column(String(11), primary_key=True)
    facility_type = Column(String(13))
    faa_id = Column(String(4), index=True)
    effective_date = Column(Date)
    # DEMOGRAPHIC DATA
    region = Column(String(3))
    field_office = Column(String(4))
    state_code = Column(String(2))
    state_name = Column(String(20))
    county = Column(String(21))
    countys_state = Column(String(2))
    city = Column(String(40))
    name = Column(String(50))
    # OWNERSHIP DATA
    ownership_type = Column(Enum(enums.OwnershipTypeEnum))
    facility_use = Column(Enum(enums.FacilityUseEnum))
    owners_name = Column(String(35))
    owners_address = Column(String(72))
    owners_city_state_zip = Column(String(45))
    owners_phone = Column(String(16))
    managers_name = Column(String(35))
    managers_address = Column(String(72))
    managers_city_state_zip = Column(String(45))
    managers_phone = Column(String(16))
    # GEOGRAPHIC DATA
    latitude_dms = Column(String(15))
    latitude_secs = Column(String(12))
    longitude_dms = Column(String(15))
    longitude_secs = Column(String(12))
    coords_method = Column(Enum(enums.DeterminationMethodEnum))
    elevation = Column(Float(1))
    elevation_method = Column(Enum(enums.DeterminationMethodEnum))
    mag_variation = Column(String(3))
    mag_variation_year = Column(Integer)
    pattern_alt = Column(Integer)
    sectional = Column(String(30))
    distance_from_city = Column(Integer)
    direction_from_city = Column(String(3))
    land_area = Column(Integer)
    # FAA SERVICES
    boundary_artcc_id = Column(String(4))
    boundary_artcc_computer_id = Column(String(3))
    boundary_artcc_name = Column(String(30))
    responsible_artcc_id = Column(String(4))
    responsible_artcc_computer_id = Column(String(3))
    responsible_artcc_name = Column(String(30))
    tie_in_fss_local = Column(Boolean)
    tie_in_fss_id = Column(String(4))
    tie_in_fss_name = Column(String(30))
    fss_local_phone = Column(String(16))
    fss_toll_free_phone = Column(String(16))
    alternate_fss_id = Column(String(4))
    alternate_fss_name = Column(String(30))
    alternate_fss_toll_free_phone = Column(String(16))
    notam_facility = Column(String(4))
    notam_d_available = Column(Boolean)
    # FEDERAL STATUS
    # AIRPORT INSPECTION DATA
    # AIRPORT SERVICES
    # AIRPORT FACILITIES
    # BASED AIRCRAFT
    # ANNUAL OPERATIONS
    # ADDITIONAL AIRPORT DATA
    icao_id = Column(String(7), index=True)

    runways = relationship("Runway", back_populates="airport")

    def __repr__(self):
        return "<Airport(name='%s', faa='%s', icao='%s')>" % (self.name, self.faa_id, self.icao_id)

    def to_dict(self, include=None):
        _include = include or []

        base_attrs = ["facility_type", "faa_id", "icao_id"]
        base_attrs += ["name", "effective_date"]

        demo_attrs = ["region", "field_office", "state_code", "state_name"]
        demo_attrs += ["county", "countys_state", "city"]

        ownership_attrs = ["ownership_type", "facility_use", "owners_name"]
        ownership_attrs += ["owners_address", "owners_city_state_zip"]
        ownership_attrs += ["owners_phone", "managers_name", "managers_address"]
        ownership_attrs += ["managers_city_state_zip", "managers_phone"]

        geo_attrs = ["latitude_dms", "latitude_secs", "longitude_dms"]
        geo_attrs += ["longitude_secs", "coords_method", "elevation"]
        geo_attrs += ["elevation_method", "mag_variation", "mag_variation_year"]
        geo_attrs += ["pattern_alt", "sectional", "distance_from_city"]
        geo_attrs += ["direction_from_city", "land_area"]

        faasrv_attrs = ["boundary_artcc_id", "boundary_artcc_computer_id"]
        faasrv_attrs += ["boundary_artcc_name", "responsible_artcc_id"]
        faasrv_attrs += ["responsible_artcc_computer_id", "responsible_artcc_name"]
        faasrv_attrs += ["tie_in_fss_local", "tie_in_fss_id", "tie_in_fss_name"]
        faasrv_attrs += ["fss_local_phone", "fss_toll_free_phone", "alternate_fss_id"]
        faasrv_attrs += ["alternate_fss_name", "alternate_fss_toll_free_phone"]
        faasrv_attrs += ["notam_facility", "notam_d_available"]

        if "demographic" in _include:
            base_attrs += demo_attrs

        if "ownership" in _include:
            base_attrs += ownership_attrs

        if "geographic" in _include:
            base_attrs += geo_attrs

        if "faaservices" in _include:
            base_attrs += faasrv_attrs

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

        return result

class Runway(Base):
    __tablename__ = "runways"

    # F A C I L I T Y   R U N W A Y   D A T A
    facility_site_number = Column(String(11), ForeignKey("airports.facility_site_number"), primary_key=True)
    name = Column(String(7), primary_key=True)
    # COMMON RUNWAY DATA
    length = Column(Integer)
    width = Column(Integer)
    surface_type_condition = Column(String(12))
    surface_treatment = Column(String(5))
    pavement_classification_number = Column(String(11))
    edge_light_intensity = Column(String(5))
    # ADDITIONAL COMMON RUNWAY DATA
    length_source = Column(String(16))
    length_source_date = Column(Date)
    weight_bearing_capacity_single_wheel = Column(String(6))
    weight_bearing_capacity_dual_wheels = Column(String(6))
    weight_bearing_capacity_two_dual_wheels_tandem = Column(String(6))
    weight_bearing_capacity_two_dual_wheels_double_tandem = Column(String(6))

    airport = relationship("Airport", back_populates="runways")
    runway_ends = relationship("RunwayEnd", back_populates="runway")

    def __repr__(self):
        return "<Runway(name='%s', airport='%s')>" % (self.name, self.airport)

    def to_dict(self, include=None):
        _include = include or []

        base_attrs = ["name", "length", "width", "surface_type_condition"]
        base_attrs += ["surface_treatment", "pavement_classification_number", "edge_light_intensity"]

        addl_attrs = ["length_source", "length_source_date", "weight_bearing_capacity_single_wheel"]
        addl_attrs += ["weight_bearing_capacity_dual_wheels", "weight_bearing_capacity_two_dual_wheels_tandem"]
        addl_attrs += ["weight_bearing_capacity_two_dual_wheels_double_tandem"]

        if "additional" in _include:
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

    __table_args__ = (ForeignKeyConstraint([facility_site_number, runway_name],
                                           [Runway.facility_site_number, Runway.name]),
                      {})

    # RUNWAY END INFORMATION
    id = Column(String(3), primary_key=True)
    true_alignment = Column(Integer)
    approach_type = Column(String(10))
    right_traffic = Column(Boolean)
    markings_type = Column(Enum(enums.RunwayMarkingsTypeEnum))
    markings_condition = Column(Enum(enums.RunwayMarkingsConditionEnum))
    # RUNWAY END GEOGRAPHIC DATA
    latitude_dms = Column(String(15))
    latitude_secs = Column(String(12))
    longitude_dms = Column(String(15))
    longitude_secs = Column(String(12))
    elevation = Column(Float(1))
    threshold_crossing_height = Column(Integer)
    visual_glide_path_angle = Column(Float(2))
    displaced_threshold_latitude_dms = Column(String(15))
    displaced_threshold_latitude_secs = Column(String(12))
    displaced_threshold_longitude_dms = Column(String(15))
    displaced_threshold_longitude_secs = Column(String(12))
    displaced_threshold_elevation = Column(Float(1))
    displaced_threshold_length = Column(Integer)
    touchdown_zone_elevation = Column(Float(1))
    # RUNWAY END LIGHTING DATA
    visual_glide_slope_indicators = Column(Enum(enums.VisualGlideSlopeIndicatorEnum))
    rvr_equipment = Column(Enum(enums.RVREquipmentEnum))
    rvv_equipment = Column(Boolean)
    approach_light_system = Column(String(8))
    reil_availability = Column(Boolean)
    centerline_light_availability = Column(Boolean)
    touchdown_lights_availability = Column(Boolean)
    # RUNWAY END OBJECT DATA
    controlling_object_description = Column(String(11))
    controlling_object_marking = Column(Enum(enums.ControllingObjectMarkingEnum))
    part77_category = Column(String(5))
    controlling_object_clearance_slope = Column(Integer)
    controlling_object_height_above_runway = Column(Integer)
    controlling_object_distance_from_runway = Column(Integer)
    controlling_object_centerline_offset = Column(String(7))
    # ADDITIONAL RUNWAY END DATA
    gradient = Column(String(5))
    gradient_direction = Column(String(4))
    position_source = Column(String(16))
    position_date = Column(Date)
    elevation_source = Column(String(16))
    elevation_date = Column(Date)
    displaced_threshold_position_source = Column(String(16))
    displaced_threshold_position_date = Column(Date)
    displaced_threshold_elevation_source = Column(String(16))
    displaced_threshold_elevation_date = Column(Date)
    touchdown_zone_elevation_source = Column(String(16))
    touchdown_zone_elevation_date = Column(Date)
    takeoff_run_available = Column(Integer)
    takeoff_distance_available = Column(Integer)
    accelerate_stop_distance_available = Column(Integer)
    landing_distance_available = Column(Integer)
    lahso_distance_available = Column(Integer)
    id_of_lahso_intersecting_runway = Column(String(7))
    description_of_lahso_entity = Column(String(40))
    lahso_latitude_dms = Column(String(15))
    lahso_latitude_secs = Column(String(12))
    lahso_longitude_dms = Column(String(15))
    lahso_longitude_secs = Column(String(12))
    lahso_coords_source = Column(String(16))
    lahso_coords_date = Column(Date)

    runway = relationship("Runway", back_populates="runway_ends")

    def __repr__(self):
        return "<Runway End(id='%s', runway='%s')>" % (self.id, self.runway)

    def to_dict(self, include=None):
        _include = include or []

        base_attrs = ["id", "approach_type", "right_traffic", "markings_type"]
        base_attrs += ["markings_condition"]

        geo_attrs = ["latitude_dms", "latitude_secs", "longitude_dms", "longitude_secs"]
        geo_attrs += ["elevation", "threshold_crossing_height", "visual_glide_path_angle"]
        geo_attrs += ["displaced_threshold_latitude_dms", "displaced_threshold_latitude_secs"]
        geo_attrs += ["displaced_threshold_longitude_dms", "displaced_threshold_longitude_secs"]
        geo_attrs += ["displaced_threshold_elevation", "displaced_threshold_length"]
        geo_attrs += ["touchdown_zone_elevation"]

        lighting_attrs = ["visual_glide_slope_indicators", "rvr_equipment", "rvv_equipment"]
        lighting_attrs += ["approach_light_system", "reil_availability"]
        lighting_attrs += ["centerline_light_availability", "touchdown_lights_availability"]

        obj_attrs = ["controlling_object_description", "controlling_object_marking"]
        obj_attrs += ["part77_category", "controlling_object_clearance_slope"]
        obj_attrs += ["controlling_object_height_above_runway", "controlling_object_distance_from_runway"]
        obj_attrs += ["controlling_object_centerline_offset"]

        addl_attrs = ["gradient", "gradient_direction", "position_source", "position_date"]
        addl_attrs += ["elevation_source", "elevation_date", "displaced_threshold_position_source"]
        addl_attrs += ["displaced_threshold_position_date", "displaced_threshold_elevation_source"]
        addl_attrs += ["displaced_threshold_elevation_date", "touchdown_zone_elevation_source"]
        addl_attrs += ["touchdown_zone_elevation_date", "takeoff_run_available"]
        addl_attrs += ["takeoff_distance_available", "accelerate_stop_distance_available"]
        addl_attrs += ["landing_distance_available", "lahso_distance_available"]
        addl_attrs += ["id_of_lahso_intersecting_runway", "description_of_lahso_entity"]
        addl_attrs += ["lahso_latitude_dms", "lahso_latitude_secs"]
        addl_attrs += ["lahso_longitude_dms", "lahso_longitude_secs"]
        addl_attrs += ["lahso_coords_source", "lahso_coords_date"]

        if "geographic" in _include:
            base_attrs += geo_attrs

        if "lighting" in _include:
            base_attrs += lighting_attrs

        if "object" in _include:
            base_attrs += obj_attrs

        if "additional" in _include:
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