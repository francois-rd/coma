# Configuration file for the Sphinx documentation builder.
import datetime

from pkg_resources import get_distribution

project = "Coma"
author = "Francois Roewer-Despres"
copyright = f"{datetime.datetime.now().year}, {author}"

release = get_distribution("coma").version
version = release

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "piccolo_theme",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "piccolo_theme"
html_theme_options = {"source_url": "https://github.com/francois-rd/coma"}

# -- Options for EPUB output

epub_show_urls = "footnote"

add_module_names = False  # Displays as 'func' rather than 'module.sub.func'.
autodoc_default_options = {
    "member-order": "bysource",  # Module members appear in source order.
}
