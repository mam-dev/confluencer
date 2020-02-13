# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
""" Tools to discover and modify content.
"""
# Copyright ©  2015 1&1 Group <git@1and1.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, unicode_literals, print_function

import re
import difflib
try:
    import html.entities as htmlentitydefs
except ImportError:  # Python 2
    import htmlentitydefs  # pylint: disable=import-error,wrong-import-order
from xml.sax.saxutils import quoteattr  # pylint: disable=wrong-import-order

import arrow
from munch import munchify as bunchify
from lxml.etree import fromstring, HTMLParser, XMLParser, XMLSyntaxError  # pylint: disable=no-name-in-module
from rudiments.reamed import click

from .._compat import BytesIO


# Mapping of CLI content format names to Confluence API names
CLI_CONTENT_FORMATS = dict(view='view', editor='editor', storage='storage', export='export_view', anon='anonymous_export_view')

# Simple replacement rules, order is important!
TIDY_REGEX_RULES = ((_name, re.compile(_rule), _subst) for _name, _rule, _subst in [
    ("FosWiki: Remove CSS class from section title",
     r'<(h[1-5]) class="[^"]*">', r'<\1>'),
    ("FosWiki: Remove static section numbering",
     r'(?<=<h.>)(<a name="[^"]+?"></a>|)[0-9.]+?\s*(?=<span class="tok">&nbsp;</span>)', r'\1'),
    ("FosWiki: Empty anchor in headers",
     r'(?<=<h.>)<a></a>\s* +', ''),
    ("FosWiki: 'tok' spans in front of headers",
     r'(?<=<h.>)(<a name="[^"]+?"></a>|)\s*<span class="tok">&nbsp;</span>', r'\1'),
    ("FosWiki: Section edit icons at the end of headers",
     r'\s*<a(?: class="[^"]*")? href="[^"]+"(?: title="[^"]*")?>'
     r'<ac:image [^>]+><ri:url ri:value="[^"]+/EditChapterPlugin/pencil.png" ?/>'
     r'</ac:image></a>(?=</span></h)', ''),
    ("FosWiki: 'Edit Chapter Plugin' spans (old)",
     r'(?<=<h.>)(<a name="[^"]+?"></a>|)\s*<span class="ecpHeading">'
     r'\s*([^<]+)(?:<br\s*/>)</span>\s*(?=</h.>)', r'\1\2'),
    ("FosWiki: 'Edit Chapter Plugin' spans (new)",
     r'(?<=<h.>)(<a name="[^"]+?"></a>|)\s*<span class="ecpHeading">'
     r'\s*([^<]+)(?:<br\s*/>)<a class="ecpEdit".+?</a></span>\s*(?=</h.>)', r'\1\2'),
    ("FosWiki: Residual leading whitespace in headers",
     r'(?<=<h.>)(<a name="[^"]+?"></a>|)\s* +', r'\1'),
    ("FosWiki: Replace TOC div with macro",
     r'(<a name="foswikiTOC" ?/>)?<div class="foswikiToc">.*?</div>', '''
          <ac:structured-macro ac:name="panel" ac:schema-version="1">
            <ac:parameter ac:name="title">Contents</ac:parameter>
            <ac:rich-text-body>
              <p>
                <ac:structured-macro ac:name="toc" ac:schema-version="1"/>
              </p>
            </ac:rich-text-body>
          </ac:structured-macro>'''),
    ("FosWiki: Replace TOC in a Twisty with Expand+TOC macro",
     r'<div class="twistyPlugin">.+?<big><strong>Table of Contents</strong></big></span></a></span></div>', '''
          <ac:structured-macro ac:name="expand" ac:schema-version="1">
            <ac:parameter ac:name="title">Table of Contents</ac:parameter>
            <ac:rich-text-body>
              <p>
                <ac:structured-macro ac:name="toc" ac:schema-version="1"/>
              </p>
            </ac:rich-text-body>
          </ac:structured-macro>'''),
    ("FosWiki: Named anchors (#WikiWords)",
     r'(<a name=[^>]+></a><a href=")http[^#]+(#[^"]+" style="[^"]+)(" title="[^"]+"><big>[^<]+</big></a>)',
     r'\1\2; float: right;\3'),
    ("FosWiki: Wrap HTML '<pre>' into 'panel' macro",
     r'(?<!<ac:rich-text-body>)(<pre(?: class="[^"]*")?>)',
     r'<ac:structured-macro ac:name="panel" ac:schema-version="1">'
     r'<ac:parameter ac:name="bgColor">#eeeeee</ac:parameter>'
     r'<ac:rich-text-body>'
     r'\1'),
    ("FosWiki: Wrap HTML '</pre>' into 'panel' macro",
     r'</pre>(?!</ac:rich-text-body>)', '</pre></ac:rich-text-body></ac:structured-macro>'),
    ("FosWiki: Embedded CSS - custom list indent",
     r'<ul style="margin-left: [.0-9]+em;">', '<ul>'),
    ("FosWiki: Empty paragraphs",
     r'<p>&nbsp;</p>', r''),
    ("FosWiki: Obsolete CSS classes",
     r'(<(?:div|p|span|h[1-5])) class="(foswikiTopic)"', r'\1'),
])


def _apply_tidy_regex_rules(body, log=None):
    """Return tidied body after applying regex rules."""
    body = body.replace(u'\u00A0', '&nbsp;')
    for name, rule, subst in TIDY_REGEX_RULES:
        length = len(body)
        try:
            body, count = rule.subn(subst, body)
        except re.error as cause:
            raise click.LoggedFailure('Error "{}" in "{}" replacement: {} => {}'.format(
                cause, name, rule.pattern, subst,
            ))
        if count and log:
            length -= len(body)
            log.info('Replaced %d matche(s) of "%s" (%d chars %s)',
                     count, name, abs(length), "added" if length < 0 else "removed")
    return body


def _make_etree(body, content_format='storage', attrs=None):
    """Create an ElementTree from a page's body."""
    attrs = (attrs or {}).copy()
    attrs.update({
        'xmlns:ac': 'http://www.atlassian.com/schema/confluence/4/ac/',
        'xmlns:ri': 'http://www.atlassian.com/schema/confluence/4/ri/',
    })
    xml_body = re.sub(r'&(?!(amp|lt|gt|quot|apos))([a-zA-Z0-9]+);',
                  lambda cref: '&#{};'.format(htmlentitydefs.name2codepoint[cref.group(2)]), body)
    #print(body.encode('utf8'))
    xmldoc = u'<{root} {attrs}>{body}</{root}>'.format(
        root=content_format,
        attrs=' '.join('{}={}'.format(k, quoteattr(v)) for k, v in sorted(attrs.items())),
        body=xml_body)

    parser = (XMLParser if content_format == 'storage' else HTMLParser)(remove_blank_text=True)
    try:
        return fromstring(xmldoc, parser)
    except XMLSyntaxError as cause:
        raise click.LoggedFailure('{}\n{}'.format(
            cause, '\n'.join(['{:7d} {}'.format(i+1, k) for i, k in enumerate(xmldoc.splitlines())])
        ))


def _pretty_xml(body, content_format='storage', attrs=None):
    """Pretty-print the given page body and return a list of lines."""
    root = _make_etree(body, content_format=content_format, attrs=attrs)
    prettyfied = BytesIO()
    root.getroottree().write(prettyfied, encoding='utf8', pretty_print=True, xml_declaration=False)
    return prettyfied.getvalue().decode('utf8').splitlines()


class ConfluencePage(object):
    """A page that holds enough state so it can be modified."""

    DIFF_COLS = {
        '+': 'green',
        '-': 'red',
        '@': 'yellow',
    }

    def __init__(self, cf, url, markup='storage', expand=None):
        """ Load the given page.
        """
        if expand and isinstance(expand, str):
            expand = expand.split(',')
        expand = set(expand or []) | {'space', 'version', 'body.' + markup}

        self.cf = cf
        self.url = url
        self.markup = markup
        self._data = cf.get(self.url, expand=','.join(expand))
        self.body = self._data.body[self.markup].value

    @property
    def page_id(self):
        """The numeric page ID."""
        return self._data.id

    @property
    def space_key(self):
        """The space this page belongs to."""
        return self._data.space.key

    @property
    def title(self):
        """The page's title."""
        return self._data.title

    @property
    def json(self):
        """The full JSON response data."""
        return self._data

    @property
    def version(self):
        """The page's version number in history."""
        return self._data.version.number

    def etree(self):
        """Parse the page's body into an ElementTree."""
        attrs = {
            'id': 'page-' + self._data.id,
            'href': self._data._links.base + (self._data._links.tinyui or ''),
            'status': self._data.status,
            'title': self._data.title,
        }
        return _make_etree(self.body, content_format=self.markup, attrs=attrs)

    def tidy(self, log=None):
        """Return a tidy copy of this page's body."""
        assert self.markup == 'storage', "Can only clean up pages in storage format!"
        return _apply_tidy_regex_rules(self.body, log=log)

    def update(self, body=None, minor=True):
        """Update a page's content."""
        assert self.markup == 'storage', "Cannot update non-storage page markup!"
        if body is None:
            body = self.body
        if body == self._data.body[self.markup].value:
            return  # No changes

        data = {
            #'id': self._data.id,
            'type': 'page',
            'space': {'key': self.space_key},
            'title': self.title,
            'version': dict(number=self.version + 1, minorEdit=minor),
            'body': {
                'storage': {
                    'value': body,
                    'representation': self.markup,
                }
            },
            'expand': 'version',
        }
        response = self.cf.session.put(self._data._links.self, json=data)
        response.raise_for_status()
        ##page = response.json(); print(page)
        result = bunchify(response.json())
        self._data.body[self.markup].value = body
        self._data.version = result.version
        return result


    def dump_diff(self, changed):
        """Dump a diff to terminal between changed and stored body."""
        if self.body == changed:
            click.secho('=== No changes to "{0}"'.format(self.title), fg='green')
            return

        diff = difflib.unified_diff(
            _pretty_xml(self.body, self.markup),
            _pretty_xml(changed, self.markup),
            u'v. {0} of "{1}"'.format(self.version, self.title),
            u'v. {0} of "{1}"'.format(self.version + 1, self.title),
            arrow.get(self._data.version.when).replace(microsecond=0).isoformat(sep=' '),
            arrow.now().replace(microsecond=0).isoformat(sep=' '),
            lineterm='', n=2)
        for line in diff:
            click.secho(line, fg=self.DIFF_COLS.get(line and line[0], None))
