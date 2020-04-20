Basic usage
===========

Create the View widget
~~~~~~~~~~~~~~~~~~~~~~

Just import :mod:`qpageview` and create a View. As the
:class:`~qpageview.view.View` is a QWidget, you need to create a QApplication
object, just as for all Qt-based applications::

    from PyQt5.QtWidgets import QApplication
    import qpageview

    app = QApplication([])

    v = qpageview.View()
    v.resize(900, 500)
    v.show()


Load contents
~~~~~~~~~~~~~

Load a PDF file with::

    v.loadPdf("path/to/a_file.pdf")

or images, or SVG files::

    import glob
    v.loadImages(glob.glob("*.jpg"))
    v.loadSvgs(glob.glob("*.svg"))

It is also possible to display pages originating from different sources
at the same time in a View, more about that later.

To clear the View again::

    v.clear()


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

(By making new :class:`~qpageview.layout.LayoutEngine` subclasses, you can
implement more layout modes.)

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

Rubberband Selection
~~~~~~~~~~~~~~~~~~~~

You can add a :class:`~qpageview.rubberband.Rubberband`, to select a square
range::

    from qpageview.rubberband import Rubberband
    r = Rubberband()
    v.setRubberband(r)

By default with the right mousebutton you can select a region. The rubberband
has various methods to access the selected area, just the rectangle, or the
rectangle of every page the selection touches, or the selected square as an
image or, depending on the underlying page type, the text or clickable links
that fall in the selected region.

