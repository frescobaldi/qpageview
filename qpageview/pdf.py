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

import contextlib
import weakref
import platform

from PyQt6.QtCore import Qt, QCoreApplication, QModelIndex, QRect, QRectF, QSize
from PyQt6.QtGui import QPainter
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions, QPdfLinkModel

from . import document
from . import page
from . import link
from . import locking
from . import render


# store the links in the page of a Poppler document as long as the document exists
_linkscache = weakref.WeakKeyDictionary()


class Link(link.Link):
    """A link that encapsulates QPdfLinkModel data."""
    def __init__(self, linkobj, index, pointSize):
        self.linkobj = linkobj
        self.index = index
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
        page = self.linkobj.data(self.index, QPdfLinkModel.Role.Page.value)
        return (page + 1) if page != -1 else -1

    @property
    def url(self):
        """The URL the link points to."""
        url = self.linkobj.data(self.index,
                                QPdfLinkModel.Role.Url.value).toString()
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
            return _linkscache[document][pageNumber]
        except KeyError:
            with locking.lock(document):
                lm = QPdfLinkModel(document=document, page=pageNumber)
                parentIndex = QModelIndex()
                links = []
                for row in range(lm.rowCount(parentIndex)):
                    index = lm.index(row, 0, parentIndex)
                    links.append(Link(lm, index,
                                      document.pagePointSize(pageNumber)))
                links = link.Links(links)
            _linkscache.setdefault(document, {})[pageNumber] = links
            return links


class PdfDocument(document.SingleSourceDocument):
    """A lazily loaded PDF document."""
    pageClass = PdfPage

    def __init__(self, source=None, renderer=None):
        super().__init__(source, renderer)
        self._document = None

    def invalidate(self):
        """Reimplemented to clear the Poppler Document reference."""
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

        # Render the image at the output device's resolution (or double
        # that if we are oversampling)
        s = matrix.scale(xMultiplier, yMultiplier).mapRect(source)
        image = self._render_image(doc, num,
            xres * xMultiplier, yres * yMultiplier,
            int(s.width()), int(s.height()), paperColor)

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
        painter.drawImage(target, image, QRectF(image.rect()))

    def _render_image(self, doc, pageNum,
                      xres=72.0, yres=72.0, w=-1, h=-1, paperColor=None):
        """Render an image.

        This always renders the full page because that is the only rendering
        mode supported by QtPdf. If you need a smaller area, you can crop
        the returned QImage by calling its copy(x, y, w, h) method.

        The document is properly locked during rendering and render options
        are set.

        """
        RenderFlag = QPdfDocumentRenderOptions.RenderFlag
        with locking.lock(doc):
            options = QPdfDocumentRenderOptions()

            # This ridiculous back-and-forth conversion is necessary because
            # PyQt6 won't let you just 'OR' together RenderFlag constants.
            renderFlags = 0
            if not self.antialiasing:
                renderFlags |= RenderFlag.TextAliased.value
                renderFlags |= RenderFlag.ImageAliased.value
                renderFlags |= RenderFlag.PathAliased.value
            options.setRenderFlags(RenderFlag(renderFlags))

            image = doc.render(pageNum, QSize(int(w), int(h)), options)
            if paperColor:
                # QtPdf leaves the page background transparent, so we need to
                # paint it ourselves.
                content = image.copy()
                painter = QPainter(image)
                painter.fillRect(image.rect(), paperColor)
                painter.drawImage(0, 0, content)
                painter.end()
            return image


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
        document = QPdfDocument(QCoreApplication.instance())
        document.load(source)
        return document


# Install a default renderer so PdfPage can be used directly
PdfPage.renderer = PdfRenderer()
