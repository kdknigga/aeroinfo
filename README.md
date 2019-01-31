# aeroinfo
Tools to deal with FAA NASR data

RDBMS settings are set via environment variables.  Tested with Postgresql 10 and 11.

Tested with Python 3.6 and 3.7.

See the following for an example implementation:
https://api.aeronautical.info/dev/?airport=ORD&include=demographic&include=geographic&include=ownership&include=runways

## Getting Started notes
* Start with setting up your python environment.  I'd suggest installing the requirements in a virtualenv.
* Next set up your database.  I'm using postgresql, but I've tried sqlite3 (with tweaks to database/__init__.py), too.  Assuming postgresql, just create the database and a user with permissions to create/alter tables.  No need to actually create tables (See caveat below)
* Now you just have to create environment variables with your database information.  See the top of database/__init__.py for details.
* Finally, use download_nasr.py to download the current FAA NASR subscription data to a local directory and then use import.py to create the database tables and populate the database.

**CAVEAT** import.py will create tables from scratch, but will not alter existing tables.  When I update the database schema, I've been dropping tables and rerunning import.py.  I do plan on implementing [a database migration system](https://github.com/kdknigga/aeroinfo/issues/6) at some point to manage schema changes.

## api.aeronautical.info information
I've set up a web-based API to query a copy of this I have running.

See detail on how to use [here](API.md).
