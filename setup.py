# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright © 2019-2020 by Wilbert Berendsen
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
Setup script.
"""

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from qpageview import pkginfo


def packagelist(directory):
    """Return a sorted list with package names for all packages under the given directory."""
    folder, basename = os.path.split(directory)
    return list(sorted(root[len(folder)+1:].replace(os.sep, '.')
        for root, dirs, files in os.walk(directory)
        if '__init__.py' in files))

scripts = []
packages = packagelist('./qpageview')
py_modules = []

with open('README.rst', encoding="utf-8") as f:
    long_description = f.read()

package_data = {

}

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Topic :: Multimedia :: Graphics',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Programming Language :: Python :: 3.6',
]

setup(
    name = pkginfo.name,
    version = pkginfo.version_string,
    description = pkginfo.description,
    long_description = long_description,
    maintainer = pkginfo.maintainer,
    maintainer_email = pkginfo.maintainer_email,
    url = pkginfo.url,
    license = pkginfo.license,

    scripts = scripts,
    packages = packages,
    package_data = package_data,
    py_modules = py_modules,
    classifiers = classifiers,
)

