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

from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QRegion, QPainter, QPicture, QTransform
from PyQt6.QtPdf import QPdfDocument, QPdfLinkModel

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


# store the links in the page of a Poppler document as long as the document exists
_linkscache = weakref.WeakKeyDictionary()


class Link(link.Link):
    """A link that encapsulates QPdfLinkModel data."""
    def __init__(self, linkobj, index):
        self.linkobj = linkobj
        self.index = index
        self.area = linkobj.data(index, QPdfLinkModel.Role.Rectangle)

    @property
    def url(self):
        """The URL the link points to."""
        return self.linkobj.data(self.index, QPdfLinkModel.Role.Url)


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
        with locking.lock(self.document):
            return self.document.getSelection(self.pageNumber, rect.topLeft(), rect.bottomRight())

    def links(self):
        """Return links inside the document."""
        document, pageNumber = self.document, self.pageNumber
        try:
            return _linkscache[document][pageNumber]
        except KeyError:
            with locking.lock(document):
                lm = QPdfLinkModel()
                lm.setDocument(document)
                lm.setPage(pageNumber)
                links = link.Links(Link(lm, i) for i in range(len(lm.children())))
            _linkscache.setdefault(document, {})[pageNumber] = links
            return links


class PdfDocument(document.SingleSourceDocument):
    """A lazily loaded PDF document."""
    pageClass = PdfPage

    def __init__(self, parent, source=None, renderer=None):
        super().__init__(source, renderer)
        self._parent = parent
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
                self._document = load(self._parent, source) or False
        return self._document


class PdfRenderer(render.AbstractRenderer):
    def render(self, page, key, tile, paperColor=None):
        """Generate an image for the Page referred to by key."""
        if paperColor is None:
            paperColor = page.paperColor or self.paperColor

        doc = page.document
        num = page.pageNumber
        size = QSize(key.width, key.height)
        if key.rotation & 1:
            size.transpose()

        renderedPage = doc.render(num, size)
        # If the page does not specify a background color, QtPdf renders
        # the background as transparent. In this case we need to paint the
        # background ourselves.
        image = renderedPage.copy()
        painter = QPainter(image)
        painter.fillRect(image.rect(), paperColor)
        painter.drawImage(0, 0, renderedPage)
        painter.end()
        return image

    @contextlib.contextmanager
    def setup(self, doc, backend=None, paperColor=None):
        """Use the poppler document in context, properly configured and locked."""
        with locking.lock(doc):
            if backend is not None:
                oldbackend = doc.renderBackend()
                doc.setRenderBackend(backend)
            oldhints = int(doc.renderHints())
            doc.setRenderHint(oldhints, False)
            self.setRenderHints(doc)
            if paperColor is not None:
                oldcolor = doc.paperColor()
                doc.setPaperColor(paperColor)
            try:
                yield
            finally:
                if backend is not None:
                    doc.setRenderBackend(oldbackend)
                doc.setRenderHint(int(doc.renderHints()), False)
                doc.setRenderHint(oldhints)
                if paperColor is not None:
                    doc.setPaperColor(oldcolor)


def load(parent, source):
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
        document = QPdfDocument(parent)
        document.load(source)
        return document


# Install a default renderer so PdfPage can be used directly
PdfPage.renderer = PdfRenderer()
