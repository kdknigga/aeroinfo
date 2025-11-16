#!/usr/bin/env python3
"""Small interactive queries used during development."""

import logging
import pprint

from aeroinfo.database import find_airport, find_navaid, find_runway, find_runway_end

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter()


def _demo() -> None:
    include = ["demographic"]

    logger.info("#  DPA ###############################")
    airport = find_airport("DPA", include=include)
    if airport is not None:
        pp.pprint(airport.to_dict(include=include))

    logger.info("#  dpa ###############################")
    airport = find_airport("dpa", include=include)
    if airport is not None:
        pp.pprint(airport.to_dict(include=include))

    logger.info("# KDPA ###############################")
    airport = find_airport("KDPA", include=include)
    if airport is not None:
        pp.pprint(airport.to_dict(include=include))

    logger.info("#  3CK ###############################")
    airport = find_airport("3CK", include=include)
    if airport is not None:
        pp.pprint(airport.to_dict(include=include))

    logger.info("#  SSI ###############################")
    airport = find_airport("SSI")
    if airport is not None:
        pp.pprint(airport.to_dict())

    include = ["demographic", "runways"]
    logger.info("# LL10 ###############################")
    airport = find_airport("LL10", include=include)
    if airport is not None:
        pp.pprint(airport.to_dict(include=include))

    include = ["additional", "runway_ends"]
    logger.info("# LL10 runway 18/36 ##################")
    if airport is not None:
        runway = find_runway("18", airport, include=include)
        if runway is not None:
            pp.pprint(runway.to_dict(include=include))

    include = ["geographic", "lighting"]
    logger.info("# LL10 runway 36 #####################")
    if airport is not None and runway is not None:
        rwend = find_runway_end("36", runway, include=include)
        if rwend is not None:
            pp.pprint(rwend.to_dict(include=include))

    logger.info("#  JOT VOR ###########################")
    navaid = find_navaid("JOT", "VOR/DME")
    pp.pprint(navaid)


if __name__ == "__main__":
    _demo()
