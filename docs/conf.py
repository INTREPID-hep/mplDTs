import datetime

project = f'mplDTs'
thisyear = datetime.datetime.now().year
copyright = '2024-%s, Daniel Estrada, Universidad de Oviedo' % thisyear
author = 'Daniel Estrada'
release = '2.0.0'

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.todo", 'sphinx_copybutton']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_show_sourcelink=False
rst_prolog = """
:github_url: https://github.com/DanielEstrada971102/mplDTs
"""

html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "titles_only": False,
}