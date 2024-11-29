<!-- Please follow this spec: https://keepachangelog.com/
[X.Y.Z] links to the GitHub list of commits in a tag/release are
defined at the bottom of this file.
-->

# Changelog

All notable changes to the qpageview project are documented in this file.

## [1.0.0] - 2025-01-06

### Added

* Port to PyQt6 (version 6.6 or higher)
* New PDF backend using QtPdf

### Changed

* Poppler is no longer required for PDF support
* Project metadata moved to `pyproject.toml`; the build backend
  is now hatchling
* The new minimum Python version is 3.7

## [0.6.2] - 2022-05-05

### Fixed

* Kept another implicit float->int conversion from happening by having
  Scrollarea.remainingScrollTime() returning an int
* Some robustness improvements

### Changed

* Documentation improvements

## [0.6.1] - 2021-11-11

### Changed

* View.strictPagingEnabled always lets PgUp/PgDn scroll a page instead
  of a screenful

### Fixed

* Don't depend on implicit float->int conversions, which were deprecated since
  Python 3.8 and not supported anymore by Python 3.10
* Fixed initial zoomfactor for ImageView when fitNaturalSizeEnabled is True

## [0.6.0] 2021-01-07

### Added

* added view.View.pages() method (#2)
* added view.View.setPages() method (inspired by #4)

## [0.5.1] 2020-04-25

### Added

* Add PagerAction.setButtonSymbols()

### Changed

* Many documentation updates
* make it easier to manipulate the edge/corner of the rubberband

### Fixed

* fix flickering mouse cursor on rubberband

## 0.5.0 2020-04-19

Initial release. The qpageview module was developed by me, Wilbert Berendsen,
as a replacement of the qpopplerview module inside Frescobaldi, the LilyPond
sheet music text editor. I decided that it would be best if qpageview became
its own project, to make it easier to use this package in other applications.

[0.5.1]: https://github.com/frescobaldi/qpageview/compare/v0.5.0...v0.5.1
[0.6.0]: https://github.com/frescobaldi/qpageview/compare/v0.5.1...v0.6.0
[0.6.1]: https://github.com/frescobaldi/qpageview/compare/v0.6.0...v0.6.1
[0.6.2]: https://github.com/frescobaldi/qpageview/compare/v0.6.1...v0.6.2
[1.0.0]: https://github.com/frescobaldi/qpageview/compare/v0.6.2...v1.0.0
