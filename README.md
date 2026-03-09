# aeroinfo

Tools to deal with FAA NASR data

RDBMS settings are set via environment variables. Tested with Postgresql 13 and 16.  Sqlite3 used for testing.

Tested with Python 3.13.

See the following for an example application:
https://api.aeronautical.info/dev/?airport=ORD&include=demographic&include=geographic&include=ownership&include=runways

## FAA's TXT to CSV Migration
The FAA is deprecating the TXT format this project was originally designed to handle, in favor of a CSV format.

Version 3.0.0 of this project has added support for the CSV format and gone through great pains to ensure the product of the CSV parsers is the same as the product of the TXT parsers, to the extent possible.

### Usage changes
`import.py` now defaults to using the CSV parsers.  The `--format txt` argument can be given to force use of the TXT parsers.  Other than that, no changes have been made to the way the script is used.

The CSV files are included in the normal NASR zip file, so no real changes were needed in the downloading process, except extracting them from a zip file that's included in the main zip file.  No changes to usage.

### Output changes
Despite our best efforts, there are some of the known changes to the CSV parsing output compared to the TXT parser output.

* boundary_artcc_* - these fields have no equivalent in the CSV files, so they are now just NULL
* airport based aircraft and annual operations - these fields were deprecated in both TXT and CSV datasets in September, 2024, and are now just NULL
* a few remarks fields no longer exist, no longer are populated, or have different contents in the CSV data files compared to the TXT files
* G100UL fuel is now represented as G100UL instead of G100


## Development
- [uv](https://docs.astral.sh/uv/getting-started/installation/) is used to manage dependencies and virtual environments.  Install that, if you don't have it yet.
- Next set up your database. I'm using postgresql, but I've tried sqlite3, too. Assuming postgresql, create the database and a user with permissions to create/alter tables.
- Clone this repo.  In the repo directory, run `uv sync` to set up the virtual environment and install dependencies.
- Create environment variables with your database information.  See details here: https://github.com/kdknigga/aeroinfo/blob/e13e314b59c1c55ee28398e821bbc2fd5b9e43d7/aeroinfo/database/__init__.py#L53-L57
- Run `uv run alembic upgrade head` to build the database schema.
- Download the current FAA NASR subscription data and import it. The FAA is transitioning from fixed-width TXT to CSV format (TXT sunset: Dec 2026).

  **Download NASR data set:**
  ```bash
  uv run aeroinfo/download_nasr.py
  ```
  This will download and extract the data set, and print the path to it.

  **CSV (recommended):**
  ```bash
  uv run aeroinfo/import.py /path/to/nasr_data --format csv
  ```

  **TXT (legacy):**
  ```bash
  uv run aeroinfo/import.py /path/to/nasr_data --format txt
  ```

It's probably a good idea to run `uv run alembic upgrade head` after pulling down a new version of aeroinfo. Or, at least check to see if there's been a database schema update and run `uv run alembic upgrade head` if required.

## Snapshot Testing

Snapshot fixture files in `tests/__snapshots__/` capture parser output field-by-field. Follow these rules when working with them:

- **Only run `--snapshot-update` against committed reference files.** The reference files in `references/` are the source of truth; running the update flag against uncommitted or modified input data produces incorrect baselines.
- **Verify anchor values before committing updated snapshots.** After running `uv run pytest --snapshot-update`, inspect the diff for key fields (e.g., airport name, facility ID, coordinates) to confirm the parser produced correct output — not just that it ran without error.
- **Run without `-k` filters when updating.** syrupy deletes snapshots for tests not collected in the session; a filtered `--snapshot-update` run will orphan snapshots for uncollected tests.

See TESTING.md for more details.

## api.aeronautical.info information

I've set up a web-based API to query an instance of aeroinfo I have running.

See details on how to use [here](API.md).
