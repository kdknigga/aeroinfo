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

## api.aeronautical.info information

I've set up a web-based API to query an instance of aeroinfo I have running.

See details on how to use [here](API.md).
