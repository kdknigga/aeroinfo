#!/usr/bin/env python3

import pprint

from database import find_airport, find_navaid, find_runway, find_runway_end

pp = pprint.PrettyPrinter()

include = ["demographic"]

print("#  DPA ###############################")
airport = find_airport("DPA", include=include)
pp.pprint(airport.to_dict(include=include))

print("#  dpa ###############################")
airport = find_airport("dpa", include=include)
pp.pprint(airport.to_dict(include=include))

print("# KDPA ###############################")
airport = find_airport("KDPA", include=include)
pp.pprint(airport.to_dict(include=include))

print("#  3CK ###############################")
airport = find_airport("3CK", include=include)
pp.pprint(airport.to_dict(include=include))

print("#  SSI ###############################")
airport = find_airport("SSI")
pp.pprint(airport.to_dict())

include = ["demographic", "runways"]
print("# LL10 ###############################")
airport = find_airport("LL10", include=include)
pp.pprint(airport.to_dict(include=include))

include = ["additional", "runway_ends"]
print("# LL10 runway 18/36 ##################")
runway = find_runway("18", airport, include=include)
pp.pprint(runway.to_dict(include=include))

include = ["geographic", "lighting"]
print("# LL10 runway 36 #####################")
rwend = find_runway_end("36", runway, include=include)
pp.pprint(rwend.to_dict(include=include))

print("#  JOT VOR ###########################")
navaid = find_navaid("JOT", "VOR/DME")
pp.pprint(navaid)
