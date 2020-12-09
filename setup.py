import sys

import setuptools

CURRENT_VERSION = sys.version_info[:2]
REQUIRED_VERSION = (3, 6)

if CURRENT_VERSION < REQUIRED_VERSION:
    sys.stderr.write(
        """
==========================
Unsupported Python version
==========================
This version of postDB requires  Python {}.{}, but you're trying to
install it on Python {}.{}.
This may be because you are using a version of pip that doesn't
understand the python_requires classifier. Make sure you
have pip >= 9.0 and setuptools >= 24.2, then try again:
    $ python -m pip install --upgrade pip setuptools
    $ python -m pip install postDB

This will install the latest version of postDB which works on your
version of Python.
    """.format(
            *(REQUIRED_VERSION + CURRENT_VERSION)
        )
    )
    sys.exit(1)

setuptools.setup(packages=setuptools.find_packages())
