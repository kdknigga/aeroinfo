# Testing Guide

This document covers everything you need to know about running, understanding, and
extending the aeroinfo test suite.

## Stack

| Tool | Version | Purpose |
|------|---------|---------|
| [pytest](https://docs.pytest.org/) | 9.0.1+ | Test runner |
| [syrupy](https://github.com/syrupy-project/syrupy) | 5.x | Snapshot regression testing (JSON format) |
| SQLAlchemy | 2.x | In-memory SQLite databases for isolated tests |
| [uv](https://docs.astral.sh/uv/) | latest | Package/dependency manager |

Tests run locally — there is no CI pipeline.

## Prerequisites

1. **Python 3.13** and **uv** installed.

2. Install dev dependencies:

   ```bash
   uv sync
   ```

   This installs pytest, syrupy, and everything else from
   `[dependency-groups.dev]` in `pyproject.toml`.

3. **Reference files** — needed for integration and snapshot tests:

   ```
   references/APT.txt                              (~46 MB, full FAA airport data)
   references/NAV.txt                              (~3.5 MB, full FAA navaid data)
   references/csv_refactor/2026-02-19/CSV_Data/    (FAA CSV dataset)
   ```

   TXT reference files are downloaded by the NASR import process. CSV reference
   files are only needed for CSV-specific tests; fast tests and TXT tests still
   work without them.

4. **`.env` file** (optional) — only needed if running against an external
   database for manual testing. All automated tests (including query behavior
   tests) use in-memory SQLite and don't need it. Format:

   ```bash
   DB_RDBM=postgresql     # or "sqlite"
   DB_USER=myuser
   DB_PASS=mypassword
   DB_HOST=localhost
   DB_NAME=aeroinfo
   ```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run only fast tests (no DB, no reference files needed)
uv run pytest -m fast

# Run only CSV parser tests
uv run pytest -m csv

# Verbose output with test names
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Filter by name pattern
uv run pytest -k "test_apt"

# List tests without running them
uv run pytest --co

# Update snapshot baselines (see "Updating Snapshots" section below)
uv run pytest --snapshot-update
```

## Test Directory Layout

```
tests/
├── conftest.py                     # Shared fixtures, CURATED_AIRPORTS (107), CURATED_NAVAIDS (5), engine fixtures
├── snapshot_helpers.py             # extract_record() -- ORM-to-dict serialization
├── parity/                         # TXT/CSV parity comparison tests
│   └── helpers/                    # Parity test helper modules
├── snapshots/
│   ├── test_apt_snapshots/         # TXT APT JSON baselines (107 airports)
│   ├── test_csv_apt_snapshots/     # CSV APT JSON baselines (107 airports)
│   ├── test_csv_nav_snapshots/     # CSV NAV JSON baselines (5 navaids)
│   └── test_nav_snapshots/         # TXT NAV JSON baselines (5 navaids)
├── test_apt_csv.py                 # CSV APT parser unit tests
├── test_apt_snapshots.py           # TXT APT snapshot regression tests
├── test_csv_apt_snapshots.py       # CSV APT snapshot regression tests
├── test_csv_nav_snapshots.py       # CSV NAV snapshot regression tests
├── test_csv_utils.py               # csv_field(), detect_encoding() unit tests
├── test_enum_serialization.py      # Enum serialization unit tests
├── test_ils_csv.py                 # ILS CSV parser unit tests
├── test_import.py                  # Import pipeline tests (format detection, --format flag)
├── test_nav_csv.py                 # CSV NAV parser unit tests
├── test_nav_snapshots.py           # TXT NAV snapshot regression tests
├── test_query_behaviors.py         # Query behavior tests (in-memory SQLite via query_engine fixture)
└── test_snapshot_helpers.py        # Tests for extract_record() helper
```

## Test Categories

### Fast Tests (`@pytest.mark.fast`)

**Files:** `test_snapshot_helpers.py`, `test_csv_utils.py`

These tests are explicitly marked `@pytest.mark.fast` and use in-memory model
instances or pure-function inputs. They need no database connection and no
large reference files — ideal for quick feedback during development.

```bash
uv run pytest -m fast
```

**What they cover:**

- `test_snapshot_helpers.py` — Verifies `extract_record()` handles enums, dates,
  nulls, and full column coverage.
- `test_csv_utils.py` — Tests `csv_field()` type coercion and `detect_encoding()`
  charset detection.

### Unit Tests (unmarked)

**Files:** `test_enum_serialization.py`, `test_csv_utils.py`

These test enum behavior, `to_dict()` serialization, and CSV utility functions
using in-memory model instances. They don't need a database or reference files
but aren't all marked `fast`, so they run with the full suite.

### Snapshot Regression Tests

**Files:** `test_apt_snapshots.py`, `test_nav_snapshots.py` (TXT), `test_csv_apt_snapshots.py`, `test_csv_nav_snapshots.py` (CSV)

Parse reference files once per module (via a module-scoped fixture), then assert
every field of curated records against committed JSON snapshot baselines. Both
TXT and CSV parsers produce snapshots for the same set of curated records,
enabling direct comparison.

**Curated test subjects:**

| Parser | Count | Examples | Why selected |
|--------|-------|----------|--------------|
| APT | 107 airports | LL10 (private GA), EDF (military), MDW (commercial), ARR (medium public GA) | Diverse airport types covering different field populations |
| NAV | 5 navaids | AST (VOR/DME), BER (TACAN), CZF (NDB), FAI (VORTAC), EDN (VOR) | Cover all navaid types and all 5 NAV sub-record types |

See `CURATED_AIRPORTS` in `tests/conftest.py` for the full list.

Each test runs two assertions:

1. **Field coverage** — Checks that `extract_record()` produces a key for every
   ORM column (fails with an actionable "missing/extra" message).
2. **Snapshot equality** — Compares the serialized dict against the committed
   JSON baseline via syrupy.

### CSV Parser Tests (`@pytest.mark.csv`)

**Files:** `test_apt_csv.py`, `test_nav_csv.py`, `test_ils_csv.py`

These exercise the CSV parser path for airports, navaids, and ILS records.
They follow the same engine-swap pattern as other parser tests.

```bash
uv run pytest -m csv
```

### Import Pipeline Tests

**File:** `test_import.py`

Tests the `--format` flag, format auto-detection logic, and the import pipeline
entry point.

### Query Behavior Tests

**File:** `test_query_behaviors.py`

These test the public query API (`find_airport()`, `find_navaid()`,
`find_runway()`, `find_runway_end()`) against an in-memory SQLite database
populated by CSV parsers via the `query_engine` fixture in `conftest.py`.

The `query_engine` fixture parses the full 2026-02-19 CSV dataset (APT + NAV)
into a single in-memory SQLite engine, making these tests fully self-contained
with no external database dependency.

## How Fixtures Work

### Environment Loading

`conftest.py` loads `.env` **at module scope** before any `aeroinfo` imports.
This is critical because `aeroinfo.database` creates a SQLAlchemy Engine at
import time — the environment must be set first.

### In-Memory Model Fixtures

Four fixtures in `conftest.py` create lightweight ORM instances without touching
a database:

| Fixture | Provides | Depends on |
|---------|----------|------------|
| `sample_airport` | `Airport` with demographic fields | — |
| `sample_runway` | `Runway` attached to `sample_airport` | `sample_airport` |
| `sample_runway_end` | `RunwayEnd` with lighting enum | `sample_runway` |
| `sample_navaid` | `Navaid` with basic fields | — |

All four use **lazy imports** inside the fixture body (e.g.,
`from aeroinfo.database.models.apt import Airport`) so that `.env` is loaded
before any model code runs.

### Module-Scoped Engine Fixtures

**TXT engine fixtures** — defined in `test_apt_snapshots.py` and
`test_nav_snapshots.py`:

- `apt_engine` — Parses `references/APT.txt` into in-memory SQLite once per
  module, shared by all TXT APT snapshot tests.
- `nav_engine` — Parses `references/NAV.txt` into in-memory SQLite once per
  module, shared by all TXT NAV snapshot tests.

**CSV engine fixtures** — defined in `conftest.py`, shared by CSV snapshot and
parity tests:

- `csv_apt_engine` — Parses the CSV APT dataset into in-memory SQLite once per
  module, shared by CSV APT snapshot and parity tests.
- `csv_nav_engine` — Parses the CSV NAV dataset into in-memory SQLite once per
  module, shared by CSV NAV snapshot and parity tests.

**Query engine fixture** — defined in `conftest.py`, used by query behavior tests:

- `query_engine` — Parses both CSV APT and NAV datasets into a single in-memory
  SQLite engine, calls `invalidate_caches()` to clear LRU entries. Used by
  `test_query_behaviors.py` to test the public query API.

All engine fixtures follow the same pattern:

1. Creates an in-memory SQLite engine.
2. Swaps `aeroinfo.database.Engine._engine` to point to it.
3. Creates the ORM schema.
4. Reloads the parser module (so it picks up the swapped engine).
5. Parses the full reference file **once**.
6. Yields the engine to all tests in the module.
7. Restores the original engine on teardown.

This avoids re-parsing large files for every test case.

### Snapshot Fixture

The `snapshot` fixture in `conftest.py` overrides syrupy's default serializer
to use JSON:

```python
@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    return snapshot.use_extension(JSONSnapshotExtension)
```

## How Database Mocking Works

The project doesn't use `unittest.mock`. Instead, it relies on **direct
`_engine` swap** (used in snapshot tests and CSV parser tests):

```python
db.Engine._engine = engine  # swap in
yield engine
db.Engine._engine = original  # restore
```

After patching, parser modules are reloaded with `importlib.reload()` so they
use the in-memory engine instead of the real one.

## Snapshot Testing In Depth

### How It Works

[syrupy](https://github.com/syrupy-project/syrupy) compares a test's output
against a committed JSON file. If the output matches, the test passes. If it
differs, syrupy shows a field-level diff.

**Configuration** (in `pyproject.toml`):

```toml
[tool.pytest.ini_options]
addopts = "--snapshot-dirname=snapshots"
```

**Snapshot file naming:**

```
tests/snapshots/<test_module_name>/test_function[parametrize_id].json
```

### Serialization Rules

`tests/snapshot_helpers.py` provides `extract_record()`, which serializes ORM
instances to plain dicts:

| Column Type | Serialization |
|-------------|---------------|
| `NASREnum` | `{"code": "AGL", "description": "GREAT LAKES"}` |
| `datetime.date` | ISO 8601 string (e.g., `"2024-01-15"`) |
| `None` | `None` |
| `String`, `Integer`, `Float`, `Boolean` | Pass through as-is |
| Anything else | Raises `TypeError` (forces you to update the helper) |

Nested records (runways, runway ends, remarks, sub-records) are serialized
recursively by helper functions in each snapshot test module (e.g.,
`_build_airport_snapshot()`, `_build_navaid_snapshot()`).

### Updating Snapshots

When parser logic or models change, snapshots need to be regenerated:

```bash
uv run pytest --snapshot-update
```

**Important rules:**

- Always update against **committed reference files** — don't regenerate
  snapshots with partial or modified data.
- **Review the diff** after updating. Check that anchor values (airport name,
  facility ID, coordinates) look correct.
- Run **without `-k` filters** when updating. syrupy deletes orphaned snapshot
  files for parametrize IDs that no longer exist — filtering can cause it to
  incorrectly delete snapshots for IDs that were just excluded from the run.
- After review, commit the updated `.json` files.

### Adding a New Snapshot Test Subject

**For airports:**

1. Add the FAA ID to `CURATED_AIRPORTS` in `tests/conftest.py`.
2. Verify the airport exists in both `references/APT.txt` and the CSV dataset
   under `references/csv_refactor/2026-02-19/CSV_Data/`.
3. Run TXT snapshot update: `uv run pytest --snapshot-update -k "test_apt_snapshot"`
4. Run CSV snapshot update: `uv run pytest --snapshot-update -k "test_csv_apt_snapshot"`
5. Review and commit both sets of baselines.

**For navaids:**

1. Add a `(facility_id, facility_type)` tuple to `CURATED_NAVAIDS` in
   `tests/conftest.py`.
2. Verify the navaid exists in both `references/NAV.txt` and the CSV dataset.
3. Run TXT snapshot update: `uv run pytest --snapshot-update -k "test_nav_snapshot"`
4. Run CSV snapshot update: `uv run pytest --snapshot-update -k "test_csv_nav_snapshot"`
5. Review and commit both sets of baselines.

## Writing New Tests

### Adding a Unit Test

1. Create or edit a `test_*.py` file in `tests/`.
2. Mark with `@pytest.mark.fast` if it needs no database or reference files.
3. Use fixtures from `conftest.py` for in-memory model instances.

```python
@pytest.mark.fast
def test_my_feature(sample_airport: Airport) -> None:
    """Description of what is being asserted."""
    result = sample_airport.some_method()
    assert result == expected_value
```

### Adding an Integration Test

Follow the engine-patching pattern from the snapshot test modules:

```python
def test_my_parser_test(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(db, "Engine", engine)
    Base.metadata.create_all(engine)

    importlib.reload(parser_module)
    parser_module.parse(str(data_path))

    # Assert against parsed records
```

Use `references/` data for full-coverage tests.

### Adding a New Model to Snapshot Tests

1. Write a `_build_*_snapshot()` function that calls `extract_record()` on the
   model and recursively serializes its child relationships.
2. Write a `_assert_*_field_coverage()` function that checks every ORM column
   is present in the serialized output.
3. If the model uses a new SQLAlchemy column type, update `extract_record()` in
   `tests/snapshot_helpers.py` to handle it (otherwise it will raise
   `TypeError`).

## Conventions

- **Naming:** Test files use `test_*.py`; test functions use `test_*` prefix
  with descriptive names.
- **Docstrings:** Every test function has a docstring explaining what is being
  asserted.
- **Structure:** AAA pattern — Arrange, Act, Assert.
- **Assertions:** Plain `assert` statements (no `self.assertEqual`). Ruff rule
  `S101` is suppressed for `tests/**` in `pyproject.toml`.
- **Imports:** Use `TYPE_CHECKING` guards for type hints to avoid
  circular/premature imports. Use lazy imports inside fixtures.
- **No async:** The codebase is synchronous — no async test patterns.

## pytest Configuration Reference

Full configuration from `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--snapshot-dirname=snapshots"
markers = [
    "fast: quick tests that use minimal fixtures and run in-memory",
    "csv: tests that exercise the CSV parser path (APT/NAV CSV parity and snapshots)",
]
```

Ruff test-specific config (also in `pyproject.toml`):

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]   # Allow assert statements in tests
```
