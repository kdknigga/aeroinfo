"""
Aeroinfo package.

Tools to work transform FAA NASR flat files into a queryable database.
"""

import importlib.metadata

__version__ = importlib.metadata.version("aeroinfo")
__all__ = ["database", "parsers"]
