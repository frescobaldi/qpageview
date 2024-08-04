The qpageview module
====================

*qpageview* provides a page based document viewer widget for Qt6/PyQt6.

It has a flexible architecture potentionally supporting many formats.
Currently, it supports PDF and SVG documents and several image formats.

.. code-block:: python

    import qpageview

    from PyQt6.QtWidgets import *
    a = QApplication([])

    v = qpageview.View()
    v.show()
    v.loadPdf("path/to/afile.pdf")

    a.exec()


`Homepage       <https://qpageview.org/>`_                      •
`Development    <https://github.com/frescobaldi/qpageview>`_    •
`Download       <https://pypi.org/project/qpageview/>`_         •
`Documentation  <https://qpageview.org/>`_                      •
`License        <https://www.gnu.org/licenses/gpl-3.0>`_

Features
~~~~~~~~

* Versatile View widget with many optional mixin classes to cater for
  anything between basic or powerful functionality.
* Rendering in a background thread, with smart priority control, so display of
  large PDF documents remains fast and smooth.
* Almost infinite zooming thanks to tile-based rendering and caching.
* Magnifier glass.
* Printing functionality, directly to cups or via Qt/QPrinter.
* Can display pages originating from different documents at the same time.
* Can show the difference between pages that are almost the same via
  color composition.
* And much more! And...all classes are extendable and heavily customizable,
  so it is easy to inherit and add any functionality you want.

Dependencies
~~~~~~~~~~~~

* Python 3.7+
* Qt 6.6+
* PyQt6
* pycups (optionally, needed to print to a local CUPS server)
