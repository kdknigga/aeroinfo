#!/usr/bin/env python

import datetime
import enum
import os
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Load, joinedload
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

db_rdbm = os.getenv("DB_RDBM")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

Base = declarative_base()
Engine = create_engine('%s://%s:%s@%s/%s' % (db_rdbm, db_user, db_pass, db_host, db_name), echo=False)
#Engine = create_engine('sqlite:///:memory:', echo=True)

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
    ownership_type = Column(Enum(OwnershipTypeEnum))
    facility_use = Column(Enum(FacilityUseEnum))
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
    coords_method = Column(Enum(DeterminationMethodEnum))
    elevation = Column(Float(1))
    elevation_method = Column(Enum(DeterminationMethodEnum))
    mag_variation = Column(String(3))
    mag_variation_year = Column(Integer)
    pattern_alt = Column(Integer)
    sectional = Column(String(30))
    distance_from_city = Column(Integer)
    direction_from_city = Column(String(3))
    land_area = Column(Integer)
    # FAA SERVICES
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

        if "demographic" in _include:
            base_attrs += demo_attrs

        if "ownership" in _include:
            base_attrs += ownership_attrs

        if "geographic" in _include:
            base_attrs += geo_attrs

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
    # BASE END INFORMATION
    # BASE END GEOGRAPHIC DATA
    # BASE END LIGHTING DATA
    # BASE END OBJECT DATA
    # RECIPROCAL END INFORMATION
    # RECIPROCAL END GEOGRAPHIC DATA
    # RECIPROCAL END LIGHTING DATA
    # RECIPROCAL END OBJECT DATA
    # ADDITIONAL COMMON RUNWAY DATA
    # ADDITIONAL BASE END DATA
    # ADDITIONAL RECIPROCAL END DATA

    airport = relationship("Airport", back_populates="runways")

    def __repr__(self):
        return "<Runway(name='%s', airport='%s')>" % (self.name, self.airport)

    def to_dict(self, include=None):
        _include = include or []
        base_attrs = ["name", "length", "width"]

        result = dict()

        for attr in base_attrs:
            value = getattr(self, attr)
            result[attr] = value

        return result

def find_airport(identifier, include=None):
    _include = include or []
    queryoptions = []

    if "runways" in _include:
        queryoptions.append(Load(Airport).joinedload("runways"))
    
    Session = sessionmaker(bind=Engine)
    session = Session()

    airport = session.query(Airport).filter(
        (Airport.faa_id == identifier.upper()) | (Airport.icao_id == identifier.upper())
    ).options(queryoptions).first()

    session.close()

    return airport    

def find_runway(name, airport):
    if isinstance(airport, Airport):
        _airport = airport
    elif isinstance(airport, str):
        _airport = find_airport(airport)
    else:
        raise(TypeError("Expecting str or Airport"))

    Session = sessionmaker(bind=Engine)
    session = Session()

    runway = session.query(Runway).with_parent(airport).filter(Runway.name.like("%" + name + "%")).scalar()

    return runway


Base.metadata.create_all(Engine)
