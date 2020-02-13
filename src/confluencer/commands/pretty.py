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

import os
import sys
import json as jsonlib

from rudiments.reamed import click

from .. import config, api
from ..tools import content


@config.cli.command()
@click.option('-R', '--recursive', is_flag=True, default=False, help='Handle all descendants.')
@click.option('-J', '--json', is_flag=True, default=False, help='Print raw API response (JSON).')
@click.option('-f', '--format', 'markup', default='view', type=click.Choice(content.CLI_CONTENT_FORMATS.keys()),
    help="Markup format.",
)
@click.argument('pages', metavar='‹page-url›…', nargs=-1)
@click.pass_context
def pretty(ctx, pages, markup, recursive=False, json=False):
    """Pretty-print page content markup."""
    content_format = content.CLI_CONTENT_FORMATS[markup]
    with api.context() as cf:
        for page_url in pages:
            try:
                page = content.ConfluencePage(cf, page_url, markup=content_format,
                                              expand='metadata.labels,metadata.properties')
            except api.ERRORS as cause:
                # Just log and otherwise ignore any errors
                api.diagnostics(cause)
            else:
                if json:
                    jsonlib.dump(page.json, sys.stdout, indent='  ', sort_keys=True)
                else:
                    root = page.etree()
                    with os.fdopen(sys.stdout.fileno(), "wb", closefd=False) as stdout:
                        root.getroottree().write(stdout, encoding='utf8', pretty_print=True, xml_declaration=False)
