Advanced usage
==============

.. currentmodule:: qpageview

Document
~~~~~~~~

A :class:`~view.View` displays :class:`Page <page.AbstractPage>` objects.

The convenience methods :meth:`View.loadPdf() <view.View.loadPdf>`,
:meth:`View.loadImages() <view.View.loadImages>` and :meth:`View.loadSvgs()
<view.View.loadSvgs>`, create :class:`~document.Document` objects containing
the pages, and then call :meth:`View.setDocument() <view.View.setDocument>` to
display the pages in the view.

You can also use the module global functions like :func:`loadPdf` which return
a Document, and then load that Document in the View::

    v = qpageview.View()
    v.show()

    doc = qpageview.loadPdf("file.pdf")
    v.setDocument(doc)

This way you can keep a document in memory, and you can load it, then load
something else in the view and later load the same document again, without the
need to load it again from disk or network.

When creating a Document using one of the global `load` functions, nothing is
really loaded until you request the
:meth:`~document.AbstractSourceDocument.pages` of the Document, and even then,
some Page types only load themselves really when their content is requested to
be rendered in the View.

Page and PageLayout
~~~~~~~~~~~~~~~~~~~

The View does not do very much with the Document it displays, rather it cares
for the Page objects that are displayed.

Those pages are in the :class:`~qpageview.layout.PageLayout` of the View, which
inherits from the Python :class:`list <python:list>` type. Using the regular
``list`` methods you can add or remove Page objects to the layout. Then you
need to call :meth:`View.updatePageLayout() <view.View.updatePageLayout>` to
update the PageLayout, which will adjust size and position of the Pages.

Instead of the above, and maybe even better and easier, you can use the
:meth:`~view.View.modifyPages` context manager of View, which will
automatically update the layout when it exits::

    with v.modifyPages() as pages:
        del pages[0]                # remove the first page
        pages.append(another_page)  # append another

This context manager yields the pages list, and when it exits it puts the pages
in the layout, and updates the page layout. Note that in the layout, and in
this ``pages`` list, the first page is at index 0.

This way, it is very easy to display Page objects originating from different
sources::

    import qpageview.image
    page1 = qpageview.image.ImagePage.load("image.jpg")
    page2 = qpageview.loadPdf("file.pdf").pages()[2]

    with v.modifyPages() as pages:
        pages[:] = [page1, page2]       # [:] replaces the current contents


Controlling a view with ViewActions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Normally, in a Qt application, you create QActions to perform tasks and put
those in a menu or toolbar.  The *qpageview* packages provides the
:mod:`viewactions` module to help you with that.

If you create a :class:`~viewactions.ViewActions` object and connect it to a
View, all actions can readily be used to control the View, and they
automatically update their state according to the View's state.

For example::

    import qpageview.viewactions
    a = qpageview.viewactions.ViewActions()

    a.setView(v)

