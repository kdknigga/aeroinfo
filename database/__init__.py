#!/usr/bin/env python
"""
Database engine and convenience helpers.

This module exposes an Engine and a few helper functions to look up
airports, runways, runway ends and navaids.
"""

import logging
import os
from collections.abc import Iterable

from sqlalchemy import create_engine
from sqlalchemy.orm import Load, sessionmaker

from .models.apt import Airport, Runway, RunwayEnd
from .models.nav import Navaid

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    """Build the database URL from environment variables and return it."""
    db_rdbm = os.getenv("DB_RDBM")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    if db_rdbm == "sqlite":
        url = f"{db_rdbm}://{db_host}"
    else:
        url = f"{db_rdbm}://{db_user}:{db_pass}@{db_host}/{db_name}"

    logger.debug("Database URL: %s", url)
    return url


Engine = create_engine(get_db_url(), echo=False)


def find_airport(
    identifier: str, include: Iterable[str] | None = None
) -> Airport | None:
    """
    Return the most recent Airport matching FAA or ICAO identifier.

    The optional "include" iterable can request joined collections like
    "runways" or "remarks".
    """
    _include: list[str] = list(include or [])
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


def find_runway(
    name: str, airport: Airport | str, include: Iterable[str] | None = None
) -> Runway | None:
    """Return a Runway by name for a given airport (object or identifier)."""
    _include: list[str] = list(include or [])
    queryoptions = []

    if "runway_ends" in _include:
        queryoptions.append(Load(Runway).joinedload("runway_ends"))

    if isinstance(airport, Airport):
        _airport = airport
    elif isinstance(airport, str):
        _airport = find_airport(airport)
    else:
        msg = "Expecting str or Airport"
        raise TypeError(msg)

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


def find_runway_end(
    name: str,
    runway: Runway | tuple[str, str] | tuple[str, Airport],
    include: Iterable[str] | None = None,
) -> RunwayEnd | None:
    """Return a RunwayEnd by id for a given runway or (runway_name, airport)."""
    _include: list[str] = list(include or [])

    if isinstance(runway, Runway):
        _runway = runway
    elif isinstance(runway, tuple):
        __runway, airport = runway

        if not isinstance(__runway, str):
            msg = "Expecting runway name as str in runway tuple"
            raise TypeError(msg)

        if isinstance(airport, Airport):
            _airport = airport
        elif isinstance(airport, str):
            _airport = find_airport(airport)
            if _airport is None:
                # Couldn't resolve the airport identifier; no runway can be found.
                return None
        else:
            msg = "Expecting str or Airport in runway tuple"
            raise TypeError(msg)

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


def find_navaid(
    identifier: str, facility_type: str, include: Iterable[str] | None = None
) -> Navaid | None:
    """Return the most recent Navaid matching an identifier and facility type."""
    _include: list[str] = list(include or [])

    Session = sessionmaker(bind=Engine)
    session = Session()

    navaid = (
        session.query(Navaid)
        .filter(
            (Navaid.facility_id == identifier.upper())
            & (Navaid.facility_type == facility_type.upper())
        )
        .order_by(Navaid.effective_date.desc())
        .first()
    )

    session.close()

    return navaid
