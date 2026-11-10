import datetime

project = f'mplDTs'
thisyear = datetime.datetime.now().year
copyright = '2024-%s, Daniel Estrada, Universidad de Oviedo' % thisyear
author = 'Daniel Estrada'
from mpldts import __version__ as _mpldts_version

release = _mpldts_version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "myst_nb",
]

# The tutorial notebooks are executed by hand and their outputs are committed,
# so the documentation build needs no kernel and no CMS data of its own.
nb_execution_mode = "off"
nb_execution_timeout = 300

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_show_sourcelink = False
html_js_files = ["versions.js"]
rst_prolog = """
:github_url: https://github.com/INTREPID-hep/mplDTs
"""

html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "titles_only": False,
}
