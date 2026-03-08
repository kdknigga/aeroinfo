#!/usr/bin/env python
"""
Command-line helper to import NASR data into the DB.

Supports both CSV and fixed-width TXT formats.  The ``--format`` flag selects
the parser; when omitted, the csv format is assumed.
"""

import argparse
import logging
from pathlib import Path

from aeroinfo.database import invalidate_caches
from aeroinfo.parsers import apt, apt_csv, nav, nav_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import parsed NASR files into the DB.",
    )
    parser.add_argument("nasrdir", help="Path to NASR data directory")
    parser.add_argument(
        "--format",
        choices=["csv", "txt"],
        default="csv",
        dest="format",
        help="Parser format: csv or txt. Default: %(default)s",
    )
    return parser


def _validate_format(nasrdir: Path, fmt: str) -> None:
    """Validate that required files exist for the chosen format."""
    csv_path = nasrdir / "CSV_Data"
    if fmt == "csv" and not (csv_path / "APT_BASE.csv").exists():
        logger.error("--format csv specified but no CSV files found in %s", nasrdir)
        raise SystemExit(1)
    if fmt == "txt" and not (nasrdir / "APT.txt").exists():
        logger.error("--format txt specified but no TXT files found in %s", nasrdir)
        raise SystemExit(1)


def main(nasrdir: str, fmt: str = "csv") -> None:
    """
    Import NASR data from the given directory.

    Args:
        nasrdir: Path to NASR data directory.
        fmt: Parser format (``"csv"`` or ``"txt"``). Default: ``"csv"``.

    """
    nasrdir_path = Path(nasrdir)

    _validate_format(nasrdir_path, fmt)

    if fmt == "csv":
        csv_path = nasrdir_path / "CSV_Data"
        logger.info("Starting CSV import from %s", csv_path)
        apt_csv.parse(str(csv_path))
        nav_csv.parse(str(csv_path))
    else:
        aptpath = nasrdir_path / "APT.txt"
        logger.info("Starting import of %s", str(aptpath))
        apt.parse(str(aptpath))
        navpath = nasrdir_path / "NAV.txt"
        logger.info("Starting import of %s", str(navpath))
        nav.parse(str(navpath))

    invalidate_caches()
    logger.info("Import complete.")


if __name__ == "__main__":
    args = _build_parser().parse_args()
    main(args.nasrdir, fmt=args.format)
