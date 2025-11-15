#!/usr/bin/env python3

"""
Base database utilities and SQLAlchemy declarative base.

This module exposes the SQLAlchemy declarative base used by the
database models.
"""

import logging
from typing import Any

from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)
Base: Any = declarative_base()
