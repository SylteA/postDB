__version__ = "0.0.1"
__author__ = "Sylte"
__licence__ = "MIT"
__copyright__ = "Copyright (c) 2020 Sylte"
__title__ = "postDB"

from .model.column import Column
from .model.model import Model

from collections import namedtuple
import logging

VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")


def get_version(version: tuple):
    """Return a cleaned up version number from VERSION."""
    return "%s %s.%s.%s" % (version[3], version[0], version[1], version[2])


VERSION = (0, 0, 1, "alpha", 0)
version_info = VersionInfo(*VERSION)

logging.getLogger(__name__).addHandler(logging.NullHandler())
