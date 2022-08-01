"""Setup lib-elro-connects."""

import os
import re
import sys

from setuptools import setup, find_packages


def get_version(package):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    path = os.path.join(os.path.dirname(__file__), package, "__init__.py")
    with open(path, "rb") as file:
        init_py = file.read().decode("utf-8")
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


if sys.version_info < (3, 8):
    sys.exit("Sorry, Python versions < 3.8 are not supported")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

install_requires = []

setup(
    name="lib-elro-connects",
    version=get_version("elro"),
    license="MIT Licence",
    author="Jan Bouwhuis",
    author_email="jan@jbsoft.nl",
    description="Elro Connects P1 API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jbouwh/lib-elro-connects",
    # package_dir={"": ""},
    packages=find_packages(where="elro"),
    data_files=[
        (
            "share/lib-elro-connects",
            [
                "examples/fire_alarm_demo.py",
                "examples/cloud_login_demo.py",
            ],
        )
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Home Automation",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=install_requires,
    scripts=[],
)
