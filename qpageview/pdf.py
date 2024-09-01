# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2019 by Wilbert Berendsen
# Copyright (c) 2024 by Benjamin Johnson
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
PDF rendering backend using QtPdf.

"""

import contextlib
import weakref
import platform

from PyQt6.QtCore import Qt, QCoreApplication, QModelIndex, QRect, QRectF, QSize
from PyQt6.QtGui import QRegion, QPainter, QPicture, QTransform
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions, QPdfLinkModel

from . import document
from . import page
from . import link
from . import locking
from . import render

from .constants import (
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,
)

# Map our rotation constants to Qt's
_rotation = {
    Rotate_0:   QPdfDocumentRenderOptions.Rotation.None_,
    Rotate_90:  QPdfDocumentRenderOptions.Rotation.Clockwise90,
    Rotate_180: QPdfDocumentRenderOptions.Rotation.Clockwise180,
    Rotate_270: QPdfDocumentRenderOptions.Rotation.Clockwise270,
}


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
        return self.linkobj.data(self.index, QPdfLinkModel.Role.Page.value)

    @property
    def url(self):
        """The URL the link points to."""
        url = self.linkobj.data(self.index, QPdfLinkModel.Role.Url.value).toString()
        if platform.system() == "Windows":
            # If this is a local path, make sure there is a colon after the
            # drive letter (QUrl likes to strip it out)
            for proto in ("file", "textedit"):
                pattern = "{0}://".format(proto)
                pos = len(pattern) + 1  # the colon should be here
                if (url.startswith(pattern)
                    and url[pos - 1].isalpha() and url[pos] == "/"):
                    url = ":".join((url[0:pos], url[pos:]))
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
        The specified Renderer is used, or else the global poppler renderer.
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
            return self.document.getSelection(self.pageNumber, rectf.topLeft(), rectf.bottomRight()).text()

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
                    links.append(Link(lm, index, document.pagePointSize(pageNumber)))
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
    oversampleThreshold = 96

    def render(self, page, key, tile, paperColor=None):
        """Generate an image for the Page referred to by key."""
        if paperColor is None:
            paperColor = page.paperColor or self.paperColor

        doc = page.document
        num = page.pageNumber
        s = page.pageSize()
        if key.rotation & 1:
            s.transpose()

        xres = 72.0 * key.width / s.width()
        yres = 72.0 * key.height / s.height()
        multiplier = 2 if xres < self.oversampleThreshold else 1
        # QtPdf forces us to render the entire page area
        image = self.render_image(doc, num,
            xres * multiplier, yres * multiplier,
            key.width * multiplier, key.height * multiplier,
            key.rotation, paperColor)
        if multiplier == 2:
            image = image.scaledToWidth(tile.w, Qt.TransformationMode.SmoothTransformation)
        image.setDotsPerMeterX(int(xres * 39.37))
        image.setDotsPerMeterY(int(yres * 39.37))
        # Crop to the tile boundaries
        return image.copy(tile.x, tile.y, tile.w, tile.h)

    def render_image(self, doc, pageNum,
                     xres=72.0, yres=72.0, w=-1, h=-1,
                     rotate=Rotate_0, paperColor=None):
        """Render an image.

        The document is properly locked during rendering and render options
        are set.

        """
        with locking.lock(doc):
            options = QPdfDocumentRenderOptions()
            options.setRotation(_rotation[rotate])
            options.setScaledSize(QSize(int(xres * w), int(yres * h)))
            renderedPage = doc.render(pageNum, QSize(int(w), int(h)), options)

            # If the page does not specify a background color, QtPdf renders
            # the background as transparent. In this case we need to paint the
            # background ourselves.
            image = renderedPage.copy()
            painter = QPainter(image)
            if paperColor:
                painter.fillRect(image.rect(), paperColor)
            painter.drawImage(0, 0, renderedPage)
            painter.end()
            return image

    def draw(self, page, painter, key, tile, paperColor=None):
        """Draw a tile on the painter.

        The painter is already at the right position and rotation.
        For the PDF renderer, draw() is only used for printing; see
        AbstractPage.print().

        """
        source = self.map(key, page.pageRect()).mapRect(QRectF(*tile)).toRect()   # rounded
        target = QRectF(0, 0, tile.w, tile.h)
        if key.rotation & 1:
            target.setSize(target.size().transposed())

        doc = page.document

        # Make an image exactly in the printer's resolution
        m = painter.transform()
        r = m.mapRect(source)       # see where the source ends up
        w, h = r.width(), r.height()
        if m.m11() == 0:
            w, h = h, w     # swap if rotation & 1  :-)
        # now we know the scale from our dpi to the paintdevice's logicalDpi!
        hscale = w / source.width()
        vscale = h / source.height()
        s = QTransform().scale(hscale, vscale).mapRect(source)
        dpiX = page.dpi * hscale
        dpiY = page.dpi * vscale
        # Render the full page...
        img = self.render_image(doc, page.pageNumber,
            dpiX, dpiY, s.width(), s.height())
        # ...and crop it to the tile size
        img = img.copy(*(map(int, (tile.x, tile.y, tile.w, tile.h))))
        painter.drawImage(target, img, img.rect().toRectF())


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
