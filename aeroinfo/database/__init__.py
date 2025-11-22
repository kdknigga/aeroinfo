#!/usr/bin/env python
"""
Database engine and convenience helpers.

This module exposes an Engine and a few helper functions to look up
airports, runways, runway ends and navaids.
"""

import logging
import os
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Engine as SAEngine
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.orm import Load, Session, sessionmaker, with_parent
from sqlalchemy.util import LRUCache

from aeroinfo.database.models.apt import Airport, Runway, RunwayEnd
from aeroinfo.database.models.nav import Navaid

logger = logging.getLogger(__name__)


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


_CACHE_ENABLED = _parse_bool(os.getenv("AEROINFO_CACHE_ENABLED"), default=True)
_AIRPORT_CACHE_SIZE = _env_int("AEROINFO_CACHE_AIRPORT_SIZE", 512)
_NAVAID_CACHE_SIZE = _env_int("AEROINFO_CACHE_NAVAID_SIZE", 512)
_CACHE_GENERATION = 0


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


def _create_engine_safely(overrides: dict[str, Any]) -> SAEngine:
    """Create and return a SQLAlchemy Engine."""
    try:
        url = get_db_url()
        engine_kwargs = overrides.copy()

        compiled_cache_size = engine_kwargs.pop("compiled_cache_size", 0)

        engine = create_engine(url, future=True, **engine_kwargs)
        if compiled_cache_size:
            engine = engine.execution_options(
                compiled_cache=LRUCache(compiled_cache_size)
            )
        return engine
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
        self._engine: SAEngine | None = None
        self._overrides: dict[str, Any] = {}

    def _ensure(self) -> SAEngine:
        if self._engine is None:
            self._engine = _create_engine_safely(self._overrides)
        return self._engine

    def __getattr__(self, name: str) -> object:
        return getattr(self._ensure(), name)

    def connect(self) -> Connection:
        """Return a new Connection from the underlying Engine."""
        return self._ensure().connect()

    def configure(self, **overrides: object) -> None:
        if overrides:
            # Coerce overrides to a dict[str, object] and merge into stored overrides.
            self._overrides |= dict(overrides)
        self.dispose()

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def __repr__(self) -> str:  # pragma: no cover - trivial
        if self._engine is None:
            return "<LazyEngine (not initialized)>"
        return repr(self._engine)


# Public Engine symbol remains available but is lazy.
Engine = _LazyEngine()

# Session factory reused by the query helpers and callers that want manual control.
SessionLocal = sessionmaker(bind=Engine, expire_on_commit=False, future=True)


def configure_engine(**overrides: object) -> None:
    """Reconfigure (or swap) the lazily created Engine."""
    Engine.configure(**overrides)


def get_session() -> Session:
    """Return a new Session bound to the shared Engine."""
    return SessionLocal()


@contextmanager
def session_scope(session: Session | None = None) -> Iterator[Session]:
    """Provide a context manager that shares or creates Sessions."""
    if session is not None:
        yield session
        return

    created = SessionLocal()
    try:
        yield created
    finally:
        created.close()


def _normalize_identifier(identifier: str) -> str:
    return identifier.strip().upper()


def _normalize_facility_type(facility_type: str) -> str:
    return facility_type.strip().upper()


def _prepare_include(
    include: Iterable[str] | None,
) -> tuple[frozenset[str], tuple[str, ...]]:
    values: list[str] = []
    if include:
        for entry in include:
            if entry not in values:
                values.append(entry)
    include_flags = frozenset(values)
    include_key = tuple(sorted(include_flags))
    return include_flags, include_key


def _fetch_airport(
    session: Session, identifier: str, include_flags: frozenset[str]
) -> Airport | None:
    queryoptions = []

    if "runways" in include_flags:
        queryoptions.append(Load(Airport).joinedload(Airport.runways))

    if "remarks" in include_flags:
        queryoptions.append(Load(Airport).joinedload(Airport.remarks))

    if "attendance" in include_flags:
        queryoptions.append(Load(Airport).joinedload(Airport.attendance_schedules))

    return (
        session.query(Airport)
        .filter((Airport.faa_id == identifier) | (Airport.icao_id == identifier))
        .order_by(Airport.effective_date.desc())
        .options(*queryoptions)
        .first()
    )


def _fetch_navaid(
    session: Session, identifier: str, facility_type: str
) -> Navaid | None:
    return (
        session.query(Navaid)
        .filter(
            (Navaid.facility_id == identifier) & (Navaid.facility_type == facility_type)
        )
        .order_by(Navaid.effective_date.desc())
        .first()
    )


if _CACHE_ENABLED and _AIRPORT_CACHE_SIZE > 0:

    @lru_cache(maxsize=_AIRPORT_CACHE_SIZE)
    def _airport_cache_lookup(
        identifier: str, include_key: tuple[str, ...], generation: int
    ) -> Airport | None:
        # `generation` is part of the cache key so callers can invalidate by
        # bumping it; reference it here to satisfy linters.
        _ = generation
        include_flags = frozenset(include_key)
        with session_scope() as session:
            return _fetch_airport(session, identifier, include_flags)


else:  # pragma: no cover - exercised when caching disabled via env

    def _airport_cache_lookup(
        identifier: str, include_key: tuple[str, ...], generation: int
    ) -> Airport | None:
        _ = generation
        include_flags = frozenset(include_key)
        with session_scope() as session:
            return _fetch_airport(session, identifier, include_flags)


if _CACHE_ENABLED and _NAVAID_CACHE_SIZE > 0:

    @lru_cache(maxsize=_NAVAID_CACHE_SIZE)
    def _navaid_cache_lookup(
        identifier: str, facility_type: str, generation: int
    ) -> Navaid | None:
        _ = generation
        with session_scope() as session:
            return _fetch_navaid(session, identifier, facility_type)


else:  # pragma: no cover - exercised when caching disabled via env

    def _navaid_cache_lookup(
        identifier: str, facility_type: str, generation: int
    ) -> Navaid | None:
        _ = generation
        with session_scope() as session:
            return _fetch_navaid(session, identifier, facility_type)


def invalidate_caches() -> None:
    """Clear local LRU caches, typically after running an import."""
    global _CACHE_GENERATION
    _CACHE_GENERATION += 1

    cache_clear = getattr(_airport_cache_lookup, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()

    cache_clear = getattr(_navaid_cache_lookup, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()


def find_airport(
    identifier: str,
    include: Iterable[str] | None = None,
    *,
    session: Session | None = None,
    use_cache: bool | None = None,
) -> Airport | None:
    """
    Return the most recent Airport matching FAA or ICAO identifier.

    The optional "include" iterable can request joined collections like
    "runways" or "remarks".
    """
    include_flags, include_key = _prepare_include(include)
    identifier_key = _normalize_identifier(identifier)
    should_cache = (
        use_cache if use_cache is not None else (_CACHE_ENABLED and session is None)
    )

    if should_cache:
        return _airport_cache_lookup(identifier_key, include_key, _CACHE_GENERATION)

    with session_scope(session) as active_session:
        return _fetch_airport(active_session, identifier_key, include_flags)


def find_runway(
    name: str,
    airport: Airport | str,
    include: Iterable[str] | None = None,
    *,
    session: Session | None = None,
) -> Runway | None:
    """Return a Runway by name for a given airport (object or identifier)."""
    include_flags, _ = _prepare_include(include)
    queryoptions = []

    if "runway_ends" in include_flags:
        queryoptions.append(Load(Runway).joinedload(Runway.runway_ends))

    with session_scope(session) as active_session:
        if isinstance(airport, Airport):
            _airport = airport
        elif isinstance(airport, str):
            _airport = find_airport(airport, session=active_session, use_cache=False)
            if _airport is None:
                return None
        else:
            msg = "Expecting str or Airport"
            raise TypeError(msg)

        stmt = (
            select(Runway)
            .where(with_parent(instance=_airport, prop=Airport.runways))
            .filter(Runway.name.like("%" + name + "%"))
            .options(*queryoptions)
        )

        return active_session.execute(stmt).scalars().first()


def find_runway_end(
    name: str,
    runway: Runway | tuple[str, str] | tuple[str, Airport],
    include: Iterable[str] | None = None,
    *,
    session: Session | None = None,
) -> RunwayEnd | None:
    """Return a RunwayEnd by id for a given runway or (runway_name, airport)."""
    _ = include
    with session_scope(session) as active_session:
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
                _airport = find_airport(
                    airport, session=active_session, use_cache=False
                )
                if _airport is None:
                    return None
            else:
                msg = "Expecting str or Airport in runway tuple"
                raise TypeError(msg)

            _runway = find_runway(__runway, _airport, session=active_session)
            if _runway is None:
                return None
        else:
            msg = "Expecting Runway or tuple"
            raise TypeError(msg)

        stmt = (
            select(RunwayEnd)
            .where(with_parent(instance=_runway, prop=Runway.runway_ends))
            .filter(RunwayEnd.id == name.upper())
        )

        return active_session.execute(stmt).scalars().first()


def find_navaid(
    identifier: str,
    facility_type: str,
    include: Iterable[str] | None = None,
    *,
    session: Session | None = None,
    use_cache: bool | None = None,
) -> Navaid | None:
    """Return the most recent Navaid matching an identifier and facility type."""
    _prepare_include(include)

    identifier_key = _normalize_identifier(identifier)
    facility_type_key = _normalize_facility_type(facility_type)
    should_cache = (
        use_cache if use_cache is not None else (_CACHE_ENABLED and session is None)
    )

    if should_cache:
        return _navaid_cache_lookup(
            identifier_key, facility_type_key, _CACHE_GENERATION
        )

    with session_scope(session) as active_session:
        return _fetch_navaid(active_session, identifier_key, facility_type_key)
