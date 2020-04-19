The qpageview module
====================

::

    import qpageview

    from PyQt5.Qt import *
    a = QApplication([])

    v = qpageview.View()
    v.show()
    v.loadPdf("path/to/afile.pdf")


`Development    <https://github.com/frescobaldi/qpageview>`_    •
`Download       <https://pypi.org/project/qpageview/>`_         •
`Documentation  <https://qpageview.readthedocs.io/>`_           •
`License        <https://www.gnu.org/licenses/gpl-3.0>`_

qpageview provides a page based document viewer widget for Qt5/PyQt5.

It has a flexible architecture potentionally supporting many formats.
Currently, it supports SVG documents, images, and, using the Poppler-Qt5
binding, PDF documents.

Dependencies
~~~~~~~~~~~~

* Python 3.6+
* Qt5
* PyQt5
* python-poppler-qt5 (needed for display of PDF documents)

