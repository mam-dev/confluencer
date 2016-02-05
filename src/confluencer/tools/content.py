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
from bunch import bunchify
from lxml.etree import fromstring, HTMLParser, XMLParser, XMLSyntaxError  # pylint: disable=no-name-in-module
from rudiments.reamed import click

from .._compat import StringIO


# Simple replacement rules, order is important!
REGEX_RULES = ((_name, re.compile(_rule), _subst) for _name, _rule, _subst in [
    ("FosWiki: Remove static section numbering",
     r'(?<=<h.>)[0-9.]+ ?(?=<span class="tok">&nbsp;</span>)', ''),
    ("FosWiki: 'tok' spans in front of headers",
     r'(?<=<h.>)<span class="tok">&nbsp;</span>', ''),
    ("FosWiki: Section edit icons at the end of headers",
     r' *<a href="[^"]+"><ac:image [^>]+><ri:url ri:value="[^"]+/EditChapterPlugin/pencil.png" ?/>'
     r'</ac:image></a>(?=</span></h)', ''),
    ("FosWiki: 'Edit Chapter Plugin' spans",
     r'(?<=<h.>)<span class="ecpHeading">([^<]+)</span>(?=</h.>)', r'\1'),
    ("FosWiki: Residual leading whitespace in headers",
     r'(?<=<h.>) +', ''),
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
    #("FosWiki: Replace HTML '<pre>' with 'code' macro",
    # r'<pre>', '<div><ac:structured-macro ac:name="code" ac:schema-version="1"><ac:plain-text-body>![CDATA['),
    #("FosWiki: Replace HTML '</pre>' with 'code' macro",
    # r'</pre>', ']]</ac:plain-text-body></ac:structured-macro></div>'),
])


def _apply_regex_rules(body, log=None):
    """Return tidied body after applying regex rules."""
    for name, rule, subst in REGEX_RULES:
        body, count = rule.subn(subst, body)
        if count and log:
            log.info('Replaced %d matche(s) of "%s"', count, name)
    return body


def _pretty_xml(body, content_format='storage'):
    """Pretty-print the given page body and return a list of lines."""
    attrs = {
        'xmlns:ac': 'http://www.atlassian.com/schema/confluence/4/ac/',
        'xmlns:ri': 'http://www.atlassian.com/schema/confluence/4/ri/',
    }
    body = re.sub(r'&(?!(amp|lt|gt|quot|apos))([a-zA-Z0-9]+);',
                  lambda cref: '&#{};'.format(htmlentitydefs.name2codepoint[cref.group(2)]), body)
    #print(body.encode('utf8'))
    xmldoc = u'<{root} {attrs}>{body}</{root}>'.format(
        root=content_format,
        attrs=' '.join('{}={}'.format(k, quoteattr(v)) for k, v in sorted(attrs.items())),
        body=body)

    parser = (XMLParser if content_format == 'storage' else HTMLParser)(remove_blank_text=True)
    try:
        root = fromstring(xmldoc, parser)
    except XMLSyntaxError as cause:
        raise click.LoggedFailure('{}\n{}'.format(
            cause, '\n'.join(['{:7d} {}'.format(i+1, k) for i, k in enumerate(xmldoc.splitlines())])
        ))
    prettyfied = StringIO()
    root.getroottree().write(prettyfied, encoding='utf8', pretty_print=True, xml_declaration=False)
    return prettyfied.getvalue().splitlines()


class ConfluencePage(object):
    """A page that holds enough state so it can be modified."""

    DIFF_COLS = {
        '+': 'green',
        '-': 'red',
        '@': 'yellow',
    }

    def __init__(self, cf, url, markup='storage'):
        """Load the given page."""
        self.cf = cf
        self.url = url
        self.markup = markup
        self._data = cf.get(self.url, expand='space,version,body.' + self.markup)
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
    def version(self):
        """The page's version number in history."""
        return self._data.version.number

    def tidy(self, log=None):
        """Return a tidy copy of this page's body."""
        assert self.markup == 'storage', "Can only clean up pages in storage format!"
        return _apply_regex_rules(self.body, log=log)

    def update(self, body=None):
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
            'version': {'number': self.version + 1},
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
            click.secho('No changes to "{0}"'.format(self.title), fg='green')
            return

        diff = difflib.unified_diff(
            _pretty_xml(self.body, self.markup),
            _pretty_xml(changed, self.markup),
            'v. {0} of "{1}"'.format(self.version, self.title),
            'v. {0} of "{1}"'.format(self.version + 1, self.title),
            arrow.get(self._data.version.when).replace(microsecond=0).isoformat(sep=b' '),
            arrow.now().replace(microsecond=0).isoformat(sep=b' '),
            lineterm='', n=2)
        for line in diff:
            click.secho(line, fg=self.DIFF_COLS.get(line and line[0], None))