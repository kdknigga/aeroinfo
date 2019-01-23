#!/usr/bin/env python3

import pprint
from database import find_airport

pp = pprint.PrettyPrinter()

print("#  DPA ###############################")

include = ["geographic", "runways"]
airport = find_airport("DPA", include=include)

pp.pprint(airport.to_dict(include=include))

print("#  dpa ###############################")

include = ["geographic", "runways"]
airport = find_airport("dpa", include=include)

pp.pprint(airport.to_dict(include=include))

print("# KDPA ###############################")

include = ["geographic", "runways"]
airport = find_airport("KDPA", include=include)

pp.pprint(airport.to_dict(include=include))

print("#  3CK ###############################")

include = ["geographic", "runways"]
airport = find_airport("3CK", include=include)

pp.pprint(airport.to_dict(include=include))

print("# LL10 ###############################")

include = ["geographic", "runways"]
airport = find_airport("LL10", include=include)

pp.pprint(airport.to_dict(include=include))

