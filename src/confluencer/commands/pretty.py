# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation, too-few-public-methods
""" 'pretty' command.
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

import sys

from rudiments.reamed import click

from .. import config, api
from ..tools import content


@config.cli.command()
@click.option('-R', '--recursive', is_flag=True, default=False, help='Handle all descendants.')
@click.option('-f', '--format', 'markup', default='view', type=click.Choice(content.CLI_CONTENT_FORMATS.keys()),
    help="Markup format.",
)
@click.argument('pages', metavar='‹page-url›…', nargs=-1)
@click.pass_context
def pretty(ctx, pages, markup, recursive=False):
    """Pretty-print page content markup."""
    content_format = content.CLI_CONTENT_FORMATS[markup]
    with api.context() as cf:
        for page_url in pages:
            try:
                page = content.ConfluencePage(cf, page_url, markup=content_format)
            except api.ERRORS as cause:
                # Just log and otherwise ignore any errors
                click.serror("API ERROR: {}", cause)
            else:
                root = page.etree()
                root.getroottree().write(sys.stdout, encoding='utf8', pretty_print=True, xml_declaration=False)
