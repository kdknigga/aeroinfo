#!/usr/bin/env python
"""Small command-line helper to import parsed NASR files into the DB."""

import logging
import sys
from pathlib import Path

from aeroinfo.database import configure_engine, invalidate_caches
from aeroinfo.parsers import apt, nav

logger = logging.getLogger(__name__)


def main(nasrdir: str) -> None:
    """Import APT.txt and NAV.txt from the given NASR directory."""
    nasrdir_path = Path(nasrdir)
    configure_engine(profile="import")
    aptpath = nasrdir_path / "APT.txt"
    logger.info("Starting import of %s", str(aptpath))
    apt.parse(str(aptpath))
    navpath = nasrdir_path / "NAV.txt"
    logger.info("Starting import of %s", str(navpath))
    nav.parse(str(navpath))
    invalidate_caches()


if __name__ == "__main__":
    main(sys.argv[1])
