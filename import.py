#!/usr/bin/env python

import os
import sys
from parsers import apt
from parsers import nav


def main(nasrdir):
    apt.parse(os.path.join(nasrdir, "APT.txt"))
    nav.parse(os.path.join(nasrdir, "NAV.txt"))


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
