#!/usr/bin/env python

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Load, sessionmaker

from .models.apt import Airport, Runway, RunwayEnd
from .models.nav import Navaid

logger = logging.getLogger(__name__)


def get_db_url():
    db_rdbm = os.getenv("DB_RDBM")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    if db_rdbm == "sqlite":
        url = "%s://%s" % (db_rdbm, db_host)
    else:
        url = "%s://%s:%s@%s/%s" % (db_rdbm, db_user, db_pass, db_host, db_name)

    logger.debug(f"Database URL: {url}")
    return url


Engine = create_engine(get_db_url(), echo=False)


def find_airport(identifier, include=None):
    _include = include or []
    queryoptions = []

    if "runways" in _include:
        queryoptions.append(Load(Airport).joinedload("runways"))

    if "remarks" in _include:
        queryoptions.append(Load(Airport).joinedload("remarks"))

    if "attendance" in _include:
        queryoptions.append(Load(Airport).joinedload("attendance_schedules"))

    Session = sessionmaker(bind=Engine)
    session = Session()

    airport = (
        session.query(Airport)
        .filter(
            (Airport.faa_id == identifier.upper())
            | (Airport.icao_id == identifier.upper())
        )
        .order_by(Airport.effective_date.desc())
        .options(queryoptions)
        .first()
    )

    session.close()

    return airport


def find_runway(name, airport, include=None):
    _include = include or []
    queryoptions = []

    if "runway_ends" in _include:
        queryoptions.append(Load(Runway).joinedload("runway_ends"))

    if isinstance(airport, Airport):
        _airport = airport
    elif isinstance(airport, str):
        _airport = find_airport(airport)
    else:
        raise (TypeError("Expecting str or Airport"))

    Session = sessionmaker(bind=Engine)
    session = Session()

    runway = (
        session.query(Runway)
        .with_parent(_airport)
        .filter(Runway.name.like("%" + name + "%"))
        .options(queryoptions)
        .scalar()
    )

    session.close()

    return runway


def find_runway_end(name, runway, include=None):
    _include = include or []

    if isinstance(runway, Runway):
        _runway = runway
    elif isinstance(runway, tuple):
        __runway, airport = runway

        assert isinstance(__runway, str)

        if isinstance(airport, Airport):
            _airport = airport
        elif isinstance(airport, str):
            _airport = find_airport(airport)
        else:
            raise (TypeError("Expecting str or Airport in runway tuple"))

        _runway = find_runway(__runway, _airport)

    Session = sessionmaker(bind=Engine)
    session = Session()

    rwend = (
        session.query(RunwayEnd)
        .with_parent(_runway)
        .filter(RunwayEnd.id == name.upper())
        .scalar()
    )

    session.close()

    return rwend


def find_navaid(identifier, type, include=None):
    _include = include or []

    Session = sessionmaker(bind=Engine)
    session = Session()

    navaid = (
        session.query(Navaid)
        .filter(
            (Navaid.facility_id == identifier.upper())
            & (Navaid.facility_type == type.upper())
        )
        .order_by(Navaid.effective_date.desc())
        .first()
    )

    session.close()

    return navaid
