Interacting with pages
======================

.. currentmodule:: qpageview.page


Coordinate systems
~~~~~~~~~~~~~~~~~~

A Page can display text or graphics, have clickable links, etc.
A Page also has certain dimensions and its own notion of natural size,
via the ``dpi`` attribute of the Page (sub)class.

There are three ways of determining a position on a Page:

1. The pixel position on the Page in a View, e.g. where a mouse button is
   pressed. A Page knows its current dimensions in pixels: in the Page's
   ``width`` and ``height`` instance attributes, and as a QSize via the
   :meth:`~AbstractPage.size` method. If a Page is rotated 90 or 270 degrees,
   then the Page's original height now corresponds to the displayed page's
   width in pixels.

   In most cases this is called "page coordinates." Page coordinates are always
   integer values.

2. A position on the Page in its default size and without rotation. The original
   size of a Page is independent of the current zoomFactor of the View, and
   rather determined by the underlying image, SVG or PDF file. This is used
   e.g. when printing or converting to vector formats. The original size is
   accessible via the ``pageWidth`` and ``pageHeight`` attributes, and as a
   QSizeF via the :meth:`~AbstractPage.pageSize` method.

   This is called "original page coordinates." Normally these are floating point
   values.

   (When the ``dpi`` Page class attribute is the same as the current DPI
   setting of the computer's display, then the displayed size of a Page at zoom
   factor 1.0 in pixels is the same as the default size.)

3. A position where both horizontal and vertical offset are floating point,
   in the range 0..1, without rotation. This is used to determine the position
   of links, rectangular areas to highlight, and to position overlay widgets
   by the widget overlay view mixin.

:class:`Page <AbstractPage>` has the method :meth:`~AbstractPage.transform` to
get a QTransform matrix that can map between page coordinates and original or
0..1 coordinates. The methods :meth:`~AbstractPage.mapToPage` and
:meth:`~AbstractPage.mapFromPage` return helper objects that can convert
QPoints and QRects from and to original page coordinates. These matrices take
into account the page's scaling and current rotation, and they always return
floating point values for original or 0..1 range coordinates, and integers
for page coordinates.


Page position and Layout position
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many methods neatly hide the computations between mouse cursor position
and position in original page coordinates on a particular page, but it is
still nice to understand it a bit.

A PageLayout is just a large rectangular (virtual) area, large enough so that
all Pages in the layout can be set to a position and size so that they do
not overlap. Every Page is assigned a ``pos()`` on the layout. The geometry() of
the layout is the rectangle encompassing all visible pages on the layout.

:meth:`View.layoutPosition() <qpageview.view.View.layoutPosition>` returns the
position of the layout relative to the top-left corner of the View's viewport.
You can find the pages that are currently visible using
:meth:`View.visiblePages() <qpageview.view.View.visiblePages>`. To find the
Page the mouse cursor points at, use::

    # pos is mouse position in viewport
    pos_on_layout = pos - view.layoutPosition()
    page = view.pageLayout().pageAt(pos)
    pos_on_page = pos_on_layout - page.pos()

    # translate the pixel position to original page coordinates
    pos = page.mapFromPage().point(pos_on_page)


Links on a page
~~~~~~~~~~~~~~~

A Page can contain clickable links, which are collected in a Links object
that is available under the :meth:`~AbstractPage.links` method of Page.

.. currentmodule:: qpageview

Every :class:`~link.Link` has at least an ``url`` property and an
``area`` property, which contains the rectangle of the clickable area in four
coordinates in the 0..1 range.

You could use the above logic to access links on the page, but if you use the
LinkViewMixin class in your View class, there are simple methods: For example,
:meth:`View.linkAt() <link.LinkViewMixin.linkAt>` returns the link at
the specified mouse cursor position, if any. To get an understanding of how
things work under the hood is here the implementation of that method::

   class View:
       # (...)
       def linkAt(self, pos):
           """If the pos (in the viewport) is over a link, return a (page, link) tuple.

           Otherwise returns (None, None).

           """
           pos = pos - self.layoutPosition()
           page = self.pageLayout().pageAt(pos)
           if page:
               links = page.linksAt(pos - page.pos())
               if links:
                   return page, links[0]
           return None, None

We see that first the mouse cursor position is translated to the layout's
position, and then the layout is asked for a page on that position
(:meth:`PageLayout.pageAt() <layout.PageLayout.pageAt>`). If a page is there,
the position is translated to the page: ``pos - page.pos()`` (coordinates (0,
0) is the top-left corner of the Page).

Then the page is asked for links at that position. Let's look at the implementation
of :meth:`Page.linksAt() <page.AbstractPage.linksAt>`::

   class Page:
       # (...)
       def linksAt(self, point):
           """Return a list() of zero or more links touched by QPoint point.

           The point is in page coordinates.
           The list is sorted with the smallest rectangle first.

           """
           # Link objects have their area ranging
           # in width and height from 0.0 to 1.0 ...
           pos = self.mapFromPage(1, 1).point(point)
           links = self.links()
           return sorted(links.at(pos.x(), pos.y()), key=links.width)

We see that a matrix is used to map from page pixel coordinates to original
coordinates, but in the 0..1 range. Then the Links object is queried for links
at that position, sorted on width. The smallest one at that position is
ultimately returned by :meth:`View.linkAt()
<link.LinkViewMixin.linkAt>`.

Both PageLayout and Links internally use :class:`rectangles.Rectangles` to
manage possibly large groups of rectangular objects and quickly find
intersections with those objects and a point or rectangle.


Links in a Document
-------------------

All links in a Document can be requested with :meth:`Document.urls()
<document.Document.urls>`. This method returns a dictionary where the url is
the key, and the value is a dictionary mapping page number to a list of
rectangular areas of all links with that url on that page.


Getting text from a page
~~~~~~~~~~~~~~~~~~~~~~~~

Besides links, depending on the Page type, a page can also contain text, such
as PDF pages do. You can get the text with the :meth:`Page.text()
<page.AbstractPage.text>` method, which returns the text in a rectangle in page
coordinates::

    page = view.currentPage()

    # get the text in some rectangle
    text = page.text(some_rect)

    # get the full text by using the page's rectangle
    full_text = page.text(page.rect())

    # using the rubberband selection
    text = view.rubberband().selectedText()


Getting image data from a page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can get pixel data using :meth:`Page.image() <page.AbstractPage.image>`::

    image = page.image()

This method returns a QImage. See the documentation for the arguments to this
function, to adjust the resolution and the area (which defaults to the whole
page).

You can also get graphic data in :meth:`PDF <page.AbstractPage.pdf>`,
:meth:`EPS <page.AbstractPage.eps>` or :meth:`SVG <page.AbstractPage.svg>`
format. For document formats that are vector based, this graphic data wil also
be vector based. For example::

    page.pdf("filename.pdf")
    page.svg("filename.svg")
    page.eps("filename.eps")

    # using the rubberband selection:
    page, rect = view.rubberband.selectedPage()
    if page:
        page.pdf("filename.pdf", rect)

See the method's documentation for more information about possible arguments
to these functions. Instead of a filename, you can also give a QIODevice object.
All these functions return True if they were successful.

For more advanced methods to get image data, see the :mod:`~qpageview.export`
module.

