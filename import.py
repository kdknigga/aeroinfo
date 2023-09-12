#!/usr/bin/env python

import logging
import os
import sys

from parsers import apt, nav

# logging.basicConfig(level=logging.DEBUG)


def main(nasrdir):
    aptpath = os.path.join(nasrdir, "APT.txt")
    logging.info(f"Starting import of {aptpath}")
    apt.parse(aptpath)
    navpath = os.path.join(nasrdir, "NAV.txt")
    logging.info(f"Starting import of {navpath}")
    nav.parse(navpath)


if __name__ == "__main__":
    main(sys.argv[1])
