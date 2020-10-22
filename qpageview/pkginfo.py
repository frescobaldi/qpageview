# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2020 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Meta-information about the qpageview package.

This information is used by the install script.

"""

import collections
Version = collections.namedtuple("Version", "major minor patch")


#: name of the package
name = "qpageview"

#: the current version
version = Version(0, 6, 0)
version_suffix = ""
version_string = "{}.{}.{}".format(*version) + version_suffix

#: short description
description = "Widget to display page-based documents for Qt5/PyQt5"

#: long description
long_description = \
    "The qpageview package provides a Python library to display page-based " \
    "documents, such as PDF and possibly other formats."

#: maintainer name
maintainer = "Wilbert Berendsen"

#: maintainer email
maintainer_email = "info@frescobaldi.org"

#: homepage
url = "https://github.com/frescobaldi/qpageview"

#: license
license = "GPL v3"

#: copyright year
copyright_year = "2020"

