# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
""" Command line interface.
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
import logging

import click
from munch import Munch as Bunch

from . import config


# Default name of the app, and its app directory
__app_name__ = 'confluencer'
config.APP_NAME = __app_name__

# The `click` custom context settings
CONTEXT_SETTINGS = dict(
    obj=Bunch(cfg=None, quiet=False, verbose=False),  # namespace for custom stuff
    help_option_names=['-h', '--help'],
    auto_envvar_prefix=config.APP_NAME.upper().replace('-', '_'),
)


# `--license` option decorator
def license_option(*param_decls, **attrs):
    """``--license`` option that prints license information and then exits."""
    def decorator(func):
        "decorator inner wrapper"
        def callback(ctx, _dummy, value):
            "click option callback"
            if not value or ctx.resilient_parsing:
                return

            from . import __doc__ as license_text
            license_text = re.sub(r"``([^`]+?)``", lambda m: click.style(m.group(1), bold=True), license_text)
            click.echo(license_text)
            ctx.exit()

        attrs.setdefault('is_flag', True)
        attrs.setdefault('expose_value', False)
        attrs.setdefault('is_eager', True)
        attrs.setdefault('help', 'Show the license and exit.')
        attrs['callback'] = callback
        return click.option(*(param_decls or ('--license',)), **attrs)(func)

    return decorator


# Main command (root)
@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(message=config.VERSION_INFO)
@license_option()
@click.option('-q', '--quiet', is_flag=True, default=False, help='Be quiet (show only errors).')
@click.option('-v', '--verbose', is_flag=True, default=False, help='Create extra verbose output.')
@click.option('-c', '--config', "config_paths", metavar='FILE',
              multiple=True, type=click.Path(), help='Load given configuration file(s).')
@click.pass_context
def cli(ctx, quiet=False, verbose=False, config_paths=None):  # pylint: disable=unused-argument
    """'confluencer' command line tool."""
    config.cfg = config.Configuration.from_context(ctx, config_paths)
    ctx.obj.quiet = quiet
    ctx.obj.verbose = verbose

    log_level = logging.INFO
    if ctx.obj.quiet:
        log_level = logging.WARNING
    if ctx.obj.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)
    if ctx.obj.verbose:
        logging.getLogger("requests").setLevel(logging.DEBUG)
    else:
        logging.getLogger("requests").setLevel(logging.WARNING)
    ctx.obj.log = logging.getLogger(ctx.info_name)


def run():
    """Call main command."""
    cli.main(prog_name=config.APP_NAME)


# Import sub-commands to define them AFTER `cli` is defined
config.cli = cli
from . import commands as _  # noqa pylint: disable=unused-import, wrong-import-position

if __name__ == "__main__":  # imported via "python -m"?
    __package__ = 'confluencer'  # pylint: disable=redefined-builtin
    run()
