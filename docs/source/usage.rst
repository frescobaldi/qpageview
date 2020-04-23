Basic usage
===========

.. currentmodule:: qpageview


Creating the View widget
~~~~~~~~~~~~~~~~~~~~~~~~

Just import :mod:`qpageview` and create a View. As the :class:`~view.View` is a
QWidget, you need to create a QApplication object, just as for all Qt-based
applications::

    from PyQt5.QtWidgets import QApplication
    import qpageview

    app = QApplication([])

    v = qpageview.View()
    v.resize(900, 500)
    v.show()


Loading contents
~~~~~~~~~~~~~~~~

Load a PDF file with::

    v.loadPdf("path/to/a_file.pdf")

or images, or SVG files::

    import glob
    v.loadImages(glob.glob("*.jpg"))
    v.loadSvgs(glob.glob("*.svg"))

It is also possible to display pages originating from different sources
at the same time in a View, see :doc:`advanced`.

To clear the View again::

    v.clear()


Navigating in the View
~~~~~~~~~~~~~~~~~~~~~~

The View numbers pages starting from 1, like printed documents do.
You can programmatically navigate through the View::

    v.pageCount()               # get the number of pages
    v.setCurrentPageNumber(11)  # go to page 11
    v.currentPageNumber()       # get the current page number
    v.gotoNextPage()            # go to the next page
    v.gotoPreviousPage()        # go to the previous page

If the page you want to go to is not completely visible, it is scrolled into
View.


Controlling the display
~~~~~~~~~~~~~~~~~~~~~~~

You can interact in the normal way with the widget, scrolling and zooming.
Note the almost infinite zoom, thanks to the tile-based rendering engine.

There are various methods to change things, like *rotation*::

    v.rotateRight()
    v.rotateLeft()
    v.setRotation(2)    # or v.setRotation(qpageview.Rotate_180)

or *zooming*::

    v.zoomIn()
    v.zoomOut()
    v.setZoomFactor(2.0)

or *how* to fit the document while resizing the View widget::

    v.setViewMode(qpageview.FitWidth)       # fits the page(s) in the width
    v.setViewMode(qpageview.FitHeight)      # fits the page's height
    v.setViewMode(qpageview.FitBoth)        # shows the full page
    v.setViewMode(qpageview.FixedScale)     # don't adjust zoom to the widget

Setting the zoomFactor automatically switches to the FixedScale mode.

Change the *orientation*::

    v.setOrientation(qpageview.Vertical)
    v.setOrientation(qpageview.Horizontal)

Change the *continuous* mode::

    v.setContinuousMode(False)      # only display the current page(s)
    v.setContinuousMode(True)       # display all pages

Change the *layout mode*::

    v.setPageLayoutMode("double_right") # Two pages, first page right
    v.setPageLayoutMode("double_left")  # Two pages, first page left
    v.setPageLayoutMode("single")       # Single pages
    v.setPageLayoutMode("raster")       # Shows pages in a grid

(The method :meth:`~view.View.pageLayoutModes` returns a dictionary mapping the
available layout mode names to the constructors of their corresponding layout
engines. By making new :class:`~layout.LayoutEngine` subclasses, you can
implement more layout modes, and you can reimplement ``pageLayoutModes()`` to
include them.)

All these properties have "getter" couterparts, like ``viewMode()``,
``orientation()``, etc.

The Magnifier
~~~~~~~~~~~~~

You can add a :class:`~qpageview.magnifier.Magnifier`::

    from qpageview.magnifier import Magnifier
    m = Magnifier()
    v.setMagnifier(m)

Now, Ctrl+click in the View, and the Magnifier appears.  You can also
show the Magnifier programmatically with::

    m.show()  # or v.magnifier().show()

Now you can only get it away with::

    m.hide()

:kbd:`Ctrl+Wheel` in the magnifier zooms the magnifier instead of the whole
View. :kbd:`Shift+Ctrl+Wheel` resizes the magnifier.

The Rubberband
~~~~~~~~~~~~~~

You can add a :class:`~rubberband.Rubberband`, to select a square
range::

    from qpageview.rubberband import Rubberband
    r = Rubberband()
    v.setRubberband(r)

By default with the right mousebutton you can select a region. The rubberband
has various methods to access the selected area, just the rectangle, or the
rectangle of every page the selection touches, or the selected square as an
image or, depending on the underlying page type, the text or clickable links
that fall in the selected region.


Controlling the behaviour
~~~~~~~~~~~~~~~~~~~~~~~~~

Scrolling
---------

By default, the View has smooth and kinetic scrolling. Kinetic scrolling
means that the View does not move the pages at once, but always scrolls with
a decreasing speed to the desired location, which is easier on the eyes.

If you want to disable kinetic scrolling altogether, set the
:attr:`~scrollarea.ScrollArea.kineticScrollingEnabled` attribute of the View to
False.

If you only want to disable kinetic scrolling when paging through the document
using the methods mentioned under `Navigating in the View`_, you can leave
:attr:`~scrollarea.ScrollArea.kineticScrollingEnabled` to True, but set
:attr:`~view.View.kineticPagingEnabled` to False.

Zooming
-------

The user can zoom in and out with Ctrl+Mousewheel, which is expected behaviour.
You can disable wheel zooming by setting the :attr:`~view.View.wheelZoomingEnabled`
attribute of View to False.

The minimum and maximum zoom factor can be set in the
:attr:`~view.View.MIN_ZOOM` and :attr:`~view.View.MAX_ZOOM` attributes. By
default you can zoom out to 5% and zoom in to 6400%.

Paging
------

By default, the :kbd:`PageUp` and :kbd:`PageDown` keys just scroll the View up
or down ca. 90%. If you set the :attr:`~view.View.strictPagingEnabled`
attribute to True, in non-continuous mode those keys call the
:meth:`~view.View.gotoPreviousPage` and :meth:`~view.View.gotoNextPage`
methods, respectively.

