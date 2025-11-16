#!/usr/bin/env python
"""
Database engine and convenience helpers.

This module exposes an Engine and a few helper functions to look up
airports, runways, runway ends and navaids.
"""

import logging
import os
from collections.abc import Iterable

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine as SAEngine
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.orm import Load, sessionmaker, with_parent

from aeroinfo.database.models.apt import Airport, Runway, RunwayEnd
from aeroinfo.database.models.nav import Navaid

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    """Build the database URL from environment variables and return it."""
    db_rdbm = os.getenv("DB_RDBM")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    # Basic validation with helpful errors to avoid cryptic SQLAlchemy failures
    if not db_rdbm:
        msg = (
            "Database configuration missing: DB_RDBM is not set.\n"
            "Set DB_RDBM to 'sqlite' or a supported dialect (e.g. 'postgresql').\n"
            "Example (sqlite file): export DB_RDBM=sqlite; export DB_HOST=/path/to/dbfile.db\n"
            "Example (postgres): export DB_RDBM=postgresql; export DB_USER=me; "
            "export DB_PASS=secret; export DB_HOST=localhost; export DB_NAME=mydb"
        )
        raise RuntimeError(msg)

    if db_rdbm == "sqlite":
        if not db_host:
            msg = (
                "DB_RDBM=sqlite requires DB_HOST to be set to the sqlite filename or ':memory:'. "
                "For an in-memory database set DB_HOST=':memory:'."
            )
            raise RuntimeError(msg)
        url = f"{db_rdbm}://{db_host}"
    else:
        missing = [
            name
            for name, val in (
                ("DB_USER", db_user),
                ("DB_PASS", db_pass),
                ("DB_HOST", db_host),
                ("DB_NAME", db_name),
            )
            if not val
        ]
        if missing:
            raise RuntimeError(
                "Database configuration incomplete; missing: " + ", ".join(missing)
            )
        url = f"{db_rdbm}://{db_user}:{db_pass}@{db_host}/{db_name}"

    logger.debug("Database URL: %s", url)
    return url


def _create_engine_safely() -> SAEngine:
    """
    Create and return a SQLAlchemy Engine, rewrapping dialect errors.

    This helper is called lazily by the Engine proxy so importing the package
    doesn't attempt to create the Engine at import time.
    """
    try:
        return create_engine(get_db_url(), echo=False)
    except NoSuchModuleError as exc:  # pragma: no cover - defensive error rewrap
        db_rdbm = os.getenv("DB_RDBM")
        raise RuntimeError(
            f"Unable to initialize database engine: unsupported DB_RDBM='{db_rdbm}'. "
            "Set DB_RDBM to a supported SQLAlchemy dialect (for example 'sqlite' or 'postgresql'). "
            "See project README for examples. Original error: " + str(exc)
        ) from exc


class _LazyEngine:
    """
    Proxy object that lazily constructs a SQLAlchemy Engine on first use.

    It forwards attribute access to the real Engine instance, creating it
    with _create_engine_safely() when needed. This allows modules to import
    `Engine` without triggering engine creation until the code actually uses
    the Engine (for example inside parser.parse or when running queries).
    """

    def __init__(self) -> None:
        self._engine = None

    def _ensure(self) -> SAEngine:
        if self._engine is None:
            self._engine = _create_engine_safely()
        return self._engine

    def __getattr__(self, name: str) -> object:
        return getattr(self._ensure(), name)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        if self._engine is None:
            return "<LazyEngine (not initialized)>"
        return repr(self._engine)


# Public Engine symbol remains available but is lazy.
Engine = _LazyEngine()


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
        queryoptions.append(Load(Airport).joinedload(Airport.runways))

    if "remarks" in _include:
        queryoptions.append(Load(Airport).joinedload(Airport.remarks))

    if "attendance" in _include:
        queryoptions.append(Load(Airport).joinedload(Airport.attendance_schedules))

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
        queryoptions.append(Load(Runway).joinedload(Runway.runway_ends))

    if isinstance(airport, Airport):
        _airport = airport
    elif isinstance(airport, str):
        _airport = find_airport(airport)
    else:
        msg = "Expecting str or Airport"
        raise TypeError(msg)

    Session = sessionmaker(bind=Engine)
    session = Session()

    stmt = (
        select(Runway)
        .where(with_parent(instance=_airport, prop=Airport.runways))
        .filter(Runway.name.like("%" + name + "%"))
        .options(*queryoptions)
    )

    runway = session.execute(stmt).scalars().first()

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

    stmt = (
        select(RunwayEnd)
        .where(with_parent(instance=_runway, prop=Runway.runway_ends))
        .filter(RunwayEnd.id == name.upper())
    )

    rwend = session.execute(stmt).scalars().first()

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
