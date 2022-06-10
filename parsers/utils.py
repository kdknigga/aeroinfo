#!/usr/bin/env python

import datetime
from dateutil import parser as dateparser

def get_field(record, start, length, var_type="str"):
    s = start - 1
    e = start + length - 1
    field = record[s:e].strip()
    #print(f"line: {record}\nstart: {start}, length: {length}\nfield: {field}\n\n")
    if field == "":
        return None
    else:
        if var_type == "int":
            return int(field)
        elif var_type == "float":
            return float(field)
        elif var_type == "bool":
            if field in ["Y", "y", "T", "t"]:
                return True
            else:
                return False
        elif var_type == "date":
            return dateparser.parse(field)
        elif var_type == "mdydate":
            return datetime.datetime.strptime(field, "%m%d%Y").date()
        elif var_type == "AirportInspectionMethodEnum":
            # Literals like 1 or 2 can't be members of an enum, so translate them
            if field == "1":
                return "O"
            elif field == "2":
                return "T"
            else:
                return field
        elif var_type == "SegmentedCircleEnum":
            # Y-L is an invalid member of an enum, so translate to YL
            if field == "Y-L":
                return "YL"
            else:
                return field
        else:
            return field

