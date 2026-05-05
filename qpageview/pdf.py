# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2019 by Wilbert Berendsen
# Copyright (c) 2024 by Benjamin Johnson
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
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
PDF rendering backend using QtPdf.

"""

import platform

from PyQt6.QtCore import Qt, QByteArray, QModelIndex, QRect, QRectF, QSize, QUrl
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions

# Check for PDF link support (added in Qt 6.6)
# As of 2026, some Linux distros still ship older Qt versions without it.
# We will attempt to run with point-and-click disabled on such systems.
try:
    from PyQt6.QtPdf import QPdfLinkModel
except ImportError:
    QPdfLinkModel = None
    import sys
    print("qpageview: "
        "PDF links are disabled because QPdfLinkModel is unavailable.",
        file=sys.stderr)

from . import document
from . import page
from . import link
from . import locking
from . import render


class Link(link.Link):
    """A link that encapsulates QPdfLinkModel data."""
    def __init__(self, linkobj, index, pointSize):
        self._targetPage = linkobj.data(index, QPdfLinkModel.Role.Page.value)
        self._url = linkobj.data(index,
                                 QPdfLinkModel.Role.Url.value).toString()
        # Convert to relative coordinates between 0.0 and 1.0 as expected
        # by link.Link, which uses them for compatibility with Poppler
        rect = linkobj.data(index, QPdfLinkModel.Role.Rectangle.value)
        x1, y1, x2, y2 = rect.normalized().getCoords()
        self.area = (x1 / pointSize.width(), y1 / pointSize.height(),
                     x2 / pointSize.width(), y2 / pointSize.height())

    @property
    def fileName(self):
        """The file name if this is an external link."""
        return QUrl(self.url).fileName() if self.isExternal else ""

    @property
    def isExternal(self):
        """Indicates whether this is an external link."""
        return (self.url and "://" in self.url)

    @property
    def targetPage(self):
        """If this is an internal link, the page number to which the
        link should jump; otherwise -1."""
        # QtPdf pages are 0-indexed, but our View is 1-indexed
        return -1 if self._targetPage == -1 else self._targetPage + 1

    @property
    def url(self):
        """The URL the link points to."""
        url = self._url
        if platform.system() == "Windows":
            # Fix weird things QUrl does to local paths
            for proto in ("file", "textedit"):
                scheme = "{0}://".format(proto)
                pos = len(scheme) + 1  # the colon should be here
                if (url.startswith(scheme)
                    and url[pos - 1].isalpha() and not url[pos].isalpha()):
                    # Capitalize the drive letter because that is the standard
                    # format, and some path-matching functions (incorrectly)
                    # assume case sensitivity
                    driveLetter = url[pos - 1].upper()
                    # Make sure there is a colon after the drive letter
                    if url[pos] != ":":
                        driveLetter = "{0}:".format(driveLetter)
                    path = url[pos:]
                    url = "".join((scheme, driveLetter, path))
        return url


class PdfPage(page.AbstractRenderedPage):
    """A Page capable of displaying one page of a QPdfDocument instance.

    It has two additional instance attributes:

        `document`: the QPdfDocument instance
        `pageNumber`: the page number to render

    """
    def __init__(self, document, pageNumber, renderer=None):
        super().__init__(renderer)
        self.document = document
        self.pageNumber = pageNumber
        self.setPageSize(document.pagePointSize(pageNumber))

    @classmethod
    def loadDocument(cls, document, renderer=None, pageSlice=None):
        """Convenience class method yielding instances of this class.

        The Page instances are created from the document, in page number order.
        The specified Renderer is used, or else the global QtPdf renderer.
        If pageSlice is given, it should be a slice object and only those pages
        are then loaded.

        """
        it = range(document.pageCount())
        if pageSlice is not None:
            it = it[pageSlice]
        for num in it:
            yield cls(document, num, renderer)

    @classmethod
    def load(cls, filename, renderer=None):
        """Load a PDF document, and yield of instances of this class.

        The filename can also be a QByteArray or a QPdfDocument instance.
        The specified Renderer is used, or else the global PDF renderer.

        """
        doc = load(filename)
        return cls.loadDocument(doc, renderer) if doc else ()

    def mutex(self):
        """No two pages of the same document are rendered at the same time."""
        return self.document

    def group(self):
        """Reimplemented to return the document our page is displayed from."""
        return self.document

    def ident(self):
        """Reimplemented to return the page number of this page."""
        return self.pageNumber

    def text(self, rect):
        """Returns text inside rectangle."""
        rectf = self.mapFromPage(self.pageWidth, self.pageHeight).rect(rect)
        with locking.lock(self.document):
            return self.document.getSelection(
                self.pageNumber, rectf.topLeft(), rectf.bottomRight()).text()

    def links(self):
        """Return links inside the document."""
        document, pageNumber = self.document, self.pageNumber
        try:
            return self._linksCache
        except AttributeError:
            if QPdfLinkModel is None:
                # Link support is unavailable; return an empty cache
                self._linksCache = link.Links()
                return self._linksCache
            with locking.lock(document):
                lm = QPdfLinkModel(document=document, page=pageNumber)
                parentIndex = QModelIndex()
                links = []
                for row in range(lm.rowCount(parentIndex)):
                    index = lm.index(row, 0, parentIndex)
                    links.append(Link(lm, index,
                                      document.pagePointSize(pageNumber)))
                self._linksCache = link.Links(links)
            return self._linksCache


class PdfDocument(document.SingleSourceDocument):
    """A lazily loaded PDF document."""
    pageClass = PdfPage

    def __init__(self, source=None, renderer=None):
        super().__init__(source, renderer)
        self._document = None

    def invalidate(self):
        """Reimplemented to clear the Document reference."""
        super().invalidate()
        self._document = None

    def createPages(self):
        doc = self.document()
        if doc:
            return self.pageClass.loadDocument(doc, self.renderer)
        return ()

    def document(self):
        """Return the QPdfDocument object.

        Returns None if no source was yet set, and False if loading failed.

        """
        if self._document is None:
            source = self.source()
            if source:
                self._document = load(source) or False
        return self._document


class PdfRenderer(render.AbstractRenderer):
    oversampleThreshold = 96    # DPI of a standard PC screen

    def tiles(self, width, height):
        """Yield four-tuples Tile(x, y, w, h) describing the tiles to render.

        For the QtPdf backend, this always returns a single tile covering
        the entire page because QtPdf does not support selectively rendering
        a smaller area.

        """
        yield render.Tile(0, 0, width, height)

    def draw(self, page, painter, key, tile, paperColor=None):
        """Draw a tile on the painter.

        The painter is already at the right position and rotation.

        """
        pageSize = page.pageSize()  # in points
        # key and tile coordinates scale with device resolution and zoom level
        source = QRectF(0, 0, key.width, key.height)
        target = QRectF(0, 0, tile.w, tile.h)
        if key.rotation & 1:
            pageSize.transpose()
            target.setSize(target.size().transposed())

        doc = page.document
        num = page.pageNumber
        xres = painter.device().logicalDpiX()
        yres = painter.device().logicalDpiY()

        # We use this to scale from key/tile to device coordinates
        matrix = painter.deviceTransform()

        # When we are displaying an image on screen, our painter coordinates
        # are "actual size" and scaling is our responsibility. When printing,
        # the painter coordinates are scaled to the device's resolution and
        # scaling is the device's responsibility.
        vscale = matrix.m11()
        hscale = matrix.m22()
        actualSize = (vscale == hscale == 1)

        # Oversampling produces more readable output at lower resolutions
        # when painting at "actual size"
        if actualSize:
            # If our effective pixel density at this zoom level is below
            # our threshold, render at double size then downscale
            xresEffective = 72.0 * key.width / pageSize.width()
            yresEffective = 72.0 * key.height / pageSize.height()
            xMultiplier = 2 if xresEffective < self.oversampleThreshold else 1
            yMultiplier = 2 if yresEffective < self.oversampleThreshold else 1
        else:
            xMultiplier = 1
            yMultiplier = 1

        # Set rendering options
        RenderFlag = QPdfDocumentRenderOptions.RenderFlag
        renderOptions = QPdfDocumentRenderOptions()
        # This ridiculous back-and-forth conversion is necessary because
        # PyQt6's enum types don't implement bitwise OR
        renderFlags = 0
        if not self.antialiasing:
            renderFlags |= RenderFlag.TextAliased.value
            renderFlags |= RenderFlag.ImageAliased.value
            renderFlags |= RenderFlag.PathAliased.value
        renderOptions.setRenderFlags(RenderFlag(renderFlags))

        # Render the image at the output device's resolution (or double
        # that if we are oversampling)
        s = matrix.scale(xMultiplier, yMultiplier).mapRect(source)
        renderSize = QSize(int(s.width()), int(s.height()))
        with locking.lock(doc):
            image = doc.render(num, renderSize, renderOptions)

        if tile != (0, 0, key.width, key.height):
            # Crop the image to the tile boundaries
            image = image.copy(matrix.mapRect(QRect(*map(int, tile))))

        if actualSize and QRectF(image.rect()) != target:
            # Scale the image to our requested resolution
            image = image.scaled(int(target.width()), int(target.height()),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation)

        # Erase the target area and draw the image
        painter.eraseRect(target)
        if paperColor:
            painter.fillRect(target, paperColor)
        painter.drawImage(target, image, QRectF(image.rect()))


def load(source):
    """Load a PDF document.

    Source may be:
        - a QPdfDocument, which is then simply returned :-)
        - a filename
        - a QByteArray instance.

    Returns None if the document could not be loaded.

    """
    if isinstance(source, QPdfDocument):
        return source
    elif isinstance(source, str) or isinstance(source, QByteArray):
        # We need to create the QPdfDocument without a parent QObject so
        # Python can garbage-collect it properly when it goes out of scope
        document = QPdfDocument(None)   # parent has no default value
        document.load(source)
        return document


# Install a default renderer so PdfPage can be used directly
PdfPage.renderer = PdfRenderer()
