# aeroinfo

Tools to deal with FAA NASR data

RDBMS settings are set via environment variables. Tested with Postgresql 13 and 16.  Sqlite3 used for testing.

Tested with Python 3.13.

See the following for an example application:
https://api.aeronautical.info/dev/?airport=ORD&include=demographic&include=geographic&include=ownership&include=runways

## Development
- [uv](https://docs.astral.sh/uv/getting-started/installation/) is used to manage dependancies and virtual environments.  Install that, if you don't have it yet.
- Next set up your database. I'm using postgresql, but I've tried sqlite3, too. Assuming postgresql, create the database and a user with permissions to create/alter tables.
- Clone this repo.  In the repo directory, run `uv sync` to set up the virtual environment and install dependancies.
- Create environment variables with your database information.  See details here: https://github.com/kdknigga/aeroinfo/blob/e13e314b59c1c55ee28398e821bbc2fd5b9e43d7/aeroinfo/database/__init__.py#L53-L57
- Run `uv run alembic upgrade head` to build the database schema.
- Finally, run `uv run aeroinfo/download_nasr.py` to download the current FAA NASR subscription data to a local directory and then run `uv run aeroinfo/import.py /path/to/unzipped/directory` to create the database tables and populate the database.

It's probably a good idea to run `uv run alembic upgrade head` after pulling down a new version of aeroinfo. Or, at least check to see if there's been a database schema update and run `uv run alembic upgrade head` if required.

## api.aeronautical.info information

I've set up a web-based API to query an instance of aeroinfo I have running.

See details on how to use [here](API.md).
