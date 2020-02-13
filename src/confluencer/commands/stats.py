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

import sys
import json
from pprint import pformat

from munch import Munch as Bunch
from rudiments.reamed import click

from .. import config, api
from ..tools import content
from .._compat import text_type, string_types


SERIALIZERS_NEED_NL = ('dict', 'json', 'html')
SERIALIZERS_TEXT = SERIALIZERS_NEED_NL + ('yaml', 'csv', 'tsv')
SERIALIZERS_BINARY = ('ods', 'xls')  # this just doesn't work right (Unicode issues): , 'xlsx')
SERIALIZERS = SERIALIZERS_TEXT + SERIALIZERS_BINARY

ENTITIES = ('macro',)  # 'label', 'page', 'title', 'attachment', 'blog', …


def print_result(ctx, obj):
    """ Dump a result to the console or an output file."""
    text = obj
    if isinstance(text, dict):
        if isinstance(text, Bunch):
            # Debunchify for ``pformat``
            text = dict(text.copy())
            for key, val in text.items():
                if isinstance(val, Bunch):
                    text[key] = dict(val)
        #text = pformat(text)
        text = json.dumps(text, indent=2, sort_keys=True)
    elif isinstance(text, list):
        text = json.dumps(text, indent=2, sort_keys=True)

    if not isinstance(text, string_types):
        text = repr(text)
    if ctx.obj.serializer in SERIALIZERS_NEED_NL:
        text += '\n'
    #if isinstance(text, text_type):
    #    text = text.encode('utf-8')
    try:
        (ctx.obj.outfile or sys.stdout).write(text)
    except EnvironmentError as cause:
        raise click.LoggedFailure('Error while writing "{}" ({})'.format(
            getattr(ctx.obj.outfile or object(), 'name', '<stream>'), cause))


@config.cli.group()
@click.option('-f', '--format', 'serializer', default=None, type=click.Choice(SERIALIZERS),
    help="Output format (defaults to extension of OUTFILE).",
)
@click.option('-s', '--space', multiple=True)
@click.option('-e', '--entity', default=None, type=click.Choice(ENTITIES),
    help="Entity to handle / search for.",
)
@click.option('-o', '--outfile', default=None, type=click.File('wb'))
@click.pass_context
def stats(ctx, space, entity, outfile, serializer):
    """Create status reports (or data exports)."""
    ctx.obj.spaces = space
    ctx.obj.entity = entity
    ctx.obj.outfile = outfile
    ctx.obj.serializer = serializer

    ctx.obj.cql = []
    if ctx.obj.spaces:
        ctx.obj.cql.append('({})'.format(
            ' OR '.join(['space="{}"'.format(x) for x in ctx.obj.spaces]),
        ))


@stats.command()
@click.option('--top', metavar='N', default=0, type=int,
              help="Show top ‹N› ranked entities.")
@click.argument('query')
@click.pass_context
def usage(ctx, query, top=0):
    """Create report on usage of different entities (macros, labels, …)."""
    if not ctx.obj.entity:
        click.serror("No --entity selected!")
        return
    if top:
        click.echo("TOP {:d}".format(top))

    outname = getattr(ctx.obj.outfile, 'name', None)

    with api.context() as cf:
        ctx.obj.cql.append('type=page AND macro != "{}"'.format(query))
        try:
            response = cf.get("content/search", cql=' AND '.join(ctx.obj.cql))
        except api.ERRORS as cause:
            # Just log and otherwise ignore any errors
            api.diagnostics(cause)
        else:
            print('Got {} results.'.format(len(response.results)))
            if response.results:
                print_result(ctx, response.results[0])


@stats.command()
@click.argument('rootpage')
@click.pass_context
def tree(ctx, rootpage):
    """Export metadata of a page tree."""
    if not rootpage:
        click.serror("No root page selected via --entity!")
        return 1

    outname = getattr(ctx.obj.outfile, 'name', None)

    with api.context() as cf:
        results = []
        try:
            #page = content.ConfluencePage(cf, rootpage, expand='metadata.labels,metadata.properties')
            #results.append(page.json)
            pagetree = cf.walk(rootpage, depth_1st=True,
                               expand='metadata.labels,metadata.properties,version')
            for depth, data in pagetree:
                data.update(dict(depth=depth))
                results.append(data)
        except api.ERRORS as cause:
            # Just log and otherwise ignore any errors
            api.diagnostics(cause)
        else:
            ctx.obj.log.info('Got {} results.'.format(len(results)))
            if results:
                print_result(ctx, results)
