#!/usr/bin/env python3

import pprint
from database import find_airport

pp = pprint.PrettyPrinter()

include = ["geographic", "runways"]
airport = find_airport("DPA", include=include)

pp.pprint(airport.to_dict(include=include))

