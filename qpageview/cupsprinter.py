# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2014 - 2019 by Wilbert Berendsen
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

r"""
A simple module using CUPS to send a document directly to a printer described
by a QPrinter. This is especially useful with PDF documents.

Uses the `cups` module, although it elegantly fails when that module is not
present. The cups module can be found in the pycups package at
https://pypi.org/project/pycups/ .

There are two methods to send a document to a printer:

1. Using the `lp` shell command
2. Using the cups module, which uses libcups to directly contact the server.

This module provides both possibilities.

Use `CmdHandle.create()` to get a CmdHandle, if `lp` is available, or use
`IppHandle.create()` to get a IppHandle, if the cups module is available and a
connection to the server can be established.

A function `handle()` is available; that tries first to get an IppHandle and
then a LprHandle. Usage of this module is this simple::

    import qpageview.cupsprinter

    h = qpageview.cupsprinter.handle()
    if h:
        h.printFile('/path/to/document.pdf')

You can supply a QPrinter instance (that'd be the normal workflow :-)

::

    h = qpageview.cupsprinter.handle(printer)
    if h:
        h.printFile('/path/to/document.pdf')

In this case all options that are set in the QPrinter object will be used
when sending the document to the printer.

If `printFile()` returns True, printing is considered successful. If False,
you can read the `status` and `error` attributes::

    if not h.printFile('/path/to/document.pdf'):
        QMessageBox.warning(None, "Printing failure",
            "There was an error:\n{0} (status: {1})".format(h.error, h.status))

To print a list of files in one job, use `printFiles()`.

"""

import os
import shutil
import subprocess

from PyQt6.QtGui import QPageSize
from PyQt6.QtPrintSupport import QPrintEngine, QPrinter


class Handle:
    """Shared implementation of a handle that can send documents to a printer."""
    def __init__(self, printer=None):
        self._printer = printer

    def setPrinter(self, printer):
        """Use the specified QPrinter."""
        self._printer = printer

    def printer(self):
        """Return the QPrinter given on init, or a new default QPrinter instance."""
        if self._printer == None:
            self._printer = QPrinter()
        return self._printer

    def options(self):
        """Return the dict of CUPS options read from the printer object."""
        return options(self.printer())

    def title(self, filenames):
        """Return a sensible job title based on the list of filenames.

        This method is called when the user did not specify a job title.

        """
        maxlen = 5
        titles = [os.path.basename(f) for f in filenames[:maxlen]]
        more = len(filenames) - maxlen
        if more > 0:
            titles.append("(+{0} more)".format(more))
        return ", ".join(titles)

    def printFile(self, filename, title=None, options=None):
        """Print the file."""
        return self.printFiles([filename], title, options)

    def printFiles(self, filenames, title=None, options=None):
        """Print a list of files.

        If the title is None, the basename of the filename is used. Options may
        be a dictionary of CUPS options.  All keys and values should be
        strings.

        Returns True if the operation was successful. Returns False if there was
        an error; after the call to printFile(), the status and error attributes
        contain the returncode of the operation and the error message.

        """
        if filenames:
            if all(f and not f.isspace() and f != "-" for f in filenames):
                if not title:
                    title = self.title(filenames)
                o = self.options()
                if options:
                    o.update(options)
                printerName = self.printer().printerName()
                self.status, self.error = self._doPrintFiles(printerName, filenames, title, o)
            else:
                self.status, self.error = 2, "Not a valid filename"
        else:
            self.status, self.error = 2, "No filenames specified"
        return self.status == 0

    def _doPrintFiles(self, printerName, filenames, title, options):
        """Implement this to perform the printing.

        Should return a tuple (status, error). If status is 0, the operation is
        considered to be successful. If not, the operation is considered to have
        failed, and the `error` message should contain some more information.

        """
        return 0, ""


class CmdHandle(Handle):
    """Print a document using the `lp` shell command."""
    def __init__(self, command, server="", port=0, user="", printer=None):
        self._command = command
        self._server = server
        self._port = port
        self._user = user
        super().__init__(printer)

    @classmethod
    def create(cls, printer=None, server="", port=0, user="", cmd="lp"):
        """Create a handle to print using a shell command, if available."""
        cmd = shutil.which(cmd)
        if cmd:
            return cls(cmd, server, port, user, printer)

    def _doPrintFiles(self, printerName, filenames, title, options):
        """Print filenames using the `lp` shell command."""
        cmd = [self._command]
        if self._server:
            if self._port:
                cmd.extend(['-h', "{0}:{1}".format(self._server, self._port)])
            else:
                cmd.extend(['-h', self._server])
        if self._user:
            cmd.extend(['-U', self._user])
        cmd.extend(['-d', printerName])
        cmd.extend(['-t', title])
        if options:
            for option, value in options.items():
                cmd.extend(['-o', '{0}={1}'.format(option, value)])
        if any(f.startswith('-') for f in filenames):
            cmd.append('--')
        cmd.extend(filenames)
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except OSError as e:
            return e.errno, e.strerror
        message = p.communicate()[1].decode('UTF-8', 'replace')
        return p.wait(), message


class IppHandle(Handle):
    """Print a document using a connection to the CUPS server."""
    def __init__(self, connection, printer=None):
        super().__init__(printer)
        self._connection = connection

    @classmethod
    def create(cls, printer=None, server="", port=0, user=""):
        """Return a handle to print using a connection to the (local) CUPS server, if available."""
        try:
            import cups
        except ImportError:
            return
        cups.setServer(server or "")
        cups.setPort(port or 0)
        cups.setUser(user or "")
        try:
            c = cups.Connection()
        except RuntimeError:
            return
        h = cls(c, printer)
        if h.printer().printerName() in c.getPrinters():
            return h

    def _doPrintFiles(self, printerName, filenames, title, options):
        """Print filenames using a connection to the CUPS server."""
        import cups
        # cups.Connection.printFiles() behaves flaky: version 1.9.74 can
        # silently fail (without returning an error), and after having fixed
        # that, there are strange error messages on some options.
        # Therefore we use cups.printFile() for every file.
        for filename in filenames:
            try:
                self._connection.printFile(printerName, filename, title, options)
            except cups.IPPError as err:
                return err.args
        return 0, ""


def handle(printer=None, server="", port=0, user=""):
    """Return the first available handle to print a document to a CUPS server."""
    return (IppHandle.create(printer, server, port, user) or
            CmdHandle.create(printer, server, port, user))


def options(printer):
    """Return the dict of CUPS options read from the QPrinter object."""
    o = {}

    # cups options that can be set in QPrintDialog on unix
    # I found this in qt5/qtbase/src/printsupport/kernel/qcups.cpp.
    # Esp. options like page-set even/odd do make sense.
    props = printer.printEngine().property(0xfe00)
    if props and isinstance(props, list) and len(props) % 2 == 0:
        for key, value in zip(props[0::2], props[1::2]):
            if value and isinstance(key, str) and isinstance(value, str):
                o[key] = value

    o['copies'] = format(printer.copyCount())
    if printer.collateCopies():
        o['collate'] = 'true'

    # TODO: in Qt5 >= 5.11 page-ranges support is more fine-grained!
    if printer.printRange() == QPrinter.PrintRange.PageRange:
        o['page-ranges'] = '{0}-{1}'.format(printer.fromPage(), printer.toPage())

    # page order
    if printer.pageOrder() == QPrinter.PageOrder.LastPageFirst:
        o['outputorder'] = 'reverse'

    # media size
    media = []
    size = printer.paperSize()
    if size == QPrinter.ZoomMode.Custom:
        media.append('Custom.{0}x{1}mm'.format(printer.heightMM(), printer.widthMM()))
    elif size in PAGE_SIZES:
        media.append(PAGE_SIZES[size])

    # media source
    source = printer.paperSource()
    if source in PAPER_SOURCES:
        media.append(PAPER_SOURCES[source])

    if media:
        o['media'] = ','.join(media)

    # page margins
    if printer.printEngine().property(QPrintEngine.PrintEnginePropertyKey.PPK_PageMargins):
        left, top, right, bottom = printer.getPageMargins(QPrinter.Unit.Point)
        o['page-left'] = format(left)
        o['page-top'] = format(top)
        o['page-right'] = format(right)
        o['page-bottom'] = format(bottom)

    # orientation
    landscape = printer.orientation() == QPrinter.Landscape
    if landscape:
        o['landscape'] = 'true'

    # double sided
    duplex = printer.duplex()
    o['sides'] = (
        'two-sided-long-edge' if duplex == QPrinter.DuplexMode.DuplexLongSide or
                        (duplex == QPrinter.DuplexMode.DuplexAuto and not landscape) else
        'two-sided-short-edge' if duplex == QPrinter.DuplexMode.DuplexShortSide or
                        (duplex == QPrinter.DuplexMode.DuplexAuto and landscape) else
        'one-sided')

    # grayscale
    if printer.colorMode() == QPrinter.ColorMode.GrayScale:
        o['print-color-mode'] = 'monochrome'

    return o


def clearPageSetSetting(printer):
    """Remove 'page-set' even/odd cups options from the printer's CUPS options.

    Qt's QPrintDialog fails to reset the 'page-set' option back to 'all pages',
    so a previous value (even or odd) could remain in the print options, even
    if the user has selected All Pages in the print dialog.

    This function clears the page-set setting from the cups options. If the
    user selects or has selected even or odd pages, it will be added again by
    the dialog.

    So call this function on a QPrinter, just before showing a QPrintDialog.

    """
    # see qt5/qtbase/src/printsupport/kernel/qcups.cpp
    key = QPrintEngine.PrintEnginePropertyKey(0xfe00)
    opts = printer.printEngine().property(key)
    if opts and isinstance(opts, list) and len(opts) % 2 == 0:
        try:
            i = opts.index('page-set')
        except ValueError:
            return
        if i % 2 == 0:
            del opts[i:i+2]
            printer.printEngine().setProperty(key, opts)


PAGE_SIZES = {
    QPageSize.PageSizeId.A0: "A0",
    QPageSize.PageSizeId.A1: "A1",
    QPageSize.PageSizeId.A2: "A2",
    QPageSize.PageSizeId.A3: "A3",
    QPageSize.PageSizeId.A4: "A4",
    QPageSize.PageSizeId.A5: "A5",
    QPageSize.PageSizeId.A6: "A6",
    QPageSize.PageSizeId.A7: "A7",
    QPageSize.PageSizeId.A8: "A8",
    QPageSize.PageSizeId.A9: "A9",
    QPageSize.PageSizeId.B0: "B0",
    QPageSize.PageSizeId.B1: "B1",
    QPageSize.PageSizeId.B10: "B10",
    QPageSize.PageSizeId.B2: "B2",
    QPageSize.PageSizeId.B3: "B3",
    QPageSize.PageSizeId.B4: "B4",
    QPageSize.PageSizeId.B5: "B5",
    QPageSize.PageSizeId.B6: "B6",
    QPageSize.PageSizeId.B7: "B7",
    QPageSize.PageSizeId.B8: "B8",
    QPageSize.PageSizeId.B9: "B9",
    QPageSize.PageSizeId.C5E: "C5",         # Correct Translation?
    QPageSize.PageSizeId.Comm10E: "Comm10", # Correct Translation?
    QPageSize.PageSizeId.DLE: "DL",         # Correct Translation?
    QPageSize.PageSizeId.Executive: "Executive",
    QPageSize.PageSizeId.Folio: "Folio",
    QPageSize.PageSizeId.Ledger: "Ledger",
    QPageSize.PageSizeId.Legal: "Legal",
    QPageSize.PageSizeId.Letter: "Letter",
    QPageSize.PageSizeId.Tabloid: "Tabloid",
}

PAPER_SOURCES = {
    QPrinter.PaperSource.Cassette: "Cassette",
    QPrinter.PaperSource.Envelope: "Envelope",
    QPrinter.PaperSource.EnvelopeManual: "EnvelopeManual",
    QPrinter.PaperSource.FormSource: "FormSource",
    QPrinter.PaperSource.LargeCapacity: "LargeCapacity",
    QPrinter.PaperSource.LargeFormat: "LargeFormat",
    QPrinter.PaperSource.Lower: "Lower",
    QPrinter.PaperSource.MaxPageSource: "MaxPageSource",
    QPrinter.PaperSource.Middle: "Middle",
    QPrinter.PaperSource.Manual: "Manual",
    QPrinter.PaperSource.OnlyOne: "OnlyOne",
    QPrinter.PaperSource.Tractor: "Tractor",
    QPrinter.PaperSource.SmallFormat: "SmallFormat",
}

