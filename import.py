#!/usr/bin/env python

import datetime
import sqlalchemy
from dateutil import parser as dateparser
from sqlalchemy.orm import sessionmaker
from database import OwnershipTypeEnum, FacilityUseEnum, DeterminationMethodEnum
from database import Airport, Runway, Engine

nasr_txt_file = "/tmp/FAA_NASR/2019-01-03/APT.txt"

def get_field(record, start, length, var_type="str"):
    s = start - 1
    e = start + length - 1
    field = record[s:e].strip()
    if field == "":
        return None
    else:
        if var_type == "int":
            return int(field)
        elif var_type == "float":
            return float(field)
        elif var_type == "date":
            return dateparser.parse(field)
        elif var_type == "OwnershipTypeEnum":
            return OwnershipTypeEnum[field]
        elif var_type == "FacilityUseEnum":
            return FacilityUseEnum[field]
        elif var_type == "DeterminationMethodEnum":
            return DeterminationMethodEnum[field]
        else:
            return field

Session = sessionmaker(bind=Engine)
session = Session()

with open(nasr_txt_file, "r", errors='replace') as f:
    for line in f:
        record_type = get_field(line, 1, 3)

        if record_type == "APT":
            airport = Airport()
            # L A N D I N G   F A C I L I T Y   D A T A
            airport.facility_site_number = get_field(line, 4, 11)
            airport.facility_type = get_field(line, 15, 13)
            airport.faa_id = get_field(line, 28, 4)
            airport.effective_date = get_field(line, 32, 10, "date")
            # DEMOGRAPHIC DATA
            airport.region = get_field(line, 42, 3)
            airport.field_office = get_field(line, 45, 4)
            airport.state_code = get_field(line, 49, 2)
            airport.state_name = get_field(line, 51, 20)
            airport.county = get_field(line, 71, 21)
            airport.countys_state = get_field(line, 92, 2)
            airport.city = get_field(line, 94, 40)
            airport.name = get_field(line, 134, 50)
            # OWNERSHIP DATA
            airport.ownership_type = get_field(line, 184, 2, "OwnershipTypeEnum")
            airport.facility_use = get_field(line, 186, 2, "FacilityUseEnum")
            airport.owners_name = get_field(line, 188, 35)
            airport.owners_address = get_field(line, 223, 72)
            airport.owners_city_state_zip = get_field(line, 295, 45)
            airport.owners_phone = get_field(line, 240, 16)
            airport.managers_name = get_field(line, 356, 35)
            airport.managers_address = get_field(line, 391, 72)
            airport.managers_city_state_zip = get_field(line, 463, 45)
            airport.managers_phone = get_field(line, 508, 16)
            # GEOGRAPHIC DATA
            airport.latitude_dms = get_field(line, 524, 15)
            airport.latitude_secs = get_field(line, 539, 12)
            airport.longitude_dms = get_field(line, 551, 15)
            airport.longitude_secs = get_field(line, 566, 12)
            airport.coords_method = get_field(line, 578, 1, "DeterminationMethodEnum")
            airport.elevation = get_field(line, 579, 7, "float")
            airport.elevation_method = get_field(line, 586, 1, "DeterminationMethodEnum")
            airport.mag_variation = get_field(line, 587, 3)
            airport.mag_variation_year = get_field(line, 590, 4, "int")
            airport.pattern_alt = get_field(line, 594, 4, "int")
            airport.sectional = get_field(line, 598, 30)
            airport.distance_from_city = get_field(line, 628, 2, "int")
            airport.direction_from_city = get_field(line, 630, 3)
            airport.land_area = get_field(line, 633, 5, "int")
            # FAA SERVICES
            # FEDERAL STATUS
            # AIRPORT INSPECTION DATA
            # AIRPORT SERVICES
            # AIRPORT FACILITIES
            # BASED AIRCRAFT
            # ANNUAL OPERATIONS
            # ADDITIONAL AIRPORT DATA
            airport.icao_id = get_field(line, 1211, 7)

            session.merge(airport)

        if record_type == "RWY":
            runway = Runway()
            # F A C I L I T Y   R U N W A Y   D A T A
            runway.facility_site_number = get_field(line, 4, 11)
            runway.name = get_field(line, 17, 7)
            # COMMON RUNWAY DATA
            runway.length = get_field(line, 24, 5, "int")
            runway.width = get_field(line, 29, 4, "int")
            runway.surface_type_condition = get_field(line, 33, 12)
            runway.surface_treatment = get_field(line, 45, 5)
            runway.pavement_classification_number = get_field(line, 50, 11)
            runway.edge_light_intensity = get_field(line, 61, 5)
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

            session.merge(runway)


session.commit()
