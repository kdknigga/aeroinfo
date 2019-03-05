#!/usr/bin/env python

import os
from .base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Load, joinedload
from sqlalchemy.orm import sessionmaker
from .models import Airport
from .models import Runway
from .models import RunwayEnd

db_rdbm = os.getenv("DB_RDBM")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

Engine = create_engine('%s://%s:%s@%s/%s' % (db_rdbm, db_user, db_pass, db_host, db_name), echo=False)

def find_airport(identifier, include=None):
    _include = include or []
    queryoptions = []

    if "runways" in _include:
        queryoptions.append(Load(Airport).joinedload("runways"))

    if "remarks" in _include:
        queryoptions.append(Load(Airport).joinedload("remarks"))

    Session = sessionmaker(bind=Engine)
    session = Session()

    airport = session.query(Airport).filter(
        (Airport.faa_id == identifier.upper()) | (Airport.icao_id == identifier.upper())
    ).options(queryoptions).scalar()

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
        raise(TypeError("Expecting str or Airport"))

    Session = sessionmaker(bind=Engine)
    session = Session()

    runway = session.query(Runway).with_parent(_airport).filter(
        Runway.name.like("%" + name + "%")
        ).options(queryoptions).scalar()

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
            raise(TypeError("Expecting str or Airport in runway tuple"))

        _runway = find_runway(__runway, _airport)

    Session = sessionmaker(bind=Engine)
    session = Session()

    rwend = session.query(RunwayEnd).with_parent(_runway).filter(
        RunwayEnd.id == name.upper()
        ).scalar()

    session.close()

    return rwend



def init_tables():
    Base.metadata.create_all(Engine)

