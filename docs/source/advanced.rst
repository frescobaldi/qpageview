Advanced usage
==============

.. currentmodule:: qpageview


Document
~~~~~~~~

A :class:`~view.View` displays :class:`Page <page.AbstractPage>` objects, which
optionally can belong to a :class:`~document.Document` object.

The convenience methods :meth:`View.loadPdf() <view.View.loadPdf>`,
:meth:`View.loadImages() <view.View.loadImages>` and :meth:`View.loadSvgs()
<view.View.loadSvgs>`, create Document objects containing the pages, and then
call :meth:`View.setDocument() <view.View.setDocument>` to display the pages in
the view.

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

The list of individual Page objects in a document is returned by the
:meth:`~document.AbstractSourceDocument.pages` method of the Document class.

The current Page object (the current page number points to) is available
through :meth:`View.currentPage() <view.View.currentPage>`.


Page and PageLayout
~~~~~~~~~~~~~~~~~~~

The View does not do very much with the Document it displays, rather it cares
for the Page objects that are displayed.

The pages are in the PageLayout of the View, which inherits from the Python
:class:`list <python:list>` type. Get the :class:`~qpageview.layout.PageLayout`
of a View using :meth:`View.pageLayout() <view.View.pageLayout>`. Using the
regular ``list`` methods you can add or remove Page objects to the layout. Then
you need to call :meth:`View.updatePageLayout() <view.View.updatePageLayout>`
to update the PageLayout, which will adjust size and position of the Pages.

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
those in a menu or toolbar.  The *qpageview* package provides the
:mod:`~qpageview.viewactions` module to help you with that.

If you create a :class:`~viewactions.ViewActions` object and connect it to a
View, all actions can readily be used to control the View, and they
automatically update their state according to the View's state.
The actions (QAction objects) are in the attributes of the ViewActions object.

For example, to add some actions to a menu::

    import qpageview.viewactions
    a = qpageview.viewactions.ViewActions()

    a.setView(v)

    menu = Qmenu()
    menu.addAction(a.fit_width)
    menu.addAction(a.fit_height)
    menu.addAction(a.fit_both)
    menu.addSeparator()
    menu.addAction(a.zoom_in)
    menu.addAction(a.zoom_out)

    menu.popup(QCursor.pos())

The ``pager`` action fits well in a toolbar, it displays a spinbox where you
can cycle through the pages, and the ``zoomer`` action displays a combobox
with different zoom levels.

The full list of available action names is returned by the
:meth:`~viewactions.ViewActions.names` classmethod. You can set icons to the
actions as you like, and replace the texts. It is also easy to inherit from
ViewActions and add actions or change existing actions.

This is the list of actions that are currently available in a
:class:`~viewactions.ViewActions` object:

.. list-table::
   :header-rows: 1
   :widths: 10 10 80

   * - Name
     - Text
     - Action

   * - ``print``
     - Print
     - Open a print dialog

   * - ``fit_width``
     - Fit Width
     - Zoom to fit pages in the width of the View

   * - ``fit_height``
     - Fit Height
     - Zoom to fit pages in the height of the View

   * - ``fit_both``
     - Fit Both
     - Zoom to fit the full page in the View

   * - ``zoom_natural``
     - Natural Size
     - Zoom to a "natural" size (Page dpi/screen dpi)

   * - ``zoom_original``
     - Original Size
     - Set zoom factor to 1.0

   * - ``zoom_in``
     - Zoom in
     -

   * - ``zoom_out``
     - Zoom out
     -

   * - ``zoomer``
     - (none)
     - Display a :class:`zoom widget <viewactions.ZoomerAction>` in a toolbar

   * - ``rotate_left``
     - Rotate Left
     - Rotate the pages 90° counter-clockwise

   * - ``rotate_right``
     - Rotate Right
     - Rotate the pages 90° clockwise

   * - ``layout_single``
     - Single Pages
     - Show single pages in a row

   * - ``layout_double_right``
     - Two Pages (first page right)
     - Show page 1 alone, to the right, then the rest two by two

   * - ``layout_double_left``
     - Two Pages (first page left)
     - Show pages two by two

   * - ``layout_raster``
     - Raster
     - Show pages in a grid

   * - ``vertical``
     - Vertical
     - Show the pages in a vertical row

   * - ``horizontal``
     - Horizontal
     - Show the pages in a horizontal row

   * - ``continuous``
     - Continuous
     - Checkbox, if checked shows all pages

   * - ``reload``
     - Reload
     - Reload pages from their files if possible

   * - ``previous_page``
     - Previous Page
     - Go to the previous page

   * - ``next_page``
     - Next Page
     - Go to the next page

   * - ``pager``
     - (none)
     - Display a :class:`pager widget <viewactions.PagerAction>` in a toolbar

   * - ``magnifier``
     - Magnifier
     - Toggle the Magnifier visibility


Lazy View instantiation
-----------------------

It is possible to create a ViewActions object first
and populate menus and toolbars with the actions, while the View is not yet
created (e.g. when the View is in a dock widget that's only created when first
shown). In this case, you want to instantiate the dock widget and View as soon
as an action is triggered. To do this, connect to the :meth:`viewRequested`
signal of the ViewActions object. The connected method must create widgets as
needed and then call :meth:`~viewactions.ViewActions.setView()` on the
ViewActions object, so the action can be performed.


Managing View settings
~~~~~~~~~~~~~~~~~~~~~~

All display settings (preferences) of a View can be stored in a QSettings
object using :meth:`View.writeProperties() <view.View.writeProperties>`, and
read with :meth:`View.readProperties() <view.View.readProperties>`. These
properties are: ``position``, ``rotation``, ``zoomFactor``, ``viewMode``,
``orientation``, ``continuousMode`` and ``pageLayoutMode``.

Under the hood, this is done using a :class:`~view.ViewProperties` object,
which handles the saving and loading of properties, and getting/setting them
from/to a View.

If you want the View to remember the position, zoom factor etc. on a
per-document basis, you can install a :class:`~view.DocumentPropertyStore` in
the View. This automatically stores the view properties for the current
Document as soon as you load a different Document (using
:meth:`View.setDocument() <view.View.setDocument>`). If you switch back to the
former document, the View restores its position and other display settings for
that document.

To use a DocumentPropertyStore::

    v = qpageview.View()
    store = qpageview.view.DocumentPropertyStore()
    v.documentPropertyStore = store

By setting a mask it is possible to influence which properties are remembered.
In this example, only zoom factor and position are remembered when switching
documents::

    store.mask = ['position', 'zoomFactor']

*Lazy View instantiation*: It is also possible to initialize the *ViewActions*
from your settings, even if you have not yet created a View (for example, when
the View is in a not yet created dock widget that is lazily instantiated). This
way, you application's user interface already reflects the corrent settings for
the yet-not-created view. Use the View.properties() static method to get an
uninitialized ViewProperties object, set some defaults and then add settings
read from a QSettings object. Finally update the state of the actions in the
ViewActions object, *before* connecting to the ``ViewActions.viewRequested``
signal.

All methods of ViewProperties return self, so these calls can be easily
chained::

    settings = QSettings()
    props = qpageview.View.properties().setdefaults().load(settings)
    actions = qpageview.viewactions.ViewActions()
    actions.updateFromProperties(props)
    actions.viewRequested.connect(createView)

Later, when you really instantiate the View, you should also load the View
settings; the ViewActions object does not actively update the View when
connecting (rather, the actions are adjusted to the View when connecting)::

    def createView():
        # creating the View....
        v = qpageview.View()
        settings = QSettings()
        v.readProperties(settings)
        actions.setView(v)



Using View Mixins
~~~~~~~~~~~~~~~~~

The View as defined in the :mod:`qpageview` module is a class composed
of the basic View class in :class:`view.View` and some View Mixin classes
that extend the functionality of the basic View.

This is a list of the currently available View Mixin classes:

:class:`link.LinkViewMixin`
    Adds functionality to click on links, e.g. in PDF pages

:class:`highlight.HighlightViewMixin`
    Adds functionality to highlight rectangular regions

:class:`shadow.ShadowViewMixin`
    Draws a nice shadow border around the pages

:class:`util.LongMousePressMixin`
    Handles long mouse presses (can be mixed in with any QWidget)

:class:`imageview.ImageViewMixin`
    A View targeted to the display of one single image (see also the
    :class:`~imageview.ImageView`)

:class:`selector.SelectorViewMixin`
    Adds functionality to make pages selectable with a checkbox

:class:`widgetoverlay.WidgetOverlayViewMixin`
    Adds functionality to display QWidgets on Pages that scroll and optionally
    zoom along and the user can interact with


So, depending on your needs, you can create your own View subclass, mixing in
only the functionality you need. Put the main View class at the end, for
example::

    class View(
        qpageview.link.LinkViewMixin,
        # other mixins here
        qpageview.view.View):
        """My View with some enhancements."""
        pass

        # my own extensions and new funcionality
        def myMethod(self):
            pass


Specialized View subclasses
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are already some specialized View subclasses available, those
are:

:class:`~imageview.ImageView`
    A View that is tailored to show one image (from file, data or a QImage)

:class:`~sidebarview.SidebarView`
    A View that shows selectable thumbnails of all pages in a connected View,
    usable as a sidebar for a normal View.

