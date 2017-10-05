# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re

from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer, HTMLTranslator
from inspect import cleandoc

from django import template

register = template.Library()


class NoHeaderHTMLTranslator(HTMLTranslator):
    """
    Docutils translator subclass to customize the generation of HTML
    from reST-formatted docstrings
    """
    def __init__(self, document):
        super().__init__(document)
        self.body_prefix = []
        self.body_suffix = []

    def visit_bullet_list(self, node):
        self.context.append((self.compact_simple, self.compact_p))
        self.compact_p = None
        self.compact_simple = self.is_compactable(node)
        self.body.append(self.starttag(node, 'ul', CLASS='docstring'))


DOCSTRING_WRITER = Writer()
DOCSTRING_WRITER.translator_class = NoHeaderHTMLTranslator


@register.filter
def safe_docstring_display(docstring):
    """
    Utility function to htmlize reST-formatted documentation in browsable
    api.
    """
    docstring = cleandoc(docstring)
    return publish_parts(docstring, writer=DOCSTRING_WRITER)['html_body']


@register.filter
def urlize_links_and_mails(text):
    """Utility function for decorating api links in browsable api.

    Args:
        text: whose content matching links should be transformed into
        contextual API or Browse html links.

    Returns
        The text transformed if any link is found.
        The text as is otherwise.

    """
    text = re.sub(r'(/api/[^"<]*/|/browse/.*/|http.*$)',
                  r'<a href="\1">\1</a>',
                  text)
    return re.sub(r'([^ <>"]+@[^ <>"]+)',
                  r'<a href="mailto:\1">\1</a>',
                  text)


@register.filter
def urlize_header_links(text):
    """Utility function for decorating headers links in browsable api.

    Args
        text: Text whose content contains Link header value

    Returns:
        The text transformed with html link if any link is found.
        The text as is otherwise.

    """
    return re.sub(r'<(/api/.*|/browse/.*)>', r'<<a href="\1">\1</a>>',
                  text)
