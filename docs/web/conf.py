import sys

sys.path.insert(0, "../source")
from conf import *


extensions.extend([
    "sphinx_rtd_theme",
])

html_theme = "sphinx_rtd_theme"
html_theme_path = [
    # we need the current git version of the theme, pip3 install fails...
    "/home/wilbert/src/sphinx_rtd_theme/",
]

html_logo = '_static/qp.png'

html_theme_options = {
    'canonical_url': 'https://qpageview.org/',
#    'analytics_id': 'UA-XXXXXXX-1',  #  Provided by Google in your dashboard
    'logo_only': True,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    #'style_nav_header_background': 'white',
    'style_nav_header_background': 'firebrick',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

html_context = {
  'display_github': True,
  'github_user': 'frescobaldi',
  'github_repo': 'qpageview',
  'github_version': 'master',
  'conf_py_path': '/docs/source/',
}

