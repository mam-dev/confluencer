# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation, too-few-public-methods
""" 'stats' command group.
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

from rudiments.reamed import click

from .. import config, api
from ..tools import content


SERIALIZERS_NEED_NL = ('dict', 'json', 'html')
SERIALIZERS_TEXT = SERIALIZERS_NEED_NL + ('yaml', 'csv', 'tsv')
SERIALIZERS_BINARY = ('ods', 'xls')  # this just doesn't work right (Unicode issues): , 'xlsx')
SERIALIZERS = SERIALIZERS_TEXT + SERIALIZERS_BINARY


@config.cli.group()
@click.option('-f', '--format', 'serializer', default=None, type=click.Choice(SERIALIZERS),
    help="Output format (defaults to extension of OUTFILE).",
)
@click.option('-o', '--outfile', default=None, type=click.File('wb'))
@click.pass_context
def stats(ctx, outfile, serializer):
    """Create status reports (or data exports)."""
    ctx.obj.outfile = outfile
    ctx.obj.serializer = serializer


@stats.command()
@click.option('--top', metavar='N', default=0, type=int,
              help="Show top ‹N› ranked entities.")
@click.pass_context
def usage(ctx, top=0):
    """Create report on usage of different entities (macros, labels, …)."""
    if top:
        click.echo("TOP {:d}".format(top))
    else:
        click.echo(ctx.get_help()) ##, color=ctx.color)
        ctx.exit()
