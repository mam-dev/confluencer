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

from rudiments.reamed import click

from .. import config, api
from ..tools import content


@config.cli.command()
@click.option('--diff', is_flag=True, default=False, help='Show differences after tidying.')
@click.option('-n', '--no-save', '--dry-run', count=True,
              help="Only show differences after tidying, don't apply them (use twice for no diff).")
@click.option('-R', '--recursive', is_flag=True, default=False, help='Handle all descendants.')
@click.argument('pages', metavar='‹page-url›…', nargs=-1)
@click.pass_context
def tidy(ctx, pages, diff=False, dry_run=0, recursive=False):
    """Tidy pages after cut&paste migration from other wikis."""
    with api.context() as cf:
        for page_url in pages:
            try:
                page = content.ConfluencePage(cf, page_url)
            except api.ERRORS as cause:
                # Just log and otherwise ignore any errors
                api.diagnostics(cause)
            else:
                ##print(page._data); xxx
                body = page.tidy(log=ctx.obj.log)
                if body == page.body:
                    ctx.obj.log.info('No changes for "%s"', page.title)
                else:
                    if diff or dry_run == 1:
                        page.dump_diff(body)
                    if dry_run:
                        ctx.obj.log.info('WOULD save page#{0} "{1}" as v. {2}'.format(page.page_id, page.title, page.version + 1))
                    else:
                        result = page.update(body)
                        if result:
                            ctx.obj.log.info('Updated page#{id} "{title}" to v. {version.number}'.format(**result))
                        else:
                            ctx.obj.log.info('Changes not saved for "%s"', page.title)
