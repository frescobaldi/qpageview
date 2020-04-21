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
   pressed. A Page also knows its current dimensions in pixels: in the Page's
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

   (When the ``dpi`` Page class attribute is the same as the current DPI
   setting of the computer's display, then the displayed size of a Page at zoom
   factor 1.0 in pixels is the same as the default size.)

   This is called "original page coordinates." Normally these are floating point
   values.

3. A position where both horizontal and vertical offset are floating point,
   in the range 0..1, without rotation. This is used to determine the position
   of links, rectangular areas to highlight, and to position overlay widgets
   by the widget overlay view mixin.

:class:`Page <AbstractPage>` has the method :meth:`~AbstractPage.transform` to
get a QTransform matrix that can map between page coordinates and original or
0..1 coordinates. The methods :meth:`~AbstractPage.mapToPage` and
:meth:`~AbstractPage.mapFromPage` return helper objects that can convert
QPoints and QRects from and to original page coordinates. These matrices take
into account the page's scaling and current rotation.


