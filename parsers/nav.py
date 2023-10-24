#!/usr/bin/env python

import logging

from sqlalchemy.orm import sessionmaker

from database import Engine
from database.models.nav import (
    AirspaceFix,
    FanMarker,
    HoldingPattern,
    Navaid,
    Remark,
    VORReceiverCheckpoint,
)

from .utils import get_field

logger = logging.getLogger(__name__)


def parse(txtfile):
    Session = sessionmaker(bind=Engine)
    session = Session()

    with open(txtfile, "r", errors="replace") as f:
        for line in f:
            logger.debug(f"line: {line}")
            record_type = get_field(line, 1, 4)

            if record_type == "NAV1":
                n = Navaid()
                n.facility_id = get_field(line, 5, 4)
                n.facility_type = get_field(line, 9, 20)
                n.official_facility_id = get_field(line, 29, 4)
                n.effective_date = get_field(line, 33, 10, "date")
                n.name = get_field(line, 43, 30)
                n.city = get_field(line, 73, 40)
                n.state_name = get_field(line, 113, 30)
                n.state_code = get_field(line, 143, 2)
                n.region = get_field(line, 145, 3)
                n.country = get_field(line, 148, 30)
                n.country_code = get_field(line, 178, 2)
                n.owners_name = get_field(line, 180, 50)
                n.operators_name = get_field(line, 230, 50)
                n.common_system_usage = get_field(line, 280, 1)
                n.public_use = get_field(line, 281, 1)
                n.navaid_class = get_field(line, 282, 11)
                n.hours_of_operation = get_field(line, 293, 11)
                n.high_altitude_artcc_id = get_field(line, 304, 4)
                n.high_altitude_artcc_name = get_field(line, 308, 30)
                n.low_altitude_artcc_id = get_field(line, 338, 4)
                n.low_altitude_artcc_name = get_field(line, 342, 30)
                n.latitude_dms = get_field(line, 372, 14)
                n.latitude_secs = get_field(line, 386, 11)
                n.longitude_dms = get_field(line, 397, 14)
                n.longitude_secs = get_field(line, 411, 11)
                n.coords_survey_accuracy = get_field(
                    line, 422, 1, "NavaidPositionSurveyAccuracyEnum"
                )
                n.tacan_only_latitude_dms = get_field(line, 423, 14)
                n.tacan_only_latitude_secs = get_field(line, 437, 11)
                n.tacan_only_longitude_dms = get_field(line, 448, 14)
                n.tacan_only_longitude_secs = get_field(line, 462, 11)
                n.elevation = get_field(line, 473, 7, "float")
                n.mag_variation = get_field(line, 480, 5)
                n.mag_variation_year = get_field(line, 485, 4, "int")
                n.simultaneous_voice = get_field(line, 489, 3)
                n.power_output_watts = get_field(line, 492, 4, "int")
                n.automatic_voice_id = get_field(line, 496, 3)
                n.monitoring_category = get_field(
                    line, 499, 1, "NavaidMonitoringCategoryEnum"
                )
                n.radio_voice_call_name = get_field(line, 500, 30)
                n.tacan_channel = get_field(line, 530, 4)
                n.frequency = get_field(line, 534, 6)
                n.transmitted_id = get_field(line, 540, 24)
                n.fan_marker_type = get_field(line, 564, 10)
                n.fan_marker_true_bearing = get_field(line, 574, 3, "int")
                n.vor_service_volume = get_field(line, 577, 2)
                n.dme_service_volume = get_field(line, 579, 2)
                n.low_altitude_facility_used_in_high_structure = get_field(line, 581, 3)
                n.z_marker_available = get_field(line, 584, 3)
                n.tweb_hours = get_field(line, 587, 9)
                n.tweb_phone_number = get_field(line, 596, 20)
                n.fss_id = get_field(line, 616, 4)
                n.fss_name = get_field(line, 620, 30)
                n.fss_hours_of_operation = get_field(line, 650, 100)
                n.notam_accountability_code = get_field(line, 750, 4)
                n.quadrant_id_and_range_leg_bearing = get_field(line, 754, 16)
                n.navaid_status = get_field(line, 770, 30)
                n.pitch = get_field(line, 800, 1)
                n.catch = get_field(line, 801, 1)
                n.sua_atcaa = get_field(line, 802, 1)
                n.navaid_restriction = get_field(line, 803, 1)
                n.hiwas = get_field(line, 804, 1)
                n.tweb = get_field(line, 805, 1)

                session.merge(n)

            if record_type == "NAV2":
                r = Remark()
                r.facility_id = get_field(line, 5, 4)
                r.facility_type = get_field(line, 9, 20)
                r.remark = get_field(line, 29, 600)

                session.merge(r)

            if record_type == "NAV3":
                f = AirspaceFix()
                f.facility_id = get_field(line, 5, 4)
                f.facility_type = get_field(line, 9, 20)
                f.fix = get_field(line, 29, 36)
                f.more_fixes = get_field(line, 65, 720)

                session.merge(f)

            if record_type == "NAV4":
                h = HoldingPattern()
                h.facility_id = get_field(line, 5, 4)
                h.facility_type = get_field(line, 9, 20)
                h.holding_pattern = get_field(line, 29, 80)
                h.holding_pattern_pattern = get_field(line, 109, 3)
                h.more_holding_patterns = get_field(line, 112, 664)

                session.merge(h)

            if record_type == "NAV5":
                f = FanMarker()
                f.facility_id = get_field(line, 5, 4)
                f.facility_type = get_field(line, 9, 20)
                f.fan_marker = get_field(line, 29, 30)
                f.more_fan_markers = get_field(line, 59, 690)

                session.merge(f)

            if record_type == "NAV6":
                v = VORReceiverCheckpoint()
                v.facility_id = get_field(line, 5, 4)
                v.facility_type = get_field(line, 9, 20)
                v.air_ground = get_field(line, 29, 2)
                v.bearing = get_field(line, 31, 3, "int")
                v.altitude = get_field(line, 34, 5, "int")
                v.airport_id = get_field(line, 39, 4)
                v.state = get_field(line, 43, 2)
                v.air_narrative = get_field(line, 45, 75)
                v.ground_narrative = get_field(line, 120, 75)

                session.merge(v)

    session.commit()
