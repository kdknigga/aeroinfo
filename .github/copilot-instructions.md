# Copilot instructions for aeroinfo

## Architecture snapshot

- Aeroinfo ingests FAA NASR data (both fixed-width TXT and CSV formats) into SQLAlchemy models exposed via `aeroinfo.database` helpers and an external API described in `API.md`.
- Data domains split into airports/runways (`database/models/apt.py`) and navaids (`database/models/nav.py`); enums in `database/enums.py` keep FAA codes literal for easy serialization.
- Parsers live in `aeroinfo/parsers/`:
  - **TXT parsers** (`apt.py`, `nav.py`): Stream FAA fixed-width files line-by-line, slice fields via `parsers/utils.get_field`, and `session.merge` into the ORM so reruns upsert safely.
  - **CSV parsers** (`apt_csv.py`, `nav_csv.py`, `frq_csv.py`, `ils_csv.py`): Read FAA CSV files using stdlib `csv`, coerce fields via `parsers/utils.csv_field`, and merge into the same ORM models.
  - `utils.py`: Shared helpers -- `get_field` (TXT field slicing), `csv_field` (CSV type coercion), `detect_encoding` (charset-normalizer with UTF-8 fallback).

## Runtime + dependencies

- Target Python 3.13 (see `pyproject.toml`) and manage environments exclusively with `uv` (`uv venv && source .venv/bin/activate`). Use `uv add <package>` for runtime deps and `uv add --dev <package>` for development-only tooling; avoid `uv pip` entirely so dependency metadata stays in `pyproject.toml`/`uv.lock`.
- Keep runtime vs dev dependencies distinct to minimize production installs. `requirements.txt` is legacy-only for older deploy targets--do not invoke it during active development.
- Core deps: SQLAlchemy 2.x, Alembic for migrations, psycopg2-binary for Postgres, requests with urllib3 Retry for downloads, python-dateutil for parsing date fields, charset-normalizer for CSV encoding detection.

## Environment + database

- Configure DB via env vars read in `database/__init__.py`: `DB_RDBM`, `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_NAME` (or set `DB_RDBM=sqlite` and point `DB_HOST` to a file).
- Run `alembic upgrade head` after changing models; `alembic/env.py` bootstraps Alembic using the same env-driven connection.

## NASR data workflow

- Fetch data with `python -m aeroinfo.download_nasr -e current -l info`; it stores zips under a temp dir keyed by edition date and retries 60 times on FAA hiccups.
- Import extracted files using the `--format` flag to select the parser path:
  - **CSV (recommended):** `uv run aeroinfo/import.py /path/to/NASR --format csv`
  - **TXT (legacy):** `uv run aeroinfo/import.py /path/to/NASR --format txt`
- CSV import calls `parsers.apt_csv.parse()` (reads APT_BASE.csv and child files), `parsers.nav_csv.parse()` (reads NAV_BASE.csv and child files), `parsers.frq_csv.parse()` (reads FRQ.csv), and `parsers.ils_csv.parse()` (reads ILS_BASE.csv for approach type enrichment).
- TXT import calls `parsers.apt.parse("APT.txt")` then `parsers.nav.parse("NAV.txt")`.
- For local/offline work, reference files live in `references/` (APT.txt, NAV.txt, \*\_rf.txt for TXT) and `references/csv_refactor/2026-02-19/CSV_Data/` (full CSV dataset).

## Query helpers

- `query.py` demonstrates how to call `find_airport`, `find_runway`, `find_runway_end`, and `find_navaid`; mimic its pattern when building CLIs or tests.
- API consumers expect include lists like ["demographic","runways"]; see `Airport.to_dict` and `API.md` for allowed groups and keep new fields grouped there.

## Coding conventions

- Stick with SQLAlchemy 2.0 typed ORM style (`Mapped[]`, `mapped_column`) and keep FAA comments above fields--agents extend models by mirroring the existing fixed-width annotations.
- When parsing TXT, always go through `get_field` so enum coercions (SegmentedCircleEnum, monitoring categories, bool coercion) stay consistent; avoid manual slicing.
- When parsing CSV, always go through `csv_field` for type coercion (empty string to None, NUMBER to float, enum normalization). This keeps CSV field handling consistent across all CSV parser modules.
- Use `detect_encoding(path)` from `utils.py` before opening CSV files -- charset-normalizer detects the actual encoding with UTF-8 as fallback.
- Database writes use a single session with `session.merge` inside tight loops--respect that pattern to keep idempotent re-imports.

## Testing + QA

- The test suite has 870+ tests covering TXT parsing, CSV parsing, TXT/CSV parity, and snapshot regression. Run `uv run pytest -m fast` for quick feedback or `uv run pytest` for the full suite.
- Test categories:
  - **Fast tests** (`@pytest.mark.fast`): Quick unit tests using minimal fixtures, no DB or reference files needed.
  - **CSV parser tests** (`@pytest.mark.csv`): Tests exercising the CSV parser path (APT/NAV CSV parsing and snapshots).
  - **Snapshot regression**: JSON baselines for both TXT and CSV parsers across 107 curated airports and 5 curated navaids. Baselines live in `tests/snapshots/` with separate directories for TXT (`test_apt_snapshots/`, `test_nav_snapshots/`) and CSV (`test_csv_apt_snapshots/`, `test_csv_nav_snapshots/`).
  - **Parity tests**: Verify TXT and CSV parsers produce identical ORM output for the same airports/navaids.
  - **E2E query tests**: Exercise database queries against imported data (requires live DB).
- `CURATED_AIRPORTS` (107 airports) and `CURATED_NAVAIDS` (5 navaids) in `conftest.py` define the test subjects for snapshot and parity tests.
- Lint with `ruff check .` (config in `pyproject.toml`) and type-check with `ty` (preferred over mypy); new modules should include docstrings to satisfy D104.

## Tooling and running commands

- Important: the project uses `uv` to manage and run the virtual environment. Any tooling that needs access to the project's virtual environment (pytest, linters, formatters, type checkers, or scripts) must be executed with `uv run` so the correct .venv and dependency metadata (pyproject.toml / uv.lock) are used. Examples:
  - `uv run pytest` # run tests inside the project's virtualenv
  - `uv run ruff check .` # run the linter with the project's installed ruff
  - `uv run ty` # run the type checker
  - `uv run python query.py` # run a script with project deps available

Using `python -m pip` or system python without `uv run` can result in missing packages or inconsistent behavior compared to CI.

## Observability + debugging

- Logging is standard library; set env `LOGLEVEL=INFO` or pass `-l info` to scripts to trace downloads/import progress.
- The download session is global with retries configured in `download_nasr.py`; reuse it when adding other FAA endpoints to inherit backoff behavior.

## When extending

- Touch `API.md` whenever include-group semantics change so the public HTTP contract stays truthful.
- Update Alembic migrations alongside ORM edits (see `alembic/versions/*`) and rerun the importer against `references/` fixtures before shipping.
