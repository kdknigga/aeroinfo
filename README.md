# aeroinfo

Tools to deal with FAA NASR data

RDBMS settings are set via environment variables. Tested with Postgresql 10 and 11.

Tested with Python 3.8 and 3.10.

See the following for an example application:
https://api.aeronautical.info/dev/?airport=ORD&include=demographic&include=geographic&include=ownership&include=runways

## Getting Started notes

- Start with setting up your python environment. I'd suggest installing the requirements in a virtualenv.
- Next set up your database. I'm using postgresql, but I've tried sqlite3, too. Assuming postgresql, create the database and a user with permissions to create/alter tables.
- Create environment variables with your database information. See the top of database/\_\_init\_\_.py for details.
- Run `alembic upgrade head` to build the database schema.
- Finally, use download_nasr.py to download the current FAA NASR subscription data to a local directory and then use import.py to create the database tables and populate the database.

It's probably a good idea to run `alembic upgrade head` after pulling down a new version of aeroinfo. Or, at least check to see if there's been a database schema update and run `alembic upgrade head` if required.

## Engine profiles, caching, and sessions

- The shared SQLAlchemy engine now exposes two tuned profiles:
	- `lambda` (default) keeps a one-connection pool optimized for bursty AWS Lambda reads.
	- `import` grows the pool and timeouts to keep bulk NASR imports flowing. The importer selects this profile automatically.
	Choose a profile via the `AEROINFO_ENGINE_PROFILE` env var or programmatically with `aeroinfo.database.configure_engine(profile="import")` before creating sessions. Both profiles enable SQLAlchemy's compiled statement cache to trim per-query CPU.
- `find_airport` and `find_navaid` include opt-in LRU caches sized via `AEROINFO_CACHE_AIRPORT_SIZE`/`AEROINFO_CACHE_NAVAID_SIZE` (set `AEROINFO_CACHE_ENABLED=0` to disable). After imports, call `aeroinfo.database.invalidate_caches()` to clear stale entries; this happens automatically after `aeroinfo.import` finishes.
- Use `aeroinfo.database.get_session()` or `session_scope()` to reuse a single session for chained lookups (airport → runway → runway end) and reduce Lambda connection churn.

## api.aeronautical.info information

I've set up a web-based API to query an instance of aeroinfo I have running.

See details on how to use [here](API.md).
