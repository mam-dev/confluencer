# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation, too-few-public-methods
""" 'rm' command.
"""
# Copyright ©  2015 – 2017 1&1 Group <git@1and1.com>
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

import sys

from munch import Munch as Bunch
from rudiments.reamed import click

from .. import config, api
from ..util import progress, CLEARLINE
from ..tools import content


@config.cli.group(name='rm')
@click.pass_context
def remove(ctx):
    """Remove contents."""


@remove.command()
## TODO: -n, --no-act, --dry-run, --simulate
## TODO: --with[out]-root (or tree vs children command?)
## TODO: include / exclude filters (title glob)
@click.argument('pages', metavar='‹page-url›…', nargs=-1)
@click.pass_context
def tree(ctx, pages):
    """Remove page(s) including their descendants."""
    with api.context() as cf:
        for page_ref in pages:
            root_page = cf.get(page_ref)
            root_children = cf.get(root_page._expandable.children, expand='page', limit=200)

            # Get confirmation
            answer = None
            while answer not in {'yes', 'no', 'n'}:
                answer = input('REALLY remove {} children of »{}« and all their descendants? [yes|No|N] '
                               .format(len(root_children.page.results), root_page.title))
                answer = answer.lower() or 'n'

            # Delete data on positive confirmation
            if answer != 'yes':
                click.echo('No confirmation, did not delete anything!')
            else:
                counter = 0
                try:
                    iter_pages = progress(sorted(root_children.page.results, key=lambda x: x.title.lower()))
                    for page in iter_pages:
                        print(CLEARLINE + "DEL", page.title, end='\r')
                        iter_pages.set_postfix_str('')
                        while True:
                            children = cf.get(page._expandable.children, expand='page', limit=200).page.results
                            if not children:
                                break
                            for child in children:
                                cf.delete_page(child)
                                counter += 1
                        cf.delete_page(page)
                        counter += 1
                finally:
                    print(CLEARLINE + "Deleted {} pages.\n".format(counter))
