# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation, too-few-public-methods
""" 'help' command.
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
import itertools

from rudiments.reamed import click

from .. import config, api


@config.cli.command(name='help')
@click.option('-c', '--config-dump', is_flag=True, default=False, help='Dump the merged configuration to stdout.')
@click.pass_context
def help_command(ctx, config_dump=False):
    """Print some information on the system environment."""
    def banner(title):
        "Helper"
        click.echo('')
        click.secho('~~~ {} ~~~'.format(title), fg='green', bg='black', bold=True)

    if config_dump:
        ctx.obj.cfg.dump()
        sys.exit(0)

    app_name = ctx.find_root().info_name
    click.secho('*** "{}" Help & Information ***'.format(app_name), fg='white', bg='blue', bold=True)

    banner('Version Information')
    click.echo(config.version_info(ctx))

    banner('Configuration')
    locations = ctx.obj.cfg.locations(exists=False)
    locations = [(u'✔' if os.path.exists(i) else u'✘', click.pretty_path(i)) for i in locations]
    click.echo(u'The following configuration files are merged in order, if they exist:\n    {0}'.format(
        u'\n    '.join(u'{}   {}'.format(*i) for i in locations),
    ))

    banner('Confluence Stats')
    with api.context() as cf:
        try:
            user = cf.user()
            spaces = list(cf.getall('space'))
        except api.ERRORS as cause:
            # Just log and otherwise ignore any errors
            api.diagnostics(cause)
        else:
            click.echo(u'Confluence API [{u._info.server} / {u._info.sen}]'
                       u' accessed as {u.displayName} [{u.username}].'.format(u=user))
            click.echo(u'{} spaces found.'.format(len(spaces)))
            click.echo(u'\nMost recently created:')
            for space in itertools.islice(sorted(spaces, key=lambda i: i.id, reverse=True), 5):
                click.echo(u'    {:10} {:>15} {}'.format(space.type, space.key, space.name))

    banner('More Help')
    click.echo("Call '{} --help' to get a list of available commands & options.".format(app_name))
    click.echo("Call '{} «command» --help' to get help on a specific command.".format(app_name))
    click.echo("Call '{} --version' to get the above version information separately.".format(app_name))
    click.echo("Call '{} --license' to get licensing informatioon.".format(app_name))

    # click.echo('\ncontext = {}'.format(repr(vars(ctx))))
    # click.echo('\nparent = {}'.format(repr(vars(ctx.parent))))
