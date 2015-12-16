# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation, too-few-public-methods
""" 'tidy' command.
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

from bunch import bunchify
from rudiments.reamed import click

from .. import config, api


# Simple replacement rules, order is important!
REGEX_RULES = ((re.compile(_rule), _subst) for _rule, _subst in [
    # FosWiki: 'tok' spans in front of headers
    (r'(?<=<h.>)<span class="tok">&nbsp;</span>', ''),
    # FosWiki: Section edit icons at the end of headers
    (r' *<a href="[^"]+"><ac:image [^>]+><ri:url ri:value="[^"]+/EditChapterPlugin/pencil.png" ?/></ac:image></a>(?=</span></h)', ''),
    # FosWiki: "Edit Chapter Plugin" spans
    (r'(?<=<h.>)<span class="ecpHeading">([^<]+)</span>(?=</h.>)', r'\1'),
    # FosWiki: Residual leading whitespace in headers
    (r'(?<=<h.>) +', ''),
])


class ConfluencePage(object):
    """A page that holds enough state so it can be modified."""

    def __init__(self, cf, url, markup='storage'):
        """Load the given page."""
        self.cf = cf
        self.url = url
        self.markup = markup
        self._data = cf.get(self.url, expand='space,version,body.' + self.markup)
        self.body = self._data.body[self.markup].value

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
            'space': {'key': self._data.space.key},
            'title': self._data.title,
            'version': {'number': self._data.version.number + 1},
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


@config.cli.command()
@click.option('-R', '--recursive', is_flag=True, default=False, help='Handle all descendants.')
@click.argument('pages', metavar='‹page-url›…', nargs=-1)
@click.pass_context
def tidy(ctx, pages, recursive=False):
    """Tidy pages after cut&paste migration from other wikis."""
    with api.context() as cf:
        for page_url in pages:
            try:
                page = ConfluencePage(cf, page_url)
            except api.ERRORS as cause:
                # Just log and otherwise ignore any errors
                click.serror("API ERROR: {}", cause)
            else:
                ctx.obj.log.info('%d attributes', len(page._data))
                ##print(page._data); xxx
                ##print(page.body)
                body = page.body
                for rule, subst in REGEX_RULES:
                    body, count = rule.subn(subst, body)
                    if count:
                        ctx.obj.log.info('Replaced %d matches of %r', count, rule.pattern)
                ##print('\n' + page.body)
                result = page.update(body)
                if result:
                    ctx.obj.log.info('Updated page#{id} to version #{version.number}'.format(**result))
